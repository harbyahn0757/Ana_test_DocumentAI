"""
파일 관련 데이터 모델

파일 정보, 업로드 요청/응답 등의 Pydantic 모델 정의
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from enum import Enum


class FileStatus(str, Enum):
    """파일 상태 열거형"""
    UPLOADED = "uploaded"           # 업로드 완료
    PROCESSING = "processing"       # 처리 중
    PROCESSED = "processed"         # 처리 완료
    ERROR = "error"                # 오류 발생
    DELETED = "deleted"            # 삭제됨


class FileType(str, Enum):
    """파일 타입 열거형"""
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"


class FileInfo(BaseModel):
    """파일 정보 모델"""
    
    # 기본 필드들  
    file_id: Optional[str] = Field(None, description="파일 고유 ID")
    file_name: str = Field(..., description="파일명")
    file_path: str = Field(..., description="저장된 파일 경로")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    file_type: FileType = Field(..., description="파일 타입")
    mime_type: Optional[str] = Field(None, description="MIME 타입")
    status: FileStatus = Field(default=FileStatus.UPLOADED, description="파일 상태")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="업로드 일시")
    updated_at: Optional[datetime] = Field(None, description="최종 수정 일시")
    file_hash: Optional[str] = Field(None, description="파일 해시값")
    memo: Optional[str] = Field(None, description="파일 메모")
    
    # 호환성 프로퍼티들
    @property
    def filename(self) -> str:
        """호환성을 위한 filename 프로퍼티"""
        return self.file_name
    
    @property
    def size(self) -> int:
        """호환성을 위한 size 프로퍼티"""
        return self.file_size
    
    # 추가 메타데이터
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")
    
    @validator('file_name')
    def validate_filename(cls, v):
        """파일명 유효성 검증"""
        if not v or v.strip() == "":
            raise ValueError("파일명은 비어있을 수 없습니다")
        return v.strip()
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """파일 크기 유효성 검증"""
        if v < 0:
            raise ValueError("파일 크기는 0 이상이어야 합니다")
        return v
    
    @property
    def file_size_mb(self) -> float:
        """파일 크기를 MB 단위로 반환"""
        file_size = self.size or self.file_size or 0
        return round(file_size / (1024 * 1024), 2)
    
    @property
    def file_extension(self) -> str:
        """파일 확장자 반환"""
        filename = self.filename or self.file_name or ""
        return Path(filename).suffix.lower() if filename else ""
    
    class Config:
        """Pydantic 설정"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SampleFileInfo(BaseModel):
    """샘플 파일 정보 모델"""
    
    # 기본 필드들
    file_name: str = Field(..., description="샘플 파일명")
    file_path: str = Field(..., description="샘플 파일 경로")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    file_type: Optional[FileType] = Field(None, description="파일 타입")
    display_name: Optional[str] = Field(None, description="표시용 이름")
    description: Optional[str] = Field(None, description="파일 설명")
    
    # 호환성 프로퍼티들
    @property
    def filename(self) -> str:
        """호환성을 위한 filename 프로퍼티"""
        return self.file_name
    
    @property
    def size(self) -> int:
        """호환성을 위한 size 프로퍼티"""
        return self.file_size
    
    @property
    def file_size_mb(self) -> float:
        """파일 크기를 MB 단위로 반환"""
        file_size = self.size or self.file_size or 0
        return round(file_size / (1024 * 1024), 2)


class FileUploadRequest(BaseModel):
    """파일 업로드 요청 모델"""
    
    description: Optional[str] = Field(None, description="파일 설명")
    tags: Optional[List[str]] = Field(default_factory=list, description="파일 태그")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 모델"""
    
    file_id: str = Field(..., description="생성된 파일 ID")
    file_name: str = Field(..., description="업로드된 파일명")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    message: str = Field(..., description="결과 메시지")
    file_info: FileInfo = Field(..., description="상세 파일 정보")
    
    @property
    def file_size_mb(self) -> float:
        """파일 크기를 MB 단위로 반환"""
        return round(self.file_size / (1024 * 1024), 2)


class FileListResponse(BaseModel):
    """파일 목록 응답 모델"""
    
    files: List[FileInfo] = Field(..., description="파일 목록")
    total_count: int = Field(..., description="총 파일 개수")
    message: str = Field(..., description="결과 메시지")
    
    # 페이지네이션 정보 (선택적)
    page: Optional[int] = Field(None, description="현재 페이지")
    page_size: Optional[int] = Field(None, description="페이지 크기")
    total_pages: Optional[int] = Field(None, description="총 페이지 수")


class SampleFilesResponse(BaseModel):
    """샘플 파일 목록 응답 모델"""
    
    samples: List[SampleFileInfo] = Field(..., description="샘플 파일 목록")
    total_count: int = Field(..., description="총 샘플 파일 개수")
    samples_dir: str = Field(..., description="샘플 디렉토리 경로")
    message: str = Field(..., description="결과 메시지")


class FileDeleteRequest(BaseModel):
    """파일 삭제 요청 모델"""
    
    file_ids: List[str] = Field(..., description="삭제할 파일 ID 목록")
    force_delete: bool = Field(default=False, description="강제 삭제 여부")


class FileDeleteResponse(BaseModel):
    """파일 삭제 응답 모델"""
    
    success: bool = Field(..., description="삭제 성공 여부")
    message: str = Field(..., description="결과 메시지")
    deleted_file_id: Optional[str] = Field(None, description="삭제된 파일 ID")
    error_details: Optional[str] = Field(None, description="오류 상세 정보")


class BatchDeleteResult(BaseModel):
    """일괄 삭제 결과 개별 항목"""
    
    file_id: str = Field(..., description="파일 ID")
    success: bool = Field(..., description="삭제 성공 여부")
    message: str = Field(..., description="결과 메시지")
    error_details: Optional[str] = Field(None, description="오류 상세 정보")


class BatchDeleteResponse(BaseModel):
    """일괄 삭제 응답 모델"""
    
    total_requested: int = Field(..., description="요청된 총 파일 수")
    successful_deletions: int = Field(..., description="성공한 삭제 수")
    failed_deletions: int = Field(..., description="실패한 삭제 수")
    results: List[BatchDeleteResult] = Field(..., description="개별 결과 목록")
    message: str = Field(..., description="전체 결과 메시지")


class FileStatistics(BaseModel):
    """파일 통계 정보 모델"""
    
    total_files: int = Field(..., description="총 파일 수")
    total_size_bytes: int = Field(..., description="총 파일 크기 (바이트)")
    file_types: Dict[str, int] = Field(..., description="파일 타입별 개수")
    status_distribution: Dict[str, int] = Field(..., description="상태별 분포")
    upload_trend: Optional[Dict[str, int]] = Field(None, description="업로드 트렌드")
    
    @property
    def total_size_mb(self) -> float:
        """총 파일 크기를 MB 단위로 반환"""
        return round(self.total_size_bytes / (1024 * 1024), 2)
    
    @property
    def total_size_gb(self) -> float:
        """총 파일 크기를 GB 단위로 반환"""
        return round(self.total_size_bytes / (1024 * 1024 * 1024), 2)
    
    @property
    def average_file_size_mb(self) -> float:
        """평균 파일 크기를 MB 단위로 반환"""
        if self.total_files == 0:
            return 0.0
        return round((self.total_size_bytes / self.total_files) / (1024 * 1024), 2)


class FileUpdateRequest(BaseModel):
    """파일 정보 업데이트 요청 모델"""
    
    file_name: Optional[str] = Field(None, description="새 파일명")
    description: Optional[str] = Field(None, description="파일 설명")
    tags: Optional[List[str]] = Field(None, description="파일 태그")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")
    
    @validator('file_name')
    def validate_filename(cls, v):
        """파일명 유효성 검증"""
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("파일명은 비어있을 수 없습니다")
        return v.strip() if v else v


class FileSearchRequest(BaseModel):
    """파일 검색 요청 모델"""
    
    query: Optional[str] = Field(None, description="검색 쿼리")
    file_types: Optional[List[FileType]] = Field(None, description="파일 타입 필터")
    status_filter: Optional[List[FileStatus]] = Field(None, description="상태 필터")
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    size_min: Optional[int] = Field(None, description="최소 파일 크기")
    size_max: Optional[int] = Field(None, description="최대 파일 크기")
    
    # 정렬 옵션
    sort_by: Optional[str] = Field("uploaded_at", description="정렬 기준")
    sort_order: Optional[str] = Field("desc", description="정렬 순서 (asc/desc)")
    
    # 페이지네이션
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(20, ge=1, le=100, description="페이지 크기")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """정렬 기준 유효성 검증"""
        allowed_fields = ["file_name", "file_size", "uploaded_at", "updated_at", "status"]
        if v not in allowed_fields:
            raise ValueError(f"정렬 기준은 다음 중 하나여야 합니다: {allowed_fields}")
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """정렬 순서 유효성 검증"""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("정렬 순서는 'asc' 또는 'desc'여야 합니다")
        return v.lower()


class FileSearchResponse(BaseModel):
    """파일 검색 응답 모델"""
    
    files: List[FileInfo] = Field(..., description="검색된 파일 목록")
    total_count: int = Field(..., description="총 검색 결과 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_pages: int = Field(..., description="총 페이지 수")
    query: Optional[str] = Field(None, description="검색 쿼리")
    filters_applied: Dict[str, Any] = Field(..., description="적용된 필터")
    message: str = Field(..., description="결과 메시지")
