"""
AI 서비스 기반 클래스

AI를 사용하는 모든 서비스의 공통 기능을 제공하는 베이스 클래스
"""

import logging
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from core.ai_prompt_manager import get_prompt_manager
from core.ai_client_service import get_ai_client
from core.prompt_debug_manager import get_prompt_debug_manager

logger = logging.getLogger(__name__)


class BaseAIService(ABC):
    """AI 서비스를 위한 베이스 클래스"""
    
    def __init__(self, service_name: str):
        """
        초기화
        
        Args:
            service_name: 서비스 이름 (로깅용)
        """
        self.service_name = service_name
        self.prompt_manager = get_prompt_manager()
        self.ai_client = get_ai_client()
        self.debug_manager = get_prompt_debug_manager()
        self._initialized = False
        self._setup_service()
    
    def _setup_service(self):
        """서비스 설정"""
        try:
            logger.info(f"{self.service_name} 초기화 완료")
            self._initialized = True
        except Exception as e:
            logger.error(f"{self.service_name} 초기화 실패: {e}")
            raise
    
    @property
    def is_ai_available(self) -> bool:
        """AI 서비스 사용 가능 여부"""
        try:
            status = self.ai_client.get_api_status()
            return status.get('api_key_set', False) and status.get('client_configured', False)
        except Exception:
            return False
    
    async def call_ai_with_prompt(
        self,
        prompt_type: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        프롬프트 타입과 파라미터로 AI 호출
        
        Args:
            prompt_type: 프롬프트 타입 (key_mapping_database.json의 _ai_prompts 키)
            **kwargs: 프롬프트 템플릿에 전달할 파라미터들
            
        Returns:
            AI 응답 결과 또는 None
        """
        if not self.is_ai_available:
            logger.warning(f"{self.service_name}: AI 서비스가 사용 불가능")
            return None
        
        start_time = time.time()
        
        try:
            # 프롬프트 생성
            system_prompt, user_prompt, model_settings = await self.prompt_manager.build_prompt(
                prompt_type, **kwargs
            )
            
            # AI 호출
            response = await self.ai_client.call_ai_with_json_response(
                system_prompt, user_prompt, model_settings
            )
            
            execution_time = time.time() - start_time
            
            if response and response.get('success'):
                # 성공한 호출 디버깅 로그
                self.debug_manager.log_prompt_execution(
                    service_name=self.service_name,
                    prompt_type=prompt_type,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model_settings=model_settings,
                    response=response.get('content'),
                    execution_time=execution_time,
                    success=True
                )
                
                logger.debug(f"{self.service_name}: AI 호출 성공 - {prompt_type}")
                return response.get('content')
            else:
                # 실패한 호출 디버깅 로그
                self.debug_manager.log_prompt_execution(
                    service_name=self.service_name,
                    prompt_type=prompt_type,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model_settings=model_settings,
                    execution_time=execution_time,
                    success=False,
                    error_message="AI 응답 실패"
                )
                
                logger.warning(f"{self.service_name}: AI 호출 실패 - {prompt_type}")
                return None
                
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 예외 발생 디버깅 로그
            self.debug_manager.log_prompt_execution(
                service_name=self.service_name,
                prompt_type=prompt_type,
                system_prompt="",
                user_prompt="",
                model_settings={},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"{self.service_name}: AI 호출 오류 - {prompt_type}: {e}")
            return None
    
    async def call_ai_with_raw_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        model_settings: Optional[Dict[str, Any]] = None,
        expect_json: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        원시 프롬프트로 AI 호출
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            model_settings: 모델 설정
            expect_json: JSON 응답 기대 여부
            
        Returns:
            AI 응답 결과 또는 None
        """
        if not self.is_ai_available:
            logger.warning(f"{self.service_name}: AI 서비스가 사용 불가능")
            return None
        
        try:
            if expect_json:
                response = await self.ai_client.call_ai_with_json_response(
                    system_prompt, user_prompt, model_settings
                )
                # JSON 응답에 에러가 없으면 성공으로 간주
                if response and not response.get('error'):
                    return response
                else:
                    logger.warning(f"{self.service_name}: AI 호출 실패 - {prompt_type}: {response.get('error', '알 수 없는 오류')}")
            else:
                response = await self.ai_client.call_openai_api(
                    system_prompt, user_prompt, model_settings
                )
                if response and response.get('success'):
                    return {'content': response.get('content')}
            
            return None
            
        except Exception as e:
            logger.error(f"{self.service_name}: AI 호출 오류: {e}")
            return None
    
    def log_info(self, message: str, **kwargs):
        """서비스별 정보 로깅"""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        full_message = f"{self.service_name}: {message}"
        if extra_info:
            full_message += f" ({extra_info})"
        logger.info(full_message)
    
    def log_warning(self, message: str, **kwargs):
        """서비스별 경고 로깅"""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        full_message = f"{self.service_name}: {message}"
        if extra_info:
            full_message += f" ({extra_info})"
        logger.warning(full_message)
    
    def log_error(self, message: str, **kwargs):
        """서비스별 에러 로깅"""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        full_message = f"{self.service_name}: {message}"
        if extra_info:
            full_message += f" ({extra_info})"
        logger.error(full_message)
    
    @abstractmethod
    async def _validate_initialization(self) -> bool:
        """
        초기화 검증 (하위 클래스에서 구현)
        
        Returns:
            bool: 초기화 성공 여부
        """
        pass
