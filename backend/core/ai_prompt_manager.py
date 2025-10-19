"""
AI 프롬프트 관리 시스템

key_mapping_database.json의 _ai_prompts 섹션을 사용하여
AI 프롬프트를 동적으로 빌드하고 관리하는 시스템
"""

import json
import logging
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AIPromptManager:
    """AI 프롬프트 매니저"""
    
    def __init__(self, database_path: str = "data/key_mapping_database.json"):
        """
        초기화
        
        Args:
            database_path: 키 매핑 데이터베이스 파일 경로
        """
        self.database_path = Path(database_path)
        self._prompts_cache: Optional[Dict[str, Any]] = None
        self._load_prompts()
        
        logger.info(f"AI 프롬프트 매니저 초기화 완료: {self.database_path}")
    
    def _load_prompts(self):
        """프롬프트 데이터 로드"""
        try:
            if not self.database_path.exists():
                logger.error(f"데이터베이스 파일을 찾을 수 없습니다: {self.database_path}")
                self._prompts_cache = {}
                return
            
            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._prompts_cache = data.get('_ai_prompts', {})
                
            logger.info(f"프롬프트 {len(self._prompts_cache)}개 로드 완료")
            
        except Exception as e:
            logger.error(f"프롬프트 데이터 로드 실패: {e}")
            self._prompts_cache = {}
    
    def reload_prompts(self):
        """프롬프트 데이터 재로드"""
        self._prompts_cache = None
        self._load_prompts()
    
    def get_available_prompts(self) -> list:
        """사용 가능한 프롬프트 타입 목록 반환"""
        return list(self._prompts_cache.keys()) if self._prompts_cache else []
    
    async def build_prompt(
        self,
        prompt_type: str,
        **kwargs
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        프롬프트 빌드
        
        Args:
            prompt_type: 프롬프트 타입 (header_analysis, value_extraction 등)
            **kwargs: 프롬프트 템플릿에 전달할 파라미터들
            
        Returns:
            Tuple[system_prompt, user_prompt, model_settings]
        """
        if not self._prompts_cache:
            raise ValueError("프롬프트 데이터가 로드되지 않았습니다")
        
        if prompt_type not in self._prompts_cache:
            available_types = list(self._prompts_cache.keys())
            raise ValueError(f"알 수 없는 프롬프트 타입: {prompt_type}. 사용 가능한 타입: {available_types}")
        
        prompt_config = self._prompts_cache[prompt_type]
        
        # 시스템 프롬프트
        system_prompt = prompt_config.get('system_prompt', '')
        
        # 사용자 프롬프트 템플릿
        user_prompt_template = prompt_config.get('user_prompt_template', '')
        
        # 모델 설정
        model_settings = prompt_config.get('model_settings', {})
        
        # 템플릿 파라미터 검증
        required_params = prompt_config.get('parameters', [])
        missing_params = [param for param in required_params if param not in kwargs]
        
        if missing_params:
            raise ValueError(f"필수 파라미터가 누락되었습니다: {missing_params}")
        
        # 추가 처리: key_specific_instructions 처리
        if prompt_type == 'value_extraction' and 'key_name' in kwargs:
            key_name = kwargs['key_name']
            kwargs['key_specific_instructions'] = self.get_key_specific_instructions(key_name)
        
        # 사용자 프롬프트 빌드
        try:
            user_prompt = user_prompt_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"프롬프트 템플릿 파라미터 에러: {e}")
        
        logger.debug(f"프롬프트 빌드 완료: {prompt_type}")
        
        return system_prompt, user_prompt, model_settings
    
    def get_key_specific_instructions(self, key_name: str) -> str:
        """키별 특화 지시사항 가져오기"""
        if not self._prompts_cache:
            return self._get_default_instructions()
        
        key_instructions = self._prompts_cache.get('key_specific_instructions', {})
        
        # 정확한 키 이름으로 찾기
        if key_name in key_instructions:
            return key_instructions[key_name]
        
        # 키 이름에 따른 패턴 매칭
        if '주민등록번호' in key_name:
            return key_instructions.get('주민등록번호', self._get_default_instructions())
        elif '신장' in key_name or '키' in key_name:
            return key_instructions.get('신장', self._get_default_instructions())
        elif '체중' in key_name:
            return key_instructions.get('체중', self._get_default_instructions())
        elif '혈압' in key_name:
            return key_instructions.get('혈압', self._get_default_instructions())
        elif '혈당' in key_name:
            return key_instructions.get('혈당', self._get_default_instructions())
        
        return key_instructions.get('default', self._get_default_instructions())
    
    def _get_default_instructions(self) -> str:
        """기본 지시사항 반환"""
        return """## 일반 규칙
- 앵커 셀 근처에서 관련된 값을 찾아주세요
- 숫자, 단위, 특수문자가 포함된 셀을 확인하세요
- 빈 셀이 아닌 실제 값이 있는 셀을 찾아주세요"""
    
    def get_prompt_info(self, prompt_type: str) -> Optional[Dict[str, Any]]:
        """특정 프롬프트 타입의 정보 반환"""
        if not self._prompts_cache:
            return None
        
        return self._prompts_cache.get(prompt_type)
    
    def validate_prompt_config(self, prompt_type: str) -> bool:
        """프롬프트 설정 유효성 검증"""
        if not self._prompts_cache or prompt_type not in self._prompts_cache:
            return False
        
        config = self._prompts_cache[prompt_type]
        required_fields = ['system_prompt', 'user_prompt_template']
        
        return all(field in config for field in required_fields)


# 전역 인스턴스
_prompt_manager = None


def get_prompt_manager() -> AIPromptManager:
    """프롬프트 매니저 싱글톤 인스턴스 반환"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = AIPromptManager()
    return _prompt_manager

