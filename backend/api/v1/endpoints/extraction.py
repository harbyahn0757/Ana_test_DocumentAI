"""
PDF 테이블 추출 API 엔드포인트

PDF 파일에서 테이블을 추출하는 API 제공
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse

from app.dependencies import get_extraction_service, get_file_service
from services.extraction_service import ExtractionService
from services.file_service import FileService
from models.table_models import ExtractionResult

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract")
async def extract_tables(
    request_data: Dict[str, Any] = Body(...),
    extraction_service: ExtractionService = Depends(get_extraction_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    PDF 파일에서 테이블 추출
    
    Request Body:
        filename (str): 추출할 파일명
        library (str, optional): 사용할 라이브러리 (기본: pdfplumber)
        options (dict, optional): 라이브러리별 옵션
        use_cache (bool, optional): 캐시 사용 여부 (기본: True)
    """
    try:
        filename = request_data.get("filename")
        library = request_data.get("library", "pdfplumber")
        options = request_data.get("options", {})
        use_cache = request_data.get("use_cache", True)
        
        if not filename:
            raise HTTPException(status_code=400, detail="filename이 필요합니다")
        
        # 파일 경로 확인
        file_path = file_service.get_upload_path(filename)
        if not file_path.exists():
            # 샘플 파일에서도 확인
            file_path = file_service.get_sample_path(filename)
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # 테이블 추출 수행
        result = await extraction_service.extract_tables_from_file(
            file_path, library, options, use_cache
        )
        
        logger.info(f"테이블 추출 API 완료: {filename}, {result.total_tables}개 테이블")
        
        return {
            "success": result.success,
            "message": "테이블 추출 완료" if result.success else "테이블 추출 실패",
            "data": result.model_dump(),
            "error": result.error_message if not result.success else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"테이블 추출 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"추출 중 오류 발생: {str(e)}")


@router.post("/extract-page")
async def extract_tables_from_page(
    request_data: Dict[str, Any] = Body(...),
    extraction_service: ExtractionService = Depends(get_extraction_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    특정 페이지에서 테이블 추출
    
    Request Body:
        filename (str): 추출할 파일명
        page_number (int): 페이지 번호 (1부터 시작)
        library (str, optional): 사용할 라이브러리 (기본: pdfplumber)
        options (dict, optional): 라이브러리별 옵션
    """
    try:
        filename = request_data.get("filename")
        page_number = request_data.get("page_number")
        library = request_data.get("library", "pdfplumber")
        options = request_data.get("options", {})
        
        if not filename:
            raise HTTPException(status_code=400, detail="filename이 필요합니다")
        
        if not page_number or page_number < 1:
            raise HTTPException(status_code=400, detail="올바른 page_number가 필요합니다")
        
        # 파일 경로 확인
        file_path = file_service.get_upload_path(filename)
        if not file_path.exists():
            file_path = file_service.get_sample_path(filename)
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # 페이지별 테이블 추출
        tables = await extraction_service.extract_tables_from_page(
            file_path, page_number, library, options
        )
        
        logger.info(f"페이지 테이블 추출 API 완료: {filename}, 페이지 {page_number}, {len(tables)}개 테이블")
        
        return {
            "success": True,
            "message": "페이지 테이블 추출 완료",
            "data": {
                "filename": filename,
                "page_number": page_number,
                "library": library,
                "total_tables": len(tables),
                "tables": [table.model_dump() for table in tables]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"페이지 테이블 추출 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"추출 중 오류 발생: {str(e)}")


@router.get("/libraries")
async def get_supported_libraries(
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """지원하는 PDF 처리 라이브러리 목록 조회"""
    try:
        libraries = await extraction_service.get_supported_libraries()
        
        return {
            "success": True,
            "message": "지원 라이브러리 조회 완료",
            "data": {
                "libraries": libraries,
                "total_count": len(libraries)
            }
        }
        
    except Exception as e:
        logger.error(f"라이브러리 조회 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"조회 중 오류 발생: {str(e)}")


@router.post("/validate-options")
async def validate_extraction_options(
    request_data: Dict[str, Any] = Body(...),
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """
    추출 옵션 유효성 검증
    
    Request Body:
        library (str): 라이브러리 이름
        options (dict): 검증할 옵션
    """
    try:
        library = request_data.get("library")
        options = request_data.get("options", {})
        
        if not library:
            raise HTTPException(status_code=400, detail="library가 필요합니다")
        
        validation_result = await extraction_service.validate_extraction_options(
            library, options
        )
        
        return {
            "success": True,
            "message": "옵션 검증 완료",
            "data": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"옵션 검증 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검증 중 오류 발생: {str(e)}")


@router.post("/compare")
async def compare_extraction_results(
    request_data: Dict[str, Any] = Body(...),
    extraction_service: ExtractionService = Depends(get_extraction_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    여러 라이브러리로 추출 결과 비교
    
    Request Body:
        filename (str): 비교할 파일명
        libraries (list): 비교할 라이브러리 목록
        options (dict, optional): 라이브러리별 옵션
    """
    try:
        filename = request_data.get("filename")
        libraries = request_data.get("libraries", ["pdfplumber", "camelot", "tabula"])
        options = request_data.get("options", {})
        
        if not filename:
            raise HTTPException(status_code=400, detail="filename이 필요합니다")
        
        if not libraries:
            raise HTTPException(status_code=400, detail="libraries가 필요합니다")
        
        # 파일 경로 확인
        file_path = file_service.get_upload_path(filename)
        if not file_path.exists():
            file_path = file_service.get_sample_path(filename)
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # 비교 추출 수행
        comparison_results = await extraction_service.compare_extraction_results(
            file_path, libraries, options
        )
        
        # 결과 요약 생성
        summary = {
            "total_libraries": len(comparison_results),
            "successful_extractions": sum(1 for result in comparison_results.values() if result.success),
            "failed_extractions": sum(1 for result in comparison_results.values() if not result.success),
            "results_by_library": {}
        }
        
        for library, result in comparison_results.items():
            summary["results_by_library"][library] = {
                "success": result.success,
                "total_tables": result.total_tables,
                "processing_time": result.processing_time,
                "error": result.error_message if not result.success else None
            }
        
        logger.info(f"라이브러리 비교 API 완료: {filename}, {len(libraries)}개 라이브러리")
        
        return {
            "success": True,
            "message": "라이브러리 비교 완료",
            "data": {
                "filename": filename,
                "summary": summary,
                "detailed_results": {
                    library: result.model_dump() 
                    for library, result in comparison_results.items()
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"라이브러리 비교 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"비교 중 오류 발생: {str(e)}")
