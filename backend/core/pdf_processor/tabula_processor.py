"""
Tabula 기반 PDF 표 추출 처리기

Java 기반의 강력한 표 추출 엔진 (tabula-java)를 사용하는 Python 래퍼
"""

import tabula
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging
import uuid
import time
import pandas as pd

from .base import PDFProcessorInterface, TableExtractionError, FileValidationError
from .pdf_utils import PDFUtils
from models.table_models import (
    TableData, CellData, GridData, TableMetadata, 
    PageTableData, ExtractionLibrary, CellType, TablePosition
)
from app.config import settings

logger = logging.getLogger(__name__)


class TabulaProcessor(PDFProcessorInterface):
    """Tabula 기반 PDF 처리기"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Tabula 처리기 초기화
        
        Args:
            options: Tabula 옵션
                - lattice: 격자 모드 사용 여부 (기본: True)
                - stream: 스트림 모드 사용 여부 (기본: False)
                - guess: 자동 테이블 감지 (기본: True)
                - multiple_tables: 다중 테이블 추출 (기본: True)
                - area: 추출 영역 지정
                - columns: 열 구분자 지정
                - pandas_options: DataFrame 옵션
        """
        default_options = {
            "lattice": True,         # 격자 모드 (선이 있는 테이블)
            "stream": False,         # 스트림 모드 (선이 없는 테이블)
            "guess": True,           # 자동 테이블 감지
            "multiple_tables": True, # 다중 테이블 추출
            "silent": True,          # 에러 메시지 억제
            "pandas_options": {      # DataFrame 변환 옵션
                "header": None,
                "encoding": "utf-8"
            }
        }
        
        if options:
            default_options.update(options)
        
        super().__init__(default_options)
        self.logger.info("Tabula 처리기 초기화 완료")
    
    def get_library_name(self) -> str:
        return "tabula"
    
    def get_library_version(self) -> str:
        try:
            import tabula
            return tabula.__version__
        except AttributeError:
            return "unknown"
    
    def get_capabilities(self) -> List[str]:
        return [
            "table_extraction",
            "java_engine",
            "lattice_mode",
            "stream_mode",
            "auto_detection",
            "area_selection",
            "multiple_tables"
        ]
    
    def validate_file(self, file_path: Path) -> bool:
        """PDF 파일 유효성 검증"""
        # 기본 검증 수행
        if not PDFUtils.validate_pdf_file_basic(file_path):
            return False
        
        try:
            # Tabula 특화 검증: 실제로 파일을 읽어서 테이블 추출 시도
            test_result = tabula.read_pdf(
                str(file_path), 
                pages=1, 
                silent=True,
                multiple_tables=False
            )
            return True  # 오류 없으면 유효
                
        except Exception as e:
            self.logger.warning(f"Tabula 파일 검증 실패: {e}")
            return False
    
    def get_page_count(self, file_path: Path) -> int:
        """PDF 총 페이지 수 반환"""
        return PDFUtils.get_page_count(file_path)
    
    def extract_tables(self, file_path: Path) -> List[TableData]:
        """모든 페이지에서 테이블 추출"""
        if not self.validate_file(file_path):
            raise FileValidationError("유효하지 않은 PDF 파일", "tabula", str(file_path))
        
        all_tables = []
        
        try:
            start_time = time.time()
            
            # Tabula 옵션 설정
            extract_options = self._prepare_extraction_options()
            
            # 모든 페이지에서 테이블 추출
            dataframes = tabula.read_pdf(
                str(file_path), 
                pages='all',
                **extract_options
            )
            
            # DataFrame이 단일 객체인 경우 리스트로 변환
            if isinstance(dataframes, pd.DataFrame):
                dataframes = [dataframes]
            elif not isinstance(dataframes, list):
                # 예상치 못한 형태인 경우 빈 리스트로 처리
                dataframes = []
            
            # 각 DataFrame을 TableData로 변환
            for df_idx, df in enumerate(dataframes):
                try:
                    if isinstance(df, pd.DataFrame):
                        table_data = self._process_dataframe(df, df_idx)
                        if table_data:
                            all_tables.append(table_data)
                except Exception as e:
                    self.logger.warning(f"DataFrame {df_idx} 처리 실패: {e}")
                    continue
            
            processing_time = time.time() - start_time
            self.logger.info(f"총 {len(all_tables)}개 테이블 추출 완료 ({processing_time:.3f}초)")
            return all_tables
            
        except Exception as e:
            raise TableExtractionError(f"테이블 추출 실패: {e}", "tabula", str(file_path))
    
    def extract_tables_from_page(self, file_path: Path, page_number: int) -> List[TableData]:
        """특정 페이지에서 테이블 추출"""
        if not self.validate_file(file_path):
            raise FileValidationError("유효하지 않은 PDF 파일", "tabula", str(file_path))
        
        try:
            start_time = time.time()
            
            # Tabula 옵션 설정
            extract_options = self._prepare_extraction_options()
            
            # 특정 페이지만 처리
            dataframes = tabula.read_pdf(
                str(file_path),
                pages=page_number,
                **extract_options
            )
            
            # DataFrame이 단일 객체인 경우 리스트로 변환
            if isinstance(dataframes, pd.DataFrame):
                dataframes = [dataframes]
            elif not isinstance(dataframes, list):
                dataframes = []
            
            page_tables = []
            for df_idx, df in enumerate(dataframes):
                try:
                    if isinstance(df, pd.DataFrame):
                        table_data = self._process_dataframe(df, df_idx, page_number)
                        if table_data:
                            page_tables.append(table_data)
                except Exception as e:
                    self.logger.warning(f"페이지 {page_number} DataFrame {df_idx} 처리 실패: {e}")
                    continue
            
            processing_time = time.time() - start_time
            self.logger.debug(f"페이지 {page_number}: {len(page_tables)}개 테이블, {processing_time:.3f}초")
            
            return page_tables
                
        except Exception as e:
            raise TableExtractionError(f"페이지 {page_number} 테이블 추출 실패: {e}", "tabula", str(file_path))
    
    def _prepare_extraction_options(self) -> Dict[str, Any]:
        """Tabula 추출 옵션 준비"""
        options = self.options.copy()
        
        # pandas_options는 제거 (tabula.read_pdf는 pandas 옵션을 직접 지원하지 않음)
        options.pop('pandas_options', {})
        
        # tabula.read_pdf에 직접 전달할 옵션만 선택
        valid_options = {
            'lattice', 'stream', 'guess', 'multiple_tables', 'area', 
            'columns', 'silent', 'encoding', 'java_options'
        }
        
        extract_options = {k: v for k, v in options.items() if k in valid_options}
        
        return extract_options
    
    def _process_dataframe(self, df: pd.DataFrame, table_index: int, page_number: Optional[int] = None) -> Optional[TableData]:
        """DataFrame을 TableData로 변환"""
        try:
            if df.empty:
                return None
            
            # 페이지 번호 추정 (Tabula는 페이지 정보를 제공하지 않음)
            estimated_page = page_number if page_number else 1
            
            # DataFrame을 리스트로 변환
            raw_data = df.values.tolist()
            
            # 컬럼명도 데이터에 포함 (헤더로 사용 가능)
            if not df.columns.empty and df.columns[0] is not None:
                # 의미 있는 컬럼명이 있는 경우
                if not all(str(col).startswith('Unnamed') for col in df.columns):
                    column_names = [str(col) for col in df.columns]
                    raw_data.insert(0, column_names)
            
            # 데이터 정리
            cleaned_data = self.clean_table_data(raw_data)
            
            if not cleaned_data:
                return None
            
            # 헤더 감지
            has_headers, headers = self.detect_headers(cleaned_data)
            
            if has_headers:
                data_rows = cleaned_data[1:]
                header_list = headers or []
            else:
                data_rows = cleaned_data
                header_list = []
            
            # 그리드 데이터 생성
            grid_data = self.convert_to_grid_data(data_rows, header_list)
            
            # 테이블 메타데이터 생성
            metadata = self._create_tabula_metadata(df)
            
            # 테이블 ID 생성
            table_id = f"page_{estimated_page}_table_{table_index + 1}_{str(uuid.uuid4())[:8]}"
            
            return TableData(
                table_id=table_id,
                page_number=estimated_page,
                headers=header_list,
                rows=data_rows,
                grid_data=grid_data,
                metadata=metadata,
                extraction_library=ExtractionLibrary.TABULA
            )
            
        except Exception as e:
            self.logger.error(f"DataFrame 처리 중 오류: {e}")
            return None
    
    def _create_tabula_metadata(self, df: pd.DataFrame) -> TableMetadata:
        """Tabula 테이블 메타데이터 생성"""
        try:
            # 기본 신뢰도 계산 (행/열 수 기반)
            confidence = settings.table_confidence_base  # 기본값
            
            # DataFrame 크기 기반 신뢰도 조정
            if df.shape[0] >= settings.table_min_rows_bonus:  # 3행 이상
                confidence += 0.1
            if df.shape[1] >= settings.table_min_cols_bonus:  # 2열 이상
                confidence += 0.1
            
            # 빈 셀 비율 계산
            total_cells = df.shape[0] * df.shape[1]
            empty_cells = df.isnull().sum().sum()
            empty_ratio = empty_cells / total_cells if total_cells > 0 else 0
            
            # 빈 셀이 적을수록 신뢰도 증가
            if empty_ratio < 0.1:
                confidence += 0.2
            elif empty_ratio < 0.3:
                confidence += 0.1
            
            return TableMetadata(
                confidence=min(1.0, confidence),
                position=TablePosition.MIDDLE,  # Tabula는 위치 정보 제공하지 않음
                bbox=None,
                extraction_method=f"tabula_{'lattice' if self.options.get('lattice') else 'stream'}",
                processing_time=0.0,
                empty_cell_ratio=empty_ratio,
                text_alignment_score=0.0
            )
            
        except Exception as e:
            self.logger.warning(f"Tabula 메타데이터 생성 실패: {e}")
            return TableMetadata(
                confidence=0.5,
                position=None,
                bbox=None,
                extraction_method=None,
                processing_time=0.0,
                empty_cell_ratio=0.0,
                text_alignment_score=0.0
            )
    
    def extract_with_area(self, file_path: Path, page_number: int, area: List[float]) -> List[TableData]:
        """지정된 영역에서 테이블 추출
        
        Args:
            file_path: PDF 파일 경로
            page_number: 페이지 번호
            area: 영역 좌표 [top, left, bottom, right] (포인트 단위)
        """
        try:
            extract_options = self._prepare_extraction_options()
            extract_options['area'] = area
            
            dataframes = tabula.read_pdf(
                str(file_path),
                pages=page_number,
                **extract_options
            )
            
            if isinstance(dataframes, pd.DataFrame):
                dataframes = [dataframes]
            elif not isinstance(dataframes, list):
                dataframes = []
            
            page_tables = []
            for df_idx, df in enumerate(dataframes):
                if isinstance(df, pd.DataFrame):
                    table_data = self._process_dataframe(df, df_idx, page_number)
                    if table_data:
                        page_tables.append(table_data)
            
            return page_tables
            
        except Exception as e:
            raise TableExtractionError(f"영역 지정 테이블 추출 실패: {e}", "tabula", str(file_path))
    
    def extract_with_columns(self, file_path: Path, page_number: int, columns: List[float]) -> List[TableData]:
        """열 구분자를 지정하여 테이블 추출
        
        Args:
            file_path: PDF 파일 경로
            page_number: 페이지 번호
            columns: 열 구분자 X 좌표 리스트
        """
        try:
            extract_options = self._prepare_extraction_options()
            extract_options['columns'] = columns
            extract_options['stream'] = True  # 열 구분자 사용 시 스트림 모드
            extract_options['lattice'] = False
            
            dataframes = tabula.read_pdf(
                str(file_path),
                pages=page_number,
                **extract_options
            )
            
            if isinstance(dataframes, pd.DataFrame):
                dataframes = [dataframes]
            elif not isinstance(dataframes, list):
                dataframes = []
            
            page_tables = []
            for df_idx, df in enumerate(dataframes):
                if isinstance(df, pd.DataFrame):
                    table_data = self._process_dataframe(df, df_idx, page_number)
                    if table_data:
                        page_tables.append(table_data)
            
            return page_tables
            
        except Exception as e:
            raise TableExtractionError(f"열 구분자 테이블 추출 실패: {e}", "tabula", str(file_path))
    
    def convert_to_csv(self, file_path: Path, output_dir: Path, pages: Union[str, int] = 'all') -> List[Path]:
        """PDF 테이블을 CSV 파일로 변환
        
        Args:
            file_path: PDF 파일 경로
            output_dir: 출력 디렉토리
            pages: 처리할 페이지 ('all' 또는 페이지 번호)
            
        Returns:
            List[Path]: 생성된 CSV 파일 경로 목록
        """
        try:
            output_dir.mkdir(exist_ok=True, parents=True)
            
            extract_options = self._prepare_extraction_options()
            
            # CSV로 직접 변환
            output_path = output_dir / f"{file_path.stem}_tables.csv"
            
            tabula.convert_into(
                str(file_path),
                str(output_path),
                pages=pages,
                **extract_options
            )
            
            return [output_path]
            
        except Exception as e:
            self.logger.error(f"CSV 변환 실패: {e}")
            return []
    
    def get_java_version(self) -> str:
        """Java 버전 확인 (Tabula는 Java 기반)"""
        try:
            import subprocess
            result = subprocess.run(['java', '-version'], capture_output=True, text=True)
            version_output = result.stderr.split('\n')[0]
            return version_output
        except Exception:
            return "Java version unknown"
    
    def extract_with_template(self, file_path: Path, template_path: Path) -> List[TableData]:
        """템플릿 파일을 사용한 테이블 추출 (Tabula의 고급 기능)
        
        Args:
            file_path: PDF 파일 경로
            template_path: 템플릿 파일 경로 (JSON)
        """
        try:
            # 템플릿 기반 추출은 tabula-py의 고급 기능
            # 실제 구현은 Java tabula의 template 기능을 활용
            
            extract_options = self._prepare_extraction_options()
            
            # 템플릿 파일이 있으면 적용
            if template_path.exists():
                # 템플릿 기반 추출 로직 구현
                # (실제로는 tabula command line tool 사용 필요)
                pass
            
            # 일반 추출로 폴백
            return self.extract_tables(file_path)
            
        except Exception as e:
            self.logger.error(f"템플릿 기반 추출 실패: {e}")
            return []
