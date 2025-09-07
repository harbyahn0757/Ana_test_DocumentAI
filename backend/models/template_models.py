"""
템플릿 모델
추출 템플릿 저장을 위한 데이터 모델
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TemplateStatus(str, Enum):
    """템플릿 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class KeyMapping(BaseModel):
    """키-값 매핑 모델"""
    id: int = Field(description="매핑 ID")
    key: str = Field(description="추출 키")
    key_label: str = Field(description="키 라벨")
    anchor_cell: Optional[Dict[str, Any]] = Field(None, description="앵커 셀 정보")
    value_cell: Optional[Dict[str, Any]] = Field(None, description="값 셀 정보")
    relative_position: Optional[Dict[str, int]] = Field(None, description="상대 위치")
    created_at: str = Field(description="생성 시간")


class FileInfo(BaseModel):
    """파일 정보 모델"""
    name: str = Field(description="파일명")
    size: int = Field(description="파일 크기")
    last_modified: Optional[datetime] = Field(None, description="마지막 수정 시간")


class ExtractionTemplate(BaseModel):
    """추출 템플릿 모델"""
    id: Optional[int] = Field(None, description="템플릿 ID")
    name: str = Field(description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    mappings: List[KeyMapping] = Field(description="키-값 매핑 목록")
    file_info: Optional[FileInfo] = Field(None, description="기준 파일 정보")
    status: TemplateStatus = Field(TemplateStatus.ACTIVE, description="템플릿 상태")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.now, description="수정 시간")
    created_by: Optional[str] = Field(None, description="생성자")


class TemplateCreateRequest(BaseModel):
    """템플릿 생성 요청"""
    name: str = Field(description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    mappings: List[Dict[str, Any]] = Field(description="키-값 매핑 목록")
    file_info: Optional[Dict[str, Any]] = Field(None, description="기준 파일 정보")


class TemplateUpdateRequest(BaseModel):
    """템플릿 수정 요청"""
    name: Optional[str] = Field(None, description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    mappings: Optional[List[Dict[str, Any]]] = Field(None, description="키-값 매핑 목록")
    status: Optional[TemplateStatus] = Field(None, description="템플릿 상태")


class TemplateResponse(BaseModel):
    """템플릿 응답"""
    id: int = Field(description="템플릿 ID")
    name: str = Field(description="템플릿 이름")
    description: Optional[str] = Field(description="템플릿 설명")
    mappings: List[KeyMapping] = Field(description="키-값 매핑 목록")
    file_info: Optional[FileInfo] = Field(description="기준 파일 정보")
    status: TemplateStatus = Field(description="템플릿 상태")
    created_at: datetime = Field(description="생성 시간")
    updated_at: datetime = Field(description="수정 시간")
    created_by: Optional[str] = Field(description="생성자")


class TemplateListResponse(BaseModel):
    """템플릿 목록 응답"""
    templates: List[TemplateResponse] = Field(description="템플릿 목록")
    total_count: int = Field(description="전체 개수")
    page: int = Field(description="현재 페이지")
    page_size: int = Field(description="페이지 크기")
    total_pages: int = Field(description="전체 페이지 수")
