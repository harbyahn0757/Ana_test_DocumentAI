"""
파일 기반 저장소

관계 설정과 기타 데이터를 파일 시스템에 저장하는 저장소 구현
"""

import json
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileStorage:
    """파일 기반 저장소 클래스"""
    
    def __init__(self, storage_dir: Path):
        """
        파일 저장소 초기화
        
        Args:
            storage_dir: 저장소 디렉토리
        """
        self.storage_dir = Path(storage_dir)
        self.relationships_dir = self.storage_dir / "relationships"
        
        # 디렉토리 생성
        self._ensure_directories()
        
        logger.info(f"파일 저장소 초기화 완료: {self.storage_dir}")
    
    def _ensure_directories(self) -> None:
        """필요한 디렉토리들을 생성"""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.relationships_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"저장소 디렉토리 생성 실패: {e}")
            raise
    
    async def save_relationship(self, relationship_id: str, data: Dict[str, Any]) -> bool:
        """
        관계 설정 저장
        
        Args:
            relationship_id: 관계 설정 ID
            data: 저장할 데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            file_path = self.relationships_dir / f"{relationship_id}.json"
            
            # 메타데이터 추가
            data["saved_at"] = datetime.now().isoformat()
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
            logger.debug(f"관계 설정 저장 완료: {relationship_id}")
            return True
            
        except Exception as e:
            logger.error(f"관계 설정 저장 실패 {relationship_id}: {e}")
            return False
    
    async def load_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        관계 설정 로드
        
        Args:
            relationship_id: 관계 설정 ID
            
        Returns:
            Optional[Dict[str, Any]]: 관계 설정 데이터
        """
        try:
            file_path = self.relationships_dir / f"{relationship_id}.json"
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
            
            logger.debug(f"관계 설정 로드 완료: {relationship_id}")
            return data
            
        except Exception as e:
            logger.error(f"관계 설정 로드 실패 {relationship_id}: {e}")
            return None
    
    async def list_relationships(self) -> List[Dict[str, Any]]:
        """
        모든 관계 설정 목록 조회
        
        Returns:
            List[Dict[str, Any]]: 관계 설정 목록
        """
        try:
            relationships = []
            
            if not self.relationships_dir.exists():
                return relationships
            
            for file_path in self.relationships_dir.glob("*.json"):
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        data = json.loads(content)
                        relationships.append(data)
                except Exception as e:
                    logger.warning(f"관계 설정 파일 읽기 실패 {file_path}: {e}")
                    continue
            
            logger.debug(f"관계 설정 목록 조회 완료: {len(relationships)}개")
            return relationships
            
        except Exception as e:
            logger.error(f"관계 설정 목록 조회 실패: {e}")
            return []
    
    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        관계 설정 삭제
        
        Args:
            relationship_id: 삭제할 관계 설정 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            file_path = self.relationships_dir / f"{relationship_id}.json"
            
            if not file_path.exists():
                logger.warning(f"삭제할 관계 설정 파일이 없음: {relationship_id}")
                return False
            
            file_path.unlink()
            
            logger.debug(f"관계 설정 삭제 완료: {relationship_id}")
            return True
            
        except Exception as e:
            logger.error(f"관계 설정 삭제 실패 {relationship_id}: {e}")
            return False
    
    async def backup_relationships(self, backup_dir: Path) -> bool:
        """
        관계 설정 백업
        
        Args:
            backup_dir: 백업 디렉토리
            
        Returns:
            bool: 백업 성공 여부
        """
        try:
            backup_dir = Path(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = backup_dir / f"relationships_backup_{timestamp}"
            backup_subdir.mkdir()
            
            # 모든 관계 설정 파일 복사
            count = 0
            for file_path in self.relationships_dir.glob("*.json"):
                backup_file = backup_subdir / file_path.name
                
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as src:
                    content = await src.read()
                
                async with aiofiles.open(backup_file, 'w', encoding='utf-8') as dst:
                    await dst.write(content)
                
                count += 1
            
            logger.info(f"관계 설정 백업 완료: {count}개 파일 → {backup_subdir}")
            return True
            
        except Exception as e:
            logger.error(f"관계 설정 백업 실패: {e}")
            return False
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        오래된 데이터 정리
        
        Args:
            days: 보관 기간 (일)
            
        Returns:
            int: 삭제된 파일 수
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            deleted_count = 0
            
            # 관계 설정 파일 정리
            for file_path in self.relationships_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    # 파일 내용 확인하여 중요한 데이터인지 판단
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                            data = json.loads(content)
                        
                        # 최근 업데이트 시간 확인
                        updated_at = data.get("updated_at")
                        if updated_at:
                            update_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            if update_time.timestamp() < cutoff_time:
                                file_path.unlink()
                                deleted_count += 1
                                logger.debug(f"오래된 관계 설정 삭제: {file_path.name}")
                        else:
                            # updated_at이 없으면 파일 수정 시간 기준
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"오래된 관계 설정 삭제: {file_path.name}")
                            
                    except Exception as e:
                        logger.warning(f"파일 정리 중 오류 {file_path}: {e}")
                        continue
            
            logger.info(f"데이터 정리 완료: {deleted_count}개 파일 삭제")
            return deleted_count
            
        except Exception as e:
            logger.error(f"데이터 정리 실패: {e}")
            return 0
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        저장소 정보 조회
        
        Returns:
            Dict[str, Any]: 저장소 정보
        """
        try:
            info = {
                "storage_dir": str(self.storage_dir),
                "relationships_dir": str(self.relationships_dir),
                "total_relationships": 0,
                "total_size": 0,
                "last_modified": None
            }
            
            if self.relationships_dir.exists():
                relationship_files = list(self.relationships_dir.glob("*.json"))
                info["total_relationships"] = len(relationship_files)
                
                total_size = 0
                last_modified = None
                
                for file_path in relationship_files:
                    stat = file_path.stat()
                    total_size += stat.st_size
                    
                    if last_modified is None or stat.st_mtime > last_modified:
                        last_modified = stat.st_mtime
                
                info["total_size"] = total_size
                if last_modified:
                    info["last_modified"] = datetime.fromtimestamp(last_modified).isoformat()
            
            return info
            
        except Exception as e:
            logger.error(f"저장소 정보 조회 실패: {e}")
            return {
                "storage_dir": str(self.storage_dir),
                "error": str(e)
            }
