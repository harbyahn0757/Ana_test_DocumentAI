# 🏗️ 건강검진 표 분석 실서비스 구조

## 📋 전체 아키텍처

### 🎯 핵심 컴포넌트
1. **페이지별 표 추출기** - 모든 표 데이터를 체계적으로 수집
2. **키-값 매핑 GUI** - 사용자가 직접 필드 매핑 설정
3. **설정 기반 프로세서** - 저장된 설정으로 자동 추출

### 🔄 처리 흐름

#### Phase 1: 데이터 수집
```
PDF 파일 → 페이지별 분석 → 모든 표 추출 → 원본 데이터 저장
```

#### Phase 2: 매핑 설정
```
표 데이터 표시 → 사용자 매핑 → 설정 저장 → 검증
```

#### Phase 3: 자동 처리
```
설정 로드 → 자동 추출 → 품질 검증 → 결과 출력
```

## 📊 데이터 구조

### 표 데이터 구조
```json
{
  "file_id": "unique_file_id",
  "pages": [
    {
      "page_number": 1,
      "tables": [
        {
          "table_id": "p1_t1",
          "extraction_method": "camelot",
          "data": [["header1", "header2"], ["value1", "value2"]],
          "confidence": 0.95,
          "position": {"x": 100, "y": 200}
        }
      ]
    }
  ]
}
```

### 매핑 설정 구조
```json
{
  "mapping_id": "health_checkup_v1",
  "target_fields": {
    "name": {
      "table_patterns": ["성명", "이름", "name"],
      "value_patterns": ["([가-힣]+)", "([A-Za-z\\s]+)"],
      "validation": "^[가-힣A-Za-z\\s]+$"
    },
    "blood_pressure": {
      "table_patterns": ["혈압", "BP", "blood pressure"],
      "value_patterns": ["([0-9]+/[0-9]+)", "([0-9]+)"],
      "validation": "^[0-9/]+$"
    }
  }
}
```

### 처리 결과 구조
```json
{
  "extraction_id": "unique_extraction_id",
  "file_id": "source_file_id",
  "mapping_id": "applied_mapping",
  "extracted_data": {
    "name": {"value": "홍길동", "confidence": 0.98, "source": "p1_t2"},
    "blood_pressure": {"value": "120/80", "confidence": 0.92, "source": "p3_t1"}
  },
  "quality_score": 0.95,
  "timestamp": "2024-09-04T00:00:00Z"
}
```

## 🎨 GUI 설계

### 페이지 구성
1. **📄 파일 업로드 페이지**
   - 드래그앤드롭 업로드
   - 진행률 표시
   - 미리보기

2. **📊 표 데이터 보기 페이지**
   - 페이지별 표 목록
   - 표 내용 미리보기
   - 표 품질 점수

3. **🎯 매핑 설정 페이지**
   - 표 데이터와 타겟 필드 연결
   - 드래그앤드롭 매핑
   - 실시간 미리보기

4. **⚙️ 프로세싱 페이지**
   - 설정 기반 자동 추출
   - 진행률 및 로그
   - 결과 검증

5. **📋 결과 관리 페이지**
   - 추출 결과 목록
   - 품질 분석
   - 내보내기 옵션

## 🔧 기술 스택

### Backend
- **Python 3.12+**
- **FastAPI** - REST API 서버
- **SQLite/PostgreSQL** - 설정 및 결과 저장
- **Redis** - 캐싱 및 세션 관리
- **Celery** - 비동기 작업 처리

### Frontend
- **Streamlit** - 웹 GUI (현재)
- **React** - 고도화된 GUI (향후)

### Data Processing
- **camelot-py** - 주요 표 추출
- **pdfplumber** - 보조 표 추출
- **pandas** - 데이터 처리
- **scikit-learn** - 품질 평가

## 📈 확장성 고려사항

### 성능 최적화
- 페이지별 병렬 처리
- 표 추출 결과 캐싱
- 점진적 로딩

### 사용성 개선
- 자동 매핑 제안
- 템플릿 저장/로드
- 배치 처리 지원

### 품질 관리
- 추출 신뢰도 점수
- 수동 검증 도구
- 오류 패턴 학습

## 🚀 개발 계획

### Sprint 1: 기반 구조 (1주)
- [ ] 페이지별 표 추출기 구현
- [ ] 기본 데이터 구조 설계
- [ ] 캐싱 시스템 구축

### Sprint 2: 매핑 GUI (1주)
- [ ] 표 데이터 뷰어 구현
- [ ] 드래그앤드롭 매핑 UI
- [ ] 설정 저장/로드 기능

### Sprint 3: 프로세서 엔진 (1주)
- [ ] 설정 기반 추출 엔진
- [ ] 품질 평가 시스템
- [ ] 결과 검증 도구

### Sprint 4: 최적화 (1주)
- [ ] 성능 최적화
- [ ] 사용성 개선
- [ ] 테스트 및 디버깅








