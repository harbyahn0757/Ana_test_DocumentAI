"""
캐시 관리자

PDF 테이블 추출 결과와 기타 데이터의 캐싱을 담당
"""

import json
import pickle
import hashlib
import aiofiles
from pathlib import Path
from typing import Any, Optional, Dict, List
import logging
from datetime import datetime, timedelta

from models.table_models import ExtractionResult

logger = logging.getLogger(__name__)


class CacheManager:
    """캐시 관리자 클래스"""
    
    def __init__(
        self, 
        cache_dir: Path, 
        max_age_hours: int = 24,
        ttl: Optional[int] = None,
        enabled: bool = True
    ):
        """
        캐시 관리자 초기화
        
        Args:
            cache_dir: 캐시 디렉토리
            max_age_hours: 캐시 최대 보관 시간 (시간)
            ttl: TTL 설정 (선택사항, max_age_hours와 동일)
            enabled: 캐시 활성화 여부
        """
        self.cache_dir = Path(cache_dir)
        self.max_age_hours = ttl or max_age_hours  # ttl 우선, 없으면 max_age_hours
        self.enabled = enabled
        self.extraction_cache_dir = self.cache_dir / "extractions"
        self.general_cache_dir = self.cache_dir / "general"
        
        # 디렉토리 생성
        self._ensure_directories()
        
        logger.info(f"캐시 관리자 초기화 완료: {self.cache_dir}")
    
    def _ensure_directories(self) -> None:
        """필요한 디렉토리들을 생성"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.extraction_cache_dir.mkdir(parents=True, exist_ok=True)
            self.general_cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"캐시 디렉토리 생성 실패: {e}")
            raise
    
    async def save_extraction_result(self, cache_key: str, result: ExtractionResult) -> bool:
        """
        추출 결과 캐시 저장
        
        Args:
            cache_key: 캐시 키
            result: 추출 결과
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            cache_file = self.extraction_cache_dir / f"{cache_key}.pkl"
            
            # Pydantic 모델을 딕셔너리로 변환
            result_dict = result.model_dump()
            
            # 메타데이터 추가
            cache_data = {
                "cached_at": datetime.now().isoformat(),
                "cache_key": cache_key,
                "data": result_dict
            }
            
            async with aiofiles.open(cache_file, 'wb') as f:
                await f.write(pickle.dumps(cache_data))
            
            logger.debug(f"추출 결과 캐시 저장 완료: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"추출 결과 캐시 저장 실패: {e}")
            return False
    
    async def get_extraction_result(self, cache_key: str) -> Optional[ExtractionResult]:
        """
        추출 결과 캐시 조회
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            Optional[ExtractionResult]: 캐시된 추출 결과
        """
        try:
            cache_file = self.extraction_cache_dir / f"{cache_key}.pkl"
            
            if not cache_file.exists():
                return None
            
            # 캐시 만료 확인
            if not self._is_cache_valid(cache_file):
                cache_file.unlink()  # 만료된 캐시 삭제
                return None
            
            async with aiofiles.open(cache_file, 'rb') as f:
                cache_data = pickle.loads(await f.read())
            
            # ExtractionResult 객체로 복원
            result = ExtractionResult.model_validate(cache_data["data"])
            
            logger.debug(f"추출 결과 캐시 조회 완료: {cache_key}")
            return result
            
        except Exception as e:
            logger.warning(f"추출 결과 캐시 조회 실패: {e}")
            return None
    
    async def save_data(self, key: str, data: Any, ttl_hours: Optional[int] = None) -> bool:
        """
        일반 데이터 캐시 저장
        
        Args:
            key: 캐시 키
            data: 저장할 데이터
            ttl_hours: 캐시 유효시간 (시간, None이면 기본값 사용)
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 안전한 파일명 생성
            safe_key = self._generate_safe_filename(key)
            cache_file = self.general_cache_dir / f"{safe_key}.json"
            
            cache_data = {
                "cached_at": datetime.now().isoformat(),
                "key": key,
                "ttl_hours": ttl_hours or self.max_age_hours,
                "data": data
            }
            
            async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(cache_data, ensure_ascii=False, indent=2))
            
            logger.debug(f"데이터 캐시 저장 완료: {key}")
            return True
            
        except Exception as e:
            logger.error(f"데이터 캐시 저장 실패: {e}")
            return False
    
    async def get_data(self, key: str) -> Optional[Any]:
        """
        일반 데이터 캐시 조회
        
        Args:
            key: 캐시 키
            
        Returns:
            Optional[Any]: 캐시된 데이터
        """
        try:
            safe_key = self._generate_safe_filename(key)
            cache_file = self.general_cache_dir / f"{safe_key}.json"
            
            if not cache_file.exists():
                return None
            
            async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                cache_data = json.loads(content)
            
            # TTL 확인
            cached_at = datetime.fromisoformat(cache_data["cached_at"])
            ttl_hours = cache_data.get("ttl_hours", self.max_age_hours)
            
            if datetime.now() - cached_at > timedelta(hours=ttl_hours):
                cache_file.unlink()  # 만료된 캐시 삭제
                return None
            
            logger.debug(f"데이터 캐시 조회 완료: {key}")
            return cache_data["data"]
            
        except Exception as e:
            logger.warning(f"데이터 캐시 조회 실패: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """
        캐시 삭제
        
        Args:
            key: 삭제할 캐시 키
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            safe_key = self._generate_safe_filename(key)
            
            # 추출 결과 캐시 확인
            extraction_cache = self.extraction_cache_dir / f"{key}.pkl"
            if extraction_cache.exists():
                extraction_cache.unlink()
                logger.debug(f"추출 결과 캐시 삭제: {key}")
                return True
            
            # 일반 데이터 캐시 확인
            general_cache = self.general_cache_dir / f"{safe_key}.json"
            if general_cache.exists():
                general_cache.unlink()
                logger.debug(f"일반 데이터 캐시 삭제: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"캐시 삭제 실패: {e}")
            return False
    
    async def clear_all_cache(self) -> int:
        """
        모든 캐시 삭제
        
        Returns:
            int: 삭제된 캐시 파일 수
        """
        try:
            deleted_count = 0
            
            # 추출 결과 캐시 삭제
            for cache_file in self.extraction_cache_dir.glob("*.pkl"):
                cache_file.unlink()
                deleted_count += 1
            
            # 일반 데이터 캐시 삭제
            for cache_file in self.general_cache_dir.glob("*.json"):
                cache_file.unlink()
                deleted_count += 1
            
            logger.info(f"모든 캐시 삭제 완료: {deleted_count}개 파일")
            return deleted_count
            
        except Exception as e:
            logger.error(f"캐시 전체 삭제 실패: {e}")
            return 0
    
    async def cleanup_expired_cache(self) -> int:
        """
        만료된 캐시 정리
        
        Returns:
            int: 삭제된 캐시 파일 수
        """
        try:
            deleted_count = 0
            
            # 추출 결과 캐시 정리
            for cache_file in self.extraction_cache_dir.glob("*.pkl"):
                if not self._is_cache_valid(cache_file):
                    cache_file.unlink()
                    deleted_count += 1
                    logger.debug(f"만료된 추출 캐시 삭제: {cache_file.name}")
            
            # 일반 데이터 캐시 정리
            for cache_file in self.general_cache_dir.glob("*.json"):
                try:
                    async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        cache_data = json.loads(content)
                    
                    cached_at = datetime.fromisoformat(cache_data["cached_at"])
                    ttl_hours = cache_data.get("ttl_hours", self.max_age_hours)
                    
                    if datetime.now() - cached_at > timedelta(hours=ttl_hours):
                        cache_file.unlink()
                        deleted_count += 1
                        logger.debug(f"만료된 일반 캐시 삭제: {cache_file.name}")
                        
                except Exception as e:
                    logger.warning(f"캐시 파일 확인 실패 {cache_file}: {e}")
                    continue
            
            logger.info(f"만료된 캐시 정리 완료: {deleted_count}개 파일 삭제")
            return deleted_count
            
        except Exception as e:
            logger.error(f"만료된 캐시 정리 실패: {e}")
            return 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        캐시 정보 조회
        
        Returns:
            Dict[str, Any]: 캐시 정보
        """
        try:
            info = {
                "cache_dir": str(self.cache_dir),
                "max_age_hours": self.max_age_hours,
                "extraction_cache_count": 0,
                "general_cache_count": 0,
                "total_size": 0,
                "last_accessed": None
            }
            
            # 추출 결과 캐시 정보
            extraction_files = list(self.extraction_cache_dir.glob("*.pkl"))
            info["extraction_cache_count"] = len(extraction_files)
            
            # 일반 데이터 캐시 정보
            general_files = list(self.general_cache_dir.glob("*.json"))
            info["general_cache_count"] = len(general_files)
            
            # 총 크기 및 최근 접근 시간 계산
            total_size = 0
            last_accessed = None
            
            for file_path in extraction_files + general_files:
                stat = file_path.stat()
                total_size += stat.st_size
                
                if last_accessed is None or stat.st_atime > last_accessed:
                    last_accessed = stat.st_atime
            
            info["total_size"] = total_size
            if last_accessed:
                info["last_accessed"] = datetime.fromtimestamp(last_accessed).isoformat()
            
            return info
            
        except Exception as e:
            logger.error(f"캐시 정보 조회 실패: {e}")
            return {"error": str(e)}
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """
        캐시 파일이 유효한지 확인
        
        Args:
            cache_file: 캐시 파일 경로
            
        Returns:
            bool: 캐시 유효 여부
        """
        try:
            stat = cache_file.stat()
            file_age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            return file_age < timedelta(hours=self.max_age_hours)
        except Exception:
            return False
    
    def _generate_safe_filename(self, key: str) -> str:
        """
        안전한 파일명 생성
        
        Args:
            key: 원본 키
            
        Returns:
            str: 안전한 파일명
        """
        # 파일명으로 사용할 수 없는 문자들을 제거하고 해시 생성
        safe_key = "".join(c for c in key if c.isalnum() or c in "._-")
        
        # 너무 길면 해시로 축약
        if len(safe_key) > 100:
            safe_key = hashlib.md5(key.encode()).hexdigest()
        
        return safe_key
