"""
템플릿 API 엔드포인트
추출 템플릿 저장/조회/수정/삭제를 위한 REST API
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
import logging

from models.template_models import (
    TemplateCreateRequest,
    TemplateUpdateRequest,
    TemplateResponse,
    TemplateListResponse
)
from services.template_service import template_service
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["templates"])


@router.post("/", response_model=TemplateResponse)
async def create_template(request: TemplateCreateRequest):
    """템플릿 생성"""
    try:
        logger.info(f"템플릿 생성 요청: {request.name}")
        
        template = template_service.create_template(request)
        
        logger.info(f"템플릿 생성 완료: {template.id}")
        return template
        
    except Exception as e:
        logger.error(f"템플릿 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=TemplateListResponse)
async def get_templates(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[str] = Query(None, description="템플릿 상태")
):
    """템플릿 목록 조회"""
    try:
        logger.info(f"템플릿 목록 조회: page={page}, page_size={page_size}, status={status}")
        
        templates = template_service.get_templates(page, page_size, status)
        
        logger.info(f"템플릿 목록 조회 완료: {templates.total_count}개")
        return templates
        
    except Exception as e:
        logger.error(f"템플릿 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int = Path(..., description="템플릿 ID")):
    """템플릿 조회"""
    try:
        logger.info(f"템플릿 조회: {template_id}")
        
        template = template_service.get_template(template_id)
        
        logger.info(f"템플릿 조회 완료: {template.name}")
        return template
        
    except ValueError as e:
        logger.warning(f"템플릿 조회 실패: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"템플릿 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int = Path(..., description="템플릿 ID"),
    request: TemplateUpdateRequest = None
):
    """템플릿 수정"""
    try:
        logger.info(f"템플릿 수정 요청: {template_id}")
        
        template = template_service.update_template(template_id, request)
        
        logger.info(f"템플릿 수정 완료: {template.name}")
        return template
        
    except ValueError as e:
        logger.warning(f"템플릿 수정 실패: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"템플릿 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(template_id: int = Path(..., description="템플릿 ID")):
    """템플릿 삭제"""
    try:
        logger.info(f"템플릿 삭제 요청: {template_id}")
        
        success = template_service.delete_template(template_id)
        
        logger.info(f"템플릿 삭제 완료: {template_id}")
        return {"success": success, "message": "템플릿이 삭제되었습니다"}
        
    except ValueError as e:
        logger.warning(f"템플릿 삭제 실패: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"템플릿 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
