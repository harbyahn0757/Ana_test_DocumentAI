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
import time

from app.config import settings
from core.base_ai_service import BaseAIService

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


class AIHeaderAnalysisResult(BaseModel):
    """AI 헤더 분석 결과"""
    column_mappings: Dict[int, str]  # {col_index: field_type}
    row_mappings: Dict[int, str] = {}  # {row_index: field_type} - 세로 헤더용
    table_structure: str = "horizontal"  # "horizontal", "vertical", "mixed"
    header_orientation: str = "top"  # "top", "left", "both", "mixed"
    confidence: float
    reasoning: str
    detected_fields: List[str]
    table_analysis: str = ""  # 테이블 구조 분석 설명
    processing_time: float = 0.0
    model_used: str = ""


class AIExtractionService(BaseAIService):
    """AI 기반 값 추출 서비스"""
    
    def __init__(self):
        super().__init__("AI값추출서비스")
    
    async def _validate_initialization(self) -> bool:
        """초기화 검증"""
        return self._initialized
    
    def is_available(self) -> bool:
        """
        AI 서비스 사용 가능 여부 확인 (호환성 메서드)
        
        Returns:
            bool: AI 서비스 사용 가능 여부
        """
        return self.is_ai_available
    
    
    async def extract_value(self, request: AIExtractionRequest) -> Optional[AIExtractionResult]:
        """
        AI를 사용하여 키에 대한 값을 추출
        
        Args:
            request: AI 추출 요청 데이터
            
        Returns:
            AIExtractionResult: 추출 결과 또는 None
        """
        if not self.is_ai_available:
            self.log_error("AI 서비스가 사용 불가능합니다")
            return None
        
        start_time = time.time()
        
        try:
            # AI 호출
            ai_result = await self.call_ai_with_prompt(
                "value_extraction",
                key_label=request.key_label,
                key_name=request.key_name,
                anchor_row=request.anchor_cell.get('row', 'N/A'),
                anchor_col=request.anchor_cell.get('col', 'N/A'),
                anchor_text=request.anchor_cell.get('value', 'N/A'),
                key_specific_instructions=self.prompt_manager.get_key_specific_instructions(request.key_name),
                page_number=request.page_number,
                table_data=self._format_table_data(request.table_data, request.anchor_cell)
            )
            
            if not ai_result:
                return None
            
            # 응답 파싱
            result = self._parse_ai_dict_response(ai_result, request.key_name)
            
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
    
    
    async def _get_key_specific_instructions(self, key_name: str, key_label: str) -> str:
        """키별 특화 지시사항 생성 (프롬프트 매니저 사용)"""
        return self.prompt_manager.get_key_specific_instructions(key_name)
    
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
    
    async def _call_openai_api(self, system_prompt: str, user_prompt: str, model_settings: Optional[dict] = None) -> Optional[str]:
        """AI 클라이언트를 통한 API 호출"""
        try:
            # 기본 모델 설정
            default_settings = {
                'model': settings.openai_model,
                'max_tokens': settings.openai_max_tokens,
                'temperature': settings.openai_temperature,
                'response_format': {"type": "json_object"}
            }
            
            # 사용자 설정 병합
            if model_settings:
                default_settings.update(model_settings)
            
            # AI 클라이언트를 통해 호출
            result = await self.ai_client.call_ai_with_json_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_settings=default_settings
            )
            
            # 에러 확인
            if 'error' in result:
                logger.error(f"❌ AI 클라이언트 호출 실패: {result['error']}")
                return None
            
            # 메타데이터 로깅
            if '_metadata' in result:
                metadata = result['_metadata']
                logger.info(f"🤖 AI 응답 메타데이터:")
                logger.info(f"   토큰 사용량: {metadata.get('usage', {}).get('total_tokens', 'N/A')}")
                logger.info(f"   응답 시간: {metadata.get('response_time', 'N/A')}초")
                logger.info(f"   모델: {metadata.get('model', 'N/A')}")
            
            # 원본 응답 반환 (JSON 파싱 전)
            return result.get('_metadata', {}).get('original_content', json.dumps(result))
                
        except Exception as e:
            logger.error(f"❌ AI API 호출 실패: {e}")
            return None
    
    def _parse_ai_dict_response(self, response: Dict[str, Any], key_name: str) -> Optional[AIExtractionResult]:
        """AI 딕셔너리 응답 파싱"""
        try:
            # 파싱된 데이터 로깅
            logger.info(f"🔍 AI 응답 파싱 결과:")
            logger.info(f"   키: {key_name}")
            logger.info(f"   추출된 값: {response.get('extracted_value', 'N/A')}")
            logger.info(f"   신뢰도: {response.get('confidence', 'N/A')}")
            logger.info(f"   추론 과정: {response.get('reasoning', 'N/A')}")
            logger.info(f"   제안 위치: {response.get('suggested_position', 'N/A')}")
            
            # 필수 필드 검증
            required_fields = ['extracted_value', 'confidence', 'reasoning', 'suggested_position']
            for field in required_fields:
                if field not in response:
                    logger.warning(f"⚠️ 필수 필드 누락: {field}")
                    return None
            
            # AIExtractionResult 생성
            return AIExtractionResult(
                key_name=key_name,
                extracted_value=str(response['extracted_value']),
                confidence=float(response.get('confidence', 0.0)),
                reasoning=str(response.get('reasoning', '')),
                suggested_position=response.get('suggested_position', {}),
                processing_time=0.0,
                model_used=""
            )
            
        except Exception as e:
            logger.error(f"❌ AI 응답 파싱 실패: {e}")
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
    
    async def analyze_table_headers(self, table_data: List[List[str]], anchor_key: str) -> Optional[AIHeaderAnalysisResult]:
        """
        AI를 사용하여 테이블 헤더 분석
        각 열이 어떤 필드 타입(검사결과, 정상치, 판정, 소견 등)인지 자동 분류
        
        Args:
            table_data: 테이블 데이터 (첫 번째 행이 헤더)
            anchor_key: 기준 키 (예: "신장", "체중")
            
        Returns:
            AIHeaderAnalysisResult: 헤더 분석 결과
        """
        if not self.is_available() or not table_data or len(table_data) < 1:
            return None
            
        start_time = time.time()
        
        try:
            self._ensure_initialized()
            
            # 헤더 행 추출
            headers = table_data[0] if table_data else []
            if not headers:
                return None
                
            # 프롬프트 매니저를 통한 헤더 분석 프롬프트 생성
            system_prompt, user_prompt, model_settings = await self.prompt_manager.build_prompt(
                "header_analysis",
                headers=headers,
                anchor_key=anchor_key,
                table_data=table_data
            )
            
            # AI 클라이언트를 통한 API 호출
            result = await self.ai_client.call_ai_with_json_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_settings=model_settings
            )
            
            # 에러 확인
            if 'error' in result:
                logger.error(f"❌ AI 헤더 분석 실패: {result['error']}")
                return None
            
            # 결과 데이터 추출 (AI 클라이언트가 이미 JSON 파싱 완료)
            result_data = {k: v for k, v in result.items() if not k.startswith('_')}
            
            processing_time = time.time() - start_time
            
            return AIHeaderAnalysisResult(
                column_mappings=result_data.get("column_mappings", {}),
                row_mappings=result_data.get("row_mappings", {}),
                table_structure=result_data.get("table_structure", "horizontal"),
                header_orientation=result_data.get("header_orientation", "top"),
                confidence=result_data.get("confidence", 0.0),
                reasoning=result_data.get("reasoning", ""),
                detected_fields=result_data.get("detected_fields", []),
                table_analysis=result_data.get("table_analysis", ""),
                processing_time=processing_time,
                model_used=settings.openai_model
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"AI 헤더 분석 응답 파싱 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"AI 헤더 분석 실패: {e}")
            return None
    
    
    def _ensure_initialized(self):
        """클라이언트 초기화 확인 및 실행"""
        if not self._initialized:
            # BaseAIService에서 이미 초기화됨
            self._initialized = True
    



# 전역 서비스 인스턴스
ai_extraction_service = AIExtractionService()
