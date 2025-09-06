# 건강검진 데이터 추출 시스템 (Health Data Extraction System)

PDF 파일에서 테이블을 추출하고 앵커-값 관계를 설정하는 웹 애플리케이션입니다.

## 🌟 주요 기능

- **PDF 테이블 추출**: 3가지 라이브러리 지원 (PDFPlumber, Camelot, Tabula)
- **인터랙티브 테이블**: 클릭 가능한 셀 그리드
- **앵커-값 관계 설정**: 셀 간 상대 위치 기반 관계 설정
- **모던 UI**: React 기반 반응형 사용자 인터페이스
- **재사용 가능한 컴포넌트**: 체계적인 디자인 시스템

## 🏗️ 기술 스택

### 백엔드
- **FastAPI**: 비동기 웹 프레임워크
- **Python 3.12**: 메인 언어
- **PDF 처리**: pdfplumber, camelot-py, tabula-py
- **데이터 처리**: pandas, numpy

### 프론트엔드  
- **React 18**: 프론트엔드 프레임워크
- **CSS 변수**: 디자인 토큰 시스템
- **모듈화 컴포넌트**: 재사용 가능한 UI 요소

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.12+
- Node.js 18+
- Java Runtime (Tabula 사용 시)

### 설치 및 실행

1. **저장소 클론**
```bash
git clone <repository-url>
cd Ana_test_DocumentAI
```

2. **백엔드 실행**
```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r backend/requirements.txt

# 백엔드 서버 시작
./backend_service.sh start
```

3. **프론트엔드 실행**
```bash
cd frontend
npm install
PORT=9003 npm start
```

4. **접속**
- 프론트엔드: http://localhost:9003
- 백엔드 API: http://localhost:9001

## 📖 사용법

1. **파일 업로드**: PDF 파일을 드래그 앤 드롭 또는 선택
2. **라이브러리 선택**: PDFPlumber, Camelot, Tabula 중 선택
3. **분석 실행**: 선택한 라이브러리로 테이블 추출
4. **결과 확인**: 페이지별 탭으로 추출된 테이블 확인
5. **관계 설정**: 셀 클릭으로 앵커-값 관계 설정

## 🏗️ 프로젝트 구조

```
Ana_test_DocumentAI/
├── backend/                 # FastAPI 백엔드
│   ├── api/v1/             # API 엔드포인트
│   ├── core/               # 핵심 비즈니스 로직
│   │   └── pdf_processor/  # PDF 처리 엔진
│   ├── models/             # 데이터 모델
│   ├── services/           # 서비스 레이어
│   └── utils/              # 공통 유틸리티
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # UI 컴포넌트
│   │   ├── hooks/          # React 훅
│   │   ├── services/       # API 서비스
│   │   └── styles/         # 디자인 시스템
├── documents/              # 프로젝트 문서
└── README.md
```

## 🎨 디자인 시스템

- **색상**: 회색 메인, 주황 포인트 컬러
- **폰트**: Pretendard
- **반응형**: 6단계 브레이크포인트
- **접근성**: ARIA, 키보드 네비게이션 지원

## 📊 지원하는 PDF 라이브러리

| 라이브러리 | 특징 | 권장 사용 |
|-----------|------|----------|
| **PDFPlumber** | 빠른 처리, 한국어 지원 | 일반적인 텍스트 기반 테이블 |
| **Camelot** | 높은 정확도, 격자 인식 | 명확한 격자선이 있는 테이블 |
| **Tabula** | Java 기반, 다양한 형식 | 복잡한 레이아웃의 테이블 |

## 🔧 개발 도구

### 백엔드 서비스 관리
```bash
./backend_service.sh start    # 서버 시작
./backend_service.sh stop     # 서버 중지
./backend_service.sh restart  # 서버 재시작
./backend_service.sh status   # 상태 확인
./backend_service.sh logs     # 로그 확인
```

### 코드 품질
- **Linting**: ESLint (프론트엔드), Flake8 (백엔드)
- **포맷팅**: Prettier (프론트엔드), Black (백엔드)
- **타입 체크**: TypeScript hints (백엔드)

## 📚 문서

자세한 기술 문서는 `documents/` 폴더를 참조하세요:

- [프로젝트 개요](documents/01_project_overview.md)
- [디자인 가이드라인](documents/02_design_guidelines.md)
- [기술 명세서](documents/03_technical_specs.md)
- [백엔드 아키텍처](documents/13_backend_architecture_policy.md)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🙏 감사의 말

- [PDFPlumber](https://github.com/jsvine/pdfplumber)
- [Camelot](https://github.com/camelot-dev/camelot)  
- [Tabula-py](https://github.com/chezou/tabula-py)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)

---

**건강검진 데이터 추출 시스템**으로 PDF 테이블 분석을 더 쉽고 정확하게! 🚀