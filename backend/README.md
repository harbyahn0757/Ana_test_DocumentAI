# 🚀 건강검진 데이터 추출 시스템 - 백엔드 API

FastAPI 기반의 고성능 PDF 테이블 추출 및 관계 설정 API 서버입니다.

## 📋 개요

이 백엔드는 건강검진 데이터 추출 시스템의 핵심 API를 제공합니다:
- **PDF 파일 처리**: 3가지 라이브러리(pdfplumber, camelot, tabula)를 통한 정확한 테이블 추출
- **관계 설정 관리**: 앵커-값 기반 자동 데이터 추출 패턴 저장/적용
- **파일 관리**: 업로드, 저장, 캐싱 등 파일 라이프사이클 관리
- **실시간 처리**: 비동기 처리와 백그라운드 작업 지원

## 🏗️ 아키텍처

### 계층형 구조
```
API Layer (FastAPI Routes)
    ↓
Service Layer (Business Logic)
    ↓
Core Layer (Domain Logic)
    ↓
Models Layer (Data Structures)
    ↓
Utils Layer (Common Utilities)
```

### 디렉토리 구조
```
backend/
├── app/                     # 애플리케이션 설정
│   ├── main.py             # FastAPI 앱 엔트리포인트
│   ├── config.py           # 환경설정 관리
│   └── dependencies.py     # 의존성 주입
├── api/v1/                 # API 엔드포인트
│   ├── endpoints/          # 개별 엔드포인트
│   └── router.py           # 라우터 통합
├── core/                   # 핵심 비즈니스 로직
│   ├── pdf_processor/      # PDF 처리 엔진
│   ├── table_extractor/    # 테이블 추출
│   └── relationship_manager/ # 관계 설정 관리
├── models/                 # Pydantic 데이터 모델
├── services/               # 서비스 레이어
├── utils/                  # 공통 유틸리티
├── storage/                # 저장소 관리
└── tests/                  # 테스트 코드
```

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 의존성 설치 (개발 시)
pip install -r requirements-dev.txt
```

### 2. 환경 설정
```bash
# 환경변수 파일 생성
cp .env.example .env

# .env 파일 편집
# HEALTH_EXTRACTION_SECRET_KEY=your-secret-key
# HEALTH_EXTRACTION_DEBUG=true
# HEALTH_EXTRACTION_HOST=localhost
# HEALTH_EXTRACTION_PORT=8000
```

### 3. 서버 실행
```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host localhost --port 8000

# 또는 Python으로 직접 실행
python app/main.py
```

### 4. API 문서 확인
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📚 API 문서

### 🗂️ 파일 관리 API

#### 샘플 파일 목록 조회
```http
GET /api/v1/files/samples
```

#### 파일 업로드
```http
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: [PDF 파일]
```

#### 파일 정보 조회
```http
GET /api/v1/files/{file_id}
```

### 🔄 추출 작업 API

#### 추출 작업 시작
```http
POST /api/v1/extraction/start
Content-Type: application/json

{
  "file_id": "abc123",
  "library": "pdfplumber",
  "options": {}
}
```

#### 추출 상태 조회
```http
GET /api/v1/extraction/status/{job_id}
```

### 📊 테이블 데이터 API

#### 파일의 모든 테이블 조회
```http
GET /api/v1/tables/{file_id}
```

#### 특정 페이지 테이블 조회
```http
GET /api/v1/tables/{file_id}/page/{page_number}
```

### 🔗 관계 설정 API

#### 관계 설정 목록 조회
```http
GET /api/v1/relationships
```

#### 새 관계 설정 생성
```http
POST /api/v1/relationships
Content-Type: application/json

{
  "key_name": "신장",
  "anchor_cell": {"row": 1, "col": 0, "content": "신장"},
  "value_cell": {"row": 1, "col": 1, "content": "181cm"},
  "file_id": "abc123",
  "table_id": "table_1_1"
}
```

## 🔧 설정 관리

### 환경변수
모든 설정은 환경변수 또는 `.env` 파일로 관리됩니다:

```bash
# 서버 설정
HEALTH_EXTRACTION_HOST=localhost
HEALTH_EXTRACTION_PORT=8000
HEALTH_EXTRACTION_DEBUG=true

# 보안 설정
HEALTH_EXTRACTION_SECRET_KEY=your-secret-key
HEALTH_EXTRACTION_ALLOWED_ORIGINS=["http://localhost:3000"]

# 파일 설정
HEALTH_EXTRACTION_UPLOAD_DIR=uploads
HEALTH_EXTRACTION_MAX_FILE_SIZE=104857600  # 100MB
HEALTH_EXTRACTION_ALLOWED_EXTENSIONS=[".pdf",".png",".jpg"]

# PDF 처리 설정
HEALTH_EXTRACTION_DEFAULT_EXTRACTION_LIBRARY=pdfplumber
HEALTH_EXTRACTION_SUPPORTED_LIBRARIES=["pdfplumber","camelot","tabula"]

# 캐시 설정
HEALTH_EXTRACTION_CACHE_TTL=3600
HEALTH_EXTRACTION_ENABLE_CACHE=true

# Redis 설정 (백그라운드 작업용)
HEALTH_EXTRACTION_REDIS_URL=redis://localhost:6379/0
```

### 디렉토리 구성
서버 시작 시 다음 디렉토리들이 자동으로 생성됩니다:
- `uploads/`: 업로드된 파일 저장
- `cache/`: 처리 결과 캐시
- `storage/`: 관계 설정 등 데이터 저장
- `logs/`: 로그 파일 저장

## 📦 주요 라이브러리

### PDF 처리
- **pdfplumber**: 텍스트 기반 표 추출, 한국어 지원 우수
- **camelot-py**: 격자 기반 정확한 표 구조 인식
- **tabula-py**: Java 기반 강력한 표 추출 엔진

### 웹 프레임워크
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 시리얼라이제이션

### 데이터 처리
- **Pandas**: 데이터 분석 및 조작
- **NumPy**: 수치 연산
- **Pillow**: 이미지 처리

### 백그라운드 작업
- **Celery**: 분산 작업 큐
- **Redis**: 메시지 브로커 및 캐시

## 🧪 테스트

### 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=.

# 특정 모듈 테스트
pytest tests/test_api/

# 특정 테스트 파일
pytest tests/test_api/test_files.py

# 테스트 환경에서 실행
ENVIRONMENT=test pytest
```

### 테스트 구조
```
tests/
├── test_api/           # API 엔드포인트 테스트
├── test_core/          # 핵심 로직 테스트
├── test_services/      # 서비스 레이어 테스트
├── conftest.py         # 테스트 설정
└── fixtures/           # 테스트 데이터
```

## 🔍 개발 도구

### 코드 품질
```bash
# 코드 포맷팅
black .

# 린팅
flake8

# 타입 체크
mypy .

# 정렬
isort .

# 보안 검사
bandit -r .
```

### Pre-commit 훅
```bash
# pre-commit 설치
pre-commit install

# 모든 파일에 대해 실행
pre-commit run --all-files
```

## 📊 모니터링 및 로깅

### 로그 레벨
- **DEBUG**: 상세한 디버깅 정보
- **INFO**: 일반적인 정보 (기본값)
- **WARNING**: 경고 메시지
- **ERROR**: 오류 메시지
- **CRITICAL**: 치명적 오류

### 로그 파일
- `logs/app.log`: 메인 애플리케이션 로그
- `logs/access.log`: HTTP 접근 로그
- `logs/error.log`: 오류 로그

### 헬스 체크
```http
GET /health
```

응답 예시:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-24T10:00:00Z",
  "version": "1.0.0",
  "checks": {
    "directories": {
      "upload_dir": true,
      "cache_dir": true,
      "storage_dir": true
    },
    "sample_files": {
      "count": 2,
      "available": true
    }
  }
}
```

## 🚀 배포

### Docker 배포
```bash
# Docker 이미지 빌드
docker build -t health-extraction-backend .

# 컨테이너 실행
docker run -p 8000:8000 health-extraction-backend
```

### 프로덕션 설정
```bash
# 프로덕션 모드로 실행
ENVIRONMENT=production uvicorn app.main:app --host 0.0.0.0 --port 8000

# 또는 Gunicorn 사용
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🔒 보안

### 파일 업로드 보안
- 파일 크기 제한 (기본 100MB)
- 확장자 검증
- MIME 타입 검증
- 악성 코드 스캔 (향후 추가 예정)

### API 보안
- CORS 설정
- 신뢰할 수 있는 호스트 제한
- 요청 크기 제한
- 레이트 리미팅 (향후 추가 예정)

## 🤝 기여하기

### 개발 워크플로
1. **브랜치 생성**: `git checkout -b feature/새기능`
2. **코드 작성**: 정책 문서 준수
3. **테스트 추가**: 새 기능에 대한 테스트 작성
4. **코드 품질 검사**: `black`, `flake8`, `mypy` 실행
5. **테스트 실행**: `pytest` 전체 테스트 통과
6. **Pull Request**: 상세한 설명과 함께 PR 생성

### 코딩 표준
- **Type Hints**: 모든 함수에 타입 힌트 필수
- **Docstring**: Google 스타일 독스트링 작성
- **에러 처리**: 적절한 예외 처리 및 로깅
- **테스트 커버리지**: 80% 이상 유지

## 📞 지원 및 문의

- **이슈 리포트**: GitHub Issues
- **기능 요청**: GitHub Discussions
- **보안 이슈**: 별도 연락 필요

---

**💡 Tips**:
- API 문서는 `/docs`에서 실시간으로 확인할 수 있습니다
- 개발 중에는 `DEBUG=true`로 설정하여 상세한 로그를 확인하세요
- 파일 처리 시간이 오래 걸릴 수 있으니 백그라운드 작업을 활용하세요
