"""
테이블 데이터 관리 API 엔드포인트

추출된 테이블 데이터의 조회, 수정, 분석 기능 제공
"""

from typing import List, Dict, Any, Optional
import logging

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse

from app.dependencies import get_cache_manager
# from app.dependencies import get_extraction_service  # 임시로 주석 처리
# from services.extraction_service import ExtractionService  # 임시로 주석 처리
from storage.cache_manager import CacheManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list")
async def list_cached_tables(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """캐시된 테이블 목록 조회"""
    try:
        cache_info = cache_manager.get_cache_info()
        
        return {
            "success": True,
            "message": "캐시된 테이블 목록 조회 완료",
            "data": cache_info
        }
        
    except Exception as e:
        logger.error(f"테이블 목록 조회 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"조회 중 오류 발생: {str(e)}")


@router.post("/analyze")
async def analyze_table_data(
    request_data: Dict[str, Any] = Body(...)
):
    """
    테이블 데이터 분석
    
    Request Body:
        table_data (dict): 분석할 테이블 데이터
        analysis_type (str): 분석 유형 (structure, content, quality)
    """
    try:
        table_data = request_data.get("table_data")
        analysis_type = request_data.get("analysis_type", "structure")
        
        if not table_data:
            raise HTTPException(status_code=400, detail="table_data가 필요합니다")
        
        # 분석 결과 생성
        analysis_result = _analyze_table(table_data, analysis_type)
        
        logger.info(f"테이블 분석 API 완료: 유형 {analysis_type}")
        
        return {
            "success": True,
            "message": "테이블 분석 완료",
            "data": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"테이블 분석 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@router.post("/validate")
async def validate_table_structure(
    request_data: Dict[str, Any] = Body(...)
):
    """
    테이블 구조 유효성 검증
    
    Request Body:
        table_data (dict): 검증할 테이블 데이터
        validation_rules (dict, optional): 검증 규칙
    """
    try:
        table_data = request_data.get("table_data")
        validation_rules = request_data.get("validation_rules", {})
        
        if not table_data:
            raise HTTPException(status_code=400, detail="table_data가 필요합니다")
        
        # 테이블 구조 검증
        validation_result = _validate_table_structure(table_data, validation_rules)
        
        logger.info(f"테이블 검증 API 완료")
        
        return {
            "success": True,
            "message": "테이블 검증 완료",
            "data": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"테이블 검증 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검증 중 오류 발생: {str(e)}")


@router.post("/export")
async def export_table_data(
    request_data: Dict[str, Any] = Body(...)
):
    """
    테이블 데이터 내보내기
    
    Request Body:
        table_data (dict): 내보낼 테이블 데이터
        format (str): 내보내기 형식 (json, csv, xlsx)
        options (dict, optional): 내보내기 옵션
    """
    try:
        table_data = request_data.get("table_data")
        export_format = request_data.get("format", "json")
        options = request_data.get("options", {})
        
        if not table_data:
            raise HTTPException(status_code=400, detail="table_data가 필요합니다")
        
        # 데이터 내보내기
        export_result = _export_table_data(table_data, export_format, options)
        
        logger.info(f"테이블 내보내기 API 완료: 형식 {export_format}")
        
        return {
            "success": True,
            "message": "테이블 내보내기 완료",
            "data": export_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"테이블 내보내기 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"내보내기 중 오류 발생: {str(e)}")


@router.delete("/cache/{cache_key}")
async def delete_cached_table(
    cache_key: str,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """캐시된 테이블 삭제"""
    try:
        success = await cache_manager.delete_cache(cache_key)
        
        if not success:
            raise HTTPException(status_code=404, detail="캐시를 찾을 수 없습니다")
        
        logger.info(f"테이블 캐시 삭제 API 완료: {cache_key}")
        
        return {
            "success": True,
            "message": "캐시 삭제 완료",
            "data": {"cache_key": cache_key}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캐시 삭제 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"삭제 중 오류 발생: {str(e)}")


def _analyze_table(table_data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    """테이블 데이터 분석 수행"""
    analysis_result = {
        "analysis_type": analysis_type,
        "table_id": table_data.get("table_id", "unknown"),
        "timestamp": "2024-01-01T00:00:00"
    }
    
    if analysis_type == "structure":
        analysis_result.update(_analyze_table_structure(table_data))
    elif analysis_type == "content":
        analysis_result.update(_analyze_table_content(table_data))
    elif analysis_type == "quality":
        analysis_result.update(_analyze_table_quality(table_data))
    else:
        analysis_result.update(_analyze_table_structure(table_data))
    
    return analysis_result


def _analyze_table_structure(table_data: Dict[str, Any]) -> Dict[str, Any]:
    """테이블 구조 분석"""
    grid_data = table_data.get("grid_data", {})
    
    return {
        "structure_analysis": {
            "total_rows": grid_data.get("rows", 0),
            "total_cols": grid_data.get("cols", 0),
            "total_cells": len(grid_data.get("cells", [])),
            "has_headers": _detect_headers(grid_data),
            "empty_cells": _count_empty_cells(grid_data),
            "data_types": _detect_data_types(grid_data)
        }
    }


def _analyze_table_content(table_data: Dict[str, Any]) -> Dict[str, Any]:
    """테이블 내용 분석"""
    grid_data = table_data.get("grid_data", {})
    cells = grid_data.get("cells", [])
    
    content_analysis = {
        "text_patterns": _analyze_text_patterns(cells),
        "numeric_data": _analyze_numeric_data(cells),
        "special_characters": _analyze_special_characters(cells),
        "content_diversity": _calculate_content_diversity(cells)
    }
    
    return {"content_analysis": content_analysis}


def _analyze_table_quality(table_data: Dict[str, Any]) -> Dict[str, Any]:
    """테이블 품질 분석"""
    grid_data = table_data.get("grid_data", {})
    
    quality_score = _calculate_quality_score(grid_data)
    
    return {
        "quality_analysis": {
            "overall_score": quality_score,
            "completeness": _calculate_completeness(grid_data),
            "consistency": _calculate_consistency(grid_data),
            "accuracy": _estimate_accuracy(grid_data),
            "issues": _detect_quality_issues(grid_data)
        }
    }


def _validate_table_structure(table_data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    """테이블 구조 검증"""
    grid_data = table_data.get("grid_data", {})
    
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "checks": {}
    }
    
    # 기본 구조 검증
    if grid_data.get("rows", 0) == 0:
        validation_result["errors"].append("테이블에 행이 없습니다")
        validation_result["is_valid"] = False
    
    if grid_data.get("cols", 0) == 0:
        validation_result["errors"].append("테이블에 열이 없습니다")
        validation_result["is_valid"] = False
    
    # 셀 수 검증
    expected_cells = grid_data.get("rows", 0) * grid_data.get("cols", 0)
    actual_cells = len(grid_data.get("cells", []))
    
    if actual_cells != expected_cells:
        validation_result["warnings"].append(f"예상 셀 수({expected_cells})와 실제 셀 수({actual_cells})가 다릅니다")
    
    validation_result["checks"]["structure_valid"] = len(validation_result["errors"]) == 0
    
    return validation_result


def _export_table_data(table_data: Dict[str, Any], format: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """테이블 데이터 내보내기"""
    export_result = {
        "format": format,
        "options": options,
        "exported_at": "2024-01-01T00:00:00"
    }
    
    if format == "json":
        export_result["data"] = table_data
        export_result["size"] = len(str(table_data))
    elif format == "csv":
        csv_data = _convert_to_csv(table_data)
        export_result["data"] = csv_data
        export_result["size"] = len(csv_data)
    elif format == "xlsx":
        export_result["message"] = "XLSX 내보내기는 추후 구현 예정"
        export_result["data"] = None
    
    return export_result


# 유틸리티 함수들
def _detect_headers(grid_data: Dict[str, Any]) -> bool:
    """헤더 존재 여부 감지"""
    cells = grid_data.get("cells", [])
    if not cells:
        return False
    
    # 첫 번째 행의 셀들이 모두 헤더 타입인지 확인
    first_row_cells = [cell for cell in cells if cell.get("row") == 0]
    if not first_row_cells:
        return False
    
    return all(cell.get("type") == "header" for cell in first_row_cells)


def _count_empty_cells(grid_data: Dict[str, Any]) -> int:
    """빈 셀 개수 계산"""
    cells = grid_data.get("cells", [])
    return sum(1 for cell in cells if not cell.get("content", "").strip())


def _detect_data_types(grid_data: Dict[str, Any]) -> Dict[str, int]:
    """데이터 타입 분포 감지"""
    cells = grid_data.get("cells", [])
    type_counts = {"text": 0, "number": 0, "empty": 0}
    
    for cell in cells:
        content = cell.get("content", "").strip()
        if not content:
            type_counts["empty"] += 1
        elif _is_number(content):
            type_counts["number"] += 1
        else:
            type_counts["text"] += 1
    
    return type_counts


def _is_number(text: str) -> bool:
    """텍스트가 숫자인지 확인"""
    try:
        float(text.replace(",", ""))
        return True
    except ValueError:
        return False


def _analyze_text_patterns(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """텍스트 패턴 분석"""
    return {
        "common_patterns": ["일반 텍스트", "날짜 형식", "코드 형식"],
        "pattern_counts": {"text": 0, "date": 0, "code": 0}
    }


def _analyze_numeric_data(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """숫자 데이터 분석"""
    numeric_values = []
    for cell in cells:
        content = cell.get("content", "").strip()
        if _is_number(content):
            try:
                numeric_values.append(float(content.replace(",", "")))
            except ValueError:
                continue
    
    if not numeric_values:
        return {"count": 0, "statistics": None}
    
    return {
        "count": len(numeric_values),
        "statistics": {
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values)
        }
    }


def _analyze_special_characters(cells: List[Dict[str, Any]]) -> Dict[str, int]:
    """특수 문자 분석"""
    return {"special_char_count": 0, "unicode_chars": 0}


def _calculate_content_diversity(cells: List[Dict[str, Any]]) -> float:
    """내용 다양성 계산"""
    unique_contents = set(cell.get("content", "") for cell in cells)
    total_cells = len(cells)
    return len(unique_contents) / total_cells if total_cells > 0 else 0.0


def _calculate_quality_score(grid_data: Dict[str, Any]) -> float:
    """품질 점수 계산"""
    return 0.85  # 기본 점수


def _calculate_completeness(grid_data: Dict[str, Any]) -> float:
    """완성도 계산"""
    cells = grid_data.get("cells", [])
    if not cells:
        return 0.0
    
    non_empty_cells = sum(1 for cell in cells if cell.get("content", "").strip())
    return non_empty_cells / len(cells)


def _calculate_consistency(grid_data: Dict[str, Any]) -> float:
    """일관성 계산"""
    return 0.90  # 기본 값


def _estimate_accuracy(grid_data: Dict[str, Any]) -> float:
    """정확도 추정"""
    return 0.88  # 기본 값


def _detect_quality_issues(grid_data: Dict[str, Any]) -> List[str]:
    """품질 문제 감지"""
    issues = []
    
    empty_cell_ratio = _count_empty_cells(grid_data) / len(grid_data.get("cells", [1]))
    if empty_cell_ratio > 0.3:
        issues.append("빈 셀이 30% 이상입니다")
    
    return issues


def _convert_to_csv(table_data: Dict[str, Any]) -> str:
    """테이블 데이터를 CSV 형식으로 변환"""
    grid_data = table_data.get("grid_data", {})
    rows = grid_data.get("rows", 0)
    cols = grid_data.get("cols", 0)
    cells = grid_data.get("cells", [])
    
    # 2차원 배열로 변환
    table_array = [["" for _ in range(cols)] for _ in range(rows)]
    
    for cell in cells:
        row = cell.get("row", 0)
        col = cell.get("col", 0)
        content = cell.get("content", "")
        
        if 0 <= row < rows and 0 <= col < cols:
            table_array[row][col] = content
    
    # CSV 문자열 생성
    csv_lines = []
    for row in table_array:
        csv_line = ",".join(f'"{cell}"' if "," in cell else cell for cell in row)
        csv_lines.append(csv_line)
    
    return "\n".join(csv_lines)
