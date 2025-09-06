# 유틸리티 함수 정책 및 재사용 가이드라인

## 📋 개요
백엔드 시스템에서 유틸리티 함수의 작성, 구성, 재사용에 대한 정책을 정의합니다.
코드 중복을 방지하고 유지보수성을 향상시키기 위한 표준을 제시합니다.

## 🎯 유틸리티 함수 정의 기준

### 1. 유틸리티 함수로 분리해야 하는 경우

#### ✅ **필수 분리 조건**
- **2개 이상의 클래스/모듈에서 동일한 로직이 사용되는 경우**
- **15줄 이상의 독립적인 기능 블록**
- **복잡한 계산이나 변환 로직**
- **외부 라이브러리 래핑이 필요한 경우**

#### ✅ **권장 분리 조건**
- **테스트가 필요한 독립적인 기능**
- **설정값에 따라 동작이 변경되는 로직**
- **에러 처리가 복잡한 기능**
- **향후 확장 가능성이 있는 기능**

### 2. 유틸리티 함수 배치 기준

```
backend/
├── core/                           # 도메인별 유틸리티
│   ├── pdf_processor/
│   │   └── pdf_utils.py           # PDF 처리 관련 공통 함수
│   ├── table_extractor/
│   │   └── table_utils.py         # 테이블 처리 관련 공통 함수
│   └── relationship_manager/
│       └── relationship_utils.py  # 관계 설정 관련 공통 함수
├── utils/                         # 전역 공통 유틸리티
│   ├── file_utils.py             # 파일 처리 공통 함수
│   ├── validation.py             # 검증 관련 공통 함수
│   ├── date_utils.py             # 날짜/시간 관련 함수
│   └── string_utils.py           # 문자열 처리 함수
└── shared/                       # 프로젝트 전체 공유
    └── utils/
        ├── constants.py          # 상수 정의
        ├── enums.py             # 열거형 정의
        └── helpers.py           # 기타 헬퍼 함수
```

## 🔧 유틸리티 함수 작성 규칙

### 1. 클래스 기반 유틸리티

```python
# ✅ 권장: 관련 기능들을 클래스로 그룹화
class PDFUtils:
    """PDF 처리 관련 공통 유틸리티"""
    
    @staticmethod
    def get_page_count(file_path: Path) -> int:
        """PDF 페이지 수 확인"""
        pass
    
    @staticmethod
    def validate_pdf_file_basic(file_path: Path) -> bool:
        """기본 PDF 파일 검증"""
        pass
    
    @classmethod
    def estimate_processing_time(cls, file_path: Path) -> float:
        """처리 시간 예측"""
        pass
```

### 2. 함수 네이밍 규칙

```python
# ✅ 동사 + 명사 패턴
def validate_email(email: str) -> bool:
def extract_numbers(text: str) -> List[int]:
def convert_to_bytes(size: str) -> int:

# ✅ get_ 접두사 (조회)
def get_file_size(path: Path) -> int:
def get_mime_type(path: Path) -> str:

# ✅ is_ 접두사 (불린 반환)
def is_valid_pdf(path: Path) -> bool:
def is_empty_table(data: List[List[str]]) -> bool:

# ✅ calculate_/estimate_ 접두사 (계산)
def calculate_confidence(table: Any) -> float:
def estimate_memory_usage(data_size: int) -> int:
```

### 3. 타입 힌트 필수

```python
# ✅ 모든 매개변수와 반환값에 타입 힌트 명시
def process_file_list(
    files: List[Path], 
    filter_ext: Optional[str] = None
) -> Dict[str, List[Path]]:
    """파일 목록 처리"""
    pass

# ✅ Union 타입 사용 시 명확한 문서화
def parse_size_value(size: Union[str, int]) -> int:
    """
    크기 값 파싱
    
    Args:
        size: "100MB" 같은 문자열 또는 바이트 수 정수
    """
    pass
```

### 4. 예외 처리 정책

```python
# ✅ 구체적인 예외 타입 사용
def read_config_file(path: Path) -> Dict[str, Any]:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ConfigFileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise ConfigParseError(f"설정 파일 파싱 실패: {e}")
    except Exception as e:
        raise ConfigError(f"설정 파일 읽기 실패: {e}")

# ✅ 선택적 예외 처리 (safe 버전 제공)
def safe_get_page_count(file_path: Path) -> Optional[int]:
    """예외를 발생시키지 않는 안전한 페이지 수 확인"""
    try:
        return PDFUtils.get_page_count(file_path)
    except Exception:
        return None
```

## 📚 도메인별 유틸리티 가이드

### 1. PDF 처리 유틸리티 (pdf_utils.py)

```python
class PDFUtils:
    """PDF 처리 관련 공통 기능"""
    
    # ✅ 페이지 관련
    @staticmethod
    def get_page_count(file_path: Path) -> int: pass
    
    # ✅ 검증 관련
    @staticmethod
    def validate_pdf_file_basic(file_path: Path) -> bool: pass
    
    # ✅ 메타데이터 관련
    @staticmethod
    def get_pdf_info(file_path: Path) -> Optional[dict]: pass
    
    # ✅ 성능 관련
    @staticmethod
    def estimate_processing_time(file_path: Path) -> float: pass
```

### 2. 테이블 처리 유틸리티 (table_utils.py)

```python
class TableUtils:
    """테이블 처리 관련 공통 기능"""
    
    # ✅ 테이블 분석
    @staticmethod
    def calculate_empty_cell_ratio(table: List[List[str]]) -> float: pass
    
    # ✅ 테이블 변환
    @staticmethod
    def normalize_table_data(table: List[List[str]]) -> List[List[str]]: pass
    
    # ✅ 테이블 검증
    @staticmethod
    def is_valid_table_structure(table: List[List[str]]) -> bool: pass
```

### 3. 파일 처리 유틸리티 (file_utils.py)

```python
class FileUtils:
    """파일 처리 관련 공통 기능"""
    
    @staticmethod
    def ensure_directory(path: Path) -> None: pass
    
    @staticmethod
    def get_safe_filename(filename: str) -> str: pass
    
    @staticmethod
    def calculate_file_hash(file_path: Path) -> str: pass
```

## 🧪 테스트 정책

### 1. 유틸리티 함수 테스트 필수

```python
# tests/test_utils/test_pdf_utils.py
class TestPDFUtils:
    """PDF 유틸리티 함수 테스트"""
    
    def test_get_page_count_valid_pdf(self):
        """유효한 PDF 파일의 페이지 수 확인"""
        pass
    
    def test_get_page_count_invalid_file(self):
        """잘못된 파일에 대한 예외 처리"""
        pass
    
    def test_validate_pdf_file_basic_success(self):
        """기본 검증 성공 케이스"""
        pass
```

### 2. 테스트 우선순위

1. **고빈도 사용 함수** - 필수 테스트
2. **복잡한 로직 함수** - 엣지 케이스 포함
3. **예외 처리 함수** - 모든 예외 경로 테스트
4. **데이터 변환 함수** - 입출력 검증

## 📖 문서화 규칙

### 1. Docstring 표준

```python
def complex_utility_function(
    input_data: List[Dict[str, Any]], 
    config: Dict[str, Any]
) -> ProcessingResult:
    """
    복잡한 데이터 처리 유틸리티 함수
    
    여러 단계의 데이터 처리를 수행하고 결과를 반환합니다.
    
    Args:
        input_data: 처리할 데이터 목록
            - 각 딕셔너리는 'id', 'value' 키를 포함해야 함
        config: 처리 설정
            - threshold: 임계값 (기본: 0.5)
            - mode: 처리 모드 ('strict' 또는 'loose')
    
    Returns:
        ProcessingResult: 처리 결과
            - processed_count: 처리된 항목 수
            - errors: 발생한 오류 목록
            - results: 처리된 데이터
    
    Raises:
        ValidationError: 입력 데이터가 유효하지 않은 경우
        ProcessingError: 처리 중 오류가 발생한 경우
    
    Example:
        >>> config = {'threshold': 0.7, 'mode': 'strict'}
        >>> data = [{'id': 1, 'value': 0.8}, {'id': 2, 'value': 0.6}]
        >>> result = complex_utility_function(data, config)
        >>> result.processed_count
        2
    """
    pass
```

## 🔄 리팩터링 가이드

### 1. 기존 코드에서 유틸리티 추출

```python
# ❌ 중복 코드 (리팩터링 전)
class ProcessorA:
    def validate_file(self, path):
        if not path.exists(): return False
        if path.suffix != '.pdf': return False
        # ... 추가 검증
        
class ProcessorB:
    def validate_file(self, path):
        if not path.exists(): return False
        if path.suffix != '.pdf': return False
        # ... 동일한 검증

# ✅ 공통 유틸리티로 추출 (리팩터링 후)
class FileUtils:
    @staticmethod
    def validate_basic_pdf(path: Path) -> bool:
        if not path.exists(): return False
        if path.suffix.lower() != '.pdf': return False
        return True

class ProcessorA:
    def validate_file(self, path):
        if not FileUtils.validate_basic_pdf(path):
            return False
        # ... 특화된 검증

class ProcessorB:
    def validate_file(self, path):
        if not FileUtils.validate_basic_pdf(path):
            return False
        # ... 특화된 검증
```

### 2. 점진적 리팩터링 단계

1. **중복 코드 식별** - grep, 정적 분석 도구 활용
2. **공통 기능 추출** - 가장 범용적인 부분부터
3. **유틸리티 함수 작성** - 타입 힌트, 문서화 포함
4. **기존 코드 수정** - 단계적으로 교체
5. **테스트 추가** - 새로운 유틸리티 함수 검증
6. **문서 업데이트** - 사용법 가이드 작성

## 🚨 주의사항

### 1. 과도한 추상화 금지

```python
# ❌ 나쁜 예: 너무 범용적인 유틸리티
def process_anything(data: Any, config: Any) -> Any:
    """모든 것을 처리하는 함수 - 사용하지 말 것"""
    pass

# ✅ 좋은 예: 구체적이고 명확한 목적
def normalize_table_headers(headers: List[str]) -> List[str]:
    """테이블 헤더 정규화"""
    pass
```

### 2. 의존성 최소화

```python
# ❌ 나쁜 예: 무거운 의존성
def pdf_utility_with_ml(path: Path) -> Result:
    import tensorflow as tf  # 너무 무거운 의존성
    pass

# ✅ 좋은 예: 가벼운 표준 라이브러리 활용
def pdf_basic_info(path: Path) -> dict:
    import os
    import mimetypes
    pass
```

---

## 📊 현재 적용 현황

### ✅ 구현 완료된 유틸리티

1. **PDFUtils** (`backend/core/pdf_processor/pdf_utils.py`)
   - `get_page_count()` - PDF 페이지 수 확인
   - `validate_pdf_file_basic()` - 기본 PDF 파일 검증
   - `get_pdf_info()` - PDF 메타데이터 추출
   - `estimate_processing_time()` - 처리 시간 예측

### 🔧 리팩터링 완료된 코드

1. **CamelotProcessor** - PDFUtils 사용으로 중복 제거
2. **TabulaProcessor** - PDFUtils 사용으로 중복 제거  
3. **PDFPlumberProcessor** - PDFUtils 사용으로 중복 제거

### 📈 개선 효과

- **코드 중복 제거**: 약 60줄의 중복 코드 제거
- **유지보수성 향상**: 단일 책임 원칙 적용
- **테스트 용이성**: 독립적인 유틸리티 함수 테스트 가능
- **확장성 개선**: 새로운 PDF 처리기 추가 시 공통 기능 재사용

---

이 정책을 통해 코드의 재사용성을 높이고 유지보수 비용을 절감할 수 있습니다.
