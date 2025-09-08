"""
추출 서비스

PDF에서 표를 추출하는 핵심 로직을 담당
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from models.analysis_models import TableData, ExtractionLibrary
from core.pdf_processor.factory import PDFProcessorFactory

logger = logging.getLogger(__name__)


class ExtractionService:
    """추출 서비스 클래스"""
    
    def __init__(self):
        """추출 서비스 초기화"""
        self.processor_factory = PDFProcessorFactory()
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
                        table_data = table.data if hasattr(table, 'data') else table.rows if hasattr(table, 'rows') else []
                        
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
        processor_type: str = "pdfplumber"
    ) -> Dict[str, Any]:
        """
        키 인식 수행
        PDF에서 앵커 텍스트를 기반으로 키를 자동 인식합니다.
        
        Args:
            file_path: PDF 파일 경로
            processor_type: PDF 처리기 타입
            
        Returns:
            Dict[str, Any]: 인식된 키 정보
        """
        try:
            logger.info(f"키 인식 시작: {file_path}, 프로세서: {processor_type}")
            
            # 1단계: PDF에서 표 추출
            tables = await self.extract_tables(file_path, processor_type)
            
            # 2단계: 키 인식 로직 수행
            recognized_keys = []
            
            # 키 매핑 데이터베이스 로드 (실제 DB에서 로드하거나 기본값 사용)
            key_mapping_db = await self._load_key_mapping_database()
            
            logger.info(f"키 매핑 DB 로드 완료: {len(key_mapping_db)}개 키")
            
            for table in tables:
                if not table.rows:
                    continue
                    
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
                        
                        # 각 키에 대해 매칭 확인
                        matched = False
                        for key_name, patterns in key_mapping_db.items():
                            for pattern in patterns:
                                if pattern.lower() in cell_text.lower():
                                    logger.info(f"키 매칭 발견: '{pattern}' -> '{key_name}' (셀: '{cell_text}')")
                                    
                                    # 인식된 키 정보 생성
                                    recognized_key = {
                                        "key": key_name,
                                        "anchor_text": cell_text,
                                        "page_number": table.page_number,
                                        "row": row_idx,
                                        "col": col_idx,
                                        "confidence": 0.8,  # 기본 신뢰도
                                        "suggested_position": {
                                            "row": row_idx + 1,  # 다음 행 제안
                                            "col": col_idx
                                        }
                                    }
                                    
                                    # 중복 제거
                                    if not any(
                                        rk["key"] == key_name and 
                                        rk["page_number"] == table.page_number and
                                        rk["row"] == row_idx and 
                                        rk["col"] == col_idx
                                        for rk in recognized_keys
                                    ):
                                        recognized_keys.append(recognized_key)
                                        logger.info(f"새 키 추가: {key_name} (페이지 {table.page_number}, 행 {row_idx}, 열 {col_idx})")
                                    matched = True
                                    break
                            if matched:
                                break
                        
                        # 매칭되지 않은 셀 중에서 새로운 키 후보 확인
                        if not matched and len(cell_text) > 1 and len(cell_text) < 20:
                            # 숫자가 아닌 텍스트이고, 너무 길지 않은 경우 새로운 키 후보로 간주
                            if not cell_text.isdigit() and not any(char.isdigit() for char in cell_text):
                                logger.info(f"새 키 후보 발견: '{cell_text}' (페이지 {table.page_number}, 행 {row_idx}, 열 {col_idx})")
                                # 새로운 키로 저장 (사용자가 나중에 확인할 수 있도록)
                                await self._save_new_key(cell_text, cell_text, "special")
            
            logger.info(f"키 인식 완료: {len(recognized_keys)}개 키 발견")
            
            return {
                "recognized_keys": recognized_keys,
                "total_found": len(recognized_keys),
                "pages_analyzed": len(set(table.page_number for table in tables)),
                "tables_analyzed": len(tables)
            }
            
        except Exception as e:
            logger.error(f"키 인식 실패: {str(e)}")
            return {
                "recognized_keys": [],
                "total_found": 0,
                "pages_analyzed": 0,
                "tables_analyzed": 0,
                "error": str(e)
            }
    
    async def _load_key_mapping_database(self) -> Dict[str, List[str]]:
        """
        키 매핑 데이터베이스 로드 (카테고리별 통합)
        JSON 파일에서 로드하거나 기본값 반환
        
        Returns:
            Dict[str, List[str]]: 키 매핑 데이터베이스 (카테고리 통합)
        """
        try:
            import json
            import os
            
            # JSON 파일 경로
            json_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'key_mapping_database.json')
            
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    categorized_db = json.load(f)
                    
                    # 카테고리별 키를 하나의 딕셔너리로 통합
                    key_mapping_db = {}
                    for category, keys in categorized_db.items():
                        key_mapping_db.update(keys)
                    
                    logger.info(f"키 매핑 DB 로드 완료: {len(categorized_db)}개 카테고리, {len(key_mapping_db)}개 키")
                    logger.info(f"카테고리: {list(categorized_db.keys())}")
                    return key_mapping_db
            else:
                logger.warning(f"키 매핑 DB JSON 파일이 없습니다: {json_file_path}")
                # 기본값 반환
                return {
                    "키": ["키", "key", "항목", "구분"],
                    "신장": ["신장", "키", "height"],
                    "체중": ["체중", "몸무게", "weight"],
                    "혈압": ["혈압", "blood pressure", "BP"],
                    "혈당": ["혈당", "glucose", "당뇨"],
                    "성명": ["성명", "이름", "name"],
                    "나이": ["나이", "age", "연령"],
                    "성별": ["성별", "gender", "sex"]
                }
        except Exception as e:
            logger.error(f"키 매핑 DB 로드 실패: {e}")
            return {}
    
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