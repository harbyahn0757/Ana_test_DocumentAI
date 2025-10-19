"""
AI 추출 스트리밍 엔드포인트
Server-Sent Events를 사용한 실시간 진행 상황 스트리밍
"""

import json
import asyncio
import time
from typing import List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.ai_extraction_service import ai_extraction_service
from services.extraction_service import ExtractionService, get_extraction_service
from services.ai_extraction_service import AIExtractionRequest
from utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

class StreamExtractionRequest(BaseModel):
    """스트리밍 AI 추출 요청 모델"""
    file_id: str
    page_number: int
    table_data: List[List[str]]
    recognized_keys: List[Dict[str, Any]]

class ProgressEvent(BaseModel):
    """진행 상황 이벤트 모델"""
    event_type: str  # "progress", "key_start", "key_complete", "key_error", "complete"
    current: int
    total: int
    key_name: str = ""
    key_label: str = ""
    extracted_value: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    error_message: str = ""
    timestamp: float

async def create_progress_event(
    event_type: str,
    current: int,
    total: int,
    **kwargs
) -> str:
    """진행 상황 이벤트 생성"""
    event = ProgressEvent(
        event_type=event_type,
        current=current,
        total=total,
        timestamp=time.time(),
        **kwargs
    )
    return f"data: {event.model_dump_json()}\n\n"

async def stream_ai_extraction(request: StreamExtractionRequest) -> AsyncGenerator[str, None]:
    """AI 추출을 스트리밍으로 처리"""
    
    try:
        # 초기 상태 전송
        yield await create_progress_event(
            "start",
            current=0,
            total=len(request.recognized_keys)
        )
        
        # AI 서비스 사용 가능 여부 확인
        if not ai_extraction_service.is_available():
            yield await create_progress_event(
                "error",
                current=0,
                total=len(request.recognized_keys),
                error_message="AI 추출 서비스가 사용할 수 없습니다. OpenAI API 키를 확인해주세요."
            )
            return
        
        # 인식된 키가 없는 경우
        if not request.recognized_keys:
            yield await create_progress_event(
                "complete",
                current=0,
                total=0
            )
            return
        
        # AI 추출 요청 생성
        ai_requests = []
        for i, key_data in enumerate(request.recognized_keys):
            ai_request = AIExtractionRequest(
                key_name=key_data.get('key', ''),
                key_label=key_data.get('key_label', key_data.get('key', '')),
                anchor_cell=key_data.get('anchor_cell', {}),
                table_data=request.table_data,
                page_number=request.page_number,
                context=f"파일 ID: {request.file_id}"
            )
            ai_requests.append(ai_request)
        
        logger.info(f"🔄 스트리밍 AI 추출 시작: {len(ai_requests)}개 키")
        
        # 각 키별로 순차 처리 (진행 상황 실시간 전송)
        successful_extractions = 0
        results = []
        
        for i, ai_request in enumerate(ai_requests):
            current = i + 1
            
            # 키 처리 시작 이벤트
            yield await create_progress_event(
                "key_start",
                current=current,
                total=len(ai_requests),
                key_name=ai_request.key_name,
                key_label=ai_request.key_label
            )
            
            try:
                # AI 추출 실행
                logger.info(f"🤖 AI 추출 중 ({current}/{len(ai_requests)}): {ai_request.key_name}")
                result = await ai_extraction_service.extract_value(ai_request)
                
                if result and result.confidence >= 0.7:  # 신뢰도 임계값
                    # 성공 이벤트
                    yield await create_progress_event(
                        "key_success",
                        current=current,
                        total=len(ai_requests),
                        key_name=result.key_name,
                        key_label=ai_request.key_label,
                        extracted_value=result.extracted_value,
                        confidence=result.confidence,
                        reasoning=result.reasoning
                    )
                    
                    successful_extractions += 1
                    results.append({
                        "key": result.key_name,
                        "extracted_value": result.extracted_value,
                        "confidence": result.confidence,
                        "reasoning": result.reasoning,
                        "anchor_cell": ai_request.anchor_cell,
                        "suggested_position": result.suggested_position
                    })
                    
                    logger.info(f"✅ AI 추출 성공 ({current}/{len(ai_requests)}): {result.key_name} -> {result.extracted_value}")
                    
                else:
                    # 실패 이벤트 (신뢰도 부족 또는 값 없음)
                    failure_reason = "신뢰도 부족" if result else "값 없음"
                    confidence = result.confidence if result else 0.0
                    reasoning = result.reasoning if result else "값을 찾을 수 없습니다"
                    
                    yield await create_progress_event(
                        "key_failure",
                        current=current,
                        total=len(ai_requests),
                        key_name=ai_request.key_name,
                        key_label=ai_request.key_label,
                        confidence=confidence,
                        reasoning=reasoning,
                        error_message=failure_reason
                    )
                    
                    logger.warning(f"❌ AI 추출 실패 ({current}/{len(ai_requests)}): {ai_request.key_name} - {failure_reason}")
                
            except Exception as e:
                # 오류 이벤트
                yield await create_progress_event(
                    "key_error",
                    current=current,
                    total=len(ai_requests),
                    key_name=ai_request.key_name,
                    key_label=ai_request.key_label,
                    error_message=str(e)
                )
                
                logger.error(f"💥 AI 추출 오류 ({current}/{len(ai_requests)}): {ai_request.key_name} - {e}")
            
            # 잠시 대기 (너무 빠른 스트림 방지)
            await asyncio.sleep(0.1)
        
        # 완료 이벤트
        yield await create_progress_event(
            "complete",
            current=len(ai_requests),
            total=len(ai_requests),
            extracted_value=json.dumps({
                "results": results,
                "total_processed": len(ai_requests),
                "successful_extractions": successful_extractions
            })
        )
        
        logger.info(f"🎉 스트리밍 AI 추출 완료: {successful_extractions}/{len(ai_requests)} 성공")
        
    except Exception as e:
        logger.error(f"💥 스트리밍 AI 추출 전체 오류: {e}")
        yield await create_progress_event(
            "error",
            current=0,
            total=len(request.recognized_keys) if request.recognized_keys else 0,
            error_message=f"추출 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/extract-values-stream")
async def extract_values_with_ai_stream(
    request: StreamExtractionRequest,
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """
    AI를 사용하여 키에 대한 값을 스트리밍으로 추출
    
    Server-Sent Events를 통해 실시간 진행 상황을 전송합니다.
    
    Args:
        request: 스트리밍 AI 추출 요청 데이터
        extraction_service: 추출 서비스 의존성
        
    Returns:
        StreamingResponse: SSE 스트림
    """
    
    logger.info(f"🚀 스트리밍 AI 추출 요청: 파일 ID {request.file_id}, {len(request.recognized_keys)}개 키")
    
    async def event_generator():
        async for event in stream_ai_extraction(request):
            yield event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@router.get("/health")
async def health_check():
    """스트리밍 서비스 상태 확인"""
    return {
        "status": "healthy",
        "ai_available": ai_extraction_service.is_available(),
        "timestamp": time.time()
    }
