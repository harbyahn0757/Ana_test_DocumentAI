"""
Camelot 기반 PDF 표 추출 처리기

격자 기반 정확한 표 구조 인식에 특화된 라이브러리
"""

import camelot
from pathlib import Path
from typing import List, Dict, Any, Optional
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


class CamelotProcessor(PDFProcessorInterface):
    """Camelot 기반 PDF 처리기"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Camelot 처리기 초기화
        
        Args:
            options: Camelot 옵션
                - flavor: 'lattice' 또는 'stream' (기본: 'lattice')
                - table_areas: 테이블 영역 지정
                - columns: 열 구분선 지정 (stream 모드)
                - edge_tol: 선 감지 허용 오차 (기본: 50)
                - row_tol: 행 감지 허용 오차 (기본: 2)
                - column_tol: 열 감지 허용 오차 (기본: 0)
        """
        default_options = {
            "flavor": "lattice",  # 격자 기반 추출
            "edge_tol": settings.camelot_edge_tol,      # 선 감지 허용 오차
            "row_tol": settings.camelot_row_tol,        # 행 감지 허용 오차
            "column_tol": settings.camelot_column_tol,  # 열 감지 허용 오차
            "split_text": False,  # 텍스트 분할 여부
            "flag_size": True,   # 작은 테이블 제외
            "strip_text": '\n'   # 제거할 문자
        }
        
        if options:
            default_options.update(options)
        
        super().__init__(default_options)
        self.logger.info("Camelot 처리기 초기화 완료")
    
    def get_library_name(self) -> str:
        return "camelot"
    
    def get_library_version(self) -> str:
        try:
            import camelot
            return getattr(camelot, '__version__', "unknown")
        except (AttributeError, ImportError):
            return "unknown"
    
    def get_capabilities(self) -> List[str]:
        return [
            "table_extraction",
            "lattice_detection",
            "stream_parsing", 
            "high_accuracy",
            "complex_tables",
            "table_areas_support"
        ]
    
    def validate_file(self, file_path: Path) -> bool:
        """PDF 파일 유효성 검증"""
        # 기본 검증 수행
        if not PDFUtils.validate_pdf_file_basic(file_path):
            return False
        
        try:
            # Camelot 특화 검증: 실제로 파일을 열어서 테이블 추출 시도
            test_tables = camelot.read_pdf(str(file_path), pages='1', flavor='lattice')
            return True  # 오류 없으면 유효
                
        except Exception as e:
            self.logger.warning(f"Camelot 파일 검증 실패: {e}")
            return False
    
    def get_page_count(self, file_path: Path) -> int:
        """PDF 총 페이지 수 반환"""
        return PDFUtils.get_page_count(file_path)
    
    def extract_tables(self, file_path: Path) -> List[TableData]:
        """모든 페이지에서 테이블 추출"""
        if not self.validate_file(file_path):
            raise FileValidationError("유효하지 않은 PDF 파일", "camelot", str(file_path))
        
        all_tables = []
        
        try:
            # 모든 페이지에서 테이블 추출
            start_time = time.time()
            
            # Camelot 옵션 설정
            extract_options = self._prepare_extraction_options()
            
            # 모든 페이지 처리
            tables = camelot.read_pdf(str(file_path), pages='all', **extract_options)
            
            for table_idx, table in enumerate(tables):
                try:
                    table_data = self._process_camelot_table(table, table_idx)
                    if table_data:
                        all_tables.append(table_data)
                except Exception as e:
                    self.logger.warning(f"테이블 {table_idx} 처리 실패: {e}")
                    continue
            
            processing_time = time.time() - start_time
            self.logger.info(f"총 {len(all_tables)}개 테이블 추출 완료 ({processing_time:.3f}초)")
            return all_tables
            
        except Exception as e:
            raise TableExtractionError(f"테이블 추출 실패: {e}", "camelot", str(file_path))
    
    def extract_tables_from_page(self, file_path: Path, page_number: int) -> List[TableData]:
        """특정 페이지에서 테이블 추출"""
        if not self.validate_file(file_path):
            raise FileValidationError("유효하지 않은 PDF 파일", "camelot", str(file_path))
        
        try:
            start_time = time.time()
            
            # Camelot 옵션 설정
            extract_options = self._prepare_extraction_options()
            
            # 특정 페이지만 처리
            tables = camelot.read_pdf(str(file_path), pages=str(page_number), **extract_options)
            
            page_tables = []
            for table_idx, table in enumerate(tables):
                try:
                    table_data = self._process_camelot_table(table, table_idx, page_number)
                    if table_data:
                        page_tables.append(table_data)
                except Exception as e:
                    self.logger.warning(f"페이지 {page_number} 테이블 {table_idx} 처리 실패: {e}")
                    continue
            
            processing_time = time.time() - start_time
            self.logger.debug(f"페이지 {page_number}: {len(page_tables)}개 테이블, {processing_time:.3f}초")
            
            return page_tables
                
        except Exception as e:
            raise TableExtractionError(f"페이지 {page_number} 테이블 추출 실패: {e}", "camelot", str(file_path))
    
    def _prepare_extraction_options(self) -> Dict[str, Any]:
        """Camelot 추출 옵션 준비"""
        options = self.options.copy()
        
        # 불필요한 옵션 제거 (내부 사용용)
        internal_options = {'table_areas', 'columns'}
        extract_options = {k: v for k, v in options.items() if k not in internal_options}
        
        # lattice flavor에서는 tolerance 옵션들을 제거
        if extract_options.get('flavor') == 'lattice':
            tolerance_options = {'column_tol', 'edge_tol', 'row_tol'}
            extract_options = {k: v for k, v in extract_options.items() if k not in tolerance_options}
        
        return extract_options
    
    def _process_camelot_table(self, table, table_index: int, page_number: Optional[int] = None) -> Optional[TableData]:
        """Camelot 테이블 객체 처리"""
        try:
            # DataFrame을 리스트로 변환
            df = table.df
            
            if df.empty:
                return None
            
            # 실제 페이지 번호 확인
            actual_page = page_number if page_number else table.page
            
            # 데이터 정리
            raw_data = df.values.tolist()
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
            metadata = self._create_camelot_metadata(table)
            
            # 테이블 ID 생성
            table_id = f"page_{actual_page}_table_{table_index + 1}_{str(uuid.uuid4())[:8]}"
            
            return TableData(
                table_id=table_id,
                page_number=actual_page,
                headers=header_list,
                rows=data_rows,
                grid_data=grid_data,
                metadata=metadata,
                extraction_library=ExtractionLibrary.CAMELOT
            )
            
        except Exception as e:
            self.logger.error(f"Camelot 테이블 처리 중 오류: {e}")
            return None
    
    def _create_camelot_metadata(self, table) -> TableMetadata:
        """Camelot 테이블 메타데이터 생성"""
        try:
            # Camelot의 정확도 점수 사용
            confidence = getattr(table, 'accuracy', 0.0) / 100.0  # 0-100을 0-1로 변환
            
            # 경계 상자 정보
            bbox = None
            if hasattr(table, '_bbox'):
                bbox = list(table._bbox)
            
            # 위치 추정
            position = TablePosition.MIDDLE
            if bbox:
                y_center = (bbox[1] + bbox[3]) / 2
                if y_center > 600:
                    position = TablePosition.TOP
                elif y_center < 200:
                    position = TablePosition.BOTTOM
            
            return TableMetadata(
                confidence=min(1.0, max(0.0, confidence)),
                position=position,
                bbox=bbox,
                extraction_method=f"camelot_{self.options.get('flavor', 'lattice')}",
                processing_time=0.0,
                empty_cell_ratio=0.0,
                text_alignment_score=getattr(table, 'whitespace', 0.0) / 100.0
            )
            
        except Exception as e:
            self.logger.warning(f"Camelot 메타데이터 생성 실패: {e}")
            return TableMetadata(
                confidence=0.5,
                position=None,
                bbox=None,
                extraction_method=None,
                processing_time=0.0,
                empty_cell_ratio=0.0,
                text_alignment_score=0.0
            )
    
    def extract_with_areas(self, file_path: Path, page_number: int, table_areas: List[str]) -> List[TableData]:
        """지정된 영역에서 테이블 추출
        
        Args:
            file_path: PDF 파일 경로
            page_number: 페이지 번호
            table_areas: 테이블 영역 좌표 ["x1,y1,x2,y2"]
        """
        try:
            extract_options = self._prepare_extraction_options()
            extract_options['table_areas'] = table_areas
            
            tables = camelot.read_pdf(
                str(file_path), 
                pages=str(page_number), 
                **extract_options
            )
            
            page_tables = []
            for table_idx, table in enumerate(tables):
                table_data = self._process_camelot_table(table, table_idx, page_number)
                if table_data:
                    page_tables.append(table_data)
            
            return page_tables
            
        except Exception as e:
            raise TableExtractionError(f"영역 지정 테이블 추출 실패: {e}", "camelot", str(file_path))
    
    def extract_with_stream_mode(self, file_path: Path, page_number: int, columns: Optional[List[str]] = None) -> List[TableData]:
        """Stream 모드로 테이블 추출 (선이 없는 테이블용)
        
        Args:
            file_path: PDF 파일 경로
            page_number: 페이지 번호 
            columns: 열 구분선 좌표 (선택사항)
        """
        try:
            extract_options = self._prepare_extraction_options()
            extract_options['flavor'] = 'stream'
            
            if columns:
                extract_options['columns'] = columns
            
            tables = camelot.read_pdf(
                str(file_path),
                pages=str(page_number),
                **extract_options
            )
            
            page_tables = []
            for table_idx, table in enumerate(tables):
                table_data = self._process_camelot_table(table, table_idx, page_number)
                if table_data:
                    page_tables.append(table_data)
            
            return page_tables
            
        except Exception as e:
            raise TableExtractionError(f"Stream 모드 테이블 추출 실패: {e}", "camelot", str(file_path))
    
    def get_extraction_report(self, file_path: Path, page_number: int) -> Dict[str, Any]:
        """추출 결과 리포트 생성"""
        try:
            extract_options = self._prepare_extraction_options()
            tables = camelot.read_pdf(str(file_path), pages=str(page_number), **extract_options)
            
            report = {
                "page_number": page_number,
                "total_tables": len(tables),
                "extraction_method": self.options.get('flavor', 'lattice'),
                "tables_info": []
            }
            
            for idx, table in enumerate(tables):
                table_info = {
                    "table_index": idx,
                    "accuracy": getattr(table, 'accuracy', 0.0),
                    "whitespace": getattr(table, 'whitespace', 0.0),
                    "order": getattr(table, 'order', idx),
                    "page": getattr(table, 'page', page_number),
                    "shape": table.df.shape
                }
                report["tables_info"].append(table_info)
            
            return report
            
        except Exception as e:
            self.logger.error(f"추출 리포트 생성 실패: {e}")
            return {"error": str(e)}
    
    def save_debug_images(self, file_path: Path, page_number: int, output_dir: Path) -> bool:
        """디버깅용 이미지 저장 (테이블 감지 결과 시각화)"""
        try:
            output_dir.mkdir(exist_ok=True, parents=True)
            
            extract_options = self._prepare_extraction_options()
            tables = camelot.read_pdf(str(file_path), pages=str(page_number), **extract_options)
            
            # 각 테이블에 대해 디버깅 이미지 저장
            for idx, table in enumerate(tables):
                try:
                    output_file = output_dir / f"page_{page_number}_table_{idx}.png"
                    plot_result = camelot.plot(table, kind='contour')
                    if plot_result is not None:
                        plot_result.savefig(str(output_file))
                        self.logger.debug(f"디버깅 이미지 저장: {output_file}")
                except Exception as e:
                    self.logger.warning(f"테이블 {idx} 이미지 저장 실패: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"디버깅 이미지 저장 실패: {e}")
            return False
