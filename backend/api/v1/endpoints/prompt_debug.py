"""
프롬프트 디버깅 API 엔드포인트

AI 프롬프트 실행 기록을 조회하고 분석할 수 있는 API
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
import logging

from core.prompt_debug_manager import get_prompt_debug_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/entries/recent")
async def get_recent_prompt_entries(
    limit: int = Query(50, ge=1, le=500, description="최대 조회 개수")
) -> Dict[str, Any]:
    """
    최근 프롬프트 실행 기록 조회
    
    Args:
        limit: 최대 조회 개수 (1-500)
        
    Returns:
        Dict: 프롬프트 실행 기록 리스트
    """
    try:
        debug_manager = get_prompt_debug_manager()
        entries = debug_manager.get_recent_entries(limit)
        
        return {
            "success": True,
            "data": {
                "entries": entries,
                "total_count": len(entries)
            }
        }
        
    except Exception as e:
        logger.error(f"최근 프롬프트 엔트리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/entries/by-service/{service_name}")
async def get_prompt_entries_by_service(
    service_name: str,
    limit: int = Query(50, ge=1, le=500, description="최대 조회 개수")
) -> Dict[str, Any]:
    """
    서비스별 프롬프트 실행 기록 조회
    
    Args:
        service_name: 서비스 이름
        limit: 최대 조회 개수 (1-500)
        
    Returns:
        Dict: 프롬프트 실행 기록 리스트
    """
    try:
        debug_manager = get_prompt_debug_manager()
        entries = debug_manager.get_entries_by_service(service_name, limit)
        
        return {
            "success": True,
            "data": {
                "service_name": service_name,
                "entries": entries,
                "total_count": len(entries)
            }
        }
        
    except Exception as e:
        logger.error(f"서비스별 프롬프트 엔트리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/entries/by-prompt-type/{prompt_type}")
async def get_prompt_entries_by_type(
    prompt_type: str,
    limit: int = Query(50, ge=1, le=500, description="최대 조회 개수")
) -> Dict[str, Any]:
    """
    프롬프트 타입별 실행 기록 조회
    
    Args:
        prompt_type: 프롬프트 타입
        limit: 최대 조회 개수 (1-500)
        
    Returns:
        Dict: 프롬프트 실행 기록 리스트
    """
    try:
        debug_manager = get_prompt_debug_manager()
        entries = debug_manager.get_entries_by_prompt_type(prompt_type, limit)
        
        return {
            "success": True,
            "data": {
                "prompt_type": prompt_type,
                "entries": entries,
                "total_count": len(entries)
            }
        }
        
    except Exception as e:
        logger.error(f"프롬프트 타입별 엔트리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/entries/{entry_id}")
async def get_prompt_entry_by_id(entry_id: str) -> Dict[str, Any]:
    """
    ID로 프롬프트 실행 기록 조회
    
    Args:
        entry_id: 엔트리 ID
        
    Returns:
        Dict: 프롬프트 실행 기록
    """
    try:
        debug_manager = get_prompt_debug_manager()
        entry = debug_manager.get_entry_by_id(entry_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="엔트리를 찾을 수 없습니다")
        
        return {
            "success": True,
            "data": entry
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프롬프트 엔트리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/stats")
async def get_prompt_execution_stats() -> Dict[str, Any]:
    """
    프롬프트 실행 통계 조회
    
    Returns:
        Dict: 실행 통계 정보
    """
    try:
        debug_manager = get_prompt_debug_manager()
        stats = debug_manager.get_execution_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"프롬프트 실행 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/services")
async def get_available_services() -> Dict[str, Any]:
    """
    사용 가능한 서비스 목록 조회
    
    Returns:
        Dict: 서비스 목록
    """
    try:
        debug_manager = get_prompt_debug_manager()
        stats = debug_manager.get_execution_stats()
        
        services = list(stats.get("service_stats", {}).keys()) if stats else []
        
        return {
            "success": True,
            "data": {
                "services": services,
                "total_count": len(services)
            }
        }
        
    except Exception as e:
        logger.error(f"서비스 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/prompt-types")
async def get_available_prompt_types() -> Dict[str, Any]:
    """
    사용 가능한 프롬프트 타입 목록 조회
    
    Returns:
        Dict: 프롬프트 타입 목록
    """
    try:
        debug_manager = get_prompt_debug_manager()
        stats = debug_manager.get_execution_stats()
        
        prompt_types = list(stats.get("prompt_type_stats", {}).keys()) if stats else []
        
        return {
            "success": True,
            "data": {
                "prompt_types": prompt_types,
                "total_count": len(prompt_types)
            }
        }
        
    except Exception as e:
        logger.error(f"프롬프트 타입 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")




