"""
키 데이터베이스 관리 API 엔드포인트
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# 키 데이터베이스 파일 경로
KEY_DATABASE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "key_database.json"


class KeyDatabaseResponse(BaseModel):
    """키 데이터베이스 응답 모델"""
    success: bool
    data: Dict[str, Dict[str, list]]
    message: str


class KeyDatabaseUpdateRequest(BaseModel):
    """키 데이터베이스 업데이트 요청 모델"""
    key_database: Dict[str, Dict[str, list]]


def load_key_database() -> Dict[str, Dict[str, list]]:
    """키 데이터베이스 로드"""
    try:
        if KEY_DATABASE_PATH.exists():
            with open(KEY_DATABASE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"키 데이터베이스 로드 완료: {list(data.keys())}")
                return data
        else:
            logger.warning(f"키 데이터베이스 파일이 존재하지 않습니다: {KEY_DATABASE_PATH}")
            return {}
    except Exception as e:
        logger.error(f"키 데이터베이스 로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"키 데이터베이스 로드 실패: {str(e)}")


def save_key_database(key_database: Dict[str, Dict[str, list]]) -> bool:
    """키 데이터베이스 저장"""
    try:
        # 디렉토리가 없으면 생성
        KEY_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(KEY_DATABASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(key_database, f, ensure_ascii=False, indent=2)
        
        logger.info(f"키 데이터베이스 저장 완료: {KEY_DATABASE_PATH}")
        return True
    except Exception as e:
        logger.error(f"키 데이터베이스 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"키 데이터베이스 저장 실패: {str(e)}")


@router.get("/key-database")
async def get_key_database():
    """키 데이터베이스 조회"""
    try:
        logger.info("키 데이터베이스 조회 요청")
        
        key_database = load_key_database()
        logger.info(f"로드된 키 데이터베이스: {list(key_database.keys())}")
        
        # 모든 카테고리가 포함되어 있는지 확인
        required_categories = ['basic', 'special', 'cancer', 'comprehensive']
        for category in required_categories:
            if category not in key_database:
                logger.warning(f"누락된 카테고리: {category}")
                key_database[category] = {}
        
        # 프론트엔드가 기대하는 형식으로 응답
        return {
            "success": True,
            "data": key_database,
            "message": "키 데이터베이스 조회 성공"
        }
    except Exception as e:
        logger.error(f"키 데이터베이스 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"키 데이터베이스 조회 실패: {str(e)}")


@router.post("/key-database")
async def update_key_database(request: KeyDatabaseUpdateRequest):
    """키 데이터베이스 업데이트"""
    try:
        logger.info("키 데이터베이스 업데이트 요청")
        
        # 키 데이터베이스 저장
        save_key_database(request.key_database)
        
        # 프론트엔드가 기대하는 형식으로 응답
        return {
            "success": True,
            "data": request.key_database,
            "message": "키 데이터베이스 업데이트 성공"
        }
    except Exception as e:
        logger.error(f"키 데이터베이스 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"키 데이터베이스 업데이트 실패: {str(e)}")


@router.get("/key-database/health")
async def check_key_database_health():
    """키 데이터베이스 상태 확인"""
    try:
        key_database = load_key_database()
        
        total_keys = sum(len(keys) for keys in key_database.values())
        
        return {
            "status": "healthy",
            "file_exists": KEY_DATABASE_PATH.exists(),
            "total_categories": len(key_database),
            "total_keys": total_keys,
            "categories": list(key_database.keys())
        }
    except Exception as e:
        logger.error(f"키 데이터베이스 상태 확인 실패: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
