"""
테이블 추출기
PDF에서 테이블을 추출하는 핵심 로직
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from models.analysis_models import TableData
from core.pdf_processor.factory import PDFProcessorFactory

logger = logging.getLogger(__name__)


class TableExtractor:
    """테이블 추출기 클래스"""
    
    def __init__(self):
        """테이블 추출기 초기화"""
        self.processor_factory = PDFProcessorFactory()
        logger.info("테이블 추출기가 초기화되었습니다")
    
    async def extract_tables(
        self, 
        file_path: str, 
        library: str = "pdfplumber"
    ) -> List[TableData]:
        """
        PDF 파일에서 테이블 추출
        
        Args:
            file_path: PDF 파일 경로
            library: 사용할 PDF 처리 라이브러리
            
        Returns:
            List[TableData]: 추출된 테이블 데이터 목록
        """
        try:
            # PDF 처리기 생성
            processor = self.processor_factory.create_processor(library)
            
            # 테이블 추출 실행
            tables = await processor.extract_tables(file_path)
            
            logger.info(f"테이블 추출 완료: {len(tables)}개 테이블 발견")
            return tables
            
        except Exception as e:
            logger.error(f"테이블 추출 실패: {e}")
            return []
    
    def validate_file(self, file_path: str) -> bool:
        """
        파일 유효성 검사
        
        Args:
            file_path: 파일 경로
            
        Returns:
            bool: 파일 유효성 여부
        """
        try:
            path = Path(file_path)
            return path.exists() and path.suffix.lower() == '.pdf'
        except Exception:
            return False
