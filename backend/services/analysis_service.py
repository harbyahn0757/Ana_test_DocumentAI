"""
분석 서비스

PDF 파일 분석, 표 추출, 관계 설정 등의 핵심 비즈니스 로직을 담당
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from pathlib import Path

from models.analysis_models import (
    AnalysisRequest, AnalysisResponse, AnalysisStatus, 
    AnalysisResults, TableData, ExtractionLibrary
)
from services.file_service import FileService
from services.extraction_service import ExtractionService
from app.config import settings

logger = logging.getLogger(__name__)


class AnalysisService:
    """분석 서비스 클래스"""
    
    def __init__(self, file_service: FileService, extraction_service: ExtractionService):
        """
        분석 서비스 초기화
        
        Args:
            file_service: 파일 서비스 인스턴스
            extraction_service: 추출 서비스 인스턴스
        """
        self.file_service = file_service
        self.extraction_service = extraction_service
        self.analyses: Dict[str, AnalysisResults] = {}
        
        logger.info("분석 서비스 초기화 완료")
    
    async def start_analysis(
        self, 
        file_id: str, 
        library: ExtractionLibrary,
        background_tasks = None
    ) -> str:
        """
        분석 시작
        
        Args:
            file_id: 분석할 파일 ID
            library: 추출 라이브러리
            background_tasks: 백그라운드 작업 관리자
            
        Returns:
            str: 분석 ID
        """
        try:
            # 분석 ID 생성
            analysis_id = str(uuid.uuid4())
            
            # 파일 정보 조회
            file_info = await self.file_service.get_file_info(file_id)
            if not file_info:
                raise ValueError(f"파일을 찾을 수 없습니다: {file_id}")
            
            # 분석 결과 초기화
            analysis_result = AnalysisResults(
                analysis_id=analysis_id,
                file_id=file_id,
                library=library,
                status=AnalysisStatus.PROCESSING,
                created_at=datetime.now(),
                updated_at=None,
                processing_time=None
            )
            
            # 분석 상태 저장
            self.analyses[analysis_id] = analysis_result
            
            # 백그라운드에서 분석 실행
            if background_tasks:
                background_tasks.add_task(
                    self._run_analysis, 
                    analysis_id, 
                    file_info.file_path, 
                    library
                )
            else:
                # 동기 실행 (테스트용)
                await self._run_analysis(analysis_id, file_info.file_path, library)
            
            logger.info(f"분석 시작: {analysis_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"분석 시작 실패 {file_id}: {e}")
            raise
    
    async def _run_analysis(
        self, 
        analysis_id: str, 
        file_path: str, 
        library: ExtractionLibrary
    ):
        """
        실제 분석 실행 (백그라운드)
        
        Args:
            analysis_id: 분석 ID
            file_path: 파일 경로
            library: 추출 라이브러리
        """
        try:
            logger.info(f"분석 실행 시작: {analysis_id}")
            
            # 분석 상태 업데이트
            if analysis_id in self.analyses:
                self.analyses[analysis_id].status = AnalysisStatus.PROCESSING
            
            # 표 추출 실행
            start_time = datetime.now()
            tables = await self.extraction_service.extract_tables(
                file_path=file_path,
                library=library.value
            )
            end_time = datetime.now()
            
            # 결과 저장
            if analysis_id in self.analyses:
                analysis = self.analyses[analysis_id]
                analysis.status = AnalysisStatus.COMPLETED
                analysis.tables = tables
                analysis.total_tables = len(tables)
                analysis.processing_time = (end_time - start_time).total_seconds()
                analysis.updated_at = end_time
                
                # 페이지 수 계산
                if tables:
                    analysis.total_pages = max(table.page_number for table in tables)
            
            logger.info(f"분석 완료: {analysis_id}, 표 개수: {len(tables)}")
            
        except Exception as e:
            logger.error(f"분석 실행 실패 {analysis_id}: {e}")
            
            # 오류 상태로 업데이트
            if analysis_id in self.analyses:
                self.analyses[analysis_id].status = AnalysisStatus.FAILED
                self.analyses[analysis_id].updated_at = datetime.now()
    
    async def get_analysis_status(self, analysis_id: str) -> Optional[AnalysisResponse]:
        """
        분석 상태 조회
        
        Args:
            analysis_id: 분석 ID
            
        Returns:
            Optional[AnalysisResponse]: 분석 상태 응답
        """
        if analysis_id not in self.analyses:
            return None
        
        analysis = self.analyses[analysis_id]
        
        # 진행률 계산
        progress = 0
        if analysis.status == AnalysisStatus.COMPLETED:
            progress = 100
        elif analysis.status == AnalysisStatus.PROCESSING:
            progress = 50  # 임시값
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status=analysis.status,
            message=self._get_status_message(analysis.status),
            progress=progress,
            started_at=analysis.created_at,
            completed_at=analysis.updated_at if analysis.status == AnalysisStatus.COMPLETED else None,
            error_message=None
        )
    
    async def get_analysis_results(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        분석 결과 조회
        
        Args:
            analysis_id: 분석 ID
            
        Returns:
            Optional[Dict[str, Any]]: 분석 결과 데이터
        """
        if analysis_id not in self.analyses:
            return None
        
        analysis = self.analyses[analysis_id]
        
        # 표준 리턴 사양에 맞게 테이블 데이터 변환
        tables_with_metadata = []
        for table in analysis.tables:
            # 표준 2차원 배열 형태로 변환
            if table.rows and len(table.rows) > 0:
                # 헤더가 있으면 헤더 + 데이터 행으로 구성
                if table.headers and len(table.headers) > 0:
                    standard_data = [table.headers] + table.rows
                else:
                    standard_data = table.rows
                
                table_dict = {
                    'table_id': table.table_id,
                    'page_number': table.page_number,
                    'rows': len(standard_data),
                    'columns': len(standard_data[0]) if standard_data else 0,
                    'data': standard_data,  # 표준 2차원 배열
                    'library': table.extraction_library.value if hasattr(table.extraction_library, 'value') else str(table.extraction_library)
                }
            else:
                table_dict = {
                    'table_id': table.table_id,
                    'page_number': table.page_number,
                    'rows': 0,
                    'columns': 0,
                    'data': [],
                    'library': table.extraction_library.value if hasattr(table.extraction_library, 'value') else str(table.extraction_library)
                }
            tables_with_metadata.append(table_dict)
        
        return {
            "analysis_id": analysis_id,
            "file_id": analysis.file_id,
            "library": analysis.library.value if hasattr(analysis.library, 'value') else str(analysis.library),
            "status": analysis.status.value if hasattr(analysis.status, 'value') else str(analysis.status),
            "tables": tables_with_metadata,
            "total_tables": analysis.total_tables,
            "total_pages": analysis.total_pages,
            "processing_time": analysis.processing_time,
            "created_at": analysis.created_at.isoformat(),
            "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None
        }
    
    async def cancel_analysis(self, analysis_id: str) -> bool:
        """
        분석 취소
        
        Args:
            analysis_id: 분석 ID
            
        Returns:
            bool: 취소 성공 여부
        """
        if analysis_id not in self.analyses:
            return False
        
        analysis = self.analyses[analysis_id]
        if analysis.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
            return False
        
        analysis.status = AnalysisStatus.CANCELLED
        analysis.updated_at = datetime.now()
        
        logger.info(f"분석 취소: {analysis_id}")
        return True
    
    def _get_status_message(self, status: AnalysisStatus) -> str:
        """상태별 메시지 반환"""
        messages = {
            AnalysisStatus.PENDING: "분석 대기 중",
            AnalysisStatus.PROCESSING: "분석 진행 중",
            AnalysisStatus.COMPLETED: "분석 완료",
            AnalysisStatus.FAILED: "분석 실패",
            AnalysisStatus.CANCELLED: "분석 취소됨"
        }
        return messages.get(status, "알 수 없는 상태")
