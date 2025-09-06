"""
관계 설정 서비스

앵커-값 기반 자동 데이터 추출을 위한 관계 설정 관리를 담당
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import asyncio
import aiofiles

from models.table_models import TableData, CellData
from storage.file_storage import FileStorage
from app.config import settings

logger = logging.getLogger(__name__)


class RelationshipService:
    """관계 설정 서비스 클래스"""
    
    def __init__(self, storage: FileStorage):
        """
        관계 설정 서비스 초기화
        
        Args:
            storage: 파일 저장소
        """
        self.storage = storage
        
        logger.info("관계 설정 서비스 초기화 완료")
    
    async def save_relationship(
        self,
        relationship_id: str,
        anchor_cell: CellData,
        value_cell: CellData,
        table_data: TableData,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        새로운 관계 설정 저장
        
        Args:
            relationship_id: 관계 설정 ID
            anchor_cell: 앵커 셀 (예: "신장")
            value_cell: 값 셀 (예: "181")
            table_data: 테이블 데이터
            description: 관계 설명
            
        Returns:
            Dict[str, Any]: 저장된 관계 정보
        """
        try:
            # 상대적 위치 계산
            relative_position = self._calculate_relative_position(anchor_cell, value_cell)
            
            # 관계 설정 데이터 구성
            relationship_data = {
                "id": relationship_id,
                "description": description or f"{anchor_cell.content} -> {value_cell.content}",
                "anchor": {
                    "content": anchor_cell.content,
                    "row": anchor_cell.row,
                    "col": anchor_cell.col,
                    "type": anchor_cell.type.value
                },
                "value": {
                    "content": value_cell.content,
                    "row": value_cell.row,
                    "col": value_cell.col,
                    "type": value_cell.type.value
                },
                "relative_position": relative_position,
                "table_context": {
                    "table_id": table_data.table_id,
                    "page_number": table_data.page_number,
                    "table_size": {
                        "rows": table_data.grid_data.rows,
                        "cols": table_data.grid_data.cols
                    }
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 파일에 저장
            await self.storage.save_relationship(relationship_id, relationship_data)
            
            logger.info(f"관계 설정 저장 완료: {relationship_id}")
            return relationship_data
            
        except Exception as e:
            logger.error(f"관계 설정 저장 실패: {e}")
            raise
    
    async def load_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        관계 설정 로드
        
        Args:
            relationship_id: 관계 설정 ID
            
        Returns:
            Optional[Dict[str, Any]]: 관계 설정 데이터
        """
        try:
            relationship_data = await self.storage.load_relationship(relationship_id)
            
            if relationship_data:
                logger.info(f"관계 설정 로드 완료: {relationship_id}")
            else:
                logger.warning(f"관계 설정을 찾을 수 없음: {relationship_id}")
            
            return relationship_data
            
        except Exception as e:
            logger.error(f"관계 설정 로드 실패: {e}")
            return None
    
    async def list_relationships(self) -> List[Dict[str, Any]]:
        """
        모든 관계 설정 목록 조회
        
        Returns:
            List[Dict[str, Any]]: 관계 설정 목록
        """
        try:
            relationships = await self.storage.list_relationships()
            
            # 최신 순으로 정렬
            relationships.sort(
                key=lambda x: x.get("updated_at", x.get("created_at", "")),
                reverse=True
            )
            
            logger.info(f"관계 설정 목록 조회 완료: {len(relationships)}개")
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
            success = await self.storage.delete_relationship(relationship_id)
            
            if success:
                logger.info(f"관계 설정 삭제 완료: {relationship_id}")
            else:
                logger.warning(f"관계 설정 삭제 실패: {relationship_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"관계 설정 삭제 실패: {e}")
            return False
    
    async def apply_relationships(
        self,
        table_data: TableData,
        relationship_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        테이블에 관계 설정 적용하여 데이터 추출
        
        Args:
            table_data: 대상 테이블 데이터
            relationship_ids: 적용할 관계 설정 ID 목록 (None이면 모든 관계 적용)
            
        Returns:
            Dict[str, Any]: 추출된 데이터
        """
        try:
            # 관계 설정 목록 가져오기
            if relationship_ids:
                relationships = []
                for rel_id in relationship_ids:
                    rel_data = await self.load_relationship(rel_id)
                    if rel_data:
                        relationships.append(rel_data)
            else:
                relationships = await self.list_relationships()
            
            extracted_data = {}
            
            # 각 관계 설정 적용
            for relationship in relationships:
                try:
                    result = await self._apply_single_relationship(table_data, relationship)
                    if result:
                        extracted_data[relationship["id"]] = result
                except Exception as e:
                    logger.warning(f"관계 적용 실패 {relationship['id']}: {e}")
                    continue
            
            logger.info(f"관계 설정 적용 완료: {len(extracted_data)}개 데이터 추출")
            return {
                "table_id": table_data.table_id,
                "extracted_data": extracted_data,
                "applied_relationships": len(extracted_data),
                "total_relationships": len(relationships),
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"관계 설정 적용 실패: {e}")
            return {
                "table_id": table_data.table_id,
                "extracted_data": {},
                "applied_relationships": 0,
                "total_relationships": 0,
                "error": str(e),
                "extracted_at": datetime.now().isoformat()
            }
    
    async def _apply_single_relationship(
        self,
        table_data: TableData,
        relationship: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        단일 관계 설정을 테이블에 적용
        
        Args:
            table_data: 테이블 데이터
            relationship: 관계 설정
            
        Returns:
            Optional[Dict[str, Any]]: 추출된 데이터
        """
        try:
            anchor_content = relationship["anchor"]["content"]
            relative_position = relationship["relative_position"]
            
            # 앵커 셀 찾기
            anchor_cells = self._find_cells_by_content(table_data, anchor_content)
            
            if not anchor_cells:
                logger.debug(f"앵커 셀을 찾을 수 없음: {anchor_content}")
                return None
            
            # 각 앵커 셀에 대해 값 셀 찾기
            extracted_values = []
            
            for anchor_cell in anchor_cells:
                value_cell = self._find_value_cell_by_position(
                    table_data, 
                    anchor_cell, 
                    relative_position
                )
                
                if value_cell:
                    extracted_values.append({
                        "anchor_cell": {
                            "content": anchor_cell.content,
                            "row": anchor_cell.row,
                            "col": anchor_cell.col
                        },
                        "value_cell": {
                            "content": value_cell.content,
                            "row": value_cell.row,
                            "col": value_cell.col
                        },
                        "confidence": self._calculate_extraction_confidence(
                            anchor_cell, value_cell, relationship
                        )
                    })
            
            if extracted_values:
                return {
                    "relationship_id": relationship["id"],
                    "description": relationship["description"],
                    "anchor_content": anchor_content,
                    "extracted_values": extracted_values,
                    "extraction_count": len(extracted_values)
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"관계 적용 실패: {e}")
            return None
    
    def _calculate_relative_position(
        self,
        anchor_cell: CellData,
        value_cell: CellData
    ) -> Dict[str, Any]:
        """
        앵커 셀과 값 셀 사이의 상대적 위치 계산
        
        Args:
            anchor_cell: 앵커 셀
            value_cell: 값 셀
            
        Returns:
            Dict[str, Any]: 상대적 위치 정보
        """
        row_diff = value_cell.row - anchor_cell.row
        col_diff = value_cell.col - anchor_cell.col
        
        # 방향 결정
        if row_diff == 0 and col_diff > 0:
            direction = "right"
        elif row_diff == 0 and col_diff < 0:
            direction = "left"
        elif row_diff > 0 and col_diff == 0:
            direction = "down"
        elif row_diff < 0 and col_diff == 0:
            direction = "up"
        elif row_diff > 0 and col_diff > 0:
            direction = "down_right"
        elif row_diff > 0 and col_diff < 0:
            direction = "down_left"
        elif row_diff < 0 and col_diff > 0:
            direction = "up_right"
        elif row_diff < 0 and col_diff < 0:
            direction = "up_left"
        else:
            direction = "same"
        
        return {
            "row_offset": row_diff,
            "col_offset": col_diff,
            "direction": direction,
            "distance": abs(row_diff) + abs(col_diff)
        }
    
    def _find_cells_by_content(
        self,
        table_data: TableData,
        content: str,
        exact_match: bool = False
    ) -> List[CellData]:
        """
        내용으로 셀 찾기
        
        Args:
            table_data: 테이블 데이터
            content: 찾을 내용
            exact_match: 정확한 일치 여부
            
        Returns:
            List[CellData]: 일치하는 셀 목록
        """
        matching_cells = []
        
        for cell in table_data.grid_data.cells:
            if exact_match:
                if cell.content == content:
                    matching_cells.append(cell)
            else:
                if content.lower() in cell.content.lower():
                    matching_cells.append(cell)
        
        return matching_cells
    
    def _find_value_cell_by_position(
        self,
        table_data: TableData,
        anchor_cell: CellData,
        relative_position: Dict[str, Any]
    ) -> Optional[CellData]:
        """
        상대적 위치를 기반으로 값 셀 찾기
        
        Args:
            table_data: 테이블 데이터
            anchor_cell: 앵커 셀
            relative_position: 상대적 위치 정보
            
        Returns:
            Optional[CellData]: 값 셀
        """
        target_row = anchor_cell.row + relative_position["row_offset"]
        target_col = anchor_cell.col + relative_position["col_offset"]
        
        # 테이블 범위 확인
        if (target_row < 0 or target_row >= table_data.grid_data.rows or
            target_col < 0 or target_col >= table_data.grid_data.cols):
            return None
        
        # 해당 위치의 셀 찾기
        for cell in table_data.grid_data.cells:
            if cell.row == target_row and cell.col == target_col:
                return cell
        
        return None
    
    def _calculate_extraction_confidence(
        self,
        anchor_cell: CellData,
        value_cell: CellData,
        relationship: Dict[str, Any]
    ) -> float:
        """
        추출 신뢰도 계산
        
        Args:
            anchor_cell: 앵커 셀
            value_cell: 값 셀
            relationship: 관계 설정
            
        Returns:
            float: 신뢰도 (0.0 ~ 1.0)
        """
        confidence = settings.confidence_base  # 기본 신뢰도
        
        # 앵커 내용 정확도
        anchor_similarity = self._calculate_text_similarity(
            anchor_cell.content,
            relationship["anchor"]["content"]
        )
        confidence += (anchor_similarity - 0.5) * settings.confidence_anchor_weight
        
        # 값 셀이 비어있지 않으면 신뢰도 증가
        if value_cell.content.strip():
            confidence += settings.confidence_value_weight
        
        # 값이 숫자인 경우 신뢰도 증가
        if self._is_numeric_value(value_cell.content):
            confidence += settings.confidence_numeric_weight
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        텍스트 유사도 계산 (간단한 구현)
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            
        Returns:
            float: 유사도 (0.0 ~ 1.0)
        """
        if text1 == text2:
            return settings.text_similarity_exact
        
        if text1.lower() == text2.lower():
            return settings.text_similarity_case_insensitive
        
        if text2.lower() in text1.lower() or text1.lower() in text2.lower():
            return settings.text_similarity_partial
        
        return settings.text_similarity_default
    
    def _is_numeric_value(self, text: str) -> bool:
        """
        텍스트가 숫자 값인지 확인
        
        Args:
            text: 확인할 텍스트
            
        Returns:
            bool: 숫자 여부
        """
        try:
            # 공백 제거
            cleaned_text = text.strip()
            
            # 빈 문자열은 숫자가 아님
            if not cleaned_text:
                return False
            
            # 쉼표 제거 후 숫자 확인
            cleaned_text = cleaned_text.replace(',', '')
            
            # 소수점 포함 숫자 확인
            float(cleaned_text)
            return True
            
        except ValueError:
            return False
    
    async def export_relationships(self, file_path: Path) -> bool:
        """
        모든 관계 설정을 파일로 내보내기
        
        Args:
            file_path: 내보낼 파일 경로
            
        Returns:
            bool: 내보내기 성공 여부
        """
        try:
            relationships = await self.list_relationships()
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "total_relationships": len(relationships),
                "relationships": relationships
            }
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(export_data, ensure_ascii=False, indent=2))
            
            logger.info(f"관계 설정 내보내기 완료: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"관계 설정 내보내기 실패: {e}")
            return False
    
    async def import_relationships(self, file_path: Path) -> Dict[str, Any]:
        """
        파일에서 관계 설정 가져오기
        
        Args:
            file_path: 가져올 파일 경로
            
        Returns:
            Dict[str, Any]: 가져오기 결과
        """
        result = {
            "success": False,
            "imported_count": 0,
            "skipped_count": 0,
            "errors": []
        }
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                import_data = json.loads(content)
            
            relationships = import_data.get("relationships", [])
            
            for relationship in relationships:
                try:
                    relationship_id = relationship["id"]
                    
                    # 기존 관계 설정 확인
                    existing = await self.load_relationship(relationship_id)
                    if existing:
                        result["skipped_count"] += 1
                        continue
                    
                    # 새 관계 설정 저장
                    await self.storage.save_relationship(relationship_id, relationship)
                    result["imported_count"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"관계 {relationship.get('id', 'unknown')} 가져오기 실패: {str(e)}")
            
            result["success"] = True
            logger.info(f"관계 설정 가져오기 완료: {result['imported_count']}개 가져옴, {result['skipped_count']}개 건너뜀")
            
        except Exception as e:
            result["errors"].append(f"파일 읽기 실패: {str(e)}")
            logger.error(f"관계 설정 가져오기 실패: {e}")
        
        return result
