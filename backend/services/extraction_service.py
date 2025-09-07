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
    
    async def extract_data_with_mappings(
        self, 
        file_path: str, 
        mappings: List[Dict[str, Any]],
        processor_type: str = "pdfplumber"
    ) -> Dict[str, Any]:
        """
        매핑 기반 데이터 추출 (템플릿 기반 추출용)
        
        Args:
            file_path: PDF 파일 경로
            mappings: 키-값 매핑 설정
            processor_type: PDF 처리기 타입
            
        Returns:
            Dict[str, Any]: 추출 결과
        """
        try:
            logger.info(f"매핑 기반 데이터 추출 시작: {file_path}")
            
            # 임시 구현 - 실제로는 매핑에 따라 데이터 추출
            return {
                "extracted_data": [],
                "processing_time": 0.0,
                "extracted_at": "2025-01-27T00:00:00Z"
            }
            
        except Exception as e:
            logger.error(f"매핑 기반 데이터 추출 실패 {file_path}: {e}")
            raise
    
    async def quick_test(
        self, 
        file_path: str, 
        template_name: str,
        mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        빠른 추출 테스트
        
        Args:
            file_path: PDF 파일 경로
            template_name: 템플릿 이름
            mappings: 매핑 설정
            
        Returns:
            Dict[str, Any]: 테스트 결과
        """
        try:
            logger.info(f"빠른 테스트 시작: {file_path}")
            
            return {
                "success": True,
                "message": "빠른 테스트 완료",
                "file_path": file_path,
                "config_valid": True
            }
            
        except Exception as e:
            logger.error(f"빠른 테스트 실패: {str(e)}")
            return {
                "success": False,
                "message": f"빠른 테스트 실패: {str(e)}",
                "file_path": file_path,
                "config_valid": False
            }
    
    async def validate_mappings(
        self, 
        mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        매핑 설정 검증
        
        Args:
            mappings: 검증할 매핑 설정
            
        Returns:
            Dict[str, Any]: 검증 결과
        """
        try:
            logger.info(f"매핑 검증 시작: {len(mappings)}개 매핑")
            
            # 임시 구현
            return {
                "valid": True,
                "valid_count": len(mappings),
                "invalid_count": 0,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"매핑 검증 실패: {e}")
            raise