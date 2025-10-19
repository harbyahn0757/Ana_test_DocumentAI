"""
AI 클라이언트 서비스

OpenAI API 호출, 응답 처리, 재시도 로직 등을 담당하는 독립적인 모듈
"""

from openai import OpenAI
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class AIClientService:
    """AI 클라이언트 서비스 클래스"""
    
    def __init__(self):
        """초기화"""
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """OpenAI 클라이언트 설정"""
        try:
            # API 키 우선순위: 설정 파일 > 환경변수
            api_key = settings.openai_api_key
            if not api_key:
                import os
                api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                raise ValueError("OpenAI API 키가 설정되지 않았습니다")
                
            self.client = OpenAI(api_key=api_key)
            logger.info("✅ OpenAI 클라이언트 설정 완료")
        except Exception as e:
            logger.error(f"❌ OpenAI 클라이언트 설정 실패: {e}")
            raise
    
    async def call_openai_api(
        self,
        system_prompt: str,
        user_prompt: str,
        model_settings: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        OpenAI API 호출 (재시도 로직 포함)
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            model_settings: 모델 설정 (temperature, max_tokens 등)
            max_retries: 최대 재시도 횟수
            
        Returns:
            AI 응답 딕셔너리
        """
        # 기본 모델 설정
        default_settings = {
            'model': 'gpt-4o-mini',
            'temperature': 0.1,
            'max_tokens': 800
        }
        
        # 사용자 설정 병합
        if model_settings:
            default_settings.update(model_settings)
        
        # 메시지 구성
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
        
        # 재시도 로직
        for attempt in range(max_retries):
            try:
                # API 호출 시작 시간
                start_time = datetime.now()
                
                logger.info(f"🤖 OpenAI API 호출 시작 (시도 {attempt + 1}/{max_retries}):")
                logger.info(f"   모델: {default_settings['model']}")
                logger.info(f"   Temperature: {default_settings['temperature']}")
                logger.info(f"   Max Tokens: {default_settings['max_tokens']}")
                logger.info(f"   메시지 수: {len(messages)}")
                
                # OpenAI API 호출
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    messages=messages,
                    **default_settings
                )
                
                # 응답 시간 계산
                elapsed_time = (datetime.now() - start_time).total_seconds()
                
                # 응답 내용 추출
                content = response.choices[0].message.content
                usage = response.usage
                
                logger.info(f"✅ OpenAI API 응답 완료:")
                logger.info(f"   응답 시간: {elapsed_time:.2f}초")
                logger.info(f"   토큰 사용량: {usage.total_tokens} (입력: {usage.prompt_tokens}, 출력: {usage.completion_tokens})")
                logger.info(f"   응답 길이: {len(content)} 문자")
                
                return {
                    'success': True,
                    'content': content,
                    'usage': {
                        'total_tokens': usage.total_tokens,
                        'prompt_tokens': usage.prompt_tokens,
                        'completion_tokens': usage.completion_tokens
                    },
                    'response_time': elapsed_time,
                    'model': default_settings['model']
                }
                
            except Exception as e:
                error_type = type(e).__name__
                if "RateLimitError" in error_type:
                    logger.warning(f"⚠️ OpenAI API 속도 제한 (시도 {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # 지수 백오프
                elif "APIError" in error_type:
                    logger.error(f"❌ OpenAI API 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"❌ OpenAI API 호출 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
        
        # 모든 재시도 실패
        raise Exception("OpenAI API 호출 최종 실패")
    
    async def extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """
        AI 응답에서 JSON 추출 및 파싱
        
        Args:
            content: AI 응답 텍스트
            
        Returns:
            파싱된 JSON 딕셔너리
        """
        try:
            # JSON 블록 찾기 (```json ... ``` 또는 { ... })
            import re
            
            # 코드 블록에서 JSON 추출 시도
            json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            json_match = re.search(json_block_pattern, content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
            else:
                # 직접 JSON 객체 찾기
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                json_match = re.search(json_pattern, content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("JSON 형식을 찾을 수 없습니다")
            
            # JSON 파싱
            result = json.loads(json_str)
            
            logger.info(f"✅ JSON 파싱 성공: {list(result.keys())}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {e}")
            logger.error(f"원본 텍스트: {content[:500]}...")
            return {
                'error': 'JSON 파싱 실패',
                'original_content': content
            }
        except Exception as e:
            logger.error(f"❌ JSON 추출 실패: {e}")
            return {
                'error': str(e),
                'original_content': content
            }
    
    async def call_ai_with_json_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        AI 호출 후 JSON 응답 자동 파싱
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            model_settings: 모델 설정
            
        Returns:
            파싱된 JSON 응답
        """
        try:
            # AI API 호출
            response = await self.call_openai_api(
                system_prompt, 
                user_prompt, 
                model_settings
            )
            
            if not response['success']:
                return {
                    'error': 'AI API 호출 실패',
                    'details': response
                }
            
            # JSON 추출 및 파싱
            content = response['content']
            parsed_result = await self.extract_json_from_response(content)
            
            # 메타데이터 추가
            parsed_result['_metadata'] = {
                'usage': response['usage'],
                'response_time': response['response_time'],
                'model': response['model'],
                'original_content': content
            }
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"❌ AI JSON 응답 처리 실패: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def batch_ai_calls(
        self,
        calls: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        여러 AI 호출을 배치로 처리
        
        Args:
            calls: AI 호출 정보 리스트 [{'system_prompt': ..., 'user_prompt': ..., 'model_settings': ...}]
            max_concurrent: 최대 동시 호출 수
            
        Returns:
            응답 리스트
        """
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def call_with_semaphore(call_info):
                async with semaphore:
                    return await self.call_ai_with_json_response(
                        call_info.get('system_prompt', ''),
                        call_info.get('user_prompt', ''),
                        call_info.get('model_settings')
                    )
            
            logger.info(f"🚀 배치 AI 호출 시작: {len(calls)}개 호출, 최대 동시: {max_concurrent}")
            
            # 모든 호출을 동시에 실행
            tasks = [call_with_semaphore(call) for call in calls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 예외 처리
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ 배치 호출 {i+1} 실패: {result}")
                    processed_results.append({
                        'error': str(result),
                        'call_index': i
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"✅ 배치 AI 호출 완료: {len(processed_results)}개 결과")
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ 배치 AI 호출 실패: {e}")
            return [{'error': str(e)} for _ in calls]
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        API 상태 정보 조회
        
        Returns:
            API 상태 딕셔너리
        """
        return {
            'client_configured': self.client is not None,
            'api_key_set': bool(settings.openai_api_key),
            'timestamp': datetime.now().isoformat()
        }


# 전역 인스턴스 (싱글톤 패턴)
_ai_client_instance = None

def get_ai_client() -> AIClientService:
    """
    AI 클라이언트 서비스 인스턴스 조회 (싱글톤)
    
    Returns:
        AIClientService 인스턴스
    """
    global _ai_client_instance
    if _ai_client_instance is None:
        _ai_client_instance = AIClientService()
    return _ai_client_instance
