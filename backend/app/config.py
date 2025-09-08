"""
애플리케이션 설정 관리

Pydantic Settings를 사용한 환경변수 기반 설정 관리
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import os


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # ===== 서버 설정 =====
    host: str = Field(default="localhost", description="서버 호스트")
    port: int = Field(default=8000, description="서버 포트")
    debug: bool = Field(default=True, description="디버그 모드")
    
    # ===== 보안 설정 =====
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT 토큰 서명용 시크릿 키"
    )
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000", "http://127.0.0.1:3000",
            "http://localhost:3003", "http://127.0.0.1:3003",
            "http://localhost:9002", "http://127.0.0.1:9002",
            "http://localhost:9003", "http://127.0.0.1:9003"
        ],
        description="CORS 허용 Origins"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="신뢰할 수 있는 호스트"
    )
    
    # ===== 파일 관리 설정 =====
    upload_dir: Path = Field(
        default=Path("uploads"),
        description="업로드된 파일 저장 디렉토리"
    )
    samples_dir: Path = Field(
        default=Path("../samples"),  # 프로젝트 루트의 samples 폴더
        description="샘플 파일 디렉토리"
    )
    cache_dir: Path = Field(
        default=Path("cache"),
        description="캐시 파일 저장 디렉토리"
    )
    storage_dir: Path = Field(
        default=Path("storage"),
        description="관계 설정 등 데이터 저장 디렉토리"
    )
    
    # ===== 파일 업로드 제한 =====
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="최대 파일 크기 (바이트)"
    )
    allowed_extensions: List[str] = Field(
        default=[".pdf", ".png", ".jpg", ".jpeg"],
        description="허용된 파일 확장자"
    )
    
    # ===== PDF 처리 설정 =====
    default_extraction_library: str = Field(
        default="pdfplumber",
        description="기본 PDF 추출 라이브러리"
    )
    supported_libraries: List[str] = Field(
        default=["pdfplumber", "camelot", "tabula"],
        description="지원하는 PDF 추출 라이브러리"
    )
    
    # ===== 캐시 설정 =====
    cache_ttl: int = Field(
        default=3600,  # 1시간
        description="캐시 TTL (초)"
    )
    enable_cache: bool = Field(
        default=True,
        description="캐시 사용 여부"
    )
    
    # ===== Redis 설정 (백그라운드 작업용) =====
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 연결 URL"
    )
    
    # ===== 로깅 설정 =====
    log_level: str = Field(
        default="INFO",
        description="로그 레벨"
    )
    log_file: Optional[str] = Field(
        default="logs/app.log",
        description="로그 파일 경로"
    )
    
    # ===== PDF 처리 상수 =====
    # Camelot 처리기 기본값
    camelot_edge_tol: int = Field(
        default=50,
        description="Camelot 선 감지 허용 오차"
    )
    camelot_row_tol: int = Field(
        default=2,
        description="Camelot 행 감지 허용 오차"
    )
    camelot_column_tol: int = Field(
        default=0,
        description="Camelot 열 감지 허용 오차"
    )
    
    # PDFPlumber 처리기 기본값
    pdfplumber_edge_min_length: int = Field(
        default=3,
        description="PDFPlumber 최소 선 길이"
    )
    pdfplumber_intersection_tolerance: int = Field(
        default=1,
        description="PDFPlumber 교차점 허용 오차"
    )
    
    # 관계 설정 신뢰도 가중치
    confidence_base: float = Field(
        default=0.5,
        description="기본 신뢰도"
    )
    confidence_anchor_weight: float = Field(
        default=0.3,
        description="앵커 유사도 가중치"
    )
    confidence_value_weight: float = Field(
        default=0.2,
        description="값 존재 가중치"
    )
    confidence_numeric_weight: float = Field(
        default=0.1,
        description="숫자 값 가중치"
    )
    
    # 텍스트 유사도 점수
    text_similarity_exact: float = Field(
        default=1.0,
        description="정확히 일치하는 텍스트 유사도"
    )
    text_similarity_case_insensitive: float = Field(
        default=0.9,
        description="대소문자 무시 일치 유사도"
    )
    text_similarity_partial: float = Field(
        default=0.7,
        description="부분 일치 유사도"
    )
    text_similarity_default: float = Field(
        default=0.3,
        description="기본 유사도"
    )
    
    # 테이블 메타데이터 기본값
    table_confidence_base: float = Field(
        default=0.6,
        description="테이블 기본 신뢰도"
    )
    table_min_rows_bonus: int = Field(
        default=3,
        description="신뢰도 증가를 위한 최소 행 수"
    )
    table_min_cols_bonus: int = Field(
        default=2,
        description="신뢰도 증가를 위한 최소 열 수"
    )
    
    @validator('upload_dir', 'cache_dir', 'storage_dir', 'samples_dir')
    def create_directories(cls, v):
        """디렉토리가 존재하지 않으면 생성"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(exist_ok=True, parents=True)
        return v
    
    @validator('allowed_extensions')
    def normalize_extensions(cls, v):
        """확장자를 소문자로 정규화"""
        return [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in v]
    
    @validator('default_extraction_library')
    def validate_extraction_library(cls, v, values):
        """기본 추출 라이브러리가 지원 목록에 있는지 확인"""
        # 기본 지원 라이브러리 목록
        default_supported = ["pdfplumber", "camelot", "tabula"]
        supported = values.get('supported_libraries', default_supported)
        if v not in supported:
            raise ValueError(f"기본 라이브러리 '{v}'는 지원 목록에 없습니다: {supported}")
        return v
    
    def get_samples_files(self) -> List[str]:
        """샘플 디렉토리의 파일 목록 반환"""
        if not self.samples_dir.exists():
            return []
        
        files = []
        for ext in self.allowed_extensions:
            files.extend(self.samples_dir.glob(f"*{ext}"))
        
        return [f.name for f in files]
    
    def get_absolute_samples_dir(self) -> Path:
        """샘플 디렉토리의 절대 경로 반환"""
        return self.samples_dir.resolve()
    
    def validate_file_extension(self, filename: str) -> bool:
        """파일 확장자 검증"""
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions
    
    def validate_file_size(self, file_size: int) -> bool:
        """파일 크기 검증"""
        return file_size <= self.max_file_size
    
    @staticmethod
    def current_timestamp() -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().isoformat()
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # 환경변수 접두사 설정
        env_prefix = "HEALTH_EXTRACTION_"


# 전역 설정 인스턴스
settings = Settings()


# 개발 환경용 설정 오버라이드
class DevelopmentSettings(Settings):
    """개발 환경 설정"""
    debug: bool = True
    log_level: str = "DEBUG"
    allowed_origins: List[str] = ["*"]  # 개발 시에는 모든 Origin 허용


# 프로덕션 환경용 설정
class ProductionSettings(Settings):
    """프로덕션 환경 설정"""
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = Field(default_factory=lambda: "PRODUCTION_SECRET_KEY_CHANGE_ME", description="프로덕션에서는 반드시 설정 필요")
    
    @validator('allowed_origins')
    def validate_production_origins(cls, v):
        """프로덕션에서는 와일드카드 허용하지 않음"""
        if "*" in v:
            raise ValueError("프로덕션 환경에서는 와일드카드 Origin을 허용할 수 없습니다")
        return v


def get_settings() -> Settings:
    """환경에 따른 설정 반환"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "development":
        return DevelopmentSettings()
    else:
        return Settings()


# 현재 환경의 설정
current_settings = get_settings()
