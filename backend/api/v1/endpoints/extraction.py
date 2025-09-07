"""
데이터 추출 API 엔드포인트
템플릿 기반 건강검진 데이터 추출을 위한 REST API 엔드포인트
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
import logging

from app.dependencies import get_error_handler
from services.extraction_service import ExtractionService
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["extraction"])


@router.post("/extract")
async def extract_data(
    file: UploadFile = File(...),
    mappings: str = Form(...),  # JSON 문자열
    processor_type: str = Form("pdfplumber"),
    error_handler = Depends(get_error_handler)
) -> JSONResponse:
    """
    데이터 추출 API (템플릿 기반)
    PDF 파일에서 설정된 매핑에 따라 건강검진 데이터를 추출합니다.
    
    Args:
        file: 업로드된 PDF 파일
        mappings: JSON 문자열로 인코딩된 키-값 매핑 설정
        processor_type: PDF 처리기 타입 (pdfplumber, camelot, tabula)
        
    Returns:
        JSONResponse: 추출 결과
    """
    try:
        import json
        import tempfile
        import os
        
        # 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 매핑 설정 파싱
            mapping_list = json.loads(mappings)
            
            # 추출 서비스 실행
            extraction_service = ExtractionService()
            result = await extraction_service.extract_data_with_mappings(
                file_path=temp_file_path,
                mappings=mapping_list,
                processor_type=processor_type
            )
            
            # 결과 포맷팅
            response_data = {
                "success": True,
                "file_name": file.filename,
                "extracted_count": len(result.get("extracted_data", [])),
                "extracted_data": result.get("extracted_data", []),
                "processing_time": result.get("processing_time", 0),
                "extracted_at": result.get("extracted_at")
            }
            
            logger.info(f"데이터 추출 완료: {file.filename}, {len(result.get('extracted_data', []))}개 항목")
            return JSONResponse(content=response_data)
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except json.JSONDecodeError as e:
        logger.error(f"매핑 설정 파싱 실패: {str(e)}")
        raise HTTPException(status_code=400, detail="잘못된 매핑 설정 형식입니다")
    
    except Exception as e:
        logger.error(f"데이터 추출 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터 추출 중 오류가 발생했습니다: {str(e)}")


@router.post("/quick-test")
async def quick_test(
    file: UploadFile = File(...),
    template_name: str = Form(...),
    mappings: str = Form(...),  # JSON 문자열
    error_handler = Depends(get_error_handler)
) -> JSONResponse:
    """
    빠른 추출 테스트 API
    설정된 매핑으로 간단한 추출 테스트를 수행합니다.
    
    Args:
        file: 업로드된 PDF 파일
        template_name: 템플릿 이름
        mappings: JSON 문자열로 인코딩된 키-값 매핑 설정
        
    Returns:
        JSONResponse: 테스트 결과
    """
    try:
        import json
        import tempfile
        import os
        
        # 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 매핑 설정 파싱
            mapping_list = json.loads(mappings)
            
            # 빠른 테스트 실행
            extraction_service = ExtractionService()
            result = await extraction_service.quick_test(
                file_path=temp_file_path,
                template_name=template_name,
                mappings=mapping_list
            )
            
            logger.info(f"빠른 테스트 완료: {file.filename}")
            return JSONResponse(content=result)
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except json.JSONDecodeError as e:
        logger.error(f"매핑 설정 파싱 실패: {str(e)}")
        raise HTTPException(status_code=400, detail="잘못된 매핑 설정 형식입니다")
    
    except Exception as e:
        logger.error(f"빠른 테스트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"빠른 테스트 중 오류가 발생했습니다: {str(e)}")


@router.post("/validate-mappings")
async def validate_mappings(
    mappings: List[Dict[str, Any]],
    error_handler = Depends(get_error_handler)
) -> JSONResponse:
    """
    매핑 설정 검증 API
    추출 매핑 설정의 유효성을 검증합니다.
    
    Args:
        mappings: 검증할 매핑 설정 목록
        
    Returns:
        JSONResponse: 검증 결과
    """
    try:
        logger.info(f"매핑 검증 요청: {len(mappings)}개 매핑")
        
        # 매핑 검증 로직
        extraction_service = ExtractionService()
        validation_result = await extraction_service.validate_mappings(mappings)
        
        logger.info(f"매핑 검증 완료: {validation_result.get('valid_count', 0)}개 유효")
        return JSONResponse(content=validation_result)
        
    except Exception as e:
        logger.error(f"매핑 검증 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매핑 검증 중 오류가 발생했습니다: {str(e)}")


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    추출 서비스 상태 확인 API
    
    Returns:
        JSONResponse: 서비스 상태
    """
    try:
        # 서비스 초기화 테스트
        service = ExtractionService()
        
        return JSONResponse(content={
            "status": "healthy",
            "service": "extraction",
            "version": "1.0.0",
            "timestamp": "2025-01-27T00:00:00Z"
        })
        
    except Exception as e:
        logger.error(f"상태 확인 실패: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "extraction",
                "error": str(e)
            }
        )