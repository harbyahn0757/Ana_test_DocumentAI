"""
AI 기반 값 추출 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from services.ai_extraction_service import (
    ai_extraction_service, 
    AIExtractionRequest, 
    AIExtractionResult
)
from services.extraction_service import ExtractionService
from app.dependencies import get_extraction_service

logger = logging.getLogger(__name__)

router = APIRouter()


class AIExtractionRequestModel(BaseModel):
    """AI 추출 요청 모델"""
    file_id: str = Field(..., description="파일 ID")
    recognized_keys: List[Dict[str, Any]] = Field(..., description="인식된 키 목록")
    page_number: int = Field(..., description="페이지 번호")
    table_data: List[List[str]] = Field(..., description="테이블 데이터")


class AIExtractionResponseModel(BaseModel):
    """AI 추출 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    results: List[Dict[str, Any]] = Field(..., description="추출 결과 목록")
    total_processed: int = Field(..., description="처리된 키 수")
    successful_extractions: int = Field(..., description="성공적으로 추출된 키 수")
    processing_time: float = Field(..., description="전체 처리 시간")
    model_used: str = Field(..., description="사용된 AI 모델")


class AIExtractionStatusModel(BaseModel):
    """AI 추출 상태 모델"""
    available: bool = Field(..., description="AI 서비스 사용 가능 여부")
    model: str = Field(..., description="사용 중인 AI 모델")
    confidence_threshold: float = Field(..., description="신뢰도 임계값")


@router.get("/status", response_model=AIExtractionStatusModel)
async def get_ai_extraction_status():
    """AI 추출 서비스 상태 확인"""
    try:
        available = ai_extraction_service.is_available()
        model = "gpt-4o-mini" if available else "N/A"
        
        return AIExtractionStatusModel(
            available=available,
            model=model,
            confidence_threshold=0.7  # settings에서 가져와야 함
        )
    except Exception as e:
        logger.error(f"AI 추출 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail="AI 서비스 상태 확인 실패")


@router.post("/extract-values", response_model=AIExtractionResponseModel)
async def extract_values_with_ai(
    request: AIExtractionRequestModel,
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """
    AI를 사용하여 키에 대한 값을 추출
    
    Args:
        request: AI 추출 요청 데이터
        extraction_service: 추출 서비스 의존성
        
    Returns:
        AIExtractionResponseModel: 추출 결과
    """
    import time
    start_time = time.time()
    
    try:
        # AI 서비스 사용 가능 여부 확인
        if not ai_extraction_service.is_available():
            raise HTTPException(
                status_code=503, 
                detail="AI 추출 서비스가 사용할 수 없습니다. OpenAI API 키를 확인해주세요."
            )
        
        # 인식된 키가 없는 경우
        if not request.recognized_keys:
            return AIExtractionResponseModel(
                success=True,
                results=[],
                total_processed=0,
                successful_extractions=0,
                processing_time=time.time() - start_time,
                model_used="N/A"
            )
        
        # AI 추출 요청 생성
        ai_requests = []
        logger.info(f"🔍 AI 추출 요청 데이터 분석:")
        logger.info(f"   파일 ID: {request.file_id}")
        logger.info(f"   페이지 번호: {request.page_number}")
        logger.info(f"   테이블 데이터 크기: {len(request.table_data)}x{len(request.table_data[0]) if request.table_data else 0}")
        logger.info(f"   인식된 키 수: {len(request.recognized_keys)}")
        
        for i, key_data in enumerate(request.recognized_keys):
            logger.info(f"   키 {i+1}: {key_data.get('key', 'N/A')}")
            logger.info(f"     - key_label: {key_data.get('key_label', 'N/A')}")
            logger.info(f"     - anchor_cell: {key_data.get('anchor_cell', {})}")
            
            ai_request = AIExtractionRequest(
                key_name=key_data.get('key', ''),
                key_label=key_data.get('key_label', key_data.get('key', '')),
                anchor_cell=key_data.get('anchor_cell', {}),
                table_data=request.table_data,
                page_number=request.page_number,
                context=f"파일 ID: {request.file_id}"
            )
            ai_requests.append(ai_request)
        
        # AI 추출 실행
        ai_results = await ai_extraction_service.batch_extract_values(ai_requests)
        
        # AI 추출 결과 로깅
        logger.info(f"🤖 AI 추출 결과 분석:")
        logger.info(f"   총 결과 수: {len(ai_results)}")
        for i, result in enumerate(ai_results):
            if result:
                logger.info(f"   결과 {i+1}: {result.key_name}")
                logger.info(f"     - 추출된 값: {result.extracted_value}")
                logger.info(f"     - 신뢰도: {result.confidence:.2f}")
                logger.info(f"     - 제안 위치: {result.suggested_position}")
                logger.info(f"     - 추론 과정: {result.reasoning}")
            else:
                logger.info(f"   결과 {i+1}: 실패 (None)")
        
        # 결과 변환
        results = []
        successful_extractions = 0
        
        for result in ai_results:
            if result and result.confidence >= 0.7:  # 신뢰도 임계값
                successful_extractions += 1
                
                # 원본 키 데이터에서 앵커 셀 정보 가져오기
                original_key = None
                for key_data in request.recognized_keys:
                    if key_data.get('key') == result.key_name:
                        original_key = key_data
                        break
                
                # 기존 키 데이터와 AI 결과 결합
                result_data = {
                    "key": result.key_name,
                    "key_label": result.key_name,
                    "extracted_value": result.extracted_value,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "suggested_position": result.suggested_position,
                    "processing_time": result.processing_time,
                    "model_used": result.model_used,
                    "anchor_cell": {
                        "row": original_key.get('anchor_cell', {}).get('row', 0),
                        "col": original_key.get('anchor_cell', {}).get('col', 0),
                        "value": original_key.get('anchor_cell', {}).get('text', result.key_name),
                        "page_number": request.page_number
                    },
                    "value_cell": {
                        "row": original_key.get('anchor_cell', {}).get('row', 0) + result.suggested_position["row"],
                        "col": original_key.get('anchor_cell', {}).get('col', 0) + result.suggested_position["col"],
                        "value": result.extracted_value,
                        "page_number": request.page_number
                    },
                    "relative_position": {
                        "row": result.suggested_position["row"],
                        "col": result.suggested_position["col"]
                    },
                    "is_ai_extracted": True
                }
                results.append(result_data)
        
        processing_time = time.time() - start_time
        
        logger.info(f"AI 추출 완료: {successful_extractions}/{len(request.recognized_keys)} 성공, "
                   f"처리 시간: {processing_time:.2f}초")
        
        # 응답 데이터 로깅
        logger.info(f"🚀 최종 응답 데이터:")
        for i, result_data in enumerate(results):
            logger.info(f"   결과 {i+1}:")
            logger.info(f"     - key: {result_data.get('key')}")
            logger.info(f"     - anchor_cell: {result_data.get('anchor_cell')}")
            logger.info(f"     - value_cell: {result_data.get('value_cell')}")
            logger.info(f"     - relative_position: {result_data.get('relative_position')}")
        
        return AIExtractionResponseModel(
            success=True,
            results=results,
            total_processed=len(request.recognized_keys),
            successful_extractions=successful_extractions,
            processing_time=processing_time,
            model_used=ai_results[0].model_used if ai_results else "N/A"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 추출 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 추출 실패: {str(e)}")


@router.post("/extract-single-key")
async def extract_single_key_with_ai(
    key_name: str,
    key_label: str,
    anchor_cell: Dict[str, Any],
    table_data: List[List[str]],
    page_number: int,
    file_id: str = "unknown"
):
    """
    단일 키에 대한 AI 추출
    
    Args:
        key_name: 키 이름
        key_label: 키 라벨
        anchor_cell: 앵커 셀 정보
        table_data: 테이블 데이터
        page_number: 페이지 번호
        file_id: 파일 ID
        
    Returns:
        Dict: 추출 결과
    """
    try:
        if not ai_extraction_service.is_available():
            raise HTTPException(
                status_code=503, 
                detail="AI 추출 서비스가 사용할 수 없습니다."
            )
        
        # AI 추출 요청 생성
        ai_request = AIExtractionRequest(
            key_name=key_name,
            key_label=key_label,
            anchor_cell=anchor_cell,
            table_data=table_data,
            page_number=page_number,
            context=f"파일 ID: {file_id}"
        )
        
        # AI 추출 실행
        result = await ai_extraction_service.extract_value(ai_request)
        
        if result and result.confidence >= 0.7:
            return {
                "success": True,
                "key": result.key_name,
                "extracted_value": result.extracted_value,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "suggested_position": result.suggested_position,
                "processing_time": result.processing_time,
                "model_used": result.model_used
            }
        else:
            return {
                "success": False,
                "key": key_name,
                "error": "신뢰도가 낮거나 값을 찾을 수 없습니다.",
                "confidence": result.confidence if result else 0.0
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"단일 키 AI 추출 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 추출 실패: {str(e)}")


@router.post("/test-connection")
async def test_ai_connection():
    """AI 서비스 연결 테스트"""
    try:
        if not ai_extraction_service.is_available():
            return {
                "success": False,
                "message": "AI 서비스가 사용할 수 없습니다.",
                "details": "OpenAI API 키를 확인해주세요."
            }
        
        # 간단한 테스트 요청
        test_request = AIExtractionRequest(
            key_name="test",
            key_label="테스트",
            anchor_cell={"row": 0, "col": 0, "value": "테스트"},
            table_data=[["테스트", "값"]],
            page_number=1
        )
        
        result = await ai_extraction_service.extract_value(test_request)
        
        if result:
            return {
                "success": True,
                "message": "AI 서비스 연결 성공",
                "model": result.model_used,
                "test_confidence": result.confidence
            }
        else:
            return {
                "success": False,
                "message": "AI 서비스 테스트 실패",
                "details": "응답을 받을 수 없습니다."
            }
            
    except Exception as e:
        logger.error(f"AI 연결 테스트 실패: {e}")
        return {
            "success": False,
            "message": "AI 서비스 연결 실패",
            "details": str(e)
        }
