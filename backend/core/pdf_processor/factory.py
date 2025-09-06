"""
PDF 프로세서 팩토리

다양한 PDF 처리 라이브러리의 인스턴스를 생성하고 관리
"""

from typing import Dict, Type, Optional, Any, List
import logging

from .base import PDFProcessorInterface, UnsupportedLibraryError
from .pdfplumber_processor import PDFPlumberProcessor
from .camelot_processor import CamelotProcessor
from .tabula_processor import TabulaProcessor

logger = logging.getLogger(__name__)


class PDFProcessorFactory:
    """PDF 프로세서 팩토리 클래스"""
    
    # 지원하는 프로세서 클래스 매핑
    _processors: Dict[str, Type[PDFProcessorInterface]] = {
        "pdfplumber": PDFPlumberProcessor,
        "camelot": CamelotProcessor, 
        "tabula": TabulaProcessor
    }
    
    # 라이브러리별 기본 설정
    _default_options: Dict[str, Dict[str, Any]] = {
        "pdfplumber": {
            "table_settings": {
                "vertical_strategy": "lines_strict",
                "horizontal_strategy": "lines_strict",
                "edge_min_length": 3,
                "intersection_tolerance": 1
            }
        },
        "camelot": {
            "flavor": "lattice",
            "edge_tol": 50,
            "row_tol": 2,
            "column_tol": 0
        },
        "tabula": {
            "lattice": True,
            "stream": False,
            "guess": True,
            "multiple_tables": True,
            "silent": True
        }
    }
    
    # 라이브러리별 설명
    _descriptions: Dict[str, str] = {
        "pdfplumber": "텍스트 기반 표 추출, 한국어 지원 우수, 복잡한 레이아웃 처리 가능",
        "camelot": "격자 기반 정확한 표 구조 인식, 높은 정확도, 선이 있는 테이블에 최적화",
        "tabula": "Java 기반 강력한 엔진, 다양한 추출 모드, 대용량 문서 처리 우수"
    }
    
    @classmethod
    def create_processor(
        cls, 
        library: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> PDFProcessorInterface:
        """
        지정된 라이브러리로 PDF 프로세서 생성
        
        Args:
            library: 사용할 라이브러리 이름
            options: 라이브러리별 옵션 설정
            
        Returns:
            PDFProcessorInterface: 생성된 프로세서 인스턴스
            
        Raises:
            UnsupportedLibraryError: 지원하지 않는 라이브러리인 경우
        """
        if library not in cls._processors:
            raise UnsupportedLibraryError(library, cls.get_supported_libraries())
        
        # 기본 옵션과 사용자 옵션 병합
        merged_options = cls._default_options.get(library, {}).copy()
        if options:
            merged_options.update(options)
        
        # 프로세서 인스턴스 생성
        processor_class = cls._processors[library]
        processor = processor_class(merged_options)
        
        logger.info(f"{library} 프로세서 생성 완료")
        return processor
    
    @classmethod
    def get_supported_libraries(cls) -> List[str]:
        """지원하는 라이브러리 목록 반환"""
        return list(cls._processors.keys())
    
    @classmethod
    def get_library_info(cls, library: str) -> Dict[str, Any]:
        """특정 라이브러리의 정보 반환"""
        if library not in cls._processors:
            raise UnsupportedLibraryError(library, cls.get_supported_libraries())
        
        return {
            "name": library,
            "description": cls._descriptions.get(library, ""),
            "default_options": cls._default_options.get(library, {}),
            "processor_class": cls._processors[library].__name__
        }
    
    @classmethod
    def get_all_libraries_info(cls) -> Dict[str, Dict[str, Any]]:
        """모든 라이브러리의 정보 반환"""
        return {
            library: cls.get_library_info(library)
            for library in cls.get_supported_libraries()
        }
    
    @classmethod
    def validate_library(cls, library: str) -> bool:
        """라이브러리가 지원되는지 확인"""
        return library in cls._processors
    
    @classmethod
    def check_library_availability(cls, library: str) -> Dict[str, Any]:
        """라이브러리 사용 가능성 확인
        
        라이브러리가 설치되어 있고 정상 작동하는지 확인
        """
        if not cls.validate_library(library):
            return {
                "library": library,
                "available": False,
                "error": f"지원하지 않는 라이브러리: {library}"
            }
        
        try:
            # 임시 프로세서 생성으로 라이브러리 동작 확인
            processor = cls.create_processor(library)
            version = processor.get_library_version()
            capabilities = processor.get_capabilities()
            
            return {
                "library": library,
                "available": True,
                "version": version,
                "capabilities": capabilities,
                "description": cls._descriptions.get(library, "")
            }
            
        except ImportError as e:
            return {
                "library": library,
                "available": False,
                "error": f"라이브러리 import 실패: {str(e)}"
            }
        except Exception as e:
            return {
                "library": library,
                "available": False,
                "error": f"라이브러리 초기화 실패: {str(e)}"
            }
    
    @classmethod
    def get_availability_report(cls) -> Dict[str, Any]:
        """모든 라이브러리의 사용 가능성 리포트"""
        report = {
            "total_libraries": len(cls.get_supported_libraries()),
            "available_libraries": [],
            "unavailable_libraries": [],
            "details": {}
        }
        
        for library in cls.get_supported_libraries():
            availability = cls.check_library_availability(library)
            report["details"][library] = availability
            
            if availability["available"]:
                report["available_libraries"].append(library)
            else:
                report["unavailable_libraries"].append(library)
        
        report["available_count"] = len(report["available_libraries"])
        report["unavailable_count"] = len(report["unavailable_libraries"])
        
        return report
    
    @classmethod
    def recommend_library(cls, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """요구사항에 따른 라이브러리 추천
        
        Args:
            requirements: 요구사항
                - accuracy_priority: 정확도 우선 여부
                - speed_priority: 속도 우선 여부
                - korean_text: 한국어 텍스트 포함 여부
                - complex_layout: 복잡한 레이아웃 여부
                - has_grid_lines: 격자선 존재 여부
        """
        recommendations = []
        
        # 기본 가용성 확인
        availability_report = cls.get_availability_report()
        available_libs = availability_report["available_libraries"]
        
        if not available_libs:
            return {
                "recommended": None,
                "alternatives": [],
                "reason": "사용 가능한 라이브러리가 없습니다"
            }
        
        # 요구사항별 점수 계산
        scores = {}
        
        for library in available_libs:
            score = 0
            reasons = []
            
            if library == "pdfplumber":
                score += 30  # 기본 점수
                if requirements.get("korean_text", False):
                    score += 20
                    reasons.append("한국어 지원 우수")
                if requirements.get("complex_layout", False):
                    score += 15
                    reasons.append("복잡한 레이아웃 처리 가능")
                if not requirements.get("speed_priority", False):
                    score += 10
                    reasons.append("안정적인 추출 품질")
            
            elif library == "camelot":
                score += 25  # 기본 점수
                if requirements.get("accuracy_priority", False):
                    score += 25
                    reasons.append("높은 정확도")
                if requirements.get("has_grid_lines", False):
                    score += 20
                    reasons.append("격자선 기반 정확한 인식")
                if not requirements.get("korean_text", False):
                    score += 5
                    reasons.append("영문 테이블에 최적화")
            
            elif library == "tabula":
                score += 20  # 기본 점수
                if requirements.get("speed_priority", False):
                    score += 20
                    reasons.append("빠른 처리 속도")
                if requirements.get("accuracy_priority", False):
                    score += 15
                    reasons.append("Java 엔진 기반 안정성")
                score += 10  # 범용성
                reasons.append("다양한 추출 모드 지원")
            
            scores[library] = {
                "score": score,
                "reasons": reasons
            }
        
        # 점수 순으로 정렬
        sorted_libs = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        if sorted_libs:
            recommended = sorted_libs[0]
            alternatives = sorted_libs[1:]
            
            return {
                "recommended": {
                    "library": recommended[0],
                    "score": recommended[1]["score"],
                    "reasons": recommended[1]["reasons"],
                    "description": cls._descriptions.get(recommended[0], "")
                },
                "alternatives": [
                    {
                        "library": alt[0],
                        "score": alt[1]["score"], 
                        "reasons": alt[1]["reasons"],
                        "description": cls._descriptions.get(alt[0], "")
                    }
                    for alt in alternatives
                ],
                "requirements_considered": requirements
            }
        
        return {
            "recommended": None,
            "alternatives": [],
            "reason": "추천할 수 있는 라이브러리가 없습니다"
        }
    
    @classmethod
    def create_multi_processor(cls, libraries: List[str], options: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, PDFProcessorInterface]:
        """여러 라이브러리의 프로세서를 동시에 생성
        
        Args:
            libraries: 생성할 라이브러리 목록
            options: 라이브러리별 옵션 (키: 라이브러리명, 값: 옵션)
            
        Returns:
            Dict[str, PDFProcessorInterface]: 라이브러리명을 키로 하는 프로세서 딕셔너리
        """
        processors = {}
        
        for library in libraries:
            try:
                lib_options = options.get(library) if options else None
                processor = cls.create_processor(library, lib_options)
                processors[library] = processor
                logger.info(f"{library} 프로세서 생성 성공")
            except Exception as e:
                logger.error(f"{library} 프로세서 생성 실패: {e}")
                continue
        
        return processors
    
    @classmethod
    def get_processor_comparison(cls) -> Dict[str, Any]:
        """지원하는 모든 프로세서의 비교 정보"""
        return {
            "libraries": cls.get_all_libraries_info(),
            "comparison_matrix": {
                "accuracy": {"camelot": "높음", "pdfplumber": "중간", "tabula": "높음"},
                "speed": {"camelot": "중간", "pdfplumber": "느림", "tabula": "빠름"},
                "korean_support": {"camelot": "보통", "pdfplumber": "우수", "tabula": "보통"},
                "complex_layout": {"camelot": "우수", "pdfplumber": "우수", "tabula": "보통"},
                "grid_detection": {"camelot": "우수", "pdfplumber": "좋음", "tabula": "좋음"},
                "memory_usage": {"camelot": "높음", "pdfplumber": "중간", "tabula": "중간"}
            },
            "use_cases": {
                "한국어 의료 문서": "pdfplumber",
                "격자가 명확한 표": "camelot", 
                "대용량 문서 처리": "tabula",
                "복잡한 레이아웃": "pdfplumber",
                "높은 정확도 필요": "camelot"
            }
        }
