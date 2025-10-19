"""
패턴 관리 API 엔드포인트
새로운 앵커 텍스트 패턴을 기존 키에 추가하는 기능 제공
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging
import json
from pathlib import Path
from pydantic import BaseModel

from services.extraction_service import ExtractionService, get_extraction_service

logger = logging.getLogger(__name__)

router = APIRouter()

class PatternAddRequest(BaseModel):
    """패턴 추가 요청 모델"""
    key_name: str
    anchor_text: str
    category: str = "basic"  # personal, basic, special, cancer, comprehensive
    
class PatternAddResponse(BaseModel):
    """패턴 추가 응답 모델"""
    success: bool
    message: str
    updated_patterns: List[str]

@router.post("/add-pattern", response_model=PatternAddResponse)
async def add_pattern_to_key(
    request: PatternAddRequest,
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """
    기존 키에 새로운 앵커 텍스트 패턴 추가
    """
    try:
        logger.info(f"패턴 추가 요청: {request.key_name}에 '{request.anchor_text}' 추가")
        
        # key_mapping_database.json 파일 경로
        db_path = Path(__file__).parent.parent.parent.parent / "data" / "key_mapping_database.json"
        
        # 기존 데이터 로드
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 카테고리 및 키 존재 확인
        if request.category not in data:
            raise HTTPException(status_code=400, detail=f"카테고리 '{request.category}'를 찾을 수 없습니다")
        
        if request.key_name not in data[request.category]:
            raise HTTPException(status_code=400, detail=f"키 '{request.key_name}'을 카테고리 '{request.category}'에서 찾을 수 없습니다")
        
        # 중복 패턴 확인
        existing_patterns = data[request.category][request.key_name]
        if request.anchor_text in existing_patterns:
            return PatternAddResponse(
                success=False,
                message=f"패턴 '{request.anchor_text}'이 이미 존재합니다",
                updated_patterns=existing_patterns
            )
        
        # 새 패턴 추가
        existing_patterns.append(request.anchor_text)
        
        # 파일에 저장
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"패턴 추가 완료: {request.key_name}에 '{request.anchor_text}' 추가됨")
        
        return PatternAddResponse(
            success=True,
            message=f"패턴 '{request.anchor_text}'이 키 '{request.key_name}'에 성공적으로 추가되었습니다",
            updated_patterns=existing_patterns
        )
        
    except Exception as e:
        logger.error(f"패턴 추가 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"패턴 추가 중 오류가 발생했습니다: {str(e)}")

@router.get("/suggest-patterns/{file_path:path}")
async def get_pattern_suggestions(
    file_path: str,
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """
    파일에서 새로운 패턴 제안 가져오기
    """
    try:
        logger.info(f"패턴 제안 요청: {file_path}")
        
        # 키 인식 수행
        result = await extraction_service.recognize_keys(file_path)
        
        # 패턴 제안만 반환
        return {
            "pattern_suggestions": result.get("pattern_suggestions", []),
            "suggestions_count": result.get("suggestions_count", 0)
        }
        
    except Exception as e:
        logger.error(f"패턴 제안 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"패턴 제안 중 오류가 발생했습니다: {str(e)}")



