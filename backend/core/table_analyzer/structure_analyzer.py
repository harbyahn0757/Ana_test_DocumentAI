"""
테이블 구조 분석기

테이블의 헤더 방향(가로/세로/혼합)을 자동으로 감지하고
최적의 추출 전략을 수립하는 모듈
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import re

from models.table_models import TableData
from core.base_ai_service import BaseAIService

logger = logging.getLogger(__name__)


class HeaderOrientation(Enum):
    """헤더 방향 타입"""
    HORIZONTAL = "horizontal"  # 가로 (행 기반)
    VERTICAL = "vertical"      # 세로 (열 기반) 
    MIXED = "mixed"           # 혼합
    UNKNOWN = "unknown"       # 알 수 없음


class TableComplexity(Enum):
    """테이블 복잡도"""
    SIMPLE = "simple"         # 단순 (일반적인 형태)
    MODERATE = "moderate"     # 보통 (중첩 헤더 등)
    COMPLEX = "complex"       # 복잡 (다중 레벨, 불규칙)


@dataclass
class HeaderInfo:
    """헤더 정보"""
    row: int
    col: int
    text: str
    level: int = 1  # 헤더 레벨 (1=메인, 2=서브 등)
    span_rows: int = 1
    span_cols: int = 1
    confidence: float = 1.0


@dataclass 
class TableStructureAnalysis:
    """테이블 구조 분석 결과"""
    table_id: str
    page_number: int
    orientation: HeaderOrientation
    complexity: TableComplexity
    headers: List[HeaderInfo]
    data_start_row: int
    data_start_col: int
    total_rows: int
    total_cols: int
    confidence: float
    analysis_notes: List[str]
    extraction_strategy: Dict[str, Any]


class TableStructureAnalyzer(BaseAIService):
    """테이블 구조 분석기 클래스"""
    
    def __init__(self):
        """초기화"""
        super().__init__("테이블구조분석기")
    
    async def _validate_initialization(self) -> bool:
        """초기화 검증"""
        return self._initialized
    
    async def analyze_table_structure(
        self, 
        table: TableData,
        use_ai: bool = True
    ) -> TableStructureAnalysis:
        """
        테이블 구조 분석
        
        Args:
            table: 분석할 테이블 데이터
            use_ai: AI 분석 사용 여부
            
        Returns:
            TableStructureAnalysis: 구조 분석 결과
        """
        try:
            self.log_info("분석 시작", page=table.page_number)
            
            # 1. 기본 정보 수집
            table_id = f"table_{table.page_number}_{id(table)}"
            total_rows = len(table.rows)
            total_cols = len(table.rows[0]) if table.rows else 0
            
            self.log_info("기본 정보 수집 완료", rows=total_rows, cols=total_cols)
            
            # 2. 규칙 기반 분석
            rule_based_analysis = await self._rule_based_analysis(table)
            
            # 3. AI 분석 (선택적)
            ai_analysis = None
            if use_ai and self.is_ai_available:
                ai_analysis = await self._ai_based_analysis(table)
            
            # 4. 분석 결과 통합
            final_analysis = await self._merge_analysis_results(
                table_id, table.page_number, total_rows, total_cols,
                rule_based_analysis, ai_analysis
            )
            
            self.log_info("분석 완료", 
                         orientation=final_analysis.orientation.value, 
                         complexity=final_analysis.complexity.value,
                         confidence=final_analysis.confidence)
            
            return final_analysis
            
        except Exception as e:
            self.log_error("분석 실패", error=str(e))
            # 기본 분석 결과 반환
            return TableStructureAnalysis(
                table_id=f"table_{table.page_number}_{id(table)}",
                page_number=table.page_number,
                orientation=HeaderOrientation.UNKNOWN,
                complexity=TableComplexity.SIMPLE,
                headers=[],
                data_start_row=1,
                data_start_col=0,
                total_rows=len(table.rows),
                total_cols=len(table.rows[0]) if table.rows else 0,
                confidence=0.0,
                analysis_notes=[f"분석 실패: {str(e)}"],
                extraction_strategy={"method": "sequential", "start_row": 1}
            )
    
    async def _rule_based_analysis(self, table: TableData) -> Dict[str, Any]:
        """규칙 기반 테이블 구조 분석"""
        try:
            if not table.rows or len(table.rows) < 2:
                return {
                    "orientation": HeaderOrientation.UNKNOWN,
                    "complexity": TableComplexity.SIMPLE,
                    "headers": [],
                    "confidence": 0.5,
                    "notes": ["테이블 데이터 부족"]
                }
            
            # 헤더 후보 감지
            potential_headers = self._detect_header_candidates(table.rows)
            
            # 방향성 분석
            orientation = self._analyze_orientation(table.rows, potential_headers)
            
            # 복잡도 평가
            complexity = self._evaluate_complexity(table.rows, potential_headers)
            
            # 데이터 시작 지점 찾기
            data_start_row, data_start_col = self._find_data_start_point(table.rows, potential_headers)
            
            return {
                "orientation": orientation,
                "complexity": complexity,
                "headers": potential_headers,
                "data_start_row": data_start_row,
                "data_start_col": data_start_col,
                "confidence": 0.8,
                "notes": ["규칙 기반 분석 완료"]
            }
            
        except Exception as e:
            logger.error(f"규칙 기반 분석 실패: {e}")
            return {
                "orientation": HeaderOrientation.UNKNOWN,
                "complexity": TableComplexity.SIMPLE,
                "headers": [],
                "confidence": 0.0,
                "notes": [f"규칙 기반 분석 실패: {str(e)}"]
            }
    
    def _detect_header_candidates(self, rows: List[List[str]]) -> List[HeaderInfo]:
        """헤더 후보 감지"""
        headers = []
        
        try:
            # 첫 번째 행 검사 (가장 일반적인 헤더 위치)
            if rows and len(rows) > 0:
                first_row = rows[0]
                for col_idx, cell_text in enumerate(first_row):
                    if self._is_likely_header(cell_text, col_idx, 0, rows):
                        headers.append(HeaderInfo(
                            row=0,
                            col=col_idx,
                            text=cell_text,
                            level=1,
                            confidence=0.8
                        ))
            
            # 첫 번째 열 검사 (세로 헤더 가능성)
            if len(rows) > 1:
                for row_idx, row in enumerate(rows):
                    if row and len(row) > 0:
                        first_cell = row[0]
                        if self._is_likely_header(first_cell, 0, row_idx, rows):
                            headers.append(HeaderInfo(
                                row=row_idx,
                                col=0,
                                text=first_cell,
                                level=1,
                                confidence=0.7
                            ))
                    
        except Exception as e:
            logger.error(f"헤더 후보 감지 실패: {e}")
        
        return headers
    
    def _is_likely_header(self, text: str, col: int, row: int, all_rows: List[List[str]]) -> bool:
        """텍스트가 헤더일 가능성 판단"""
        if not text or text.strip() == "":
            return False
        
        text = text.strip()
        
        # 헤더 패턴 매칭
        header_patterns = [
            r'^[가-힣]+(\([가-힣a-zA-Z0-9\s/]+\))?$',  # 한글 + 괄호
            r'^[a-zA-Z]+(\s+[a-zA-Z]+)*$',              # 영문 단어
            r'^[가-힣]{2,}$',                            # 한글 2글자 이상
            r'^[가-힣]+[0-9]*$',                         # 한글 + 숫자
            r'.*검사.*|.*결과.*|.*수치.*|.*값.*',          # 검사 관련 키워드
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, text):
                return True
        
        # 숫자만 있으면 헤더 아닐 가능성 높음
        if text.replace('.', '').replace(',', '').replace('-', '').isdigit():
            return False
        
        # 특수 문자만 있으면 헤더 아님
        if re.match(r'^[^\w가-힣]+$', text):
            return False
        
        return len(text) > 1 and len(text) < 50  # 적절한 길이
    
    def _analyze_orientation(self, rows: List[List[str]], headers: List[HeaderInfo]) -> HeaderOrientation:
        """테이블 방향성 분석"""
        try:
            if not headers:
                return HeaderOrientation.UNKNOWN
            
            # 첫 번째 행의 헤더 수
            first_row_headers = len([h for h in headers if h.row == 0])
            # 첫 번째 열의 헤더 수  
            first_col_headers = len([h for h in headers if h.col == 0])
            
            # 전체 열 수 대비 첫 번째 행 헤더 비율
            total_cols = len(rows[0]) if rows else 1
            horizontal_ratio = first_row_headers / total_cols if total_cols > 0 else 0
            
            # 전체 행 수 대비 첫 번째 열 헤더 비율
            total_rows = len(rows)
            vertical_ratio = first_col_headers / total_rows if total_rows > 0 else 0
            
            logger.debug(f"방향성 분석: 가로={horizontal_ratio:.2f}, 세로={vertical_ratio:.2f}")
            
            # 방향성 결정
            if horizontal_ratio > 0.5 and vertical_ratio < 0.3:
                return HeaderOrientation.HORIZONTAL
            elif vertical_ratio > 0.5 and horizontal_ratio < 0.3:
                return HeaderOrientation.VERTICAL
            elif horizontal_ratio > 0.3 and vertical_ratio > 0.3:
                return HeaderOrientation.MIXED
            else:
                return HeaderOrientation.HORIZONTAL  # 기본값
                
        except Exception as e:
            logger.error(f"방향성 분석 실패: {e}")
            return HeaderOrientation.UNKNOWN
    
    def _evaluate_complexity(self, rows: List[List[str]], headers: List[HeaderInfo]) -> TableComplexity:
        """테이블 복잡도 평가"""
        try:
            complexity_score = 0
            
            # 크기 기반 복잡도
            if len(rows) > 20 or (len(rows) > 0 and len(rows[0]) > 10):
                complexity_score += 1
            
            # 헤더 수 기반
            if len(headers) > 10:
                complexity_score += 1
            
            # 빈 셀 비율 확인
            total_cells = sum(len(row) for row in rows)
            empty_cells = sum(1 for row in rows for cell in row if not cell or cell.strip() == "")
            empty_ratio = empty_cells / total_cells if total_cells > 0 else 0
            
            if empty_ratio > 0.3:
                complexity_score += 1
            
            # 불규칙한 행 길이
            if len(rows) > 1:
                row_lengths = [len(row) for row in rows]
                if len(set(row_lengths)) > 1:  # 서로 다른 길이의 행이 있음
                    complexity_score += 1
            
            # 복잡도 결정
            if complexity_score <= 1:
                return TableComplexity.SIMPLE
            elif complexity_score <= 2:
                return TableComplexity.MODERATE
            else:
                return TableComplexity.COMPLEX
                
        except Exception as e:
            logger.error(f"복잡도 평가 실패: {e}")
            return TableComplexity.SIMPLE
    
    def _find_data_start_point(self, rows: List[List[str]], headers: List[HeaderInfo]) -> Tuple[int, int]:
        """데이터 시작 지점 찾기"""
        try:
            # 헤더가 있는 행 중 최대값 + 1
            header_rows = [h.row for h in headers if h.row is not None]
            max_header_row = max(header_rows) if header_rows else -1
            
            # 헤더가 있는 열 중 최대값 + 1
            header_cols = [h.col for h in headers if h.col is not None]
            max_header_col = max(header_cols) if header_cols else -1
            
            data_start_row = max(1, max_header_row + 1)
            data_start_col = max(0, max_header_col + 1) if max_header_col > 0 else 0
            
            return data_start_row, data_start_col
            
        except Exception as e:
            logger.error(f"데이터 시작 지점 찾기 실패: {e}")
            return 1, 0
    
    async def _ai_based_analysis(self, table: TableData) -> Optional[Dict[str, Any]]:
        """AI 기반 테이블 구조 분석"""
        try:
            self.log_info("AI 분석 시작")
            
            # 테이블 데이터를 문자열로 변환 (처음 5행만 분석에 사용)
            sample_rows = table.rows[:5] if len(table.rows) > 5 else table.rows
            table_str = "\n".join(["\t".join(row) for row in sample_rows])
            
            # AI 호출
            ai_result = await self.call_ai_with_prompt(
                "header_analysis",
                table_data=table_str,
                total_rows=len(table.rows),
                total_cols=len(table.rows[0]) if table.rows else 0,
                page_number=table.page_number
            )
            
            if ai_result:
                self.log_info("AI 분석 완료", orientation=ai_result.get('orientation', 'unknown'))
                return {
                    "orientation": HeaderOrientation(ai_result.get('orientation', 'unknown')),
                    "complexity": TableComplexity(ai_result.get('complexity', 'simple')),
                    "headers": self._parse_ai_headers(ai_result.get('headers', [])),
                    "data_start_row": ai_result.get('data_start_row', 1),
                    "data_start_col": ai_result.get('data_start_col', 0),
                    "confidence": ai_result.get('confidence', 0.7),
                    "notes": ai_result.get('notes', [])
                }
            
        except Exception as e:
            self.log_error("AI 분석 실패", error=str(e))
        
        return None
    
    def _parse_ai_headers(self, ai_headers: List[Dict]) -> List[HeaderInfo]:
        """AI가 감지한 헤더 정보 파싱"""
        headers = []
        try:
            for header_data in ai_headers:
                headers.append(HeaderInfo(
                    row=header_data.get('row', 0),
                    col=header_data.get('col', 0),
                    text=header_data.get('text', ''),
                    level=header_data.get('level', 1),
                    confidence=header_data.get('confidence', 0.7)
                ))
        except Exception as e:
            logger.error(f"AI 헤더 파싱 실패: {e}")
        
        return headers
    
    async def _merge_analysis_results(
        self,
        table_id: str,
        page_number: int,
        total_rows: int,
        total_cols: int,
        rule_analysis: Dict[str, Any],
        ai_analysis: Optional[Dict[str, Any]]
    ) -> TableStructureAnalysis:
        """규칙 기반과 AI 분석 결과 통합"""
        
        # AI 분석이 있으면 우선 사용, 없으면 규칙 기반 사용
        if ai_analysis and ai_analysis.get('confidence', 0) > 0.6:
            primary_analysis = ai_analysis
            fallback_analysis = rule_analysis
            confidence = ai_analysis.get('confidence', 0.7)
            notes = ai_analysis.get('notes', []) + ["AI 분석 결과 사용"]
        else:
            primary_analysis = rule_analysis
            fallback_analysis = ai_analysis or {}
            confidence = rule_analysis.get('confidence', 0.6)
            notes = rule_analysis.get('notes', []) + ["규칙 기반 분석 결과 사용"]
        
        # 추출 전략 결정
        extraction_strategy = self._determine_extraction_strategy(
            primary_analysis.get('orientation', HeaderOrientation.HORIZONTAL),
            primary_analysis.get('complexity', TableComplexity.SIMPLE),
            primary_analysis.get('data_start_row', 1),
            primary_analysis.get('data_start_col', 0)
        )
        
        return TableStructureAnalysis(
            table_id=table_id,
            page_number=page_number,
            orientation=primary_analysis.get('orientation', HeaderOrientation.HORIZONTAL),
            complexity=primary_analysis.get('complexity', TableComplexity.SIMPLE),
            headers=primary_analysis.get('headers', []),
            data_start_row=primary_analysis.get('data_start_row', 1),
            data_start_col=primary_analysis.get('data_start_col', 0),
            total_rows=total_rows,
            total_cols=total_cols,
            confidence=confidence,
            analysis_notes=notes,
            extraction_strategy=extraction_strategy
        )
    
    def _determine_extraction_strategy(
        self,
        orientation: HeaderOrientation,
        complexity: TableComplexity,
        data_start_row: int,
        data_start_col: int
    ) -> Dict[str, Any]:
        """추출 전략 결정"""
        
        strategy = {
            "method": "sequential",
            "start_row": data_start_row,
            "start_col": data_start_col,
            "scan_direction": "horizontal",
            "header_orientation": orientation.value,
            "complexity_level": complexity.value
        }
        
        # 방향성에 따른 전략 조정
        if orientation == HeaderOrientation.VERTICAL:
            strategy["scan_direction"] = "vertical"
            strategy["primary_axis"] = "column"
        elif orientation == HeaderOrientation.HORIZONTAL:
            strategy["scan_direction"] = "horizontal" 
            strategy["primary_axis"] = "row"
        elif orientation == HeaderOrientation.MIXED:
            strategy["scan_direction"] = "both"
            strategy["primary_axis"] = "adaptive"
        
        # 복잡도에 따른 전략 조정
        if complexity == TableComplexity.COMPLEX:
            strategy["method"] = "adaptive"
            strategy["use_ai_assistance"] = True
            strategy["multi_pass"] = True
        elif complexity == TableComplexity.MODERATE:
            strategy["method"] = "structured"
            strategy["use_pattern_matching"] = True
        
        return strategy


# 싱글톤 인스턴스
_analyzer_instance = None

def get_table_structure_analyzer() -> TableStructureAnalyzer:
    """테이블 구조 분석기 인스턴스 반환"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = TableStructureAnalyzer()
    return _analyzer_instance
