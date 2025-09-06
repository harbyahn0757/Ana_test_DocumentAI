"""
로깅 관련 상수 및 포맷 정의

표준화된 로깅 메시지 포맷과 상수들을 정의
"""

from typing import Dict

# 로깅 메시지 포맷 상수
class LogFormat:
    """로깅 메시지 포맷 상수 클래스"""
    
    # 기본 포맷
    SUCCESS = "{action} 완료: {details}"
    ERROR = "{action} 실패: {error}"
    WARNING = "{action} 경고: {message}"
    INFO = "{action}: {details}"
    DEBUG = "디버그 - {function}: {details}"
    
    # PDF 처리 관련
    PDF_START = "PDF 처리 시작: {filename}"
    PDF_SUCCESS = "PDF 처리 완료: {filename} ({processing_time:.2f}초)"
    PDF_ERROR = "PDF 처리 실패: {filename} - {error}"
    
    # 테이블 추출 관련
    TABLE_FOUND = "테이블 발견: 페이지 {page_num}, 테이블 {table_idx}"
    TABLE_EXTRACTED = "테이블 추출 완료: {table_count}개 테이블, {cell_count}개 셀"
    
    # 파일 관리 관련
    FILE_UPLOAD = "파일 업로드: {filename} ({file_size}MB)"
    FILE_DELETE = "파일 삭제: {filename}"
    
    # 관계 설정 관련
    RELATIONSHIP_CREATE = "관계 생성: {relationship_id}"
    RELATIONSHIP_APPLY = "관계 적용: {relationship_id}, 신뢰도 {confidence:.2f}"
    
    # 캐시 관련
    CACHE_HIT = "캐시 히트: {key}"
    CACHE_MISS = "캐시 미스: {key}"
    CACHE_SAVE = "캐시 저장: {key}"

# 로깅 레벨별 접두사
LEVEL_PREFIXES: Dict[str, str] = {
    "DEBUG": "[DEBUG]",
    "INFO": "[INFO]",
    "WARNING": "[WARNING]",
    "ERROR": "[ERROR]",
    "CRITICAL": "[CRITICAL]"
}

# 액션별 접두사
ACTION_PREFIXES: Dict[str, str] = {
    "start": "[START]",
    "complete": "[DONE]",
    "fail": "[FAIL]",
    "warning": "[WARN]",
    "processing": "[PROC]",
    "upload": "[UPLOAD]",
    "download": "[DOWNLOAD]",
    "delete": "[DELETE]",
    "create": "[CREATE]",
    "update": "[UPDATE]",
    "search": "[SEARCH]",
    "cache": "[CACHE]"
}

def format_log_message(template: str, **kwargs) -> str:
    """로그 메시지 포맷팅 헬퍼 함수
    
    Args:
        template (str): 메시지 템플릿
        **kwargs: 템플릿에 삽입할 변수들
        
    Returns:
        str: 포맷된 로그 메시지
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"로그 포맷 오류 - 누락된 키: {e}, 템플릿: {template}"
