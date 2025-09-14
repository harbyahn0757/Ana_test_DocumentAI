"""
AI 기반 값 추출 서비스
OpenAI API를 사용하여 키 인식 후 적절한 값을 자동으로 추출
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pydantic import BaseModel
import openai
from openai import AsyncOpenAI
import time

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AIExtractionRequest:
    """AI 추출 요청 데이터"""
    key_name: str
    key_label: str
    anchor_cell: Dict[str, Any]
    table_data: List[List[str]]
    page_number: int
    context: Optional[str] = None


class AIExtractionResult(BaseModel):
    """AI 추출 결과"""
    key_name: str
    extracted_value: str
    confidence: float
    reasoning: str
    suggested_position: Dict[str, int]
    processing_time: float = 0.0
    model_used: str = ""


class AIExtractionService:
    """AI 기반 값 추출 서비스"""
    
    def __init__(self):
        self.client = None
        self._initialized = False
    
    def _initialize_client(self):
        """OpenAI 클라이언트 초기화"""
        try:
            # API 키 확인 (환경변수 우선, 설정 파일 차선)
            api_key = os.getenv('OPENAI_API_KEY') or settings.openai_api_key
            
            if not api_key:
                logger.warning("OpenAI API 키가 설정되지 않았습니다.")
                return
            
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("OpenAI 클라이언트가 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {e}")
            self.client = None
    
    async def extract_value(self, request: AIExtractionRequest) -> Optional[AIExtractionResult]:
        """
        AI를 사용하여 키에 대한 값을 추출
        
        Args:
            request: AI 추출 요청 데이터
            
        Returns:
            AIExtractionResult: 추출 결과 또는 None
        """
        if not self.client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return None
        
        start_time = time.time()
        
        try:
            # 프롬프트 생성
            prompt = self._create_extraction_prompt(request)
            
            # OpenAI API 호출
            response = await self._call_openai_api(prompt)
            
            if not response:
                return None
            
            # 응답 파싱
            result = self._parse_ai_response(response, request.key_name)
            
            if result:
                result.processing_time = time.time() - start_time
                result.model_used = settings.openai_model
                
                # 신뢰도 검증
                if result.confidence >= settings.ai_confidence_threshold:
                    logger.info(f"AI 추출 성공: {request.key_name} -> {result.extracted_value} (신뢰도: {result.confidence:.2f})")
                    return result
                else:
                    logger.warning(f"AI 추출 신뢰도 부족: {request.key_name} (신뢰도: {result.confidence:.2f})")
                    return None
            
        except Exception as e:
            logger.error(f"AI 추출 실패: {e}")
            logger.error(f"AI 추출 실패 상세: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"AI 추출 실패 스택 트레이스: {traceback.format_exc()}")
            return None
        
        return None
    
    def _create_extraction_prompt(self, request: AIExtractionRequest) -> str:
        """AI 추출을 위한 프롬프트 생성"""
        
        # 테이블 데이터를 문자열로 변환
        table_str = self._format_table_data(request.table_data, request.anchor_cell)
        
        # 키별 특화 지시사항 생성
        key_specific_instructions = self._get_key_specific_instructions(request.key_name, request.key_label)
        
        prompt = f"""
당신은 의료 검진 보고서에서 특정 키에 대한 값을 정확하게 추출하는 AI입니다.

## 작업 지시사항
1. 주어진 테이블 데이터에서 "{request.key_label}" ({request.key_name}) 키에 해당하는 값을 찾아주세요.
2. 앵커 셀 위치: 행 {request.anchor_cell.get('row', 'N/A')}, 열 {request.anchor_cell.get('col', 'N/A')} - "{request.anchor_cell.get('value', 'N/A')}"
3. 앵커 셀 근처에서 해당 키의 값을 찾아주세요.

## 테이블 데이터 구조 설명
- 테이블은 2차원 배열로 구성: data[row][col]
- 행(row): 세로 방향 (위에서 아래로)
- 열(col): 가로 방향 (왼쪽에서 오른쪽으로)
- 앵커 셀 기준으로:
  * 오른쪽: col + 1
  * 왼쪽: col - 1  
  * 아래쪽: row + 1
  * 위쪽: row - 1

{key_specific_instructions}

## 테이블 데이터 (페이지 {request.page_number})
{table_str}

## 응답 형식 (JSON)
{{
    "extracted_value": "추출된 값 (문자열)",
    "confidence": 0.95,
    "reasoning": "값을 찾은 근거와 추론 과정",
    "suggested_position": {{
        "row": 1,
        "col": 0
    }}
}}

## 중요 규칙
- extracted_value는 반드시 문자열로 반환
- confidence는 0.0~1.0 사이의 실수
- suggested_position은 반드시 앵커 셀 기준 상대 좌표로 반환
  * 앵커 셀 위치: 행 {request.anchor_cell.get('row', 'N/A')}, 열 {request.anchor_cell.get('col', 'N/A')}
  * 상대 좌표 계산: (값_행 - 앵커_행, 값_열 - 앵커_열)
  * 예시: 앵커가 (1,15)이고 값이 (1,18)이면 상대좌표는 (0,3)
  * 오른쪽 1칸: {{"row": 0, "col": 1}}
  * 아래쪽 1칸: {{"row": 1, "col": 0}}
  * 왼쪽 1칸: {{"row": 0, "col": -1}}
  * 위쪽 1칸: {{"row": -1, "col": 0}}
- 값을 찾을 수 없으면 extracted_value를 "NOT_FOUND"로 설정
- confidence가 0.7 미만이면 신뢰할 수 없는 결과로 간주

## 예시
키: "신장" -> 값: "170cm" 또는 "170"
키: "체중" -> 값: "65kg" 또는 "65"
키: "혈압" -> 값: "120/80" 또는 "120/80mmHg"

## 상대 좌표 계산 예시
- 앵커 셀: (1, 15) "전화번호"
- 값 셀: (1, 18) "01036595213"
- 상대 좌표: (1-1, 18-15) = (0, 3)
- 따라서 suggested_position: {{"row": 0, "col": 3}}

이제 "{request.key_label}" 키의 값을 찾고 정확한 상대 좌표를 계산해주세요:
"""
        
        # 프롬프트 콘솔 로깅
        logger.info(f"🤖 AI 추출 프롬프트 생성:")
        logger.info(f"   키: {request.key_name} ({request.key_label})")
        logger.info(f"   앵커 셀: {request.anchor_cell}")
        logger.info(f"   페이지: {request.page_number}")
        logger.info(f"   테이블 데이터 크기: {len(request.table_data)}x{len(request.table_data[0]) if request.table_data else 0}")
        logger.info(f"📝 생성된 프롬프트:\n{prompt}")
        
        return prompt
    
    def _get_key_specific_instructions(self, key_name: str, key_label: str) -> str:
        """키별 특화 지시사항 생성"""
        key_lower = key_name.lower()
        
        if "주민등록번호" in key_name or "주민번호" in key_name or "resident" in key_lower:
            return """
## 주민등록번호 특화 규칙
- 주민등록번호는 13자리 숫자 (000000-0000000 형식)
- 앵커 셀 근처에서 숫자 패턴을 찾아주세요
- 일반적으로 앵커 셀의 오른쪽이나 아래쪽에 위치
- 하이픈(-)이 포함된 13자리 숫자 문자열을 찾아주세요
- 예시: "123456-1234567", "1234561234567" (하이픈 없음)
- 숫자만 있는 셀을 우선적으로 확인하세요
"""
        elif "신장" in key_name or "키" in key_name or "height" in key_lower:
            return """
## 신장 특화 규칙
- 신장은 보통 cm 단위로 표시됩니다
- 예시: "170cm", "170", "170.5cm"
- 숫자와 cm가 함께 있는 셀을 찾아주세요
"""
        elif "체중" in key_name or "몸무게" in key_name or "weight" in key_lower:
            return """
## 체중 특화 규칙
- 체중은 보통 kg 단위로 표시됩니다
- 예시: "65kg", "65", "65.5kg"
- 숫자와 kg가 함께 있는 셀을 찾아주세요
"""
        elif "혈압" in key_name or "blood pressure" in key_lower or "bp" in key_lower:
            return """
## 혈압 특화 규칙
- 혈압은 보통 "수축기/이완기" 형식으로 표시됩니다
- 예시: "120/80", "120/80mmHg", "120-80"
- 슬래시(/)나 하이픈(-)으로 구분된 두 숫자를 찾아주세요
"""
        elif "혈당" in key_name or "glucose" in key_lower or "당뇨" in key_name:
            return """
## 혈당 특화 규칙
- 혈당은 보통 mg/dl 단위로 표시됩니다
- 예시: "100mg/dl", "100", "100.5"
- 숫자와 mg/dl가 함께 있는 셀을 찾아주세요
"""
        else:
            return """
## 일반 규칙
- 앵커 셀 근처에서 관련된 값을 찾아주세요
- 숫자, 단위, 특수문자가 포함된 셀을 확인하세요
- 빈 셀이 아닌 실제 값이 있는 셀을 찾아주세요
"""
    
    def _format_table_data(self, table_data: List[List[str]], anchor_cell: Dict[str, Any]) -> str:
        """테이블 데이터를 읽기 쉬운 형태로 포맷팅"""
        if not table_data:
            return "테이블 데이터가 없습니다."
        
        # 테이블 데이터 상세 로깅
        logger.info(f"📊 테이블 데이터 포맷팅:")
        logger.info(f"   테이블 크기: {len(table_data)}x{len(table_data[0]) if table_data else 0}")
        logger.info(f"   앵커 셀 위치: ({anchor_cell.get('row', 0)}, {anchor_cell.get('col', 0)})")
        logger.info(f"   앵커 셀 값: '{anchor_cell.get('value', 'N/A')}'")
        
        # 앵커 셀 주변 데이터 로깅
        anchor_row = anchor_cell.get('row', 0)
        anchor_col = anchor_cell.get('col', 0)
        
        logger.info(f"🔍 앵커 셀 주변 데이터:")
        for i in range(max(0, anchor_row-2), min(len(table_data), anchor_row+3)):
            row_data = []
            for j in range(max(0, anchor_col-2), min(len(table_data[i]) if i < len(table_data) else 0, anchor_col+3)):
                cell_value = table_data[i][j] if i < len(table_data) and j < len(table_data[i]) else ""
                if i == anchor_row and j == anchor_col:
                    row_data.append(f"[{cell_value}]")
                else:
                    row_data.append(cell_value or "")
            logger.info(f"   행 {i}: {' | '.join(row_data)}")
        
        formatted_rows = []
        for i, row in enumerate(table_data):
            formatted_cells = []
            for j, cell in enumerate(row):
                # 앵커 셀 하이라이트
                if i == anchor_row and j == anchor_col:
                    formatted_cells.append(f"[{cell}]")  # 앵커 셀 표시
                else:
                    formatted_cells.append(cell or "")
            
            formatted_rows.append(f"행 {i}: {' | '.join(formatted_cells)}")
        
        formatted_table = "\n".join(formatted_rows)
        logger.info(f"📝 포맷된 테이블 데이터:\n{formatted_table}")
        
        return formatted_table
    
    async def _call_openai_api(self, prompt: str) -> Optional[str]:
        """OpenAI API 호출"""
        for attempt in range(settings.ai_max_retries):
            try:
                logger.info(f"🚀 OpenAI API 호출 시작 (시도 {attempt + 1}/{settings.ai_max_retries})")
                
                response = await self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 의료 검진 보고서 데이터 추출 전문가입니다. 정확하고 신뢰할 수 있는 값을 추출해주세요."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=settings.openai_max_tokens,
                    temperature=settings.openai_temperature,
                    response_format={"type": "json_object"}
                )
                
                ai_response = response.choices[0].message.content
                
                # AI 응답 콘솔 로깅
                logger.info(f"🤖 AI 응답 수신:")
                logger.info(f"   모델: {settings.openai_model}")
                logger.info(f"   토큰 사용량: {response.usage.total_tokens if response.usage else 'N/A'}")
                logger.info(f"📤 AI 응답 내용:\n{ai_response}")
                
                return ai_response
                
            except Exception as e:
                logger.warning(f"OpenAI API 호출 실패 (시도 {attempt + 1}/{settings.ai_max_retries}): {e}")
                
                if attempt < settings.ai_max_retries - 1:
                    await asyncio.sleep(settings.ai_retry_delay)
                else:
                    logger.error("OpenAI API 호출 최종 실패")
                    return None
        
        return None
    
    def _parse_ai_response(self, response: str, key_name: str) -> Optional[AIExtractionResult]:
        """AI 응답 파싱"""
        try:
            data = json.loads(response)
            
            # 파싱된 데이터 로깅
            logger.info(f"🔍 AI 응답 파싱 결과:")
            logger.info(f"   키: {key_name}")
            logger.info(f"   추출된 값: {data.get('extracted_value', 'N/A')}")
            logger.info(f"   신뢰도: {data.get('confidence', 'N/A')}")
            logger.info(f"   추론 과정: {data.get('reasoning', 'N/A')}")
            logger.info(f"   제안 위치: {data.get('suggested_position', 'N/A')}")
            
            # 필수 필드 검증
            required_fields = ['extracted_value', 'confidence', 'reasoning', 'suggested_position']
            for field in required_fields:
                if field not in data:
                    logger.error(f"AI 응답에 필수 필드 '{field}'가 없습니다.")
                    return None
            
            # suggested_position 검증
            position = data['suggested_position']
            if not isinstance(position, dict) or 'row' not in position or 'col' not in position:
                logger.error("AI 응답의 suggested_position 형식이 올바르지 않습니다.")
                return None
            
            result = AIExtractionResult(
                key_name=key_name,
                extracted_value=str(data['extracted_value']),
                confidence=float(data['confidence']),
                reasoning=data['reasoning'],
                suggested_position=position,
                processing_time=0.0,  # 나중에 설정
                model_used=""
            )
            
            logger.info(f"✅ AI 추출 결과 생성 완료: {result.extracted_value} (신뢰도: {result.confidence:.2f})")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"AI 응답 JSON 파싱 실패: {e}")
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"AI 응답 데이터 타입 오류: {e}")
            return None
    
    async def batch_extract_values(self, requests: List[AIExtractionRequest]) -> List[AIExtractionResult]:
        """여러 키에 대한 값을 배치로 추출"""
        if not requests:
            return []
        
        # 동시 처리할 수 있는 최대 요청 수 제한
        max_concurrent = 5
        results = []
        
        for i in range(0, len(requests), max_concurrent):
            batch = requests[i:i + max_concurrent]
            tasks = [self.extract_value(req) for req in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, AIExtractionResult):
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"배치 추출 중 오류: {result}")
        
        return results
    
    def _ensure_initialized(self):
        """클라이언트 초기화 확인 및 실행"""
        if not self._initialized:
            self._initialize_client()
            self._initialized = True
    
    def is_available(self) -> bool:
        """AI 서비스 사용 가능 여부 확인"""
        self._ensure_initialized()
        api_key = os.getenv('OPENAI_API_KEY') or settings.openai_api_key
        return self.client is not None and api_key is not None


# 전역 서비스 인스턴스
ai_extraction_service = AIExtractionService()
