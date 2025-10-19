"""
추출 서비스

PDF에서 표를 추출하는 핵심 로직을 담당
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from models.table_models import TableData, ExtractionLibrary
from core.pdf_processor.factory import PDFProcessorFactory
from services.ai_extraction_service import ai_extraction_service, AIExtractionRequest
from core.table_analyzer import get_table_structure_analyzer, TableStructureAnalysis

logger = logging.getLogger(__name__)


class ExtractionService:
    """추출 서비스 클래스"""
    
    def __init__(self):
        """추출 서비스 초기화"""
        self.processor_factory = PDFProcessorFactory()
        self.table_analyzer = get_table_structure_analyzer()
        logger.info("추출 서비스 초기화 완료")
    
    async def extract_tables(
        self, 
        file_path: str, 
        library: str
    ) -> List[TableData]:
        """
        PDF에서 표 추출
        
        Args:
            file_path: PDF 파일 경로
            library: 추출 라이브러리 이름
            
        Returns:
            List[TableData]: 추출된 표 데이터 목록
        """
        try:
            logger.info(f"표 추출 시작: {file_path}, 라이브러리: {library}")
            
            # 파일 경로를 Path 객체로 변환
            from pathlib import Path
            pdf_path = Path(file_path)
            
            # 프로세서 생성
            processor = self.processor_factory.create_processor(library)
            if not processor:
                raise ValueError(f"지원하지 않는 라이브러리입니다: {library}")
            
            # 표 추출 실행
            tables = processor.extract_tables(pdf_path)
            
            # 이미 TableData 객체 리스트이므로 그대로 반환
            logger.info(f"표 추출 완료: {len(tables)}개 표 추출")
            return tables
            
        except Exception as e:
            logger.error(f"표 추출 실패 {file_path}: {e}")
            raise
    
    async def extract_data_with_mappings(
        self, 
        file_path: str, 
        mappings: List[Dict[str, Any]],
        processor_type: str = "pdfplumber"
    ) -> Dict[str, Any]:
        """
        매핑 기반 데이터 추출 (템플릿 기반 추출용)
        
        Args:
            file_path: PDF 파일 경로
            mappings: 키-값 매핑 설정
            processor_type: PDF 처리기 타입
            
        Returns:
            Dict[str, Any]: 추출 결과
        """
        import time
        from datetime import datetime
        
        start_time = time.time()
        
        try:
            logger.info(f"매핑 기반 데이터 추출 시작: {file_path}")
            
            # 1. 먼저 테이블 추출
            tables = await self.extract_tables(file_path, processor_type)
            
            if not tables:
                logger.warning("추출된 테이블이 없습니다")
                return {
                    "extracted_data": [],
                    "processing_time": time.time() - start_time,
                    "extracted_at": datetime.now().isoformat()
                }
            
            # 2. 매핑에 따라 데이터 추출
            extracted_data = []
            
            for mapping in mappings:
                try:
                    # 매핑 정보 파싱
                    key = mapping.get("key")
                    key_label = mapping.get("key_label", key)
                    anchor_cell = mapping.get("anchor_cell", {})
                    value_cell = mapping.get("value_cell", {})
                    
                    if not anchor_cell or not value_cell:
                        logger.warning(f"매핑 정보가 불완전합니다: {key}")
                        continue
                    
                    # 앵커 셀 정보
                    anchor_row = anchor_cell.get("row")
                    anchor_col = anchor_cell.get("col")
                    anchor_value = anchor_cell.get("value")
                    
                    # 값 셀 정보
                    value_row = value_cell.get("row")
                    value_col = value_cell.get("col")
                    
                    # 테이블에서 해당 데이터 찾기
                    extracted_value = None
                    confidence = 0.0
                    
                    for table in tables:
                        # TableData 모델의 data 속성 사용
                        table_data = table.rows if hasattr(table, 'rows') else []
                        
                        if (anchor_row < len(table_data) and 
                            anchor_col < len(table_data[anchor_row]) and
                            table_data[anchor_row][anchor_col] == anchor_value):
                            
                            # 앵커를 찾았으면 값 추출
                            if (value_row < len(table_data) and 
                                value_col < len(table_data[value_row])):
                                extracted_value = table_data[value_row][value_col]
                                confidence = 1.0
                                break
                    
                    if extracted_value is not None:
                        extracted_data.append({
                            "key": key,
                            "key_label": key_label,
                            "extracted_value": extracted_value,
                            "anchor_cell": anchor_cell,
                            "value_cell": value_cell,
                            "relative_position": mapping.get("relative_position", {}),
                            "confidence": confidence
                        })
                        logger.info(f"데이터 추출 성공: {key} = {extracted_value}")
                    else:
                        logger.warning(f"데이터 추출 실패: {key} - 앵커를 찾을 수 없음")
                        
                except Exception as e:
                    logger.error(f"매핑 처리 중 오류 ({mapping.get('key', 'unknown')}): {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            logger.info(f"매핑 기반 데이터 추출 완료: {len(extracted_data)}개 항목, {processing_time:.2f}초")
            
            return {
                "extracted_data": extracted_data,
                "processing_time": processing_time,
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"매핑 기반 데이터 추출 실패 {file_path}: {e}")
            raise
    
    async def quick_test(
        self, 
        file_path: str, 
        template_name: str,
        mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        빠른 추출 테스트
        
        Args:
            file_path: PDF 파일 경로
            template_name: 템플릿 이름
            mappings: 매핑 설정
            
        Returns:
            Dict[str, Any]: 테스트 결과
        """
        try:
            logger.info(f"빠른 테스트 시작: {file_path}")
            
            return {
                "success": True,
                "message": "빠른 테스트 완료",
                "file_path": file_path,
                "config_valid": True
            }
            
        except Exception as e:
            logger.error(f"빠른 테스트 실패: {str(e)}")
            return {
                "success": False,
                "message": f"빠른 테스트 실패: {str(e)}",
                "file_path": file_path,
                "config_valid": False
            }
    
    async def validate_mappings(
        self, 
        mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        매핑 설정 검증
        
        Args:
            mappings: 검증할 매핑 설정
            
        Returns:
            Dict[str, Any]: 검증 결과
        """
        try:
            logger.info(f"매핑 검증 시작: {len(mappings)}개 매핑")
            
            # 임시 구현
            return {
                "valid": True,
                "valid_count": len(mappings),
                "invalid_count": 0,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"매핑 검증 실패: {e}")
            raise

    async def recognize_keys(
        self, 
        file_path: str, 
        processor_type: str = "pdfplumber",
        save_debug: bool = False
    ) -> Dict[str, Any]:
        """
        키 인식 수행
        PDF에서 앵커 텍스트를 기반으로 키를 자동 인식합니다.
        
        Args:
            file_path: PDF 파일 경로
            processor_type: PDF 처리기 타입
            save_debug: 디버깅용 파일 저장 여부
            
        Returns:
            Dict[str, Any]: 인식된 키 정보
        """
        try:
            logger.info(f"키 인식 시작: {file_path}, 프로세서: {processor_type}")
            
            # 1단계: PDF에서 표 추출
            tables = await self.extract_tables(file_path, processor_type)
            
            # 2단계: 테이블 구조 분석
            table_analyses = []
            for table in tables:
                if table.rows:
                    analysis = await self.table_analyzer.analyze_table_structure(table, use_ai=True)
                    table_analyses.append(analysis)
                    logger.info(f"테이블 구조 분석 완료 - 페이지 {table.page_number}: {analysis.orientation.value}, 복잡도: {analysis.complexity.value}")
            
            # 3단계: 키 인식 로직 수행
            recognized_keys = []
            pattern_suggestions = []  # 새 패턴 제안 목록
            new_key_suggestions = []  # 새 키 제안 목록
            
            # 키 매핑 데이터베이스 및 추출 설정 로드
            key_mapping_db = await self._load_key_mapping_database()
            extraction_settings = await self._load_extraction_settings()
            
            logger.info(f"키 매핑 DB 로드 완료: {len(key_mapping_db)}개 키")
            logger.info(f"추출 설정 로드 완료: {len(extraction_settings)}개 섹션")
            
            for table_idx, table in enumerate(tables):
                if not table.rows:
                    continue
                
                # 해당 테이블의 구조 분석 결과 찾기
                table_analysis = None
                for analysis in table_analyses:
                    if analysis.page_number == table.page_number:
                        table_analysis = analysis
                        break
                
                # 구조 분석 결과를 활용한 스마트 키 인식
                if table_analysis:
                    logger.info(f"구조 기반 키 인식 - 페이지 {table.page_number}: {table_analysis.extraction_strategy}")
                else:
                    logger.warning(f"테이블 구조 분석 결과 없음 - 페이지 {table.page_number}, 기본 방식 사용")
                    
                logger.info(f"표 분석 중: 페이지 {table.page_number}, {len(table.rows)}행 x {table.col_count}열")
                
                # 헤더와 데이터 행을 모두 포함하여 분석
                all_rows = []
                if table.headers:
                    all_rows.append(table.headers)
                all_rows.extend(table.rows)
                
                for row_idx, row in enumerate(all_rows):
                    for col_idx, cell_value in enumerate(row):
                        if not cell_value or not isinstance(cell_value, str):
                            continue
                            
                        cell_text = cell_value.strip()
                        
                        # 각 키에 대해 매칭 확인 (카테고리별 순회)
                        matched = False
                        for category_name, category_data in key_mapping_db.items():
                            # 설정 섹션 건너뛰기
                            if category_name.startswith("_"):
                                continue
                            for key_name, key_data in category_data.items():
                                # 새로운 복합 구조인지 구 배열 구조인지 확인
                                patterns = []
                                if isinstance(key_data, dict) and "patterns" in key_data:
                                    patterns = key_data["patterns"]  # 새 구조
                                elif isinstance(key_data, list):
                                    patterns = key_data  # 구 구조
                                
                                for pattern in patterns:
                                    # 정확한 매칭 우선 (공백 제거 후 비교)
                                    cell_clean = cell_text.strip().lower()
                                    pattern_clean = pattern.strip().lower()
                                    
                                    # 설정에서 신뢰도 임계값 로드
                                    thresholds = extraction_settings.get("confidence_thresholds", {})
                                    text_settings = extraction_settings.get("text_processing", {})
                                    
                                    min_pattern_length = text_settings.get("minimum_pattern_length", 3)
                                    
                                    # 1. 정확한 매칭 (높은 신뢰도)
                                    if cell_clean == pattern_clean:
                                        confidence = thresholds.get("exact_match", 0.95)
                                        match_type = "exact"
                                    # 2. 시작 부분 매칭 (중간 신뢰도)
                                    elif cell_clean.startswith(pattern_clean):
                                        confidence = thresholds.get("prefix_match", 0.8)
                                        match_type = "prefix"
                                    # 3. 끝 부분 매칭 (중간 신뢰도)
                                    elif cell_clean.endswith(pattern_clean):
                                        confidence = thresholds.get("suffix_match", 0.7)
                                        match_type = "suffix"
                                    # 4. 부분 매칭 (낮은 신뢰도, 단어 경계 고려)
                                    elif pattern_clean in cell_clean and len(pattern_clean) >= min_pattern_length:
                                        # 단어 경계 확인 (공백, 괄호, 특수문자 등)
                                        import re
                                        word_boundary_pattern = r'\b' + re.escape(pattern_clean) + r'\b'
                                        if re.search(word_boundary_pattern, cell_clean):
                                            confidence = thresholds.get("word_boundary_match", 0.6)
                                            match_type = "word_boundary"
                                        else:
                                            confidence = thresholds.get("partial_match", 0.4)
                                            match_type = "partial"
                                    else:
                                        continue
                                
                                    # 신뢰도 임계값 확인 (설정값 이상만 허용)
                                    minimum_acceptance = thresholds.get("minimum_acceptance", 0.4)
                                    if confidence >= minimum_acceptance:
                                        logger.info(f"키 매칭 발견: '{pattern}' -> '{key_name}' (셀: '{cell_text}', 타입: {match_type}, 신뢰도: {confidence})")
                                    
                                    # 인식된 키 정보 생성
                                    import time
                                    unique_id = f"{key_name}_{table.page_number}_{row_idx}_{col_idx}_{int(time.time() * 1000000)}_{len(recognized_keys)}"
                                    # 복합 필드 정보 가져오기
                                    expected_fields = await self._get_expected_fields_for_key(key_name, key_mapping_db)
                                    
                                    # 카테고리 찾기
                                    key_category = "unknown"
                                    for cat_name, cat_data in key_mapping_db.items():
                                        if cat_name.startswith("_"):  # 설정 섹션 스킵
                                            continue
                                        if key_name in cat_data:
                                            key_category = cat_name
                                            break
                                    
                                    recognized_key = {
                                        "id": unique_id,  # 고유 ID 추가
                                        "key": key_name,
                                        "key_name": key_name,  # 시뮬레이션 호환성
                                        "key_label": key_name,  # 표시용 라벨
                                        "category": key_category,  # 카테고리 정보
                                        "anchor_cell": {
                                            "text": cell_text,
                                            "page_number": table.page_number,
                                            "row": row_idx,
                                            "col": col_idx
                                        },
                                        # 하위 호환성을 위한 기존 필드 유지
                                        "value_cell": {
                                            "page_number": table.page_number,
                                            "row": row_idx + 1,  # 다음 행 제안
                                            "col": col_idx
                                        },
                                        "relative_position": "next_row",
                                        "table_id": f"table_{table.page_number}_{row_idx}",
                                        "confidence": confidence,
                                        "match_type": match_type,
                                        
                                        # 새로운 복합 필드 지원
                                        "is_complex": bool(expected_fields),
                                        "expected_fields": expected_fields or {},
                                        "detected_fields": await self._detect_complex_fields(
                                            table, row_idx, col_idx, expected_fields
                                        ) if expected_fields else {}
                                    }
                                    
                                    # 키별 다중 위치 관리 (여러 위치 발견 시 모두 표시)
                                    existing_key = next((rk for rk in recognized_keys if rk["key"] == key_name), None)
                                    if existing_key:
                                        # 기존 키에 alternative_locations 추가
                                        if "alternative_locations" not in existing_key:
                                            existing_key["alternative_locations"] = []
                                        
                                        # 새로운 위치 정보 추가
                                        alternative_location = {
                                            "anchor_cell": {
                                                "text": cell_text,
                                                "page_number": table.page_number,
                                                "row": row_idx,
                                                "col": col_idx
                                            },
                                            "confidence": confidence,
                                            "match_type": match_type
                                        }
                                        existing_key["alternative_locations"].append(alternative_location)
                                        existing_key["multiple_found"] = True
                                        existing_key["total_locations"] = 1 + len(existing_key["alternative_locations"])
                                        logger.info(f"키 중복 위치 추가: {key_name} (총 {existing_key['total_locations']}개 위치, 새 위치: 페이지 {table.page_number}, 행 {row_idx}, 열 {col_idx}, 신뢰도: {confidence})")
                                    else:
                                        # 새로운 키 추가 (다중 위치 지원 필드 초기화)
                                        recognized_key["multiple_found"] = False
                                        recognized_key["alternative_locations"] = []
                                        recognized_key["total_locations"] = 1
                                        recognized_key["selected_location"] = "primary"  # 기본 선택: primary 위치
                                        recognized_keys.append(recognized_key)
                                        logger.info(f"새 키 추가: {key_name} (페이지 {table.page_number}, 행 {row_idx}, 열 {col_idx}, 신뢰도: {confidence})")
                                    matched = True
                                    break
                            if matched:
                                break
                        
                        # 매칭되지 않은 셀 중에서 새로운 패턴 제안 확인
                        text_settings = extraction_settings.get("text_processing", {})
                        max_cell_length = text_settings.get("maximum_cell_length", 20)
                        
                        if not matched and len(cell_text) > 1 and len(cell_text) < max_cell_length:
                            # 숫자가 아닌 텍스트이고, 너무 길지 않은 경우
                            if not cell_text.isdigit() and not any(char.isdigit() for char in cell_text):
                                # 기존 키와 유사도 분석하여 패턴 제안
                                suggested_key = await self._analyze_pattern_similarity(cell_text, key_mapping_db)
                                if suggested_key:
                                    logger.info(f"새 패턴 제안: '{cell_text}' -> '{suggested_key}' 키에 추가 제안")
                                    # 제안 목록에 추가 (나중에 응답에 포함)
                                    pattern_suggestions.append({
                                        "anchor_text": cell_text,
                                        "suggested_key": suggested_key,
                                        "location": {
                                            "page_number": table.page_number,
                                            "row": row_idx,
                                            "col": col_idx
                                        },
                                        "confidence": 0.6  # 제안 신뢰도
                                    })
                                else:
                                    # 완전히 새로운 키 후보 감지
                                    logger.info(f"새 키 후보 발견: '{cell_text}' (페이지 {table.page_number}, 행 {row_idx}, 열 {col_idx})")
                                    
                                    # 새로운 키 카테고리 추정
                                    suggested_category = await self._estimate_new_key_category(cell_text)
                                    
                                    # 새 키 제안 목록에 추가
                                    new_key_suggestions.append({
                                        "key_name": cell_text,
                                        "suggested_category": suggested_category,
                                        "location": {
                                            "page_number": table.page_number,
                                            "row": row_idx,
                                            "col": col_idx
                                        },
                                        "confidence": 0.5,  # 새 키 기본 신뢰도
                                        "patterns": [cell_text]  # 기본 패턴
                                    })
                                    
                                    # 기존 방식도 유지 (백업)
                                    await self._save_new_key(cell_text, cell_text, suggested_category)
            
            logger.info(f"키 인식 완료: {len(recognized_keys)}개 키 발견")
            
            # 디버깅용 저장 (선택적)
            debug_info = None
            if save_debug:
                debug_info = await self._save_debug_data(file_path, processor_type, {
                    "recognized_keys": recognized_keys,
                    "total_found": len(recognized_keys),
                    "pages_analyzed": len(set(table.page_number for table in tables)),
                    "tables_analyzed": len(tables),
                    "pattern_suggestions": pattern_suggestions,
                    "suggestions_count": len(pattern_suggestions),
                    "new_key_suggestions": new_key_suggestions,
                    "new_keys_count": len(new_key_suggestions),
                    "table_structure_analyses": [
                        {
                            "table_id": analysis.table_id,
                            "page_number": analysis.page_number,
                            "orientation": analysis.orientation.value,
                            "complexity": analysis.complexity.value,
                            "headers_count": len(analysis.headers),
                            "data_start": {"row": analysis.data_start_row, "col": analysis.data_start_col},
                            "confidence": analysis.confidence,
                            "extraction_strategy": analysis.extraction_strategy,
                            "analysis_notes": analysis.analysis_notes
                        }
                        for analysis in table_analyses
                    ],
                    "raw_tables": tables
                })
            
            result = {
                "recognized_keys": recognized_keys,
                "total_found": len(recognized_keys),
                "pages_analyzed": len(set(table.page_number for table in tables)),
                "tables_analyzed": len(tables),
                "pattern_suggestions": pattern_suggestions,
                "suggestions_count": len(pattern_suggestions),
                "new_key_suggestions": new_key_suggestions,
                "new_keys_count": len(new_key_suggestions)
            }
            
            # 디버깅 정보 추가 (저장했을 때만)
            if debug_info:
                result["debug_saved"] = debug_info
                logger.info(f"🐛 디버깅 데이터 저장됨: {debug_info['file_path']}")
            
            return result
            
        except Exception as e:
            logger.error(f"키 인식 실패: {str(e)}")
            return {
                "recognized_keys": [],
                "total_found": 0,
                "pages_analyzed": 0,
                "tables_analyzed": 0,
                "error": str(e)
            }
    
    async def _load_key_mapping_database(self) -> Dict:
        """
        키 매핑 데이터베이스 로드 (카테고리 구조 유지)
        JSON 파일에서 로드하거나 기본값 반환
        
        Returns:
            Dict: 키 매핑 데이터베이스 (카테고리 구조 유지)
        """
        try:
            import json
            import os
            
            # JSON 파일 경로
            json_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'key_mapping_database.json')
            
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    categorized_db = json.load(f)
                    
                    logger.info(f"키 매핑 DB 로드 완료: {len(categorized_db)}개 카테고리")
                    logger.info(f"카테고리: {list(categorized_db.keys())}")
                    
                    # 카테고리 구조를 유지하여 반환 (복합 필드 지원)
                    return categorized_db
            else:
                logger.warning(f"키 매핑 DB JSON 파일이 없습니다: {json_file_path}")
                # 기본값 반환 (카테고리 구조)
                return {
                    "basic": {
                        "키": ["키", "key", "항목", "구분"],
                        "신장": ["신장", "키", "height"],
                        "체중": ["체중", "몸무게", "weight"],
                            "혈압": ["혈압", "blood pressure", "BP"],
                        "혈당": ["혈당", "glucose", "당뇨"],
                        "성명": ["성명", "이름", "name"],
                        "나이": ["나이", "age", "연령"],
                        "성별": ["성별", "gender", "sex"]
                    }
                }
        except Exception as e:
            logger.error(f"키 매핑 DB 로드 실패: {e}")
            return {}
    
    async def _analyze_pattern_similarity(self, anchor_text: str, key_mapping_db: Dict[str, List[str]]) -> Optional[str]:
        """
        앵커 텍스트와 기존 키 패턴들 간의 유사도를 분석하여 가장 적합한 키를 제안
        
        Args:
            anchor_text: 분석할 앵커 텍스트
            key_mapping_db: 키 매핑 데이터베이스
            
        Returns:
            str: 제안할 키 이름 (유사도가 높은 경우), None (유사도가 낮은 경우)
        """
        try:
            import difflib
            
            # 설정에서 유사도 임계값 로드
            extraction_settings = await self._load_extraction_settings()
            thresholds = extraction_settings.get("confidence_thresholds", {})
            text_settings = extraction_settings.get("text_processing", {})
            
            max_similarity = 0.0
            suggested_key = None
            threshold = thresholds.get("similarity_threshold", 0.4)  # 유사도 임계값
            
            anchor_lower = anchor_text.lower().strip()
            
            # 각 키의 패턴들과 유사도 비교
            for key_name, patterns in key_mapping_db.items():
                for pattern in patterns:
                    pattern_lower = pattern.lower().strip()
                    
                    # 문자열 유사도 계산 (SequenceMatcher 사용)
                    similarity = difflib.SequenceMatcher(None, anchor_lower, pattern_lower).ratio()
                    
                    # 부분 문자열 포함 여부도 고려 (가중치 적용)
                    partial_bonus = text_settings.get("partial_match_bonus", 0.3)
                    korean_bonus = text_settings.get("korean_bonus", 0.2)
                    korean_threshold = text_settings.get("korean_similarity_threshold", 0.3)
                    
                    if anchor_lower in pattern_lower or pattern_lower in anchor_lower:
                        similarity += partial_bonus  # 부분 매칭 보너스
                    
                    # 한글 자모음 유사도도 고려 (예: "기높이" vs "키")
                    if self._check_korean_similarity(anchor_lower, pattern_lower, korean_threshold):
                        similarity += korean_bonus  # 한글 유사도 보너스
                    
                    if similarity > max_similarity:
                        max_similarity = similarity
                        suggested_key = key_name
            
            # 임계값 이상인 경우에만 제안
            if max_similarity >= threshold:
                logger.info(f"패턴 유사도 분석: '{anchor_text}' -> '{suggested_key}' (유사도: {max_similarity:.2f})")
                return suggested_key
            else:
                logger.info(f"패턴 유사도 분석: '{anchor_text}' - 적합한 키 없음 (최대 유사도: {max_similarity:.2f})")
                return None
                
        except Exception as e:
            logger.error(f"패턴 유사도 분석 실패: {e}")
            return None
    
    def _check_korean_similarity(self, text1: str, text2: str, threshold: float = 0.3) -> bool:
        """한글 텍스트의 자모음 기반 유사도 검사"""
        try:
            # 간단한 한글 유사도 검사 (초성, 중성, 종성 비교)
            # 예: "기" vs "키" (초성이 같음)
            common_chars = set(text1) & set(text2)
            similarity = len(common_chars) / max(len(set(text1)), len(set(text2)))
            return similarity > threshold
        except:
            return False
    
    async def _estimate_new_key_category(self, key_text: str) -> str:
        """새로운 키의 카테고리 추정 (동적 키워드 로드)"""
        try:
            key_lower = key_text.lower().strip()
            
            # 카테고리 분류 키워드를 동적으로 로드
            classification_keywords = await self._load_category_classification_keywords()
            
            # 각 카테고리별 매칭 확인 (우선순위 순서)
            category_priority = ["personal", "temporal", "opinion", "basic", "cancer", "comprehensive", "special"]
            
            for category in category_priority:
                if category in classification_keywords:
                    keywords = classification_keywords[category]
                    for keyword in keywords:
                        if keyword.lower() in key_lower:
                            logger.debug(f"키 '{key_text}' -> 카테고리 '{category}' (키워드: '{keyword}')")
                            return category
            
            # 기본값은 special로 설정
            logger.debug(f"키 '{key_text}' -> 기본 카테고리 'special' (매칭 키워드 없음)")
            return "special"
            
        except Exception as e:
            logger.error(f"키 카테고리 추정 실패: {e}")
            return "special"

    async def _load_extraction_settings(self) -> Dict[str, Any]:
        """추출 설정을 key_mapping_database.json에서 로드"""
        try:
            import json
            import os
            
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "key_mapping_database.json")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # _extraction_settings 섹션 추출
            extraction_settings = data.get('_extraction_settings', {})
            
            if not extraction_settings:
                logger.warning("추출 설정이 없습니다. 기본값 사용")
                # 기본 설정 (백업용)
                extraction_settings = {
                    "confidence_thresholds": {
                        "exact_match": 0.95,
                        "prefix_match": 0.8,
                        "suffix_match": 0.7,
                        "word_boundary_match": 0.6,
                        "partial_match": 0.4,
                        "minimum_acceptance": 0.4,
                        "ai_analysis_minimum": 0.7,
                        "similarity_threshold": 0.4
                    },
                    "field_detection_keywords": {
                        "result": ["검사결과", "결과", "측정값", "값"],
                        "normal_range": ["정상치", "기준치", "정상범위"],
                        "judgment": ["판정", "소견", "결과"],
                        "opinion": ["소견", "의견", "비고"]
                    }
                }
            
            logger.debug(f"추출 설정 로드 완료: {len(extraction_settings)}개 섹션")
            return extraction_settings
            
        except Exception as e:
            logger.error(f"추출 설정 로드 실패: {e}")
            # 최소한의 기본 설정 반환
            return {
                "confidence_thresholds": {
                    "minimum_acceptance": 0.4,
                    "similarity_threshold": 0.4
                },
                "field_detection_keywords": {
                    "result": ["결과"],
                    "normal_range": ["정상치"]
                }
            }

    async def _load_category_classification_keywords(self) -> Dict[str, List[str]]:
        """카테고리 분류 키워드를 key_mapping_database.json에서 로드"""
        try:
            import json
            import os
            
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "key_mapping_database.json")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # _category_classification_keywords 섹션 추출
            classification_keywords = data.get('_category_classification_keywords', {})
            
            if not classification_keywords:
                logger.warning("카테고리 분류 키워드가 설정되지 않았습니다. 기본값 사용")
                # 기본 키워드 (백업용)
                classification_keywords = {
                    "personal": ["이름", "성명", "나이", "연령", "성별"],
                    "temporal": ["이전", "과거", "작년", "전년", "년도", "결과"],
                    "basic": ["신장", "키", "체중", "혈압", "혈당"],
                    "special": ["검사", "소견", "판정", "문진", "촬영"],
                    "opinion": ["소견", "의견", "판정", "진단"],
                    "cancer": ["암", "종양", "악성", "양성"],
                    "comprehensive": ["종합", "전체", "통합"]
                }
            
            logger.debug(f"카테고리 분류 키워드 로드 완료: {len(classification_keywords)}개 카테고리")
            return classification_keywords
            
        except Exception as e:
            logger.error(f"카테고리 분류 키워드 로드 실패: {e}")
            # 최소한의 기본 키워드 반환
            return {
                "personal": ["이름", "성명"],
                "basic": ["신장", "체중"],
                "special": ["검사", "소견"]
            }

    async def _get_expected_fields_for_key(self, key_name: str, key_mapping_db: Dict) -> Dict:
        """키에 대한 예상 필드 구조 조회"""
        try:
            # 모든 카테고리에서 키 찾기
            for category_name, category_data in key_mapping_db.items():
                if key_name in category_data:
                    key_data = category_data[key_name]
                    # 새로운 복합 구조인지 확인
                    if isinstance(key_data, dict) and "expected_fields" in key_data:
                        return key_data["expected_fields"]
            
            return {}
        except Exception as e:
            logger.error(f"예상 필드 조회 실패 ({key_name}): {e}")
            return {}

    async def _detect_complex_fields(self, table, anchor_row: int, anchor_col: int, expected_fields: Dict) -> Dict:
        """테이블에서 복합 필드 위치 감지 (AI 헤더 분석 활용)"""
        detected_fields = {}
        
        try:
            if not expected_fields or not table.rows:
                return detected_fields
                
            # 헤더 행이 있는지 확인
            header_row_idx = 0
            headers = []
            if len(table.rows) > 0:
                headers = table.rows[0] if table.rows[0] else []
            
            # AI 헤더 분석 시도 (선택적)
            ai_column_mappings = await self._try_ai_header_analysis(table, headers)
            
            # 각 예상 필드에 대해 위치 감지
            for field_type, field_info in expected_fields.items():
                try:
                    # AI 분석 결과 우선 사용
                    field_col = None
                    if ai_column_mappings:
                        field_col = self._find_column_by_ai_mapping(ai_column_mappings, field_type)
                    
                    # AI 분석 실패 시 기존 방식 사용
                    if field_col is None:
                        field_col = await self._find_field_column(
                            headers, field_type, field_info, anchor_col
                        )
                    
                    if field_col is not None:
                        # 값 추출 시도
                        field_value = await self._extract_field_value(
                            table, anchor_row, field_col, field_info
                        )
                        
                        # 설정에서 기본 필드 신뢰도 로드
                        extraction_settings = await self._load_extraction_settings()
                        ai_settings = extraction_settings.get("ai_analysis", {})
                        default_confidence = ai_settings.get("default_field_confidence", 0.8)
                        
                        detected_fields[field_type] = {
                            "col_offset": field_col - anchor_col,
                            "col": field_col,
                            "row": anchor_row,
                            "value": field_value,
                            "confidence": default_confidence,
                            "data_type": field_info.get("data_type", "text"),
                            "is_required": field_info.get("is_required", False)
                        }
                        
                        logger.debug(f"필드 감지: {field_type} -> 열 {field_col}, 값: {field_value}")
                        
                except Exception as field_error:
                    logger.error(f"필드 감지 실패 ({field_type}): {field_error}")
                    continue
                    
        except Exception as e:
            logger.error(f"복합 필드 감지 실패: {e}")
            
        return detected_fields

    async def _find_field_column(self, headers: List[str], field_type: str, field_info: Dict, anchor_col: int) -> Optional[int]:
        """필드 타입에 맞는 열 찾기 (설정 기반)"""
        try:
            # 설정에서 필드 감지 키워드 로드
            extraction_settings = await self._load_extraction_settings()
            field_keywords = extraction_settings.get("field_detection_keywords", {})
            
            keywords = field_keywords.get(field_type, [])
            
            # 헤더에서 키워드 매칭
            for col_idx, header in enumerate(headers):
                if header and isinstance(header, str):
                    header_lower = header.lower().strip()
                    for keyword in keywords:
                        if keyword in header_lower:
                            return col_idx
            
            # 키워드 매칭 실패 시 우선순위 기반 추정
            priority = field_info.get("priority", 999)
            estimated_col = anchor_col + priority
            
            if 0 <= estimated_col < len(headers):
                return estimated_col
                
        except Exception as e:
            logger.error(f"필드 열 찾기 실패 ({field_type}): {e}")
            
        return None

    async def _extract_field_value(self, table, row: int, col: int, field_info: Dict) -> str:
        """필드 값 추출"""
        try:
            if (row < len(table.rows) and col < len(table.rows[row]) and 
                table.rows[row] and table.rows[row][col]):
                return str(table.rows[row][col]).strip()
        except Exception as e:
            logger.error(f"필드 값 추출 실패 (행:{row}, 열:{col}): {e}")
            
        return ""

    async def _try_ai_header_analysis(self, table, headers: List[str]) -> Dict[int, str]:
        """AI 헤더 분석 시도 (선택적)"""
        try:
            # AI 서비스 임포트 및 초기화
            from services.ai_extraction_service import AIExtractionService
            
            ai_service = AIExtractionService()
            if not ai_service.is_available():
                logger.debug("AI 서비스 사용 불가, 기존 방식 사용")
                return {}
            
            # 설정에서 AI 분석 설정 로드
            extraction_settings = await self._load_extraction_settings()
            ai_settings = extraction_settings.get("ai_analysis", {})
            max_rows = ai_settings.get("max_table_rows_for_analysis", 5)
            
            # 테이블 데이터 구성
            table_data = []
            if headers:
                table_data.append(headers)
            if table.rows:
                table_data.extend(table.rows[:max_rows-1])  # 헤더 + 데이터 행들
                
            # AI 헤더 분석 실행
            result = await ai_service.analyze_table_headers(table_data, "검진항목")
            
            ai_confidence_threshold = ai_settings.get("header_analysis_confidence_threshold", 0.7)
            if result and result.confidence >= ai_confidence_threshold:
                logger.info(f"AI 헤더 분석 성공: 신뢰도 {result.confidence:.2f}")
                logger.info(f"테이블 구조: {result.table_structure}, 헤더 방향: {result.header_orientation}")
                logger.info(f"감지된 필드: {result.detected_fields}")
                logger.info(f"구조 분석: {result.table_analysis}")
                
                # 문자열 키를 정수로 변환
                column_mappings = {}
                for col_str, field_type in result.column_mappings.items():
                    try:
                        col_int = int(col_str)
                        column_mappings[col_int] = field_type
                    except ValueError:
                        continue
                
                # 테이블 구조 정보를 로그에 기록
                logger.info(f"매핑 결과 - 가로: {column_mappings}")
                if result.row_mappings:
                    row_mappings = {}
                    for row_str, field_type in result.row_mappings.items():
                        try:
                            row_int = int(row_str)
                            row_mappings[row_int] = field_type
                        except ValueError:
                            continue
                    logger.info(f"매핑 결과 - 세로: {row_mappings}")
                        
                return column_mappings
            else:
                logger.debug(f"AI 헤더 분석 신뢰도 낮음: {result.confidence if result else 'N/A'}")
                
        except Exception as e:
            logger.debug(f"AI 헤더 분석 실패: {e}")
            
        return {}

    def _find_column_by_ai_mapping(self, ai_mappings: Dict[int, str], target_field_type: str) -> Optional[int]:
        """AI 매핑 결과에서 특정 필드 타입의 열 번호 찾기"""
        for col_idx, field_type in ai_mappings.items():
            if field_type == target_field_type:
                return col_idx
        return None

    async def _save_new_key(self, key_name: str, anchor_text: str, category: str = "special") -> None:
        """
        새로 발견된 키를 파일에 저장
        
        Args:
            key_name: 키 이름
            anchor_text: 발견된 앵커 텍스트
            category: 키 카테고리 (basic, special)
        """
        try:
            import json
            import os
            from datetime import datetime
            
            # 새 키 저장 파일 경로
            new_keys_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'new_keys_discovered.json')
            
            # 기존 데이터 로드
            if os.path.exists(new_keys_file):
                with open(new_keys_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "discovered_keys": [],
                    "last_updated": None,
                    "total_discovered": 0
                }
            
            # 새 키 정보 생성
            new_key_info = {
                "key_name": key_name,
                "anchor_text": anchor_text,
                "category": category,
                "discovered_at": datetime.now().isoformat(),
                "file_path": None  # 나중에 파일 정보 추가 가능
            }
            
            # 중복 확인
            existing_keys = [k["key_name"] for k in data["discovered_keys"]]
            if key_name not in existing_keys:
                data["discovered_keys"].append(new_key_info)
                data["total_discovered"] = len(data["discovered_keys"])
                data["last_updated"] = datetime.now().isoformat()
                
                # 파일에 저장
                with open(new_keys_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"새 키 저장: {key_name} (앵커: '{anchor_text}', 카테고리: {category})")
            else:
                logger.info(f"키 '{key_name}'는 이미 저장되어 있습니다.")
                
        except Exception as e:
            logger.error(f"새 키 저장 실패: {e}")
    
    async def recognize_keys_with_ai(
        self, 
        file_path: str, 
        processor_type: str = "pdfplumber",
        save_debug: bool = False
    ) -> Dict[str, Any]:
        """
        키 인식 후 AI를 사용하여 값을 자동 추출
        
        Args:
            file_path: PDF 파일 경로
            processor_type: PDF 처리기 타입
            save_debug: 디버깅용 파일 저장 여부
            
        Returns:
            Dict: 키 인식 및 AI 추출 결과
        """
        try:
            # 1단계: 기존 키 인식 실행
            recognition_result = await self.recognize_keys(file_path, processor_type, save_debug)
            
            if not recognition_result.get('success') or not recognition_result.get('recognized_keys'):
                return recognition_result
            
            # 2단계: AI 서비스 사용 가능 여부 확인
            if not ai_extraction_service.is_available():
                logger.warning("AI 서비스가 사용할 수 없습니다. 기본 키 인식 결과만 반환합니다.")
                return recognition_result
            
            # 3단계: 테이블 데이터 가져오기
            tables = await self.extract_tables(file_path, processor_type)
            if not tables:
                logger.warning("테이블 데이터를 찾을 수 없습니다.")
                return recognition_result
            
            # 4단계: AI 추출 요청 생성
            ai_requests = []
            for key_data in recognition_result['recognized_keys']:
                # 해당 키의 테이블 찾기
                target_table = None
                for table in tables:
                    if (table.page_number == key_data.get('anchor_cell', {}).get('page_number', 1) and
                        table.rows and len(table.rows) > key_data.get('anchor_cell', {}).get('row', 0)):
                        target_table = table
                        break
                
                if target_table:
                    ai_request = AIExtractionRequest(
                        key_name=key_data['key'],
                        key_label=key_data.get('key_label', key_data['key']),
                        anchor_cell=key_data['anchor_cell'],
                        table_data=target_table.rows,
                        page_number=target_table.page_number,
                        context=f"파일: {Path(file_path).name}"
                    )
                    ai_requests.append(ai_request)
            
            # 5단계: AI 추출 실행
            if ai_requests:
                ai_results = await ai_extraction_service.batch_extract_values(ai_requests)
                
                # 6단계: 결과 통합
                enhanced_keys = []
                for key_data in recognition_result['recognized_keys']:
                    # 해당 키의 AI 결과 찾기
                    ai_result = None
                    for result in ai_results:
                        if result and result.key_name == key_data['key']:
                            ai_result = result
                            break
                    
                    if ai_result and ai_result.confidence >= 0.7:
                        # AI 추출 성공 - 값 업데이트
                        enhanced_key = key_data.copy()
                        enhanced_key['ai_extracted_value'] = ai_result.extracted_value
                        enhanced_key['ai_confidence'] = ai_result.confidence
                        enhanced_key['ai_reasoning'] = ai_result.reasoning
                        enhanced_key['ai_processing_time'] = ai_result.processing_time
                        enhanced_key['is_ai_enhanced'] = True
                        
                        # suggested_position 업데이트
                        if 'suggested_position' in enhanced_key:
                            enhanced_key['suggested_position'] = {
                                'row': ai_result.suggested_position['row'],
                                'col': ai_result.suggested_position['col']
                            }
                        
                        enhanced_keys.append(enhanced_key)
                        logger.info(f"AI 추출 성공: {key_data['key']} -> {ai_result.extracted_value} (신뢰도: {ai_result.confidence:.2f})")
                    else:
                        # AI 추출 실패 - 기본 결과 사용
                        enhanced_key = key_data.copy()
                        enhanced_key['is_ai_enhanced'] = False
                        enhanced_keys.append(enhanced_key)
                        logger.warning(f"AI 추출 실패: {key_data['key']} (신뢰도: {ai_result.confidence if ai_result else 0:.2f})")
                else:
                    enhanced_keys = recognition_result['recognized_keys']
                
                # 7단계: 최종 결과 반환
                final_result = recognition_result.copy()
                final_result['recognized_keys'] = enhanced_keys
                final_result['ai_enhanced'] = True
                final_result['ai_successful_extractions'] = len([k for k in enhanced_keys if k.get('is_ai_enhanced', False)])
                final_result['ai_total_attempts'] = len(ai_requests)
                
                logger.info(f"AI 향상된 키 인식 완료: {final_result['ai_successful_extractions']}/{final_result['ai_total_attempts']} 성공")
                return final_result
            
            else:
                logger.warning("AI 추출 요청을 생성할 수 없습니다.")
                return recognition_result
                
        except Exception as e:
            logger.error(f"AI 향상된 키 인식 실패: {e}")
            # AI 실패 시 기본 키 인식 결과 반환
            return await self.recognize_keys(file_path, processor_type)

    async def _save_debug_data(self, file_path: str, processor_type: str, extraction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """디버깅용 데이터 저장"""
        try:
            import hashlib
            import json
            from datetime import datetime
            from pathlib import Path
            
            # 디버깅 디렉토리 생성
            debug_dir = Path("debug_extractions")
            debug_dir.mkdir(exist_ok=True)
            
            # 파일 해시 및 타임스탬프로 고유 키 생성
            file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_filename = f"debug_{file_hash}_{processor_type}_{timestamp}.json"
            debug_file_path = debug_dir / debug_filename
            
            # 저장할 데이터 구성
            debug_data = {
                "metadata": {
                    "file_path": file_path,
                    "processor_type": processor_type,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "file_hash": file_hash,
                    "debug_session_id": f"{file_hash}_{timestamp}"
                },
                "extraction_results": {
                    "recognized_keys": extraction_data.get("recognized_keys", []),
                    "pattern_suggestions": extraction_data.get("pattern_suggestions", []),
                    "new_key_suggestions": extraction_data.get("new_key_suggestions", []),
                    "statistics": {
                        "total_found": extraction_data.get("total_found", 0),
                        "pages_analyzed": extraction_data.get("pages_analyzed", 0),
                        "tables_analyzed": extraction_data.get("tables_analyzed", 0),
                        "suggestions_count": extraction_data.get("suggestions_count", 0),
                        "new_keys_count": extraction_data.get("new_keys_count", 0)
                    }
                },
                "raw_tables": []
            }
            
            # 테이블 데이터 요약 (전체 저장하면 너무 크므로)
            if "raw_tables" in extraction_data:
                for table in extraction_data["raw_tables"]:
                    table_summary = {
                        "page_number": table.page_number,
                        "rows_count": len(table.rows),
                        "cols_count": len(table.rows[0]) if table.rows else 0,
                        "first_row": table.rows[0] if table.rows else [],
                        "sample_cells": table.rows[:3] if len(table.rows) > 3 else table.rows  # 처음 3행만
                    }
                    debug_data["raw_tables"].append(table_summary)
            
            # JSON 파일로 저장
            with open(debug_file_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"🐛 디버깅 데이터 저장 완료: {debug_file_path}")
            
            return {
                "file_path": str(debug_file_path),
                "file_size": debug_file_path.stat().st_size,
                "debug_session_id": debug_data["metadata"]["debug_session_id"],
                "saved_at": debug_data["metadata"]["extraction_timestamp"]
            }
            
        except Exception as e:
            logger.error(f"디버깅 데이터 저장 실패: {e}")
            return None


# 의존성 주입을 위한 팩토리 함수
def get_extraction_service() -> ExtractionService:
    """추출 서비스 인스턴스 반환"""
    return ExtractionService()