"""
분석 관련 데이터 모델

분석 요청/응답, 상태 관리 등의 Pydantic 모델 정의
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """분석 상태 열거형"""
    PENDING = "pending"           # 대기 중
    PROCESSING = "processing"     # 처리 중
    COMPLETED = "completed"       # 완료
    FAILED = "failed"            # 실패
    CANCELLED = "cancelled"      # 취소됨


class ExtractionLibrary(str, Enum):
    """추출 라이브러리 열거형"""
    PDFPLUMBER = "pdfplumber"
    CAMELOT = "camelot"
    TABULA = "tabula"


class AnalysisRequest(BaseModel):
    """분석 요청 모델"""
    
    file_id: str = Field(..., description="분석할 파일 ID")
    library: ExtractionLibrary = Field(default=ExtractionLibrary.PDFPLUMBER, description="추출 라이브러리")
    options: Optional[Dict[str, Any]] = Field(default=None, description="추출 옵션")
    
    @validator('file_id')
    def validate_file_id(cls, v):
        if not v or not v.strip():
            raise ValueError('파일 ID는 필수입니다')
        return v.strip()


class AnalysisResponse(BaseModel):
    """분석 응답 모델"""
    
    analysis_id: str = Field(..., description="분석 ID")
    status: AnalysisStatus = Field(..., description="분석 상태")
    message: str = Field(..., description="상태 메시지")
    progress: Optional[int] = Field(None, ge=0, le=100, description="진행률 (%)")
    started_at: Optional[datetime] = Field(None, description="시작 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    
    class Config:
        use_enum_values = True


class TableData(BaseModel):
    """표 데이터 모델"""
    
    page_number: int = Field(..., description="페이지 번호")
    table_index: int = Field(..., description="표 인덱스")
    data: List[List[str]] = Field(..., description="표 데이터 (2차원 배열)")
    headers: Optional[List[str]] = Field(None, description="헤더 정보")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="신뢰도")
    bbox: Optional[Dict[str, float]] = Field(None, description="바운딩 박스 좌표")


class AnalysisResults(BaseModel):
    """분석 결과 모델"""
    
    analysis_id: str = Field(..., description="분석 ID")
    file_id: str = Field(..., description="파일 ID")
    library: ExtractionLibrary = Field(..., description="사용된 라이브러리")
    status: AnalysisStatus = Field(..., description="분석 상태")
    tables: List[TableData] = Field(default=[], description="추출된 표 목록")
    total_tables: int = Field(default=0, description="총 표 개수")
    total_pages: int = Field(default=0, description="총 페이지 수")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")
    
    class Config:
        use_enum_values = True


class AnalysisProgress(BaseModel):
    """분석 진행률 모델"""
    
    analysis_id: str = Field(..., description="분석 ID")
    current_step: str = Field(..., description="현재 단계")
    progress: int = Field(..., ge=0, le=100, description="진행률 (%)")
    message: str = Field(..., description="진행 메시지")
    estimated_remaining: Optional[int] = Field(None, description="예상 남은 시간 (초)")


class AnalysisError(BaseModel):
    """분석 오류 모델"""
    
    analysis_id: str = Field(..., description="분석 ID")
    error_type: str = Field(..., description="오류 타입")
    error_message: str = Field(..., description="오류 메시지")
    error_details: Optional[Dict[str, Any]] = Field(None, description="오류 상세 정보")
    occurred_at: datetime = Field(default_factory=datetime.now, description="발생 시간")
