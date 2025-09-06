"""
테이블 관련 데이터 모델

테이블 구조, 셀 데이터, 그리드 데이터 등의 Pydantic 모델 정의
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class CellType(str, Enum):
    """셀 타입 열거형"""
    HEADER = "header"           # 헤더 셀
    DATA = "data"              # 데이터 셀
    EMPTY = "empty"            # 빈 셀
    MERGED = "merged"          # 병합된 셀


class TablePosition(str, Enum):
    """테이블 위치 열거형"""
    TOP = "top"                # 페이지 상단
    MIDDLE = "middle"          # 페이지 중앙
    BOTTOM = "bottom"          # 페이지 하단
    FULL = "full"              # 페이지 전체


class ExtractionLibrary(str, Enum):
    """추출 라이브러리 열거형"""
    PDFPLUMBER = "pdfplumber"
    CAMELOT = "camelot"
    TABULA = "tabula"


class CellData(BaseModel):
    """개별 셀 데이터 모델"""
    
    row: int = Field(..., ge=0, description="행 번호 (0부터 시작)")
    col: int = Field(..., ge=0, description="열 번호 (0부터 시작)")
    content: str = Field(..., description="셀 내용")
    type: CellType = Field(default=CellType.DATA, description="셀 타입")
    
    # 병합 정보
    rowspan: int = Field(default=1, ge=1, description="행 병합 수")
    colspan: int = Field(default=1, ge=1, description="열 병합 수")
    
    # 스타일 정보 (선택사항)
    style: Optional[Dict[str, Any]] = Field(default=None, description="셀 스타일 정보")
    
    @validator('content')
    def clean_content(cls, v):
        """셀 내용 정리"""
        if v is None:
            return ""
        return str(v).strip()
    
    @property
    def is_empty(self) -> bool:
        """빈 셀 여부"""
        return not self.content or self.content.strip() == ""
    
    @property
    def is_numeric(self) -> bool:
        """숫자 데이터 여부"""
        try:
            float(self.content.replace(',', '').replace('%', ''))
            return True
        except (ValueError, AttributeError):
            return False
    
    @property
    def is_merged(self) -> bool:
        """병합된 셀 여부"""
        return self.rowspan > 1 or self.colspan > 1


class GridData(BaseModel):
    """그리드 형태 테이블 데이터"""
    
    rows: int = Field(..., ge=0, description="총 행 수")
    cols: int = Field(..., ge=0, description="총 열 수")
    cells: List[CellData] = Field(..., description="셀 데이터 목록")
    
    def get_cell(self, row: int, col: int) -> Optional[CellData]:
        """특정 위치의 셀 데이터 반환"""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None
    
    def get_row_cells(self, row: int) -> List[CellData]:
        """특정 행의 모든 셀 반환"""
        return [cell for cell in self.cells if cell.row == row]
    
    def get_col_cells(self, col: int) -> List[CellData]:
        """특정 열의 모든 셀 반환"""
        return [cell for cell in self.cells if cell.col == col]
    
    def to_matrix(self) -> List[List[str]]:
        """2차원 배열로 변환"""
        matrix = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        
        for cell in self.cells:
            if cell.row < self.rows and cell.col < self.cols:
                matrix[cell.row][cell.col] = cell.content
        
        return matrix
    
    @property
    def header_row(self) -> Optional[List[CellData]]:
        """헤더 행 반환 (첫 번째 행이 모두 헤더인 경우)"""
        if self.rows == 0:
            return None
        
        first_row = self.get_row_cells(0)
        if all(cell.type == CellType.HEADER for cell in first_row):
            return first_row
        
        return None
    
    @property
    def data_rows(self) -> List[List[CellData]]:
        """데이터 행들 반환 (헤더 제외)"""
        start_row = 1 if self.header_row else 0
        return [self.get_row_cells(row) for row in range(start_row, self.rows)]


class TableMetadata(BaseModel):
    """테이블 메타데이터"""
    
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="추출 신뢰도")
    position: Optional[TablePosition] = Field(None, description="테이블 위치")
    bbox: Optional[List[float]] = Field(None, description="경계 상자 [x1, y1, x2, y2]")
    
    # 추출 정보
    extraction_method: Optional[str] = Field(None, description="추출 방법")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    
    # 품질 지표
    empty_cell_ratio: Optional[float] = Field(None, description="빈 셀 비율")
    text_alignment_score: Optional[float] = Field(None, description="텍스트 정렬 점수")
    
    @validator('bbox')
    def validate_bbox(cls, v):
        """경계 상자 유효성 검증"""
        if v is not None and len(v) != 4:
            raise ValueError("경계 상자는 [x1, y1, x2, y2] 형태여야 합니다")
        return v


class TableData(BaseModel):
    """테이블 데이터 모델"""
    
    table_id: str = Field(..., description="테이블 고유 ID")
    page_number: int = Field(..., ge=1, description="페이지 번호 (1부터 시작)")
    
    # 기본 테이블 구조
    headers: List[str] = Field(default_factory=list, description="헤더 행")
    rows: List[List[str]] = Field(default_factory=list, description="데이터 행들")
    
    # 그리드 데이터 (셀 단위 접근용)
    grid_data: GridData = Field(..., description="그리드 형태 데이터")
    
    # 메타데이터
    metadata: TableMetadata = Field(
        default_factory=lambda: TableMetadata(
            confidence=0.5,
            position=None,
            bbox=None,
            extraction_method=None,
            processing_time=0.0,
            empty_cell_ratio=0.0,
            text_alignment_score=0.0
        ), 
        description="테이블 메타데이터"
    )
    
    # 추출 정보
    extraction_library: ExtractionLibrary = Field(..., description="사용된 추출 라이브러리")
    extracted_at: datetime = Field(default_factory=datetime.now, description="추출 일시")
    
    @validator('table_id')
    def validate_table_id(cls, v):
        """테이블 ID 유효성 검증"""
        if not v or not v.strip():
            raise ValueError("테이블 ID는 비어있을 수 없습니다")
        return v.strip()
    
    @property
    def row_count(self) -> int:
        """총 행 수 (헤더 포함)"""
        return len(self.rows) + (1 if self.headers else 0)
    
    @property
    def col_count(self) -> int:
        """총 열 수"""
        if self.headers:
            return len(self.headers)
        elif self.rows:
            return max(len(row) for row in self.rows)
        return 0
    
    @property
    def is_empty(self) -> bool:
        """빈 테이블 여부"""
        return len(self.rows) == 0 and len(self.headers) == 0
    
    @property
    def has_headers(self) -> bool:
        """헤더 존재 여부"""
        return len(self.headers) > 0
    
    def get_column_data(self, col_index: int) -> List[str]:
        """특정 열의 모든 데이터 반환"""
        column_data = []
        
        # 헤더가 있으면 추가
        if self.headers and col_index < len(self.headers):
            column_data.append(self.headers[col_index])
        
        # 각 행에서 해당 열 데이터 추출
        for row in self.rows:
            if col_index < len(row):
                column_data.append(row[col_index])
            else:
                column_data.append("")  # 빈 셀
        
        return column_data
    
    def search_cell_content(self, search_text: str, case_sensitive: bool = False) -> List[tuple]:
        """셀 내용 검색
        
        Args:
            search_text: 검색할 텍스트
            case_sensitive: 대소문자 구분 여부
            
        Returns:
            List[tuple]: (row, col, content) 형태의 결과 목록
        """
        results = []
        search_lower = search_text.lower() if not case_sensitive else search_text
        
        # 헤더에서 검색
        if self.headers:
            for col, header in enumerate(self.headers):
                header_text = header.lower() if not case_sensitive else header
                if search_lower in header_text:
                    results.append((0, col, header))  # 헤더는 0행으로 처리
        
        # 데이터 행에서 검색
        for row_idx, row in enumerate(self.rows):
            for col_idx, cell in enumerate(row):
                cell_text = cell.lower() if not case_sensitive else cell
                if search_lower in cell_text:
                    # 헤더가 있으면 행 번호를 1부터 시작
                    actual_row = row_idx + (1 if self.headers else 0)
                    results.append((actual_row, col_idx, cell))
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "table_id": self.table_id,
            "page_number": self.page_number,
            "headers": self.headers,
            "rows": self.rows,
            "row_count": self.row_count,
            "col_count": self.col_count,
            "has_headers": self.has_headers,
            "metadata": self.metadata.dict(),
            "extraction_library": self.extraction_library.value,
            "extracted_at": self.extracted_at.isoformat()
        }


class PageTableData(BaseModel):
    """페이지별 테이블 데이터"""
    
    page_number: int = Field(..., ge=1, description="페이지 번호")
    tables: List[TableData] = Field(default_factory=list, description="페이지의 테이블 목록")
    
    # 페이지 메타데이터
    page_width: Optional[float] = Field(None, description="페이지 너비")
    page_height: Optional[float] = Field(None, description="페이지 높이")
    text_content: Optional[str] = Field(None, description="페이지 텍스트 내용")
    
    @property
    def table_count(self) -> int:
        """페이지의 테이블 개수"""
        return len(self.tables)
    
    @property
    def total_cells(self) -> int:
        """페이지의 총 셀 개수"""
        return sum(table.grid_data.rows * table.grid_data.cols for table in self.tables)
    
    def get_table_by_id(self, table_id: str) -> Optional[TableData]:
        """ID로 테이블 검색"""
        for table in self.tables:
            if table.table_id == table_id:
                return table
        return None
    
    def search_across_tables(self, search_text: str, case_sensitive: bool = False) -> Dict[str, List[tuple]]:
        """페이지의 모든 테이블에서 검색"""
        results = {}
        for table in self.tables:
            table_results = table.search_cell_content(search_text, case_sensitive)
            if table_results:
                results[table.table_id] = table_results
        return results


class ExtractionResult(BaseModel):
    """전체 추출 결과"""
    
    # 파일 정보 (더 유연하게 변경)
    file_path: str = Field(..., description="파일 경로")
    file_id: Optional[str] = Field(None, description="파일 ID")
    file_name: Optional[str] = Field(None, description="파일명")
    
    # 결과 정보
    success: bool = Field(default=True, description="추출 성공 여부")
    error_message: Optional[str] = Field(None, description="에러 메시지 (실패시)")
    
    total_pages: int = Field(default=0, ge=0, description="총 페이지 수")
    total_tables: int = Field(default=0, ge=0, description="총 테이블 수")
    
    # 테이블 데이터 (기존 구조와 호환)
    tables: List[TableData] = Field(default_factory=list, description="추출된 테이블 목록")
    page_data: List[PageTableData] = Field(default_factory=list, description="페이지별 테이블 데이터")
    pages: List[PageTableData] = Field(default_factory=list, description="페이지별 테이블 데이터 (호환성)")
    
    # 추출 메타데이터
    extraction_library: ExtractionLibrary = Field(..., description="사용된 라이브러리")
    library_options: Dict[str, Any] = Field(default_factory=dict, description="라이브러리 옵션")
    extraction_options: Dict[str, Any] = Field(default_factory=dict, description="추출 옵션 (호환성)")
    processing_time: float = Field(default=0.0, description="총 처리 시간 (초)")
    extracted_at: datetime = Field(default_factory=datetime.now, description="추출 완료 일시")
    
    # 품질 지표
    extraction_quality: Optional[Dict[str, Any]] = Field(None, description="추출 품질 지표")
    
    @property
    def pages_with_tables(self) -> int:
        """테이블이 있는 페이지 수"""
        return sum(1 for page in self.pages if page.table_count > 0)
    
    @property
    def average_tables_per_page(self) -> float:
        """페이지당 평균 테이블 수"""
        if self.total_pages == 0:
            return 0.0
        return self.total_tables / self.total_pages
    
    def get_page_data(self, page_number: int) -> Optional[PageTableData]:
        """특정 페이지 데이터 반환"""
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None
    
    def get_all_tables(self) -> List[TableData]:
        """모든 페이지의 테이블을 하나의 리스트로 반환"""
        all_tables = []
        for page in self.pages:
            all_tables.extend(page.tables)
        return all_tables
    
    def search_all_tables(self, search_text: str, case_sensitive: bool = False) -> Dict[str, Dict[str, List[tuple]]]:
        """모든 테이블에서 검색"""
        results = {}
        for page in self.pages:
            page_results = page.search_across_tables(search_text, case_sensitive)
            if page_results:
                results[f"page_{page.page_number}"] = page_results
        return results
    
    def to_summary(self) -> Dict[str, Any]:
        """요약 정보 반환"""
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "total_pages": self.total_pages,
            "total_tables": self.total_tables,
            "pages_with_tables": self.pages_with_tables,
            "average_tables_per_page": round(self.average_tables_per_page, 2),
            "extraction_library": self.extraction_library.value,
            "processing_time": round(self.processing_time, 3),
            "extracted_at": self.extracted_at.isoformat()
        }
