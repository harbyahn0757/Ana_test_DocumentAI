"""
분석 API 엔드포인트 (설정을 위한 추출)
PDF 파일에서 모든 테이블을 추출하여 화면에 표시하는 용도
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging

from services.analysis_service import AnalysisService
from app.dependencies import get_analysis_service, get_error_handler
from models.analysis_models import AnalysisRequest, AnalysisResponse, AnalysisStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])


@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    error_handler = Depends(get_error_handler)
):
    """분석 시작 (설정을 위한 추출)
    
    PDF 파일에서 모든 테이블을 추출하여 화면에 표시하기 위한 분석을 시작합니다.
    
    Args:
        request: 분석 요청 데이터
        background_tasks: 백그라운드 작업 관리
        
    Returns:
        AnalysisResponse: 분석 시작 응답
    """
    try:
        logger.info(f"분석 시작 요청: {request.file_id}, 라이브러리: {request.library}")
        
        # 분석 시작
        analysis_id = await analysis_service.start_analysis(
            file_id=request.file_id,
            library=request.library,
            background_tasks=background_tasks
        )
        
        logger.info(f"분석 시작 완료: {analysis_id}")
        return AnalysisResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.PROCESSING,
            message="분석이 시작되었습니다",
            progress=0,
            started_at=None,
            completed_at=None,
            error_message=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 시작 실패: {e}")
        error_handler.handle_internal_error(str(e))


@router.get("/status/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_status(
    analysis_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    error_handler = Depends(get_error_handler)
):
    """분석 상태 조회
    
    Args:
        analysis_id: 분석 ID
        
    Returns:
        AnalysisResponse: 분석 상태 응답
    """
    try:
        logger.info(f"분석 상태 조회: {analysis_id}")
        
        status = await analysis_service.get_analysis_status(analysis_id)
        
        if not status:
            error_handler.handle_analysis_not_found(analysis_id)
        
        logger.info(f"분석 상태 조회 완료: {analysis_id} - {status.status if status else 'None'}")
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 상태 조회 실패 {analysis_id}: {e}")
        error_handler.handle_internal_error(str(e))


@router.get("/results/{analysis_id}")
async def get_analysis_results(
    analysis_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    error_handler = Depends(get_error_handler)
):
    """분석 결과 조회 (설정을 위한 추출 결과)
    
    PDF에서 추출된 모든 테이블 데이터를 반환합니다.
    
    Args:
        analysis_id: 분석 ID
        
    Returns:
        dict: 분석 결과 데이터 (테이블 목록)
    """
    try:
        logger.info(f"분석 결과 조회: {analysis_id}")
        
        results = await analysis_service.get_analysis_results(analysis_id)
        
        if not results:
            error_handler.handle_analysis_not_found(analysis_id)
        
        # 프론트엔드에 맞춰서 results 객체로 감싸서 응답
        # 페이지별로 테이블을 그룹화
        pages = {}
        for table in results["tables"]:
            page_num = table.get("page_number", 1)
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(table)
        
        response_data = {
            "analysis_id": results["analysis_id"],
            "file_id": results["file_id"],
            "library": results["library"],
            "status": results["status"],
            "results": {
                "pages": pages,  # 페이지별 테이블 그룹
                "tables": results["tables"],  # 전체 테이블 목록
                "total_tables": results["total_tables"],
                "total_pages": results.get("total_pages", len(pages)),
                "processing_time": results["processing_time"],
                "created_at": results["created_at"]
            }
        }
        
        logger.info(f"분석 결과 조회 완료: {analysis_id}")
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 결과 조회 실패 {analysis_id}: {e}")
        error_handler.handle_internal_error(str(e))


@router.delete("/{analysis_id}")
async def cancel_analysis(
    analysis_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    error_handler = Depends(get_error_handler)
):
    """분석 취소
    
    Args:
        analysis_id: 분석 ID
        
    Returns:
        dict: 취소 결과
    """
    try:
        logger.info(f"분석 취소 요청: {analysis_id}")
        
        success = await analysis_service.cancel_analysis(analysis_id)
        
        if not success:
            error_handler.handle_analysis_not_found(analysis_id)
        
        logger.info(f"분석 취소 완료: {analysis_id}")
        return {"success": True, "message": "분석이 취소되었습니다"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 취소 실패 {analysis_id}: {e}")
        error_handler.handle_internal_error(str(e))