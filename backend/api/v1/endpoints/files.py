"""
파일 관리 API 엔드포인트

파일 목록 조회, 업로드, 정보 조회 등의 API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
import logging

from app.dependencies import (
    get_file_service,
    validate_file_upload,
    get_error_handler,
    get_logger
)
from models.file_models import (
    FileInfo,
    FileListResponse,
    FileUploadResponse,
    SampleFilesResponse
)
from services.file_service import FileService
from utils.logging_config import log_exceptions, log_performance

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/list", response_model=FileListResponse)
async def get_uploaded_files(
    file_service: FileService = Depends(get_file_service)
) -> FileListResponse:
    """업로드된 파일 목록 조회
    
    Returns:
        FileListResponse: 업로드된 파일들의 목록
    """
    try:
        files = await file_service.get_uploaded_files()
        logger.info(f"📁 업로드된 파일 목록 조회 완료: {len(files)}개")
        
        return FileListResponse(
            files=files,
            total_count=len(files),
            message="파일 목록 조회 성공",
            page=None,
            page_size=None,
            total_pages=None
        )
    
    except Exception as e:
        logger.error(f"파일 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="파일 목록을 조회하는 중 오류가 발생했습니다"
        )


@router.get("/samples", response_model=SampleFilesResponse)
async def get_sample_files(
    file_service: FileService = Depends(get_file_service)
) -> SampleFilesResponse:
    """샘플 파일 목록 조회
    
    Returns:
        SampleFilesResponse: 샘플 파일들의 목록
    """
    try:
        samples = await file_service.get_sample_files()
        logger.info(f"📋 샘플 파일 목록 조회 완료: {len(samples)}개")
        
        return SampleFilesResponse(
            samples=samples,
            total_count=len(samples),
            samples_dir=str(file_service.samples_dir),
            message="샘플 파일 목록 조회 성공"
        )
    
    except Exception as e:
        logger.error(f"샘플 파일 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="샘플 파일 목록을 조회하는 중 오류가 발생했습니다"
        )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service)
) -> FileUploadResponse:
    """새 파일 업로드
    
    Args:
        file: 업로드할 파일
        
    Returns:
        FileUploadResponse: 업로드 결과 정보
    """
    try:
        logger.info(f"📤 파일 업로드 시작: {file.filename}")
        
        # 파일 저장
        file_content = await file.read()
        file_info = await file_service.save_uploaded_file(file_content, file.filename or "unknown")
        
        if not file_info:
            raise HTTPException(status_code=500, detail="파일 정보 생성 실패")
            
        logger.info(f"✅ 파일 업로드 완료: {file_info.file_id or file_info.filename}")
        
        return FileUploadResponse(
            file_id=file_info.file_id or file_info.filename,
            file_name=file_info.file_name or file_info.filename,
            file_size=file_info.file_size,
            message="파일 업로드 성공",
            file_info=file_info
        )
    
    except Exception as e:
        logger.error(f"파일 업로드 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="파일 업로드 중 오류가 발생했습니다"
        )


@router.get("/{file_id}", response_model=FileInfo)
async def get_file_info(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
    error_handler = Depends(get_error_handler)
) -> FileInfo:
    """파일 정보 조회
    
    Args:
        file_id: 파일 ID
        
    Returns:
        FileInfo: 파일 상세 정보
    """
    try:
        file_info = await file_service.get_file_info(file_id)
        
        if not file_info:
            error_handler.handle_file_not_found(file_id)
        
        logger.info(f"📄 파일 정보 조회 완료: {file_id}")
        return file_info  # type: ignore
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 정보 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="파일 정보를 조회하는 중 오류가 발생했습니다"
        )


@router.put("/{file_id}/memo")
async def update_file_memo(
    file_id: str,
    memo_data: dict,
    file_service: FileService = Depends(get_file_service),
    error_handler = Depends(get_error_handler)
):
    """파일 메모 업데이트
    
    Args:
        file_id: 파일 ID
        memo_data: 메모 데이터 {"memo": "메모 내용"}
        
    Returns:
        dict: 업데이트 결과
    """
    try:
        logger.info(f"📝 파일 메모 업데이트 시작: {file_id}")
        
        memo = memo_data.get("memo", "")
        success = await file_service.update_file_memo(file_id, memo)
        
        if not success:
            error_handler.handle_file_not_found(file_id)
        
        logger.info(f"✅ 파일 메모 업데이트 완료: {file_id}")
        return {"success": True, "message": "파일 메모가 업데이트되었습니다", "memo": memo}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 메모 업데이트 실패 {file_id}: {e}")
        error_handler.handle_internal_error(str(e))


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
    error_handler = Depends(get_error_handler)
):
    """파일 삭제
    
    Args:
        file_id: 삭제할 파일 ID
        
    Returns:
        dict: 삭제 결과
    """
    try:
        logger.info(f"🗑️ 파일 삭제 시작: {file_id}")
        
        success = await file_service.delete_file(file_id)
        
        if not success:
            error_handler.handle_file_not_found(file_id)
        
        logger.info(f"✅ 파일 삭제 완료: {file_id}")
        
        return {
            "success": True,
            "message": "파일이 성공적으로 삭제되었습니다",
            "file_id": file_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 삭제 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="파일 삭제 중 오류가 발생했습니다"
        )


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
    error_handler = Depends(get_error_handler)
):
    """파일 다운로드
    
    Args:
        file_id: 다운로드할 파일 ID
        
    Returns:
        FileResponse: 파일 다운로드 응답
    """
    try:
        logger.info(f"⬇️ 파일 다운로드 시작: {file_id}")
        
        file_response = await file_service.get_file_download(file_id)
        
        if not file_response:
            error_handler.handle_file_not_found(file_id)
        
        logger.info(f"✅ 파일 다운로드 준비 완료: {file_id}")
        return file_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 다운로드 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="파일 다운로드 중 오류가 발생했습니다"
        )


@router.post("/batch-delete")
async def batch_delete_files(
    file_ids: List[str],
    file_service: FileService = Depends(get_file_service)
):
    """여러 파일 일괄 삭제
    
    Args:
        file_ids: 삭제할 파일 ID 목록
        
    Returns:
        dict: 일괄 삭제 결과
    """
    try:
        logger.info(f"🗑️ 일괄 파일 삭제 시작: {len(file_ids)}개")
        
        results = await file_service.batch_delete_files(file_ids)
        
        success_count = results.get("successful_deletions", 0)
        failure_count = results.get("failed_deletions", 0)
        
        logger.info(f"📊 일괄 삭제 완료 - 성공: {success_count}, 실패: {failure_count}")
        
        return {
            "total_requested": len(file_ids),
            "successful_deletions": success_count,
            "failed_deletions": failure_count,
            "results": results,
            "message": f"{success_count}개 파일이 성공적으로 삭제되었습니다"
        }
    
    except Exception as e:
        logger.error(f"일괄 파일 삭제 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="일괄 파일 삭제 중 오류가 발생했습니다"
        )


@router.get("/stats/summary")
async def get_file_stats(
    file_service: FileService = Depends(get_file_service)
):
    """파일 통계 정보 조회
    
    Returns:
        dict: 파일 관련 통계 정보
    """
    try:
        stats = await file_service.get_file_statistics()
        logger.info("📈 파일 통계 정보 조회 완료")
        
        return {
            "statistics": stats,
            "message": "파일 통계 조회 성공"
        }
    
    except Exception as e:
        logger.error(f"파일 통계 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="파일 통계를 조회하는 중 오류가 발생했습니다"
        )
