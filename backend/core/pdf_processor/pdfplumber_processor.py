"""
pdfplumber 기반 PDF 표 추출 처리기

텍스트 기반 표 추출에 특화된 라이브러리로, 한국어 지원이 우수
"""

import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import uuid
import time

from .base import PDFProcessorInterface, TableExtractionError, FileValidationError
from .pdf_utils import PDFUtils
from models.table_models import (
    TableData, CellData, GridData, TableMetadata, 
    PageTableData, ExtractionLibrary, CellType, TablePosition
)
from app.config import settings

logger = logging.getLogger(__name__)


class PDFPlumberProcessor(PDFProcessorInterface):
    """pdfplumber 기반 PDF 처리기"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        pdfplumber 처리기 초기화
        
        Args:
            options: pdfplumber 옵션
                - table_settings: 테이블 감지 설정
                - text_extraction: 텍스트 추출 설정
                - edge_min_length: 최소 선 길이 (기본: 3)
                - intersection_tolerance: 교차점 허용 오차 (기본: 1)
        """
        default_options = {
            "table_settings": {
                "vertical_strategy": "lines_strict",
                "horizontal_strategy": "lines_strict",
                "edge_min_length": settings.pdfplumber_edge_min_length,
                "intersection_tolerance": settings.pdfplumber_intersection_tolerance,
                "intersection_x_tolerance": settings.pdfplumber_intersection_tolerance,
                "intersection_y_tolerance": settings.pdfplumber_intersection_tolerance
            },
            "text_extraction": {
                "x_tolerance": settings.pdfplumber_intersection_tolerance,
                "y_tolerance": settings.pdfplumber_intersection_tolerance
            }
        }
        
        if options:
            default_options.update(options)
        
        super().__init__(default_options)
        self.logger.info("PDFPlumber 처리기 초기화 완료")
    
    def get_library_name(self) -> str:
        return "pdfplumber"
    
    def get_library_version(self) -> str:
        try:
            return pdfplumber.__version__
        except AttributeError:
            return "unknown"
    
    def get_capabilities(self) -> List[str]:
        return [
            "table_extraction",
            "text_extraction", 
            "line_detection",
            "korean_text_support",
            "complex_layouts"
        ]
    
    def validate_file(self, file_path: Path) -> bool:
        """PDF 파일 유효성 검증"""
        # 기본 검증 수행
        if not PDFUtils.validate_pdf_file_basic(file_path):
            return False
        
        try:
            # pdfplumber 특화 검증: 실제로 파일을 열어서 페이지 확인
            with pdfplumber.open(file_path) as pdf:
                # 최소한 1페이지는 있어야 함
                return len(pdf.pages) > 0
                
        except Exception as e:
            self.logger.warning(f"pdfplumber 파일 검증 실패: {e}")
            return False
    
    def get_page_count(self, file_path: Path) -> int:
        """PDF 총 페이지 수 반환"""
        return PDFUtils.get_page_count(file_path)
    
    def extract_tables(self, file_path: Path) -> List[TableData]:
        """모든 페이지에서 테이블 추출"""
        if not self.validate_file(file_path):
            raise FileValidationError("유효하지 않은 PDF 파일", "pdfplumber", str(file_path))
        
        all_tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = self._extract_tables_from_page_object(page, page_num)
                    all_tables.extend(page_tables)
                    
            self.logger.info(f"총 {len(all_tables)}개 테이블 추출 완료")
            return all_tables
            
        except Exception as e:
            raise TableExtractionError(f"테이블 추출 실패: {e}", "pdfplumber", str(file_path))
    
    def extract_tables_from_page(self, file_path: Path, page_number: int) -> List[TableData]:
        """특정 페이지에서 테이블 추출"""
        if not self.validate_file(file_path):
            raise FileValidationError("유효하지 않은 PDF 파일", "pdfplumber", str(file_path))
        
        try:
            with pdfplumber.open(file_path) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    raise TableExtractionError(
                        f"잘못된 페이지 번호: {page_number} (총 {len(pdf.pages)}페이지)",
                        "pdfplumber", str(file_path)
                    )
                
                page = pdf.pages[page_number - 1]
                return self._extract_tables_from_page_object(page, page_number)
                
        except Exception as e:
            raise TableExtractionError(f"페이지 {page_number} 테이블 추출 실패: {e}", "pdfplumber", str(file_path))
    
    def _extract_tables_from_page_object(self, page, page_number: int) -> List[TableData]:
        """페이지 객체에서 테이블 추출"""
        start_time = time.time()
        tables = []
        
        try:
            # pdfplumber의 테이블 추출 설정 적용
            table_settings = self.options.get("table_settings", {})
            
            # 페이지에서 테이블 찾기
            page_tables = page.find_tables(table_settings=table_settings)
            
            for table_idx, table in enumerate(page_tables):
                try:
                    table_data = self._process_table(table, page_number, table_idx)
                    if table_data:
                        tables.append(table_data)
                except Exception as e:
                    self.logger.warning(f"페이지 {page_number} 테이블 {table_idx} 처리 실패: {e}")
                    continue
            
            processing_time = time.time() - start_time
            self.logger.debug(f"페이지 {page_number}: {len(tables)}개 테이블, {processing_time:.3f}초")
            
        except Exception as e:
            self.logger.error(f"페이지 {page_number} 처리 실패: {e}")
        
        return tables
    
    def _process_table(self, table, page_number: int, table_index: int) -> Optional[TableData]:
        """개별 테이블 처리"""
        try:
            # 테이블 데이터 추출
            raw_data = table.extract()
            
            if not raw_data or len(raw_data) == 0:
                return None
            
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
            metadata = self._create_table_metadata(table, len(cleaned_data))
            
            # 테이블 ID 생성
            table_id = f"page_{page_number}_table_{table_index + 1}_{str(uuid.uuid4())[:8]}"
            
            return TableData(
                table_id=table_id,
                page_number=page_number,
                headers=header_list,
                rows=data_rows,
                grid_data=grid_data,
                metadata=metadata,
                extraction_library=ExtractionLibrary.PDFPLUMBER
            )
            
        except Exception as e:
            self.logger.error(f"테이블 처리 중 오류: {e}")
            return None
    
    def _create_table_metadata(self, table, row_count: int) -> TableMetadata:
        """테이블 메타데이터 생성"""
        try:
            # 경계 상자 정보
            bbox = None
            if hasattr(table, 'bbox'):
                bbox = list(table.bbox)
            
            # 위치 추정 (Y 좌표 기준)
            position = TablePosition.MIDDLE
            if bbox:
                y_center = (bbox[1] + bbox[3]) / 2
                if y_center > 600:  # 상단
                    position = TablePosition.TOP
                elif y_center < 200:  # 하단
                    position = TablePosition.BOTTOM
            
            # 신뢰도 계산 (휴리스틱)
            confidence = self._calculate_confidence(table, row_count)
            
            return TableMetadata(
                confidence=confidence,
                position=position,
                bbox=bbox,
                extraction_method="pdfplumber_lines_strict",
                processing_time=0.0,
                empty_cell_ratio=0.0,
                text_alignment_score=0.0
            )
            
        except Exception as e:
            self.logger.warning(f"메타데이터 생성 실패: {e}")
            return TableMetadata(
                confidence=0.5,
                position=None,
                bbox=None,
                extraction_method=None,
                processing_time=0.0,
                empty_cell_ratio=0.0,
                text_alignment_score=0.0
            )
    
    def _calculate_confidence(self, table, row_count: int) -> float:
        """테이블 추출 신뢰도 계산"""
        try:
            confidence = 0.5  # 기본값
            
            # 행 수가 많을수록 신뢰도 증가
            if row_count >= 3:
                confidence += 0.2
            if row_count >= 5:
                confidence += 0.1
            
            # 테이블에 명확한 경계가 있으면 신뢰도 증가
            if hasattr(table, 'cells') and table.cells:
                confidence += 0.2
            
            return min(1.0, confidence)
            
        except Exception:
            return 0.5
    
    def extract_text_from_page(self, file_path: Path, page_number: int) -> str:
        """특정 페이지에서 텍스트 추출 (추가 기능)"""
        try:
            with pdfplumber.open(file_path) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    return ""
                
                page = pdf.pages[page_number - 1]
                text_settings = self.options.get("text_extraction", {})
                return page.extract_text(**text_settings) or ""
                
        except Exception as e:
            self.logger.error(f"텍스트 추출 실패: {e}")
            return ""
    
    def get_page_dimensions(self, file_path: Path, page_number: int) -> Optional[tuple]:
        """페이지 크기 반환 (width, height)"""
        try:
            with pdfplumber.open(file_path) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    return None
                
                page = pdf.pages[page_number - 1]
                return (page.width, page.height)
                
        except Exception as e:
            self.logger.error(f"페이지 크기 확인 실패: {e}")
            return None
    
    def extract_detailed_page_data(self, file_path: Path, page_number: int) -> Optional[PageTableData]:
        """페이지의 상세 데이터 추출 (테이블 + 텍스트 + 메타데이터)"""
        try:
            # 테이블 추출
            tables = self.extract_tables_from_page(file_path, page_number)
            
            # 페이지 텍스트 추출
            text_content = self.extract_text_from_page(file_path, page_number)
            
            # 페이지 크기
            dimensions = self.get_page_dimensions(file_path, page_number)
            page_width, page_height = dimensions if dimensions else (None, None)
            
            return PageTableData(
                page_number=page_number,
                tables=tables,
                page_width=page_width,
                page_height=page_height,
                text_content=text_content
            )
            
        except Exception as e:
            self.logger.error(f"상세 페이지 데이터 추출 실패: {e}")
            return None
