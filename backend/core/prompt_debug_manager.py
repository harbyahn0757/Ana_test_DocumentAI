"""
프롬프트 디버깅 시스템

AI 프롬프트와 응답을 저장, 조회, 분석할 수 있는 디버깅 시스템
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class PromptDebugEntry:
    """프롬프트 디버깅 엔트리"""
    
    def __init__(
        self,
        service_name: str,
        prompt_type: str,
        system_prompt: str,
        user_prompt: str,
        model_settings: Dict[str, Any],
        response: Optional[Dict[str, Any]] = None,
        execution_time: float = 0.0,
        success: bool = False,
        error_message: str = ""
    ):
        self.timestamp = datetime.now()
        self.service_name = service_name
        self.prompt_type = prompt_type
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.model_settings = model_settings
        self.response = response
        self.execution_time = execution_time
        self.success = success
        self.error_message = error_message
        
        # 고유 ID 생성 (프롬프트 내용 기반)
        content_hash = hashlib.md5(
            f"{system_prompt}{user_prompt}".encode('utf-8')
        ).hexdigest()[:8]
        self.entry_id = f"{self.timestamp.strftime('%Y%m%d_%H%M%S')}_{content_hash}"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "service_name": self.service_name,
            "prompt_type": self.prompt_type,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "model_settings": self.model_settings,
            "response": self.response,
            "execution_time": self.execution_time,
            "success": self.success,
            "error_message": self.error_message
        }


class PromptDebugManager:
    """프롬프트 디버깅 매니저"""
    
    def __init__(self, debug_dir: str = "debug_prompts"):
        """
        초기화
        
        Args:
            debug_dir: 디버깅 파일 저장 디렉토리
        """
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
        self._entries: List[PromptDebugEntry] = []
        self._max_entries = 1000  # 메모리에 보관할 최대 엔트리 수
        
        logger.info(f"프롬프트 디버깅 매니저 초기화 완료: {self.debug_dir}")
    
    def log_prompt_execution(
        self,
        service_name: str,
        prompt_type: str,
        system_prompt: str,
        user_prompt: str,
        model_settings: Dict[str, Any],
        response: Optional[Dict[str, Any]] = None,
        execution_time: float = 0.0,
        success: bool = False,
        error_message: str = ""
    ) -> str:
        """
        프롬프트 실행 결과 로깅
        
        Args:
            service_name: 서비스 이름
            prompt_type: 프롬프트 타입
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            model_settings: 모델 설정
            response: AI 응답
            execution_time: 실행 시간
            success: 성공 여부
            error_message: 에러 메시지
            
        Returns:
            str: 엔트리 ID
        """
        try:
            entry = PromptDebugEntry(
                service_name=service_name,
                prompt_type=prompt_type,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_settings=model_settings,
                response=response,
                execution_time=execution_time,
                success=success,
                error_message=error_message
            )
            
            # 메모리에 추가
            self._entries.append(entry)
            
            # 최대 개수 초과 시 오래된 것 제거
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries:]
            
            # 파일에 저장
            self._save_entry_to_file(entry)
            
            logger.debug(f"프롬프트 실행 로그 저장: {entry.entry_id}")
            return entry.entry_id
            
        except Exception as e:
            logger.error(f"프롬프트 디버깅 로그 저장 실패: {e}")
            return ""
    
    def _save_entry_to_file(self, entry: PromptDebugEntry):
        """엔트리를 파일에 저장"""
        try:
            # 날짜별 디렉토리 생성
            date_dir = self.debug_dir / entry.timestamp.strftime('%Y-%m-%d')
            date_dir.mkdir(exist_ok=True)
            
            # 파일명 생성
            filename = f"{entry.entry_id}.json"
            filepath = date_dir / filename
            
            # JSON으로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"프롬프트 디버깅 파일 저장 실패: {e}")
    
    def get_recent_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        최근 엔트리 조회
        
        Args:
            limit: 최대 조회 개수
            
        Returns:
            List[Dict[str, Any]]: 엔트리 리스트
        """
        try:
            # 최신순으로 정렬하여 반환
            recent_entries = sorted(
                self._entries,
                key=lambda x: x.timestamp,
                reverse=True
            )[:limit]
            
            return [entry.to_dict() for entry in recent_entries]
            
        except Exception as e:
            logger.error(f"최근 엔트리 조회 실패: {e}")
            return []
    
    def get_entries_by_service(self, service_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        서비스별 엔트리 조회
        
        Args:
            service_name: 서비스 이름
            limit: 최대 조회 개수
            
        Returns:
            List[Dict[str, Any]]: 엔트리 리스트
        """
        try:
            filtered_entries = [
                entry for entry in self._entries
                if entry.service_name == service_name
            ]
            
            # 최신순으로 정렬하여 반환
            recent_entries = sorted(
                filtered_entries,
                key=lambda x: x.timestamp,
                reverse=True
            )[:limit]
            
            return [entry.to_dict() for entry in recent_entries]
            
        except Exception as e:
            logger.error(f"서비스별 엔트리 조회 실패: {e}")
            return []
    
    def get_entries_by_prompt_type(self, prompt_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        프롬프트 타입별 엔트리 조회
        
        Args:
            prompt_type: 프롬프트 타입
            limit: 최대 조회 개수
            
        Returns:
            List[Dict[str, Any]]: 엔트리 리스트
        """
        try:
            filtered_entries = [
                entry for entry in self._entries
                if entry.prompt_type == prompt_type
            ]
            
            # 최신순으로 정렬하여 반환
            recent_entries = sorted(
                filtered_entries,
                key=lambda x: x.timestamp,
                reverse=True
            )[:limit]
            
            return [entry.to_dict() for entry in recent_entries]
            
        except Exception as e:
            logger.error(f"프롬프트 타입별 엔트리 조회 실패: {e}")
            return []
    
    def get_entry_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 엔트리 조회
        
        Args:
            entry_id: 엔트리 ID
            
        Returns:
            Optional[Dict[str, Any]]: 엔트리 또는 None
        """
        try:
            for entry in self._entries:
                if entry.entry_id == entry_id:
                    return entry.to_dict()
            
            # 메모리에 없으면 파일에서 검색
            return self._load_entry_from_file(entry_id)
            
        except Exception as e:
            logger.error(f"엔트리 조회 실패: {e}")
            return None
    
    def _load_entry_from_file(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """파일에서 엔트리 로드"""
        try:
            # 모든 날짜 디렉토리 검색
            for date_dir in self.debug_dir.iterdir():
                if date_dir.is_dir():
                    filepath = date_dir / f"{entry_id}.json"
                    if filepath.exists():
                        with open(filepath, 'r', encoding='utf-8') as f:
                            return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"파일에서 엔트리 로드 실패: {e}")
            return None
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        실행 통계 조회
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            if not self._entries:
                return {}
            
            total_entries = len(self._entries)
            successful_entries = sum(1 for entry in self._entries if entry.success)
            failed_entries = total_entries - successful_entries
            
            # 서비스별 통계
            service_stats = {}
            for entry in self._entries:
                service = entry.service_name
                if service not in service_stats:
                    service_stats[service] = {"total": 0, "success": 0, "failed": 0}
                
                service_stats[service]["total"] += 1
                if entry.success:
                    service_stats[service]["success"] += 1
                else:
                    service_stats[service]["failed"] += 1
            
            # 프롬프트 타입별 통계
            prompt_type_stats = {}
            for entry in self._entries:
                prompt_type = entry.prompt_type
                if prompt_type not in prompt_type_stats:
                    prompt_type_stats[prompt_type] = {"total": 0, "success": 0, "failed": 0}
                
                prompt_type_stats[prompt_type]["total"] += 1
                if entry.success:
                    prompt_type_stats[prompt_type]["success"] += 1
                else:
                    prompt_type_stats[prompt_type]["failed"] += 1
            
            # 평균 실행 시간
            execution_times = [entry.execution_time for entry in self._entries if entry.execution_time > 0]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            return {
                "total_entries": total_entries,
                "successful_entries": successful_entries,
                "failed_entries": failed_entries,
                "success_rate": (successful_entries / total_entries * 100) if total_entries > 0 else 0,
                "average_execution_time": avg_execution_time,
                "service_stats": service_stats,
                "prompt_type_stats": prompt_type_stats
            }
            
        except Exception as e:
            logger.error(f"실행 통계 조회 실패: {e}")
            return {}


# 전역 인스턴스
_prompt_debug_manager = None


def get_prompt_debug_manager() -> PromptDebugManager:
    """프롬프트 디버깅 매니저 싱글톤 인스턴스 반환"""
    global _prompt_debug_manager
    if _prompt_debug_manager is None:
        _prompt_debug_manager = PromptDebugManager()
    return _prompt_debug_manager




