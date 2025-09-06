"""
PDF 처리기 기본 인터페이스

모든 PDF 처리 라이브러리가 구현해야 하는 공통 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from models.table_models import TableData, CellData, GridData, CellType

logger = logging.getLogger(__name__)


class PDFProcessorInterface(ABC):
    """PDF 처리기 인터페이스"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """PDF 처리기 초기화
        
        Args:
            options (Optional[Dict[str, Any]]): 라이브러리별 옵션 설정
        """
        self.options = options or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def extract_tables(self, file_path: Path) -> List[TableData]:
        """PDF 파일에서 테이블 추출
        
        Args:
            file_path (Path): PDF 파일 경로
            
        Returns:
            List[TableData]: 추출된 테이블 목록
            
        Raises:
            PDFProcessingError: 처리 중 오류 발생 시
        """
        pass
    
    @abstractmethod
    def extract_tables_from_page(self, file_path: Path, page_number: int) -> List[TableData]:
        """
        특정 페이지에서 테이블 추출
        
        Args:
            file_path: PDF 파일 경로
            page_number: 페이지 번호 (1부터 시작)
            
        Returns:
            List[TableData]: 추출된 테이블 목록
        """
        pass
    
    @abstractmethod
    def get_page_count(self, file_path: Path) -> int:
        """
        PDF의 총 페이지 수 반환
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            int: 총 페이지 수
        """
        pass
    
    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """
        PDF 파일 유효성 검증
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            bool: 유효한 PDF 파일 여부
        """
        pass
    
    def get_library_info(self) -> Dict[str, Any]:
        """
        라이브러리 정보 반환
        
        Returns:
            Dict[str, Any]: 라이브러리 메타데이터
        """
        return {
            "name": self.__class__.__name__,
            "library": self.get_library_name(),
            "version": self.get_library_version(),
            "capabilities": self.get_capabilities(),
            "options": self.options
        }
    
    @abstractmethod
    def get_library_name(self) -> str:
        """라이브러리 이름 반환"""
        pass
    
    @abstractmethod
    def get_library_version(self) -> str:
        """라이브러리 버전 반환"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """라이브러리 기능 목록 반환"""
        return [
            "table_extraction",
            "multi_page_support",
            "text_extraction"
        ]
    
    def convert_to_grid_data(self, table_rows: List[List[str]], headers: Optional[List[str]] = None) -> GridData:
        """
        테이블 데이터를 그리드 형태로 변환
        
        Args:
            table_rows: 테이블 행 데이터
            headers: 헤더 행 (선택사항)
            
        Returns:
            GridData: 그리드 형태 데이터
        """
        cells = []
        all_rows = []
        
        # 헤더가 있으면 추가
        if headers:
            all_rows.append(headers)
        
        # 데이터 행들 추가
        all_rows.extend(table_rows)
        
        # 각 셀을 CellData로 변환
        for row_idx, row in enumerate(all_rows):
            for col_idx, cell_content in enumerate(row):
                cell_type = CellType.HEADER if headers and row_idx == 0 else CellType.DATA
                
                cell = CellData(
                    row=row_idx,
                    col=col_idx,
                    content=str(cell_content).strip(),
                    type=cell_type
                )
                cells.append(cell)
        
        return GridData(
            rows=len(all_rows),
            cols=max(len(row) for row in all_rows) if all_rows else 0,
            cells=cells
        )
    
    def clean_table_data(self, raw_data: List[List[str]]) -> List[List[str]]:
        """
        원시 테이블 데이터 정리
        
        Args:
            raw_data: 원시 테이블 데이터
            
        Returns:
            List[List[str]]: 정리된 테이블 데이터
        """
        cleaned_data = []
        
        for row in raw_data:
            # 빈 행 제거
            if not any(cell.strip() for cell in row if cell):
                continue
            
            # 각 셀 데이터 정리
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_cell = ""
                else:
                    # 불필요한 공백 제거 및 개행 문자 처리
                    cleaned_cell = str(cell).strip().replace('\n', ' ').replace('\r', '')
                cleaned_row.append(cleaned_cell)
            
            cleaned_data.append(cleaned_row)
        
        return cleaned_data
    
    def detect_headers(self, table_data: List[List[str]]) -> Tuple[bool, Optional[List[str]]]:
        """
        테이블에서 헤더 행 감지
        
        Args:
            table_data: 테이블 데이터
            
        Returns:
            Tuple[bool, Optional[List[str]]]: (헤더 존재 여부, 헤더 행)
        """
        if not table_data or len(table_data) < 2:
            return False, None
        
        first_row = table_data[0]
        
        # 헤더 감지 휴리스틱
        # 1. 첫 번째 행의 셀들이 모두 텍스트인지 확인
        has_text_only = all(
            not self._is_numeric(cell) for cell in first_row if cell.strip()
        )
        
        # 2. 첫 번째 행과 두 번째 행의 패턴이 다른지 확인
        second_row = table_data[1]
        pattern_different = self._has_different_pattern(first_row, second_row)
        
        if has_text_only and pattern_different:
            return True, first_row
        
        return False, None
    
    def _is_numeric(self, text: str) -> bool:
        """문자열이 숫자인지 확인"""
        try:
            float(text.replace(',', '').replace('%', ''))
            return True
        except (ValueError, AttributeError):
            return False
    
    def _has_different_pattern(self, row1: List[str], row2: List[str]) -> bool:
        """두 행의 패턴이 다른지 확인"""
        if len(row1) != len(row2):
            return True
        
        numeric_count_1 = sum(1 for cell in row1 if self._is_numeric(cell))
        numeric_count_2 = sum(1 for cell in row2 if self._is_numeric(cell))
        
        # 숫자 비율이 다르면 패턴이 다름
        return abs(numeric_count_1 - numeric_count_2) > len(row1) * 0.3


class PDFProcessingError(Exception):
    """PDF 처리 관련 예외"""
    
    def __init__(self, message: str, library: str = "unknown", file_path: str = ""):
        self.message = message
        self.library = library
        self.file_path = file_path
        super().__init__(f"[{library}] {message}")


class TableExtractionError(PDFProcessingError):
    """테이블 추출 관련 예외"""
    pass


class FileValidationError(PDFProcessingError):
    """파일 검증 관련 예외"""
    pass


class UnsupportedLibraryError(Exception):
    """지원하지 않는 라이브러리 예외"""
    
    def __init__(self, library: str, supported_libraries: List[str]):
        self.library = library
        self.supported_libraries = supported_libraries
        message = f"지원하지 않는 라이브러리: {library}. 지원 라이브러리: {supported_libraries}"
        super().__init__(message)
