"""
FastAPI 의존성 주입 관리

공통으로 사용되는 의존성들을 정의하고 관리
"""

from fastapi import Depends, HTTPException, UploadFile, File
from typing import Optional, List, Generator
import logging
from pathlib import Path

from app.config import settings
from services.file_service import FileService
from services.extraction_service import ExtractionService
from services.relationship_service import RelationshipService
from services.analysis_service import AnalysisService
from core.pdf_processor.factory import PDFProcessorFactory
from storage.cache_manager import CacheManager
from storage.file_storage import FileStorage

logger = logging.getLogger(__name__)


# ===== 서비스 의존성 =====

def get_file_service() -> FileService:
    """파일 서비스 의존성 주입"""
    return FileService(
        upload_dir=settings.upload_dir,
        samples_dir=settings.samples_dir,
        allowed_extensions=settings.allowed_extensions,
        max_file_size=settings.max_file_size
    )


def get_extraction_service() -> ExtractionService:
    """추출 서비스 의존성 주입"""
    return ExtractionService()


def get_relationship_service() -> RelationshipService:
    """관계 설정 서비스 의존성 주입"""
    file_storage = get_file_storage()
    
    return RelationshipService(storage=file_storage)


# 분석 서비스 싱글톤 인스턴스
_analysis_service_instance = None

def get_analysis_service() -> AnalysisService:
    """분석 서비스 의존성 주입 (싱글톤)"""
    global _analysis_service_instance
    if _analysis_service_instance is None:
        _analysis_service_instance = AnalysisService(
            file_service=get_file_service(),
            extraction_service=get_extraction_service()
        )
    return _analysis_service_instance


# ===== 스토리지 의존성 =====

def get_cache_manager() -> CacheManager:
    """캐시 매니저 의존성 주입"""
    return CacheManager(
        cache_dir=settings.cache_dir,
        ttl=settings.cache_ttl,
        enabled=settings.enable_cache
    )


def get_file_storage() -> FileStorage:
    """파일 스토리지 의존성 주입"""
    return FileStorage(
        storage_dir=settings.storage_dir
    )


# ===== 프로세서 팩토리 의존성 =====

def get_pdf_processor_factory() -> PDFProcessorFactory:
    """PDF 프로세서 팩토리 의존성 주입"""
    return PDFProcessorFactory()


# ===== 유효성 검증 의존성 =====

async def validate_file_upload(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service)
) -> UploadFile:
    """업로드 파일 유효성 검증"""
    
    # 파일명 검증
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="파일명이 없습니다"
        )
    
    # 확장자 검증
    if not file_service.validate_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용된 확장자: {settings.allowed_extensions}"
        )
    
    # 파일 크기 검증
    if hasattr(file, 'size') and file.size:
        if not file_service.validate_size(file.size):
            max_size_mb = settings.max_file_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {max_size_mb}MB"
            )
    
    logger.info(f"파일 업로드 검증 완료: {file.filename}")
    return file


def validate_extraction_library(library: str) -> str:
    """추출 라이브러리 유효성 검증"""
    if library not in settings.supported_libraries:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 라이브러리입니다. 지원 라이브러리: {settings.supported_libraries}"
        )
    return library


def validate_file_id(file_id: str) -> str:
    """파일 ID 유효성 검증"""
    if not file_id or len(file_id) < 8:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 파일 ID입니다"
        )
    return file_id


def validate_relationship_id(relationship_id: str) -> str:
    """관계 설정 ID 유효성 검증"""
    if not relationship_id:
        raise HTTPException(
            status_code=400,
            detail="관계 설정 ID가 필요합니다"
        )
    return relationship_id


# ===== 페이지네이션 의존성 =====

class PaginationParams:
    """페이지네이션 매개변수"""
    
    def __init__(
        self,
        page: int = 1,
        size: int = 10,
        max_size: int = 100
    ):
        self.page = max(1, page)
        self.size = min(max_size, max(1, size))
        self.offset = (self.page - 1) * self.size


def get_pagination_params(
    page: int = 1,
    size: int = 10
) -> PaginationParams:
    """페이지네이션 매개변수 의존성 주입"""
    return PaginationParams(page=page, size=size)


# ===== 정렬 및 필터링 의존성 =====

def get_sort_params(
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc"
) -> dict:
    """정렬 매개변수 의존성 주입"""
    allowed_sort_fields = ["created_at", "updated_at", "file_name", "file_size"]
    allowed_sort_orders = ["asc", "desc"]
    
    if sort_by and sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"정렬 필드가 유효하지 않습니다. 허용된 필드: {allowed_sort_fields}"
        )
    
    if sort_order not in allowed_sort_orders:
        sort_order = "asc"
    
    return {
        "sort_by": sort_by,
        "sort_order": sort_order
    }


# ===== 로깅 의존성 =====

def get_logger(name: str = __name__) -> logging.Logger:
    """로거 의존성 주입"""
    return logging.getLogger(name)


# ===== 설정 의존성 =====

def get_app_settings():
    """애플리케이션 설정 의존성 주입"""
    return settings


# ===== 백그라운드 작업 의존성 =====

class BackgroundTaskManager:
    """백그라운드 작업 관리자"""
    
    def __init__(self):
        self.tasks = {}
    
    def add_task(self, task_id: str, task_info: dict):
        """작업 추가"""
        self.tasks[task_id] = task_info
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """작업 정보 조회"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, update_info: dict):
        """작업 정보 업데이트"""
        if task_id in self.tasks:
            self.tasks[task_id].update(update_info)
    
    def remove_task(self, task_id: str):
        """작업 제거"""
        self.tasks.pop(task_id, None)


# 전역 백그라운드 작업 관리자
_background_task_manager = BackgroundTaskManager()


def get_background_task_manager() -> BackgroundTaskManager:
    """백그라운드 작업 관리자 의존성 주입"""
    return _background_task_manager


# ===== 헬스 체크 의존성 =====

async def check_system_health() -> dict:
    """시스템 헬스 체크"""
    health_status = {
        "status": "healthy",
        "timestamp": settings.current_timestamp(),
        "checks": {}
    }
    
    # 디렉토리 존재 확인
    health_status["checks"]["directories"] = {
        "upload_dir": settings.upload_dir.exists(),
        "cache_dir": settings.cache_dir.exists(),
        "storage_dir": settings.storage_dir.exists(),
        "samples_dir": settings.samples_dir.exists()
    }
    
    # 샘플 파일 개수 확인
    sample_files = settings.get_samples_files()
    health_status["checks"]["sample_files"] = {
        "count": len(sample_files),
        "available": len(sample_files) > 0
    }
    
    # 전체 상태 결정
    all_checks_passed = all(
        all(check.values()) if isinstance(check, dict) else check
        for check in health_status["checks"].values()
    )
    
    if not all_checks_passed:
        health_status["status"] = "degraded"
    
    return health_status


# ===== 에러 핸들링 의존성 =====

class ErrorHandler:
    """에러 처리 유틸리티"""
    
    @staticmethod
    def handle_file_not_found(file_id: str):
        """파일을 찾을 수 없는 경우"""
        raise HTTPException(
            status_code=404,
            detail=f"파일을 찾을 수 없습니다: {file_id}"
        )
    
    @staticmethod
    def handle_processing_error(error: Exception):
        """처리 중 오류 발생"""
        logger.error(f"처리 오류: {error}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="파일 처리 중 오류가 발생했습니다"
        )
    
    @staticmethod
    def handle_validation_error(field: str, value: str):
        """유효성 검증 오류"""
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 {field}: {value}"
        )
    
    @staticmethod
    def handle_analysis_not_found(analysis_id: str):
        """분석을 찾을 수 없는 경우"""
        raise HTTPException(
            status_code=404,
            detail=f"분석을 찾을 수 없습니다: {analysis_id}"
        )
    
    @staticmethod
    def handle_internal_error(message: str):
        """내부 서버 오류"""
        raise HTTPException(
            status_code=500,
            detail=message
        )


def get_error_handler() -> ErrorHandler:
    """에러 핸들러 의존성 주입"""
    return ErrorHandler()
