"""
로깅 설정 관리

애플리케이션 전체의 로깅을 설정하고 관리
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON 형태로 로그를 포맷하는 포매터"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON으로 포맷"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 예외 정보가 있으면 추가
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 추가 속성들
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = getattr(record, 'user_id', None)
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = getattr(record, 'request_id', None)
        if hasattr(record, 'file_id'):
            log_entry["file_id"] = getattr(record, 'file_id', None)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """컬러가 적용된 콘솔 로그 포매터"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # 청록색
        'INFO': '\033[32m',       # 녹색
        'WARNING': '\033[33m',    # 노란색
        'ERROR': '\033[31m',      # 빨간색
        'CRITICAL': '\033[35m',   # 자주색
        'RESET': '\033[0m'        # 리셋
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """컬러가 적용된 로그 메시지 포맷"""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # 레벨별 접두어
        level_prefix = {
            'DEBUG': '[DEBUG]',
            'INFO': '[INFO]',
            'WARNING': '[WARNING]',
            'ERROR': '[ERROR]',
            'CRITICAL': '[CRITICAL]'
        }
        
        prefix = level_prefix.get(record.levelname, '')
        
        # 기본 포맷 적용
        formatted = super().format(record)
        
        # 컬러와 접두어 적용
        return f"{log_color}{prefix} {formatted}{reset_color}"


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = False
) -> None:
    """로깅 시스템 설정
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로
        enable_console: 콘솔 로그 활성화 여부
        enable_file: 파일 로그 활성화 여부
        enable_json: JSON 형태 로그 활성화 여부
    """
    
    # 설정값 적용
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file
    
    # 로그 레벨 설정
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 포맷터 생성
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # 콘솔 핸들러
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        if enable_json:
            console_handler.setFormatter(formatter)
        else:
            # 개발 환경에서는 컬러 포매터 사용
            if settings.debug:
                console_formatter = ColoredFormatter(
                    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
                console_handler.setFormatter(console_formatter)
            else:
                console_handler.setFormatter(formatter)
        
        root_logger.addHandler(console_handler)
    
    # 파일 핸들러
    if enable_file and log_file:
        # 로그 디렉토리 생성
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 로테이팅 파일 핸들러 (10MB 단위로 로테이션, 최대 5개 파일)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        
        root_logger.addHandler(file_handler)
    
    # 특정 로거 설정
    configure_loggers()
    
    # 시작 로그
    logger = logging.getLogger(__name__)
    logger.info("로깅 시스템이 초기화되었습니다")
    logger.info(f"로그 레벨: {log_level}")
    logger.info(f"콘솔 로그: {'활성화' if enable_console else '비활성화'}")
    logger.info(f"파일 로그: {'활성화' if enable_file else '비활성화'}")
    logger.info(f"JSON 형식: {'활성화' if enable_json else '비활성화'}")


def configure_loggers():
    """특정 로거들에 대한 개별 설정"""
    
    # FastAPI 관련 로거
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # HTTP 클라이언트 로거 (너무 자세한 로그 방지)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # PDF 처리 라이브러리 로거
    logging.getLogger("pdfplumber").setLevel(logging.WARNING)
    logging.getLogger("camelot").setLevel(logging.WARNING)
    logging.getLogger("tabula").setLevel(logging.WARNING)
    
    # 애플리케이션 로거들
    app_loggers = [
        "app",
        "api",
        "core",
        "services",
        "models",
        "utils"
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)


def get_logger(name: str, **extra_fields) -> logging.LoggerAdapter:
    """추가 필드가 포함된 로거 어댑터 반환
    
    Args:
        name: 로거 이름
        **extra_fields: 추가 필드들 (user_id, request_id 등)
    
    Returns:
        LoggerAdapter: 추가 필드가 포함된 로거
    """
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, extra_fields)


def log_request_start(request_id: str, method: str, url: str, user_id: Optional[str] = None):
    """요청 시작 로그"""
    extra = {"request_id": request_id}
    if user_id:
        extra["user_id"] = user_id
    
    logger = get_logger("api.request", **extra)
    logger.info(f"요청 시작 - {method} {url}")


def log_request_end(request_id: str, status_code: int, duration: float):
    """요청 종료 로그"""
    logger = get_logger("api.request", request_id=request_id)
    
    status_text = "SUCCESS" if status_code < 400 else "ERROR"
    logger.info(f"요청 완료 - 상태: {status_code} ({status_text}), 소요시간: {duration:.3f}s")


def log_file_processing_start(file_id: str, filename: str, library: str):
    """파일 처리 시작 로그"""
    logger = get_logger("core.processing", file_id=file_id)
    logger.info(f"파일 처리 시작 - {filename} (라이브러리: {library})")


def log_file_processing_end(file_id: str, success: bool, duration: float, table_count: int = 0):
    """파일 처리 종료 로그"""
    logger = get_logger("core.processing", file_id=file_id)
    
    if success:
        logger.info(f"파일 처리 완료 - 테이블 {table_count}개 추출, 소요시간: {duration:.3f}s")
    else:
        logger.error(f"파일 처리 실패 - 소요시간: {duration:.3f}s")


def log_relationship_action(action: str, relationship_id: str, key_name: str):
    """관계 설정 액션 로그"""
    logger = get_logger("core.relationship")
    
    action_text = {
        "create": "생성",
        "update": "수정",
        "delete": "삭제",
        "apply": "적용"
    }
    
    text = action_text.get(action, action)
    logger.info(f"관계 설정 {text} - ID: {relationship_id}, 키: {key_name}")


# 예외 로깅을 위한 데코레이터
def log_exceptions(logger_name: Optional[str] = None):
    """예외를 자동으로 로깅하는 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"예외 발생 in {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
                )
                raise
        return wrapper
    return decorator


# 성능 측정을 위한 데코레이터
def log_performance(logger_name: Optional[str] = None):
    """함수 실행 시간을 로깅하는 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger = logging.getLogger(logger_name or func.__module__)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"{func.__name__} 실행 완료 - {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{func.__name__} 실행 실패 - {duration:.3f}s: {str(e)}")
                raise
        return wrapper
    return decorator
