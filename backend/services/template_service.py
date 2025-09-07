"""
템플릿 서비스
추출 템플릿 저장/조회/수정/삭제를 담당하는 서비스
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

from models.template_models import (
    ExtractionTemplate, 
    TemplateCreateRequest, 
    TemplateUpdateRequest,
    TemplateResponse,
    TemplateListResponse,
    KeyMapping,
    FileInfo,
    TemplateStatus
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


class TemplateService:
    """템플릿 서비스 클래스"""
    
    def __init__(self, db_path: str = "templates.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 템플릿 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS extraction_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        mappings TEXT NOT NULL,  -- JSON 문자열
                        file_info TEXT,          -- JSON 문자열
                        status TEXT NOT NULL DEFAULT 'active',
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_templates_name 
                    ON extraction_templates(name)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_templates_status 
                    ON extraction_templates(status)
                """)
                
                conn.commit()
                logger.info("템플릿 데이터베이스 초기화 완료")
                
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    def create_template(self, request: TemplateCreateRequest) -> TemplateResponse:
        """템플릿 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 매핑 데이터에 ID와 생성 시간 추가
                processed_mappings = []
                for i, mapping in enumerate(request.mappings):
                    processed_mapping = mapping.copy()
                    processed_mapping['id'] = i + 1  # 임시 ID
                    processed_mapping['created_at'] = datetime.now().isoformat()
                    processed_mappings.append(processed_mapping)
                
                # 매핑 데이터를 JSON으로 변환
                mappings_json = json.dumps(processed_mappings, ensure_ascii=False)
                file_info_json = json.dumps(request.file_info, ensure_ascii=False) if request.file_info else None
                
                cursor.execute("""
                    INSERT INTO extraction_templates 
                    (name, description, mappings, file_info, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.name,
                    request.description,
                    mappings_json,
                    file_info_json,
                    TemplateStatus.ACTIVE.value,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                template_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"템플릿 생성 완료: {template_id}")
                
                # 생성된 템플릿 조회
                return self.get_template(template_id)
                
        except Exception as e:
            logger.error(f"템플릿 생성 실패: {e}")
            raise
    
    def get_template(self, template_id: int) -> TemplateResponse:
        """템플릿 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, description, mappings, file_info, status, 
                           created_at, updated_at, created_by
                    FROM extraction_templates 
                    WHERE id = ?
                """, (template_id,))
                
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"템플릿을 찾을 수 없습니다: {template_id}")
                
                return self._row_to_template_response(row)
                
        except Exception as e:
            logger.error(f"템플릿 조회 실패: {e}")
            raise
    
    def get_templates(self, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> TemplateListResponse:
        """템플릿 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # WHERE 조건 구성
                where_clause = ""
                params = []
                
                if status:
                    where_clause = "WHERE status = ?"
                    params.append(status)
                
                # 전체 개수 조회
                count_query = f"SELECT COUNT(*) FROM extraction_templates {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # 페이지네이션 계산
                offset = (page - 1) * page_size
                total_pages = (total_count + page_size - 1) // page_size
                
                # 템플릿 목록 조회
                query = f"""
                    SELECT id, name, description, mappings, file_info, status, 
                           created_at, updated_at, created_by
                    FROM extraction_templates 
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                
                cursor.execute(query, params + [page_size, offset])
                rows = cursor.fetchall()
                
                templates = [self._row_to_template_response(row) for row in rows]
                
                return TemplateListResponse(
                    templates=templates,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages
                )
                
        except Exception as e:
            logger.error(f"템플릿 목록 조회 실패: {e}")
            raise
    
    def update_template(self, template_id: int, request: TemplateUpdateRequest) -> TemplateResponse:
        """템플릿 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 수정할 필드들 구성
                update_fields = []
                params = []
                
                if request.name is not None:
                    update_fields.append("name = ?")
                    params.append(request.name)
                
                if request.description is not None:
                    update_fields.append("description = ?")
                    params.append(request.description)
                
                if request.mappings is not None:
                    # 매핑 데이터에 ID와 생성 시간 추가
                    processed_mappings = []
                    for i, mapping in enumerate(request.mappings):
                        processed_mapping = mapping.copy()
                        processed_mapping['id'] = i + 1  # 임시 ID
                        processed_mapping['created_at'] = datetime.now().isoformat()
                        processed_mappings.append(processed_mapping)
                    
                    update_fields.append("mappings = ?")
                    params.append(json.dumps(processed_mappings, ensure_ascii=False))
                
                if request.status is not None:
                    update_fields.append("status = ?")
                    params.append(request.status.value)
                
                if not update_fields:
                    raise ValueError("수정할 필드가 없습니다")
                
                update_fields.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(template_id)
                
                query = f"""
                    UPDATE extraction_templates 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """
                
                cursor.execute(query, params)
                
                if cursor.rowcount == 0:
                    raise ValueError(f"템플릿을 찾을 수 없습니다: {template_id}")
                
                conn.commit()
                
                logger.info(f"템플릿 수정 완료: {template_id}")
                
                # 수정된 템플릿 조회
                return self.get_template(template_id)
                
        except Exception as e:
            logger.error(f"템플릿 수정 실패: {e}")
            raise
    
    def delete_template(self, template_id: int) -> bool:
        """템플릿 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM extraction_templates WHERE id = ?", (template_id,))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"템플릿을 찾을 수 없습니다: {template_id}")
                
                conn.commit()
                
                logger.info(f"템플릿 삭제 완료: {template_id}")
                return True
                
        except Exception as e:
            logger.error(f"템플릿 삭제 실패: {e}")
            raise
    
    def _row_to_template_response(self, row) -> TemplateResponse:
        """데이터베이스 행을 TemplateResponse로 변환"""
        try:
            # JSON 필드 파싱
            mappings_data = json.loads(row[3]) if row[3] else []
            file_info_data = json.loads(row[4]) if row[4] else None
            
            # KeyMapping 객체들 생성 (호환성 처리)
            mappings = []
            for mapping_data in mappings_data:
                # 이전 버전 호환성: camelCase를 snake_case로 변환
                converted_mapping = self._convert_mapping_format(mapping_data)
                mappings.append(KeyMapping(**converted_mapping))
            
            # FileInfo 객체 생성
            file_info = FileInfo(**file_info_data) if file_info_data else None
            
            return TemplateResponse(
                id=row[0],
                name=row[1],
                description=row[2],
                mappings=mappings,
                file_info=file_info,
                status=TemplateStatus(row[5]),
                created_at=datetime.fromisoformat(row[6]),
                updated_at=datetime.fromisoformat(row[7]),
                created_by=row[8]
            )
            
        except Exception as e:
            logger.error(f"템플릿 응답 변환 실패: {e}")
            raise
    
    def _convert_mapping_format(self, mapping_data: Dict[str, Any]) -> Dict[str, Any]:
        """매핑 데이터 형식을 snake_case로 변환 (이전 버전 호환성)"""
        converted = mapping_data.copy()
        
        # camelCase를 snake_case로 변환
        if 'keyLabel' in converted and 'key_label' not in converted:
            converted['key_label'] = converted.pop('keyLabel')
        
        if 'anchorCell' in converted and 'anchor_cell' not in converted:
            converted['anchor_cell'] = converted.pop('anchorCell')
        
        if 'valueCell' in converted and 'value_cell' not in converted:
            converted['value_cell'] = converted.pop('valueCell')
        
        if 'relativePosition' in converted and 'relative_position' not in converted:
            converted['relative_position'] = converted.pop('relativePosition')
        
        if 'createdAt' in converted and 'created_at' not in converted:
            converted['created_at'] = converted.pop('createdAt')
        
        return converted


# 싱글톤 인스턴스
template_service = TemplateService()
