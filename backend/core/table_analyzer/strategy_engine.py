"""
테이블 전략 엔진

테이블 구조별 최적 추출 전략을 수립하고 
헤더 방향에 따른 셀 탐색 알고리즘을 최적화하는 모듈
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from .structure_analyzer import HeaderOrientation, TableComplexity, TableStructureAnalysis

logger = logging.getLogger(__name__)


class SearchDirection(Enum):
    """검색 방향"""
    RIGHT = "right"      # 오른쪽
    DOWN = "down"        # 아래쪽
    LEFT = "left"        # 왼쪽
    UP = "up"           # 위쪽
    DIAGONAL = "diagonal" # 대각선


class CellSearchStrategy(Enum):
    """셀 검색 전략"""
    HORIZONTAL_SCAN = "horizontal_scan"    # 가로 스캔
    VERTICAL_SCAN = "vertical_scan"        # 세로 스캔
    CROSS_PATTERN = "cross_pattern"        # 십자 패턴
    PROXIMITY_BASED = "proximity_based"    # 근접성 기반
    HEADER_GUIDED = "header_guided"        # 헤더 가이드


@dataclass
class ExtractionStrategy:
    """추출 전략"""
    name: str
    description: str
    primary_search_direction: SearchDirection
    secondary_search_directions: List[SearchDirection]
    cell_search_strategy: CellSearchStrategy
    max_search_distance: int
    confidence_threshold: float
    use_header_mapping: bool
    require_exact_match: bool
    fallback_strategies: List[str]


@dataclass
class SearchResult:
    """검색 결과"""
    found: bool
    row: int
    col: int
    value: str
    confidence: float
    search_path: List[Tuple[int, int]]
    strategy_used: str


class TableStrategyEngine:
    """테이블 전략 엔진"""
    
    def __init__(self):
        """초기화"""
        self._strategies = self._initialize_strategies()
        logger.info("테이블 전략 엔진 초기화 완료")
    
    def _initialize_strategies(self) -> Dict[str, ExtractionStrategy]:
        """전략 초기화"""
        strategies = {}
        
        # 가로 헤더 전략
        strategies["horizontal_header"] = ExtractionStrategy(
            name="가로 헤더 전략",
            description="헤더가 가로로 배치된 테이블을 위한 전략",
            primary_search_direction=SearchDirection.DOWN,
            secondary_search_directions=[SearchDirection.RIGHT, SearchDirection.LEFT],
            cell_search_strategy=CellSearchStrategy.VERTICAL_SCAN,
            max_search_distance=10,
            confidence_threshold=0.8,
            use_header_mapping=True,
            require_exact_match=False,
            fallback_strategies=["proximity_based", "cross_pattern"]
        )
        
        # 세로 헤더 전략
        strategies["vertical_header"] = ExtractionStrategy(
            name="세로 헤더 전략",
            description="헤더가 세로로 배치된 테이블을 위한 전략",
            primary_search_direction=SearchDirection.RIGHT,
            secondary_search_directions=[SearchDirection.DOWN, SearchDirection.UP],
            cell_search_strategy=CellSearchStrategy.HORIZONTAL_SCAN,
            max_search_distance=15,
            confidence_threshold=0.8,
            use_header_mapping=True,
            require_exact_match=False,
            fallback_strategies=["proximity_based", "cross_pattern"]
        )
        
        # 혼합 헤더 전략
        strategies["mixed_header"] = ExtractionStrategy(
            name="혼합 헤더 전략",
            description="헤더가 혼합으로 배치된 복잡한 테이블을 위한 전략",
            primary_search_direction=SearchDirection.RIGHT,
            secondary_search_directions=[SearchDirection.DOWN, SearchDirection.LEFT, SearchDirection.UP],
            cell_search_strategy=CellSearchStrategy.CROSS_PATTERN,
            max_search_distance=8,
            confidence_threshold=0.7,
            use_header_mapping=True,
            require_exact_match=False,
            fallback_strategies=["proximity_based", "horizontal_scan"]
        )
        
        # 근접성 기반 전략
        strategies["proximity_based"] = ExtractionStrategy(
            name="근접성 기반 전략",
            description="앵커 근처에서 값을 찾는 전략",
            primary_search_direction=SearchDirection.RIGHT,
            secondary_search_directions=[SearchDirection.DOWN, SearchDirection.LEFT, SearchDirection.UP],
            cell_search_strategy=CellSearchStrategy.PROXIMITY_BASED,
            max_search_distance=5,
            confidence_threshold=0.6,
            use_header_mapping=False,
            require_exact_match=False,
            fallback_strategies=["cross_pattern"]
        )
        
        # 십자 패턴 전략
        strategies["cross_pattern"] = ExtractionStrategy(
            name="십자 패턴 전략",
            description="앵커를 중심으로 십자 방향으로 검색하는 전략",
            primary_search_direction=SearchDirection.RIGHT,
            secondary_search_directions=[SearchDirection.DOWN, SearchDirection.LEFT, SearchDirection.UP],
            cell_search_strategy=CellSearchStrategy.CROSS_PATTERN,
            max_search_distance=6,
            confidence_threshold=0.5,
            use_header_mapping=False,
            require_exact_match=False,
            fallback_strategies=[]
        )
        
        return strategies
    
    def select_strategy(self, table_analysis: TableStructureAnalysis) -> ExtractionStrategy:
        """
        테이블 분석 결과에 따른 최적 전략 선택
        
        Args:
            table_analysis: 테이블 구조 분석 결과
            
        Returns:
            ExtractionStrategy: 선택된 추출 전략
        """
        try:
            # 헤더 방향에 따른 기본 전략 선택
            if table_analysis.orientation == HeaderOrientation.HORIZONTAL:
                strategy_name = "horizontal_header"
            elif table_analysis.orientation == HeaderOrientation.VERTICAL:
                strategy_name = "vertical_header"
            elif table_analysis.orientation == HeaderOrientation.MIXED:
                strategy_name = "mixed_header"
            else:
                # 알 수 없는 구조의 경우 근접성 기반 전략
                strategy_name = "proximity_based"
            
            # 복잡도에 따른 조정
            strategy = self._strategies[strategy_name]
            
            if table_analysis.complexity == TableComplexity.COMPLEX:
                # 복잡한 테이블의 경우 더 보수적인 설정
                strategy.max_search_distance = min(strategy.max_search_distance, 6)
                strategy.confidence_threshold = max(strategy.confidence_threshold, 0.7)
            elif table_analysis.complexity == TableComplexity.SIMPLE:
                # 단순한 테이블의 경우 더 적극적인 설정
                strategy.max_search_distance += 2
                strategy.confidence_threshold = max(strategy.confidence_threshold - 0.1, 0.5)
            
            logger.info(f"테이블 전략 선택: {strategy.name} (방향: {table_analysis.orientation.value}, 복잡도: {table_analysis.complexity.value})")
            
            return strategy
            
        except Exception as e:
            logger.error(f"전략 선택 실패: {e}")
            # 기본 전략 반환
            return self._strategies["proximity_based"]
    
    def find_value_cell(
        self,
        table_data: List[List[str]],
        anchor_row: int,
        anchor_col: int,
        strategy: ExtractionStrategy,
        target_patterns: List[str] = None
    ) -> SearchResult:
        """
        전략에 따른 값 셀 검색
        
        Args:
            table_data: 테이블 데이터
            anchor_row: 앵커 행
            anchor_col: 앵커 열
            strategy: 추출 전략
            target_patterns: 찾을 패턴들 (선택사항)
            
        Returns:
            SearchResult: 검색 결과
        """
        try:
            if strategy.cell_search_strategy == CellSearchStrategy.VERTICAL_SCAN:
                return self._vertical_scan(table_data, anchor_row, anchor_col, strategy, target_patterns)
            elif strategy.cell_search_strategy == CellSearchStrategy.HORIZONTAL_SCAN:
                return self._horizontal_scan(table_data, anchor_row, anchor_col, strategy, target_patterns)
            elif strategy.cell_search_strategy == CellSearchStrategy.CROSS_PATTERN:
                return self._cross_pattern_search(table_data, anchor_row, anchor_col, strategy, target_patterns)
            elif strategy.cell_search_strategy == CellSearchStrategy.PROXIMITY_BASED:
                return self._proximity_based_search(table_data, anchor_row, anchor_col, strategy, target_patterns)
            else:
                # 기본: 근접성 기반 검색
                return self._proximity_based_search(table_data, anchor_row, anchor_col, strategy, target_patterns)
                
        except Exception as e:
            logger.error(f"값 셀 검색 실패: {e}")
            return SearchResult(
                found=False, row=-1, col=-1, value="", confidence=0.0,
                search_path=[], strategy_used=strategy.name
            )
    
    def _vertical_scan(
        self,
        table_data: List[List[str]],
        anchor_row: int,
        anchor_col: int,
        strategy: ExtractionStrategy,
        target_patterns: List[str] = None
    ) -> SearchResult:
        """세로 스캔 검색"""
        search_path = []
        
        # 아래쪽으로 검색
        for distance in range(1, strategy.max_search_distance + 1):
            new_row = anchor_row + distance
            if new_row >= len(table_data):
                break
            
            search_path.append((new_row, anchor_col))
            
            if anchor_col < len(table_data[new_row]):
                cell_value = table_data[new_row][anchor_col].strip()
                
                if cell_value and self._is_value_cell(cell_value, target_patterns):
                    confidence = self._calculate_confidence(cell_value, distance, strategy)
                    
                    if confidence >= strategy.confidence_threshold:
                        return SearchResult(
                            found=True, row=new_row, col=anchor_col,
                            value=cell_value, confidence=confidence,
                            search_path=search_path, strategy_used=strategy.name
                        )
        
        return SearchResult(
            found=False, row=-1, col=-1, value="", confidence=0.0,
            search_path=search_path, strategy_used=strategy.name
        )
    
    def _horizontal_scan(
        self,
        table_data: List[List[str]],
        anchor_row: int,
        anchor_col: int,
        strategy: ExtractionStrategy,
        target_patterns: List[str] = None
    ) -> SearchResult:
        """가로 스캔 검색"""
        search_path = []
        
        if anchor_row >= len(table_data):
            return SearchResult(
                found=False, row=-1, col=-1, value="", confidence=0.0,
                search_path=[], strategy_used=strategy.name
            )
        
        # 오른쪽으로 검색
        for distance in range(1, strategy.max_search_distance + 1):
            new_col = anchor_col + distance
            if new_col >= len(table_data[anchor_row]):
                break
            
            search_path.append((anchor_row, new_col))
            
            cell_value = table_data[anchor_row][new_col].strip()
            
            if cell_value and self._is_value_cell(cell_value, target_patterns):
                confidence = self._calculate_confidence(cell_value, distance, strategy)
                
                if confidence >= strategy.confidence_threshold:
                    return SearchResult(
                        found=True, row=anchor_row, col=new_col,
                        value=cell_value, confidence=confidence,
                        search_path=search_path, strategy_used=strategy.name
                    )
        
        return SearchResult(
            found=False, row=-1, col=-1, value="", confidence=0.0,
            search_path=search_path, strategy_used=strategy.name
        )
    
    def _cross_pattern_search(
        self,
        table_data: List[List[str]],
        anchor_row: int,
        anchor_col: int,
        strategy: ExtractionStrategy,
        target_patterns: List[str] = None
    ) -> SearchResult:
        """십자 패턴 검색"""
        search_path = []
        best_result = None
        best_confidence = 0.0
        
        # 4방향으로 검색
        directions = [
            (0, 1),   # 오른쪽
            (1, 0),   # 아래
            (0, -1),  # 왼쪽
            (-1, 0)   # 위
        ]
        
        for dr, dc in directions:
            for distance in range(1, strategy.max_search_distance + 1):
                new_row = anchor_row + (dr * distance)
                new_col = anchor_col + (dc * distance)
                
                # 범위 체크
                if (new_row < 0 or new_row >= len(table_data) or 
                    new_col < 0 or new_col >= len(table_data[new_row])):
                    break
                
                search_path.append((new_row, new_col))
                
                cell_value = table_data[new_row][new_col].strip()
                
                if cell_value and self._is_value_cell(cell_value, target_patterns):
                    confidence = self._calculate_confidence(cell_value, distance, strategy)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_result = SearchResult(
                            found=True, row=new_row, col=new_col,
                            value=cell_value, confidence=confidence,
                            search_path=search_path.copy(), strategy_used=strategy.name
                        )
        
        if best_result and best_confidence >= strategy.confidence_threshold:
            return best_result
        
        return SearchResult(
            found=False, row=-1, col=-1, value="", confidence=0.0,
            search_path=search_path, strategy_used=strategy.name
        )
    
    def _proximity_based_search(
        self,
        table_data: List[List[str]],
        anchor_row: int,
        anchor_col: int,
        strategy: ExtractionStrategy,
        target_patterns: List[str] = None
    ) -> SearchResult:
        """근접성 기반 검색"""
        search_path = []
        candidates = []
        
        # 앵커 주변 영역 검색
        for dr in range(-strategy.max_search_distance, strategy.max_search_distance + 1):
            for dc in range(-strategy.max_search_distance, strategy.max_search_distance + 1):
                if dr == 0 and dc == 0:  # 앵커 자체는 제외
                    continue
                
                new_row = anchor_row + dr
                new_col = anchor_col + dc
                
                # 범위 체크
                if (new_row < 0 or new_row >= len(table_data) or 
                    new_col < 0 or new_col >= len(table_data[new_row])):
                    continue
                
                search_path.append((new_row, new_col))
                
                cell_value = table_data[new_row][new_col].strip()
                
                if cell_value and self._is_value_cell(cell_value, target_patterns):
                    distance = abs(dr) + abs(dc)  # 맨해튼 거리
                    confidence = self._calculate_confidence(cell_value, distance, strategy)
                    
                    candidates.append({
                        "row": new_row,
                        "col": new_col,
                        "value": cell_value,
                        "confidence": confidence,
                        "distance": distance
                    })
        
        # 신뢰도가 가장 높은 후보 선택
        if candidates:
            best_candidate = max(candidates, key=lambda x: x["confidence"])
            
            if best_candidate["confidence"] >= strategy.confidence_threshold:
                return SearchResult(
                    found=True,
                    row=best_candidate["row"],
                    col=best_candidate["col"],
                    value=best_candidate["value"],
                    confidence=best_candidate["confidence"],
                    search_path=search_path,
                    strategy_used=strategy.name
                )
        
        return SearchResult(
            found=False, row=-1, col=-1, value="", confidence=0.0,
            search_path=search_path, strategy_used=strategy.name
        )
    
    def _is_value_cell(self, cell_value: str, target_patterns: List[str] = None) -> bool:
        """값 셀인지 판단"""
        if not cell_value or cell_value.isspace():
            return False
        
        # 패턴이 지정된 경우 패턴 매칭
        if target_patterns:
            for pattern in target_patterns:
                if pattern.lower() in cell_value.lower():
                    return True
            return False
        
        # 기본적으로 숫자나 의미있는 텍스트가 있으면 값으로 간주
        # 헤더 키워드는 제외
        header_keywords = ["항목", "구분", "검사", "결과", "수치", "값", "기준"]
        
        for keyword in header_keywords:
            if keyword in cell_value:
                return False
        
        return True
    
    def _calculate_confidence(self, cell_value: str, distance: int, strategy: ExtractionStrategy) -> float:
        """신뢰도 계산"""
        base_confidence = 1.0
        
        # 거리에 따른 신뢰도 감소
        distance_penalty = distance * 0.1
        base_confidence -= distance_penalty
        
        # 값의 형태에 따른 보정
        if cell_value.replace(".", "").replace("-", "").replace("+", "").isdigit():
            # 숫자인 경우 신뢰도 증가
            base_confidence += 0.1
        elif len(cell_value) > 20:
            # 너무 긴 텍스트는 신뢰도 감소
            base_confidence -= 0.2
        
        return max(0.0, min(1.0, base_confidence))
    
    def get_available_strategies(self) -> Dict[str, str]:
        """
        사용 가능한 전략 목록 반환
        
        Returns:
            Dict[str, str]: 전략명과 설명의 매핑
        """
        return {name: strategy.description for name, strategy in self._strategies.items()}


# 전역 인스턴스
_table_strategy_engine = None


def get_table_strategy_engine() -> TableStrategyEngine:
    """테이블 전략 엔진 싱글톤 인스턴스 반환"""
    global _table_strategy_engine
    if _table_strategy_engine is None:
        _table_strategy_engine = TableStrategyEngine()
    return _table_strategy_engine




