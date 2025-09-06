"""
PDF 테이블 추출 관련 헬퍼 함수들

ExtractionResult 생성 등 공통 로직을 모음
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.table_models import (
    TableData, PageTableData, ExtractionResult, ExtractionLibrary
)


class ExtractionResultBuilder:
    """ExtractionResult 생성을 위한 빌더 클래스"""
    
    def __init__(self, file_path: Path, library: str):
        """빌더 초기화
        
        Args:
            file_path (Path): PDF 파일 경로
            library (str): 사용된 라이브러리명
        """
        self.file_path = file_path
        self.library = library
        self.tables: List[TableData] = []
        self.page_data: List[PageTableData] = []
        self.processing_time: float = 0.0
        self.library_options: Dict[str, Any] = {}
        self.success: bool = True
        self.error_message: Optional[str] = None
        self.extraction_quality: Optional[Dict[str, Any]] = None
    
    def with_tables(self, tables: List[TableData]) -> 'ExtractionResultBuilder':
        """테이블 데이터 설정
        
        Args:
            tables (List[TableData]): 추출된 테이블 목록
            
        Returns:
            ExtractionResultBuilder: 체이닝을 위한 빌더 인스턴스
        """
        self.tables = tables
        return self
    
    def with_page_data(self, page_data: List[PageTableData]) -> 'ExtractionResultBuilder':
        """페이지 데이터 설정
        
        Args:
            page_data (List[PageTableData]): 페이지별 테이블 데이터
            
        Returns:
            ExtractionResultBuilder: 체이닝을 위한 빌더 인스턴스
        """
        self.page_data = page_data
        return self
    
    def with_processing_time(self, processing_time: float) -> 'ExtractionResultBuilder':
        """처리 시간 설정
        
        Args:
            processing_time (float): 처리 시간 (초)
            
        Returns:
            ExtractionResultBuilder: 체이닝을 위한 빌더 인스턴스
        """
        self.processing_time = processing_time
        return self
    
    def with_options(self, options: Dict[str, Any]) -> 'ExtractionResultBuilder':
        """라이브러리 옵션 설정
        
        Args:
            options (Dict[str, Any]): 라이브러리 옵션
            
        Returns:
            ExtractionResultBuilder: 체이닝을 위한 빌더 인스턴스
        """
        self.library_options = options
        return self
    
    def with_error(self, error_message: str) -> 'ExtractionResultBuilder':
        """에러 상태 설정
        
        Args:
            error_message (str): 에러 메시지
            
        Returns:
            ExtractionResultBuilder: 체이닝을 위한 빌더 인스턴스
        """
        self.success = False
        self.error_message = error_message
        self.extraction_quality = {"score": 0.0}
        return self
    
    def with_quality(self, quality_score: float) -> 'ExtractionResultBuilder':
        """품질 점수 설정
        
        Args:
            quality_score (float): 추출 품질 점수 (0.0 ~ 1.0)
            
        Returns:
            ExtractionResultBuilder: 체이닝을 위한 빌더 인스턴스
        """
        self.extraction_quality = {"score": quality_score}
        return self
    
    def build(self) -> ExtractionResult:
        """ExtractionResult 인스턴스 생성
        
        Returns:
            ExtractionResult: 완성된 추출 결과 객체
        """
        return ExtractionResult(
            file_path=str(self.file_path),
            file_id=str(self.file_path.stem),
            file_name=self.file_path.name,
            extraction_library=ExtractionLibrary(self.library),
            total_tables=len(self.tables),
            total_pages=len(self.page_data),
            tables=self.tables,
            page_data=self.page_data,
            processing_time=self.processing_time,
            extracted_at=datetime.now(),
            library_options=self.library_options,
            success=self.success,
            error_message=self.error_message,
            extraction_quality=self.extraction_quality or {"score": 0.8}
        )


def create_success_result(
    file_path: Path,
    library: str,
    tables: List[TableData],
    page_data: List[PageTableData],
    processing_time: float,
    options: Optional[Dict[str, Any]] = None,
    quality_score: float = 0.8
) -> ExtractionResult:
    """성공적인 추출 결과 생성
    
    Args:
        file_path (Path): PDF 파일 경로
        library (str): 사용된 라이브러리명
        tables (List[TableData]): 추출된 테이블 목록
        page_data (List[PageTableData]): 페이지별 테이블 데이터
        processing_time (float): 처리 시간 (초)
        options (Optional[Dict[str, Any]]): 라이브러리 옵션
        quality_score (float): 품질 점수 (기본: 0.8)
        
    Returns:
        ExtractionResult: 추출 결과 객체
    """
    return (ExtractionResultBuilder(file_path, library)
            .with_tables(tables)
            .with_page_data(page_data)
            .with_processing_time(processing_time)
            .with_options(options or {})
            .with_quality(quality_score)
            .build())


def create_error_result(
    file_path: Path,
    library: str,
    error_message: str,
    processing_time: float = 0.0,
    options: Optional[Dict[str, Any]] = None
) -> ExtractionResult:
    """실패한 추출 결과 생성
    
    Args:
        file_path (Path): PDF 파일 경로
        library (str): 사용된 라이브러리명
        error_message (str): 에러 메시지
        processing_time (float): 처리 시간 (초)
        options (Optional[Dict[str, Any]]): 라이브러리 옵션
        
    Returns:
        ExtractionResult: 추출 결과 객체
    """
    return (ExtractionResultBuilder(file_path, library)
            .with_processing_time(processing_time)
            .with_options(options or {})
            .with_error(error_message)
            .build())
