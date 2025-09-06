# 현재 화면 기능 분석 및 백엔드 연동 계획

## 📊 현재 프론트엔드 기능 분석

### 🎯 구현된 UI 구조
```
Header
├── 브랜드명: "건강검진 데이터 추출 시스템"
├── 서브타이틀: "빠르고 정확한 PDF 데이터 분석"
└── 액션 버튼들 (설정, 내보내기, 도움말)

SubHeader
└── 브레드크럼: "건강검진 데이터 추출 시스템 • 파일 분석 및 관계 설정"

3-Section Layout (1:2:1 비율)
├── Section 1: 파일 업로드 & 처리
├── Section 2: 테이블 데이터 (중앙 메인)
└── Section 3: 관계 설정
```

### 📋 섹션별 기능 상세

#### Section 1: 파일 업로드 & 처리
**현재 구현된 UI:**
- PDF 파일 선택 드롭다운 (samples 폴더 파일 목록)
- 추출 라이브러리 선택 (pdfplumber, camelot, tabula)
- "분석 시작" 버튼
- 상태 표시 카드 (상태: 대기 중, 진행률: 0%)

**필요한 백엔드 API:**
```python
# 파일 관련 API
GET  /api/v1/files/list              # 사용 가능한 파일 목록
POST /api/v1/files/upload            # 새 파일 업로드
POST /api/v1/extract/start           # 추출 작업 시작
GET  /api/v1/extract/status/{job_id} # 추출 진행 상태
```

#### Section 2: 테이블 데이터
**현재 구현된 UI:**
- 플레이스홀더 영역 (PDF 아이콘, 안내 메시지)
- 테이블 그리드 컨테이너 (실제 그리드는 구현 예정)

**필요한 백엔드 API:**
```python
# 테이블 데이터 API
GET /api/v1/tables/{file_id}         # 파일의 모든 테이블 데이터
GET /api/v1/tables/{file_id}/page/{page} # 특정 페이지 테이블
```

**예상 데이터 구조:**
```json
{
  "file_id": "abc123",
  "total_pages": 8,
  "total_tables": 44,
  "pages": [
    {
      "page_number": 1,
      "tables": [
        {
          "table_id": "table_1_1",
          "headers": ["검사항목", "결과", "참고치"],
          "rows": [
            ["신장", "181cm", "160-180cm"],
            ["체중", "75kg", "60-80kg"]
          ],
          "grid_data": {
            "rows": 3,
            "cols": 3,
            "cells": [
              {"row": 0, "col": 0, "content": "검사항목", "type": "header"},
              {"row": 1, "col": 0, "content": "신장", "type": "data"},
              {"row": 1, "col": 1, "content": "181cm", "type": "data"}
            ]
          }
        }
      ]
    }
  ]
}
```

#### Section 3: 관계 설정
**현재 구현된 UI:**
- 키 관리 영역 (키 입력, 키 추가 버튼, 키 목록)
- 관계 설정 상태 표시 (선택된 키, 앵커 셀, 값 셀, 관계)
- "관계 저장" 버튼 (비활성화)

**필요한 백엔드 API:**
```python
# 관계 설정 API
GET  /api/v1/relationships           # 저장된 관계 설정 목록
POST /api/v1/relationships          # 새 관계 설정 저장
PUT  /api/v1/relationships/{id}     # 관계 설정 수정
DELETE /api/v1/relationships/{id}   # 관계 설정 삭제
POST /api/v1/extract/apply-relationships # 관계 설정 적용하여 데이터 추출
```

**관계 설정 데이터 구조:**
```json
{
  "relationship_id": "rel_001",
  "key_name": "신장",
  "anchor_pattern": "신장",
  "value_position": {
    "relative_position": "right",
    "offset": 1,
    "same_row": true
  },
  "file_template": "건강검진표_템플릿_A",
  "created_at": "2024-01-24T10:00:00Z"
}
```

## 🏗️ 백엔드 아키텍처 계획

### 📁 폴더 구조 설계
```
backend/
├── app/
│   ├── main.py                 # FastAPI 앱 엔트리포인트
│   ├── config.py              # 설정 관리
│   └── dependencies.py        # 의존성 주입
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── files.py       # 파일 관련 API
│       │   ├── extraction.py  # 추출 관련 API
│       │   ├── tables.py      # 테이블 데이터 API
│       │   └── relationships.py # 관계 설정 API
│       └── router.py          # 라우터 통합
├── core/
│   ├── pdf_processor/
│   │   ├── base.py           # 추상 클래스
│   │   ├── pdfplumber_processor.py
│   │   ├── camelot_processor.py
│   │   └── tabula_processor.py
│   ├── table_extractor/
│   │   ├── extractor.py      # 메인 추출기
│   │   └── grid_converter.py # 그리드 변환기
│   └── relationship_manager/
│       ├── manager.py        # 관계 관리자
│       └── pattern_matcher.py # 패턴 매칭
├── models/
│   ├── file_models.py        # 파일 관련 모델
│   ├── table_models.py       # 테이블 모델
│   ├── relationship_models.py # 관계 모델
│   └── extraction_models.py  # 추출 작업 모델
├── services/
│   ├── file_service.py       # 파일 관리 서비스
│   ├── extraction_service.py # 추출 서비스
│   └── relationship_service.py # 관계 관리 서비스
├── storage/
│   ├── file_storage.py       # 파일 저장소
│   └── cache_manager.py      # 캐시 관리
└── utils/
    ├── file_utils.py         # 파일 유틸리티
    └── validation.py         # 검증 유틸리티
```

### 🔄 API 엔드포인트 상세 설계

#### 1. 파일 관리 API
```python
# api/v1/endpoints/files.py

@router.get("/list")
async def get_file_list() -> List[FileInfo]:
    """samples 폴더의 파일 목록 반환"""
    pass

@router.post("/upload")
async def upload_file(file: UploadFile) -> FileUploadResponse:
    """새 파일 업로드"""
    pass

@router.get("/{file_id}")
async def get_file_info(file_id: str) -> FileInfo:
    """파일 정보 조회"""
    pass
```

#### 2. 추출 작업 API
```python
# api/v1/endpoints/extraction.py

@router.post("/start")
async def start_extraction(request: ExtractionRequest) -> ExtractionJobResponse:
    """추출 작업 시작"""
    # 백그라운드 작업으로 PDF 처리
    pass

@router.get("/status/{job_id}")
async def get_extraction_status(job_id: str) -> ExtractionStatus:
    """추출 진행 상태 조회"""
    pass

@router.get("/result/{job_id}")
async def get_extraction_result(job_id: str) -> ExtractionResult:
    """추출 완료 결과 조회"""
    pass
```

#### 3. 테이블 데이터 API
```python
# api/v1/endpoints/tables.py

@router.get("/{file_id}")
async def get_tables(file_id: str) -> TableDataResponse:
    """파일의 모든 테이블 데이터"""
    pass

@router.get("/{file_id}/page/{page}")
async def get_page_tables(file_id: str, page: int) -> PageTableData:
    """특정 페이지의 테이블 데이터"""
    pass

@router.get("/{file_id}/table/{table_id}")
async def get_table_details(file_id: str, table_id: str) -> TableDetails:
    """특정 테이블의 상세 데이터"""
    pass
```

#### 4. 관계 설정 API
```python
# api/v1/endpoints/relationships.py

@router.get("/")
async def get_relationships() -> List[RelationshipConfig]:
    """저장된 관계 설정 목록"""
    pass

@router.post("/")
async def create_relationship(config: RelationshipCreateRequest) -> RelationshipConfig:
    """새 관계 설정 생성"""
    pass

@router.put("/{relationship_id}")
async def update_relationship(relationship_id: str, config: RelationshipUpdateRequest) -> RelationshipConfig:
    """관계 설정 수정"""
    pass

@router.delete("/{relationship_id}")
async def delete_relationship(relationship_id: str) -> StatusResponse:
    """관계 설정 삭제"""
    pass

@router.post("/apply")
async def apply_relationships(request: ApplyRelationshipsRequest) -> ExtractionResult:
    """관계 설정 적용하여 데이터 추출"""
    pass
```

### 📊 데이터 모델 설계

#### 파일 관련 모델
```python
# models/file_models.py

class FileInfo(BaseModel):
    file_id: str
    file_name: str
    file_path: str
    file_size: int
    uploaded_at: datetime
    status: FileStatus

class FileUploadResponse(BaseModel):
    file_id: str
    message: str
    status: str

class ExtractionRequest(BaseModel):
    file_id: str
    library: ExtractionLibrary  # pdfplumber, camelot, tabula
    options: Optional[Dict[str, Any]] = None
```

#### 테이블 관련 모델
```python
# models/table_models.py

class CellData(BaseModel):
    row: int
    col: int
    content: str
    type: CellType  # header, data, empty
    
class TableData(BaseModel):
    table_id: str
    page_number: int
    headers: List[str]
    rows: List[List[str]]
    grid_data: GridData
    
class GridData(BaseModel):
    rows: int
    cols: int
    cells: List[CellData]

class TableDataResponse(BaseModel):
    file_id: str
    total_pages: int
    total_tables: int
    pages: List[PageTableData]
```

#### 관계 설정 모델
```python
# models/relationship_models.py

class ValuePosition(BaseModel):
    relative_position: RelativePosition  # right, left, below, above
    offset: int
    same_row: bool
    same_col: bool

class RelationshipConfig(BaseModel):
    relationship_id: str
    key_name: str
    anchor_pattern: str
    value_position: ValuePosition
    file_template: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class RelationshipCreateRequest(BaseModel):
    key_name: str
    anchor_cell: CellPosition
    value_cell: CellPosition
    file_id: str
    table_id: str
```

### 🔧 핵심 서비스 로직

#### 1. PDF 처리 서비스
```python
# services/extraction_service.py

class ExtractionService:
    def __init__(self):
        self.processors = {
            'pdfplumber': PDFPlumberProcessor(),
            'camelot': CamelotProcessor(),
            'tabula': TabulaProcessor()
        }
    
    async def extract_tables(self, file_path: str, library: str) -> ExtractionResult:
        """PDF에서 테이블 추출"""
        processor = self.processors.get(library)
        if not processor:
            raise ValueError(f"Unsupported library: {library}")
        
        # 백그라운드 작업으로 처리
        job_id = self._create_job()
        await self._process_in_background(job_id, processor, file_path)
        return {"job_id": job_id, "status": "started"}
    
    def _convert_to_grid(self, tables: List[TableData]) -> List[GridData]:
        """테이블을 그리드 형태로 변환"""
        pass
```

#### 2. 관계 설정 서비스
```python
# services/relationship_service.py

class RelationshipService:
    def __init__(self):
        self.storage_path = "storage/relationships.json"
    
    def create_relationship(self, anchor_cell: CellPosition, value_cell: CellPosition, key_name: str) -> RelationshipConfig:
        """앵커와 값 셀 위치로부터 관계 설정 생성"""
        relative_position = self._calculate_relative_position(anchor_cell, value_cell)
        
        config = RelationshipConfig(
            relationship_id=str(uuid.uuid4()),
            key_name=key_name,
            anchor_pattern=anchor_cell.content,
            value_position=relative_position,
            created_at=datetime.now()
        )
        
        self._save_relationship(config)
        return config
    
    def apply_relationships(self, file_id: str, relationships: List[RelationshipConfig]) -> Dict[str, str]:
        """관계 설정을 적용하여 데이터 추출"""
        pass
```

### 🚀 구현 우선순위

#### Phase 1: 기본 인프라 (1주)
1. **백엔드 폴더 구조 생성**
2. **FastAPI 앱 초기화**
3. **기본 모델 정의**
4. **파일 관리 API 구현**

#### Phase 2: PDF 처리 (1주)
1. **PDF 프로세서 팩토리 구현**
2. **3가지 라이브러리 통합**
3. **테이블 추출 API 구현**
4. **그리드 변환 로직 구현**

#### Phase 3: 프론트엔드 연동 (1주)
1. **API 클라이언트 구현**
2. **상태 관리 추가**
3. **테이블 그리드 컴포넌트 구현**
4. **실시간 업데이트 구현**

#### Phase 4: 관계 설정 (1주)
1. **관계 설정 API 구현**
2. **패턴 매칭 로직 구현**
3. **관계 설정 UI 완성**
4. **자동 추출 기능 구현**

#### Phase 5: 최적화 및 완성 (1주)
1. **성능 최적화**
2. **에러 처리 강화**
3. **사용자 가이드 완성**
4. **테스트 및 배포**

## 📋 필요한 라이브러리 목록

### 백엔드 requirements.txt
```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# PDF Processing
pdfplumber==0.10.3
camelot-py[cv]==0.11.0
tabula-py==2.8.2

# Data Processing
pandas==2.1.4
numpy==1.26.2

# Async & Background Jobs
celery==5.3.4
redis==5.0.1

# File Handling
python-multipart==0.0.6
aiofiles==23.2.1

# Validation & Serialization
pydantic==2.5.0
pydantic-settings==2.1.0

# Utils
python-jose[cryptography]==3.3.0
uuid==1.30
```

### 프론트엔드 추가 패키지
```json
{
  "axios": "^1.6.0",
  "react-query": "^3.39.3",
  "react-table": "^7.8.0",
  "react-virtualized": "^9.22.5"
}
```

## 🎯 다음 단계 액션 아이템

1. **백엔드 폴더 구조 생성**: 정의된 구조대로 디렉토리 및 초기 파일 생성
2. **requirements.txt 작성**: 필요한 모든 라이브러리 정의
3. **FastAPI 앱 초기화**: 기본 서버 구동 및 CORS 설정
4. **파일 관리 API 구현**: samples 폴더 파일 목록 API부터 시작
5. **프론트엔드 API 클라이언트**: axios 기반 API 호출 유틸리티 구현

이 계획을 바탕으로 체계적이고 단계적인 백엔드 구현을 진행할 수 있습니다.
