"""
API v1 라우터 통합

모든 v1 API 엔드포인트를 통합하고 관리
"""

from fastapi import APIRouter

from api.v1.endpoints import files, extraction, tables, relationships, analysis, templates, ai_extraction, ai_extraction_stream, key_database, pattern_management, prompt_debug

# 메인 API v1 라우터
api_router = APIRouter()

# 각 모듈별 라우터 등록
api_router.include_router(
    files.router,
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "파일을 찾을 수 없음"}}
)

api_router.include_router(
    extraction.router,
    prefix="/extraction",
    tags=["extraction"],
    responses={500: {"description": "추출 처리 오류"}}
)

api_router.include_router(
    tables.router,
    prefix="/tables",
    tags=["tables"],
    responses={404: {"description": "테이블 데이터를 찾을 수 없음"}}
)

api_router.include_router(
    relationships.router,
    prefix="/relationships",
    tags=["relationships"],
    responses={404: {"description": "관계 설정을 찾을 수 없음"}}
)

api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["analysis"],
    responses={500: {"description": "분석 처리 오류"}}
)

api_router.include_router(
    templates.router,
    prefix="/templates",
    tags=["templates"],
    responses={404: {"description": "템플릿을 찾을 수 없음"}}
)

api_router.include_router(
    ai_extraction.router,
    prefix="/ai-extraction",
    tags=["ai-extraction"],
    responses={503: {"description": "AI 서비스 사용 불가"}}
)

api_router.include_router(
    ai_extraction_stream.router,
    prefix="/ai-extraction",
    tags=["ai-extraction-stream"],
    responses={503: {"description": "AI 스트리밍 서비스 사용 불가"}}
)

api_router.include_router(
    key_database.router,
    prefix="/extraction",
    tags=["key-database"],
    responses={500: {"description": "키 데이터베이스 처리 오류"}}
)

api_router.include_router(
    pattern_management.router,
    prefix="/patterns",
    tags=["pattern-management"],
    responses={500: {"description": "패턴 관리 처리 오류"}}
)

api_router.include_router(
    prompt_debug.router,
    prefix="/prompt-debug",
    tags=["prompt-debug"],
    responses={500: {"description": "프롬프트 디버깅 처리 오류"}}
)
