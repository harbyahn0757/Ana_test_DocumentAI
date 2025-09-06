"""
추출 서비스

PDF에서 표를 추출하는 핵심 로직을 담당
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from models.analysis_models import TableData, ExtractionLibrary
from core.pdf_processor.factory import PDFProcessorFactory

logger = logging.getLogger(__name__)


class ExtractionService:
    """추출 서비스 클래스"""
    
    def __init__(self):
        """추출 서비스 초기화"""
        self.processor_factory = PDFProcessorFactory()
        logger.info("추출 서비스 초기화 완료")
    
    async def extract_tables(
        self, 
        file_path: str, 
        library: str
    ) -> List[TableData]:
        """
        PDF에서 표 추출
        
        Args:
            file_path: PDF 파일 경로
            library: 추출 라이브러리 이름
            
        Returns:
            List[TableData]: 추출된 표 데이터 목록
        """
        try:
            logger.info(f"표 추출 시작: {file_path}, 라이브러리: {library}")
            
            # 파일 경로를 Path 객체로 변환
            from pathlib import Path
            pdf_path = Path(file_path)
            
            # 프로세서 생성
            processor = self.processor_factory.create_processor(library)
            if not processor:
                raise ValueError(f"지원하지 않는 라이브러리입니다: {library}")
            
            # 표 추출 실행
            tables = processor.extract_tables(pdf_path)
            
            # 이미 TableData 객체 리스트이므로 그대로 반환
            logger.info(f"표 추출 완료: {len(tables)}개 표 추출")
            return tables
            
        except Exception as e:
            logger.error(f"표 추출 실패 {file_path}: {e}")
            raise
    
    async def extract_tables_with_options(
        self, 
        file_path: str, 
        library: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[TableData]:
        """
        옵션을 포함한 표 추출
        
        Args:
            file_path: PDF 파일 경로
            library: 추출 라이브러리 이름
            options: 추출 옵션
            
        Returns:
            List[TableData]: 추출된 표 데이터 목록
        """
        try:
            logger.info(f"옵션 포함 표 추출 시작: {file_path}, 라이브러리: {library}")
            
            # 프로세서 생성
            processor = self.processor_factory.create_processor(library)
            if not processor:
                raise ValueError(f"지원하지 않는 라이브러리입니다: {library}")
            
            # 옵션 적용하여 표 추출
            tables = await processor.extract_tables_with_options(file_path, options or {})
            
            # TableData 객체로 변환
            table_data_list = []
            for page_num, page_tables in tables.items():
                for table_idx, table in enumerate(page_tables):
                    table_data = TableData(
                        page_number=page_num,
                        table_index=table_idx,
                        data=table.get('data', []),
                        headers=table.get('headers'),
                        confidence=table.get('confidence'),
                        bbox=table.get('bbox')
                    )
                    table_data_list.append(table_data)
            
            logger.info(f"옵션 포함 표 추출 완료: {len(table_data_list)}개 표 추출")
            return table_data_list
            
        except Exception as e:
            logger.error(f"옵션 포함 표 추출 실패 {file_path}: {e}")
            raise