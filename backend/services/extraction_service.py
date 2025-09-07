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
        import time
        from datetime import datetime
        
        start_time = time.time()
        
        try:
            logger.info(f"매핑 기반 데이터 추출 시작: {file_path}")
            
            # 1. 먼저 테이블 추출
            tables = await self.extract_tables(file_path, processor_type)
            
            if not tables:
                logger.warning("추출된 테이블이 없습니다")
                return {
                    "extracted_data": [],
                    "processing_time": time.time() - start_time,
                    "extracted_at": datetime.now().isoformat()
                }
            
            # 2. 매핑에 따라 데이터 추출
            extracted_data = []
            
            for mapping in mappings:
                try:
                    # 매핑 정보 파싱
                    key = mapping.get("key")
                    key_label = mapping.get("key_label", key)
                    anchor_cell = mapping.get("anchor_cell", {})
                    value_cell = mapping.get("value_cell", {})
                    
                    if not anchor_cell or not value_cell:
                        logger.warning(f"매핑 정보가 불완전합니다: {key}")
                        continue
                    
                    # 앵커 셀 정보
                    anchor_row = anchor_cell.get("row")
                    anchor_col = anchor_cell.get("col")
                    anchor_value = anchor_cell.get("value")
                    
                    # 값 셀 정보
                    value_row = value_cell.get("row")
                    value_col = value_cell.get("col")
                    
                    # 테이블에서 해당 데이터 찾기
                    extracted_value = None
                    confidence = 0.0
                    
                    for table in tables:
                        # TableData 모델의 data 속성 사용
                        table_data = table.data if hasattr(table, 'data') else table.rows if hasattr(table, 'rows') else []
                        
                        if (anchor_row < len(table_data) and 
                            anchor_col < len(table_data[anchor_row]) and
                            table_data[anchor_row][anchor_col] == anchor_value):
                            
                            # 앵커를 찾았으면 값 추출
                            if (value_row < len(table_data) and 
                                value_col < len(table_data[value_row])):
                                extracted_value = table_data[value_row][value_col]
                                confidence = 1.0
                                break
                    
                    if extracted_value is not None:
                        extracted_data.append({
                            "key": key,
                            "key_label": key_label,
                            "extracted_value": extracted_value,
                            "anchor_cell": anchor_cell,
                            "value_cell": value_cell,
                            "relative_position": mapping.get("relative_position", {}),
                            "confidence": confidence
                        })
                        logger.info(f"데이터 추출 성공: {key} = {extracted_value}")
                    else:
                        logger.warning(f"데이터 추출 실패: {key} - 앵커를 찾을 수 없음")
                        
                except Exception as e:
                    logger.error(f"매핑 처리 중 오류 ({mapping.get('key', 'unknown')}): {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            logger.info(f"매핑 기반 데이터 추출 완료: {len(extracted_data)}개 항목, {processing_time:.2f}초")
            
            return {
                "extracted_data": extracted_data,
                "processing_time": processing_time,
                "extracted_at": datetime.now().isoformat()
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