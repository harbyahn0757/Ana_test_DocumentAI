"""
건강검진 데이터 추출 시스템 - FastAPI 메인 애플리케이션

PDF 파일에서 테이블을 추출하고 키-값 관계를 설정하는 웹 API 서버
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from api.v1.router import api_router
from utils.logging_config import setup_logging

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="건강검진 데이터 추출 시스템",
    description="PDF 파일에서 테이블을 추출하고 키-값 관계를 설정하는 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트"""
    logger.info("건강검진 데이터 추출 시스템 시작")
    logger.info(f"Debug 모드: {settings.debug}")
    logger.info(f"허용된 Origins: {settings.allowed_origins}")
    
    # 필요한 디렉토리 생성
    settings.upload_dir.mkdir(exist_ok=True)
    settings.cache_dir.mkdir(exist_ok=True)
    settings.storage_dir.mkdir(exist_ok=True)
    
    logger.info("필요한 디렉토리들이 생성되었습니다")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    logger.info("건강검진 데이터 추출 시스템 종료")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 핸들러"""
    logger.error(f"HTTP 오류 {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 핸들러"""
    logger.error(f"서버 오류: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "서버 내부 오류가 발생했습니다",
            "status_code": 500
        }
    )


@app.get("/")
async def root():
    """루트 엔드포인트 - 서버 상태 확인"""
    return {
        "message": "건강검진 데이터 추출 시스템 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": settings.current_timestamp(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
