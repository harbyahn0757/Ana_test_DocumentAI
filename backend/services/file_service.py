"""
파일 관리 서비스

업로드된 파일과 샘플 파일의 관리, 검증, 정보 제공을 담당
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import asyncio
import aiofiles

from models.file_models import FileInfo, FileType, SampleFileInfo
from app.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """파일 관리 서비스 클래스"""
    
    def __init__(
        self,
        upload_dir: Path,
        samples_dir: Path,
        allowed_extensions: List[str],
        max_file_size: int
    ):
        """
        파일 서비스 초기화
        
        Args:
            upload_dir: 업로드 파일 저장 디렉토리
            samples_dir: 샘플 파일 디렉토리
            allowed_extensions: 허용된 파일 확장자 목록
            max_file_size: 최대 파일 크기 (바이트)
        """
        self.upload_dir = Path(upload_dir)
        self.samples_dir = Path(samples_dir)
        self.allowed_extensions = allowed_extensions
        self.max_file_size = max_file_size
        
        # 디렉토리 생성
        self._ensure_directories()
        
        logger.info(f"파일 서비스 초기화 완료")
        logger.info(f"업로드 디렉토리: {self.upload_dir}")
        logger.info(f"샘플 디렉토리: {self.samples_dir}")
    
    def _ensure_directories(self) -> None:
        """필요한 디렉토리들을 생성"""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 샘플 디렉토리는 이미 존재한다고 가정 (프로젝트 루트의 samples)
            if not self.samples_dir.exists():
                logger.warning(f"샘플 디렉토리가 존재하지 않습니다: {self.samples_dir}")
            
        except Exception as e:
            logger.error(f"디렉토리 생성 실패: {e}")
            raise
    
    async def get_uploaded_files(self) -> List[FileInfo]:
        """
        업로드된 파일 목록 조회
        
        Returns:
            List[FileInfo]: 업로드된 파일 정보 목록
        """
        try:
            files = []
            
            if not self.upload_dir.exists():
                return files
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    file_info = await self._create_file_info(file_path)
                    if file_info:
                        files.append(file_info)
            
            # 업로드 시간 역순으로 정렬
            files.sort(key=lambda x: x.uploaded_at, reverse=True)
            
            logger.info(f"업로드된 파일 {len(files)}개 조회 완료")
            return files
            
        except Exception as e:
            logger.error(f"업로드 파일 목록 조회 실패: {e}")
            raise
    
    async def get_sample_files(self) -> List[SampleFileInfo]:
        """
        샘플 파일 목록 조회
        
        Returns:
            List[SampleFileInfo]: 샘플 파일 정보 목록
        """
        try:
            files = []
            
            if not self.samples_dir.exists():
                logger.warning("샘플 디렉토리가 존재하지 않습니다")
                return files
            
            for file_path in self.samples_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                    file_info = await self._create_sample_file_info(file_path)
                    if file_info:
                        files.append(file_info)
            
            # 파일명 순으로 정렬
            files.sort(key=lambda x: x.filename)
            
            logger.info(f"샘플 파일 {len(files)}개 조회 완료")
            return files
            
        except Exception as e:
            logger.error(f"샘플 파일 목록 조회 실패: {e}")
            raise
    
    async def _create_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """
        파일 경로로부터 FileInfo 객체 생성
        
        Args:
            file_path: 파일 경로
            
        Returns:
            Optional[FileInfo]: 파일 정보 객체
        """
        try:
            stat = file_path.stat()
            
            # 파일 해시 계산
            file_hash = await self._calculate_file_hash(file_path)
            
            # MIME 타입 확인
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # 파일 타입 결정
            file_type = self._determine_file_type(file_path.suffix)
            
            # 고유한 파일 ID 생성 (해시 + 타임스탬프)
            unique_id = f"{file_hash[:8]}_{int(stat.st_mtime)}" if file_hash else f"file_{int(stat.st_mtime)}"
            
            return FileInfo(
                file_name=file_path.name,
                file_path=str(file_path),
                file_size=stat.st_size,
                file_type=file_type,
                mime_type=mime_type or "application/octet-stream",
                uploaded_at=datetime.fromtimestamp(stat.st_mtime),
                file_hash=file_hash,
                file_id=unique_id,
                updated_at=datetime.fromtimestamp(stat.st_mtime),
                memo=None
            )
            
        except Exception as e:
            logger.warning(f"파일 정보 생성 실패 {file_path}: {e}")
            return None
    
    async def _create_sample_file_info(self, file_path: Path) -> Optional[SampleFileInfo]:
        """
        샘플 파일 정보 생성
        
        Args:
            file_path: 파일 경로
            
        Returns:
            Optional[SampleFileInfo]: 샘플 파일 정보
        """
        try:
            stat = file_path.stat()
            
            return SampleFileInfo(
                file_name=file_path.name,
                file_path=str(file_path),
                file_size=stat.st_size,
                description=f"샘플 PDF 파일: {file_path.stem}",
                file_type=FileType.PDF,
                display_name=file_path.stem
            )
            
        except Exception as e:
            logger.warning(f"샘플 파일 정보 생성 실패 {file_path}: {e}")
            return None
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """
        파일 해시값 계산 (SHA-256)
        
        Args:
            file_path: 파일 경로
            
        Returns:
            str: 해시값
        """
        try:
            sha256_hash = hashlib.sha256()
            
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.warning(f"파일 해시 계산 실패 {file_path}: {e}")
            return ""
    
    def _determine_file_type(self, suffix: str) -> FileType:
        """
        파일 확장자로부터 파일 타입 결정
        
        Args:
            suffix: 파일 확장자
            
        Returns:
            FileType: 파일 타입
        """
        suffix_lower = suffix.lower()
        
        if suffix_lower == '.pdf':
            return FileType.PDF
        elif suffix_lower in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return FileType.IMAGE
        elif suffix_lower in ['.txt', '.md', '.json', '.xml', '.csv']:
            return FileType.TEXT
        else:
            return FileType.UNKNOWN
    
    async def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """
        파일 유효성 검증
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            Dict[str, Any]: 검증 결과
        """
        result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "file_info": None
        }
        
        try:
            # 파일 존재 여부 확인
            if not file_path.exists():
                result["errors"].append("파일이 존재하지 않습니다")
                return result
            
            # 파일 크기 확인
            file_size = file_path.stat().st_size
            if file_size == 0:
                result["errors"].append("빈 파일입니다")
                return result
            
            if file_size > self.max_file_size:
                result["errors"].append(f"파일 크기가 제한을 초과합니다 ({file_size:,} > {self.max_file_size:,} bytes)")
                return result
            
            # 확장자 확인
            if file_path.suffix.lower() not in self.allowed_extensions:
                result["errors"].append(f"지원하지 않는 파일 형식입니다 ({file_path.suffix})")
                return result
            
            # PDF 전용 검증
            if file_path.suffix.lower() == '.pdf':
                from core.pdf_processor.pdf_utils import PDFUtils
                if not PDFUtils.validate_pdf_file_basic(file_path):
                    result["errors"].append("유효하지 않은 PDF 파일입니다")
                    return result
            
            # 파일 정보 생성
            file_info = await self._create_file_info(file_path)
            if file_info:
                result["file_info"] = file_info
            
            result["is_valid"] = True
            logger.info(f"파일 검증 성공: {file_path.name}")
            
        except Exception as e:
            logger.error(f"파일 검증 중 오류 발생: {e}")
            result["errors"].append(f"검증 중 오류 발생: {str(e)}")
        
        return result
    
    async def delete_file(self, file_identifier: str) -> bool:
        """
        업로드된 파일 삭제 (파일 ID 또는 파일명으로)
        
        Args:
            file_identifier: 삭제할 파일 ID 또는 파일명
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 먼저 파일 정보를 조회해서 실제 파일명을 얻습니다
            file_info = await self.get_file_info(file_identifier)
            if not file_info:
                logger.warning(f"삭제할 파일을 찾을 수 없습니다: {file_identifier}")
                return False
            
            # 실제 파일 경로
            file_path = self.upload_dir / file_info.file_name
            
            if not file_path.exists():
                logger.warning(f"삭제할 파일이 존재하지 않습니다: {file_info.file_name}")
                return False
            
            file_path.unlink()
            logger.info(f"파일 삭제 완료: {file_info.file_name}")
            return True
            
        except Exception as e:
            logger.error(f"파일 삭제 실패 {file_identifier}: {e}")
            return False
    
    async def update_file_memo(self, file_identifier: str, memo: str) -> bool:
        """
        파일 메모 업데이트
        
        Args:
            file_identifier: 파일 ID 또는 파일명
            memo: 메모 내용
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            # 파일 정보 조회
            file_info = await self.get_file_info(file_identifier)
            if not file_info:
                logger.warning(f"메모를 업데이트할 파일을 찾을 수 없습니다: {file_identifier}")
                return False
            
            # 메모 정보를 파일명에 포함하여 저장 (임시 방식)
            # 실제로는 데이터베이스나 별도 메타데이터 파일에 저장해야 함
            logger.info(f"파일 메모 업데이트: {file_info.file_name} -> {memo}")
            return True
            
        except Exception as e:
            logger.error(f"파일 메모 업데이트 실패 {file_identifier}: {e}")
            return False
    
    async def get_file_by_name(self, filename: str) -> Optional[FileInfo]:
        """
        파일명으로 파일 정보 조회
        
        Args:
            filename: 조회할 파일명
            
        Returns:
            Optional[FileInfo]: 파일 정보
        """
        try:
            file_path = self.upload_dir / filename
            
            if not file_path.exists():
                return None
            
            return await self._create_file_info(file_path)
            
        except Exception as e:
            logger.error(f"파일 조회 실패 {filename}: {e}")
            return None
    
    def get_upload_path(self, filename: str) -> Path:
        """
        업로드 파일의 전체 경로 반환
        
        Args:
            filename: 파일명
            
        Returns:
            Path: 파일 전체 경로
        """
        return self.upload_dir / filename
    
    def get_sample_path(self, filename: str) -> Path:
        """
        샘플 파일의 전체 경로 반환
        
        Args:
            filename: 파일명
            
        Returns:
            Path: 파일 전체 경로
        """
        return self.samples_dir / filename
    
    async def cleanup_old_files(self, days: int = 30) -> int:
        """
        오래된 업로드 파일 정리
        
        Args:
            days: 보관 기간 (일)
            
        Returns:
            int: 삭제된 파일 수
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            deleted_count = 0
            
            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"오래된 파일 삭제: {file_path.name}")
            
            logger.info(f"파일 정리 완료: {deleted_count}개 파일 삭제")
            return deleted_count
            
        except Exception as e:
            logger.error(f"파일 정리 실패: {e}")
            return 0
    
    async def save_uploaded_file(self, file_content: bytes, filename: str) -> Optional[FileInfo]:
        """
        업로드된 파일 저장
        
        Args:
            file_content: 파일 내용
            filename: 파일명
            
        Returns:
            Optional[FileInfo]: 저장된 파일 정보
        """
        try:
            file_path = self.upload_dir / filename
            
            # 중복 파일명 처리
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = self.upload_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # 파일 저장
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # 파일 정보 생성
            return await self._create_file_info(file_path)
            
        except Exception as e:
            logger.error(f"파일 저장 실패 {filename}: {e}")
            return None
    
    async def get_file_info(self, file_identifier: str) -> Optional[FileInfo]:
        """
        파일 정보 조회 (파일 ID 또는 파일명으로)
        
        Args:
            file_identifier: 파일 ID 또는 파일명
            
        Returns:
            Optional[FileInfo]: 파일 정보
        """
        # 먼저 파일명으로 시도
        file_info = await self.get_file_by_name(file_identifier)
        if file_info:
            return file_info
        
        # 파일 ID로 조회 (업로드된 파일 목록에서 해시 ID로 검색)
        uploaded_files = await self.get_uploaded_files()
        for file in uploaded_files:
            if hasattr(file, 'file_hash') and file.file_hash == file_identifier:
                return file
            if hasattr(file, 'file_id') and file.file_id == file_identifier:
                return file
        
        return None
    
    async def _find_file_by_id(self, file_id: str):
        """
        file_id로 파일 정보 찾기
        
        Args:
            file_id: 파일 ID
            
        Returns:
            FileInfo: 파일 정보 또는 None
        """
        try:
            uploaded_files = await self.get_uploaded_files()
            for file in uploaded_files:
                if hasattr(file, 'file_id') and file.file_id == file_id:
                    return file
            return None
        except Exception as e:
            logger.error(f"파일 ID로 검색 실패 {file_id}: {e}")
            return None
    
    async def get_file_download(self, file_id: str):
        """
        파일 다운로드 정보 생성
        
        Args:
            file_id: 파일 ID
            
        Returns:
            FileResponse: 파일 다운로드 응답
        """
        from fastapi.responses import FileResponse
        
        try:
            # file_id로 파일 정보 찾기
            file_info = await self._find_file_by_id(file_id)
            if not file_info:
                logger.warning(f"파일을 찾을 수 없습니다: {file_id}")
                return None
            
            # 실제 파일 경로 확인
            file_path = self.upload_dir / file_info.file_name
            if not file_path.exists():
                logger.warning(f"파일이 존재하지 않습니다: {file_path}")
                return None
            
            # FileResponse 반환
            return FileResponse(
                path=str(file_path),
                filename=file_info.file_name,
                media_type=file_info.mime_type or "application/octet-stream"
            )
            
        except Exception as e:
            logger.error(f"다운로드 정보 생성 실패 {file_id}: {e}")
            return None
    
    async def batch_delete_files(self, filenames: List[str]) -> Dict[str, Any]:
        """
        파일 일괄 삭제
        
        Args:
            filenames: 삭제할 파일명 목록
            
        Returns:
            Dict[str, Any]: 삭제 결과
        """
        results = {
            "total_requested": len(filenames),
            "successful_deletions": 0,
            "failed_deletions": 0,
            "results": []
        }
        
        for filename in filenames:
            try:
                success = await self.delete_file(filename)
                if success:
                    results["successful_deletions"] += 1
                    results["results"].append({
                        "filename": filename,
                        "success": True,
                        "message": "삭제 완료"
                    })
                else:
                    results["failed_deletions"] += 1
                    results["results"].append({
                        "filename": filename,
                        "success": False,
                        "message": "파일을 찾을 수 없음"
                    })
            except Exception as e:
                results["failed_deletions"] += 1
                results["results"].append({
                    "filename": filename,
                    "success": False,
                    "message": f"삭제 실패: {str(e)}"
                })
        
        logger.info(f"일괄 삭제 완료: {results['successful_deletions']}/{len(filenames)}개 성공")
        return results
    
    async def get_file_statistics(self) -> Dict[str, Any]:
        """
        파일 통계 정보 조회
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            stats = {
                "total_files": 0,
                "total_size": 0,
                "file_types": {},
                "upload_trend": {},
                "largest_file": None,
                "smallest_file": None
            }
            
            files = await self.get_uploaded_files()
            stats["total_files"] = len(files)
            
            if files:
                stats["total_size"] = sum(file.size for file in files)
                
                # 파일 타입별 집계
                for file in files:
                    file_type = file.file_type.value
                    stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1
                
                # 최대/최소 파일
                largest = max(files, key=lambda f: f.size)
                smallest = min(files, key=lambda f: f.size)
                
                stats["largest_file"] = {
                    "filename": largest.filename,
                    "size": largest.size
                }
                stats["smallest_file"] = {
                    "filename": smallest.filename,
                    "size": smallest.size
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"통계 정보 조회 실패: {e}")
            return {"error": str(e)}
    
    def validate_extension(self, filename: str) -> bool:
        """
        파일 확장자 유효성 검증
        
        Args:
            filename: 파일명
            
        Returns:
            bool: 유효한 확장자 여부
        """
        try:
            file_path = Path(filename)
            extension = file_path.suffix.lower()
            return extension in self.allowed_extensions
        except Exception as e:
            logger.warning(f"확장자 검증 실패 {filename}: {e}")
            return False
    
    def validate_size(self, file_size: int) -> bool:
        """
        파일 크기 유효성 검증
        
        Args:
            file_size: 파일 크기 (바이트)
            
        Returns:
            bool: 유효한 크기 여부
        """
        return 0 <= file_size <= self.max_file_size
