# 📚 프로젝트 문서 통합 가이드

건강검진 데이터 추출 시스템의 모든 문서를 체계적으로 정리한 통합 가이드입니다.
AI 어시스턴트가 언제든지 참조할 수 있도록 프론트엔드/백엔드 모든 정보를 연결합니다.

## 🎯 프로젝트 개요

> **PDF 테이블 추출 및 관계 설정을 통한 자동화된 건강검진 데이터 처리 시스템**

### 핵심 가치
- **자동화**: 수작업 데이터 입력의 80% 시간 절약
- **정확성**: 인간 실수 최소화와 일관된 데이터 추출
- **재사용성**: 한 번 설정한 관계로 반복 자동 처리
- **확장성**: 모듈화된 구조로 기능 확장 용이

## 📖 문서 구조 및 참조 가이드

### 🏗️ 기획 및 설계 문서

| 문서 | 목적 | 주요 내용 | 참조 시점 |
|------|------|-----------|-----------|
| **[01_project_overview.md](./01_project_overview.md)** | 전체 프로젝트 이해 | 목표, 기능, 기술스택, 일정 | 프로젝트 시작 시 |
| **[02_design_guidelines.md](./02_design_guidelines.md)** | 디자인 시스템 정의 | 색상, 폰트, 컴포넌트, 규칙 | UI 작업 시 필수 |
| **[03_technical_specs.md](./03_technical_specs.md)** | 기술 아키텍처 | API 명세, 컴포넌트 구조, 데이터 플로우 | 개발 작업 시 |
| **[04_ui_wireframes.md](./04_ui_wireframes.md)** | 화면 설계 | 와이어프레임, 사용자 플로우 | UI 구현 시 |
| **[05_development_plan.md](./05_development_plan.md)** | 개발 로드맵 | 5주차 개발 계획, 마일스톤 | 진행 상황 확인 시 |

### 🎨 디자인 및 레이아웃 시스템

| 문서 | 목적 | 주요 내용 | 참조 시점 |
|------|------|-----------|-----------|
| **[09_color_system_specification.md](./09_color_system_specification.md)** | 색상 시스템 | 승인된 색상 팔레트, 사용 규칙 | 스타일링 작업 시 |
| **[10_layout_system_design.md](./10_layout_system_design.md)** | 레이아웃 구조 | 표준화된 레이아웃 컴포넌트 설계 | 레이아웃 구현 시 |
| **[11_layout_usage_guide.md](./11_layout_usage_guide.md)** | 레이아웃 활용법 | 실제 사용 예시와 가이드라인 | 레이아웃 적용 시 |
| **[12_design_policy_violations_report.md](./12_design_policy_violations_report.md)** | 정책 위반 체크리스트 | 하드코딩 색상, 폰트 등 위반 사항 | 코드 리뷰 시 |

### 🏗️ 아키텍처 및 개발 규칙

| 문서 | 목적 | 주요 내용 | 참조 시점 |
|------|------|-----------|-----------|
| **[13_backend_architecture_policy.md](./13_backend_architecture_policy.md)** | 백엔드 구조 정의 | FastAPI 아키텍처, 폴더 구조, 코딩 표준 | 백엔드 개발 시 |
| **[14_file_module_organization_rules.md](./14_file_module_organization_rules.md)** | 파일 구조 규칙 | 프론트엔드/백엔드 폴더링, 명명 규칙 | 새 파일 생성 시 |
| **[06_folder_structure_policy.md](./06_folder_structure_policy.md)** | 폴더 구조 정책 | 기능별 모듈화 원칙 | 구조 설계 시 |

### 🛠️ 개발 환경 및 도구

| 문서 | 목적 | 주요 내용 | 참조 시점 |
|------|------|-----------|-----------|
| **[07_setup_commands.md](./07_setup_commands.md)** | 환경 구축 | 설치 명령어, 서버 시작 방법 | 초기 설정 시 |
| **[08_health_data_extraction_system.md](./08_health_data_extraction_system.md)** | 핵심 기능 명세 | 앵커-값 관계 설정 시스템 상세 | 기능 구현 시 |

## 🎯 AI 어시스턴트를 위한 빠른 참조

### 🚨 필수 준수 사항
1. **디자인 정책**: [02_design_guidelines.md](./02_design_guidelines.md) - CSS 변수만 사용, 이모티콘 금지
2. **색상 제한**: [09_color_system_specification.md](./09_color_system_specification.md) - 승인된 색상만 사용
3. **레이아웃 시스템**: [10_layout_system_design.md](./10_layout_system_design.md) - 표준 레이아웃 컴포넌트 사용
4. **폴더 구조**: [14_file_module_organization_rules.md](./14_file_module_organization_rules.md) - 명명 규칙 준수

### 🔍 작업별 참조 문서

#### 🎨 프론트엔드 작업 시
```
1. 디자인 확인: 02_design_guidelines.md
2. 색상 확인: 09_color_system_specification.md  
3. 레이아웃 선택: 10_layout_system_design.md
4. 컴포넌트 구조: 03_technical_specs.md
5. 정책 위반 체크: 12_design_policy_violations_report.md
```

#### 🐍 백엔드 작업 시
```
1. 아키텍처 확인: 13_backend_architecture_policy.md
2. 폴더 구조: 14_file_module_organization_rules.md
3. API 명세: 03_technical_specs.md
4. 환경 설정: 07_setup_commands.md
```

#### 📋 기능 구현 시
```
1. 요구사항 확인: 01_project_overview.md
2. 기능 명세: 08_health_data_extraction_system.md
3. UI 설계: 04_ui_wireframes.md
4. 기술 구조: 03_technical_specs.md
```

## 🏗️ 현재 구현 상태

### ✅ 완료된 작업
- **프론트엔드 기반 구조**: React 애플리케이션 초기화
- **디자인 시스템**: CSS 변수 기반 디자인 토큰 완성
- **컴포넌트 시스템**: Button, Input, Select, Card, ConfirmDialog 등 기본 UI 컴포넌트
- **레이아웃 시스템**: BaseLayout, BasicLayout, TwoColumnLayout, MultiSectionLayout, SidebarLayout
- **사이드바 시스템**: 계층적 메뉴 구조, 홈 페이지, 데이터 추출 설정 페이지
- **추출 설정 시스템**: 키-앵커-값 매핑, 템플릿 저장/로드, 빠른 테스트 기능
- **백엔드 API**: 추출 서비스, 템플릿 관리 API 구현
- **정책 문서**: 모든 개발 가이드라인 문서 완성
- **폴더 구조**: 체계적인 frontend/shared 구조

### 🔄 최근 완료된 주요 기능
- **모달 컴포넌트 통합**: ConfirmDialog로 통일된 모달 시스템
- **추출 API 서비스**: 백엔드/프론트엔드 통합 추출 시스템
- **템플릿 관리 시스템**: 저장/로드/테스트 기능 완비
- **정책 위반 수정**: 중복 컴포넌트 제거, 이모티콘 제거

### 📋 다음 단계
1. **사용자 테스트**: 구현된 기능들의 실제 사용성 검증
2. **성능 최적화**: 대용량 PDF 처리 최적화
3. **에러 처리 강화**: 예외 상황 처리 개선
4. **문서화 완성**: API 문서 및 사용 가이드 보완

## 📚 참조 우선순위

### 🥇 최고 우선순위 (항상 확인)
- **[02_design_guidelines.md](./02_design_guidelines.md)**: 모든 UI 작업 시 필수
- **[09_color_system_specification.md](./09_color_system_specification.md)**: 색상 사용 시 필수
- **[13_backend_architecture_policy.md](./13_backend_architecture_policy.md)**: 백엔드 작업 시 필수

### 🥈 높은 우선순위 (기능 구현 시)
- **[03_technical_specs.md](./03_technical_specs.md)**: API 및 컴포넌트 구현
- **[08_health_data_extraction_system.md](./08_health_data_extraction_system.md)**: 핵심 기능 구현
- **[10_layout_system_design.md](./10_layout_system_design.md)**: 레이아웃 컴포넌트 사용

### 🥉 보통 우선순위 (필요 시 참조)
- **[01_project_overview.md](./01_project_overview.md)**: 전체 맥락 이해
- **[04_ui_wireframes.md](./04_ui_wireframes.md)**: UI 구조 확인
- **[05_development_plan.md](./05_development_plan.md)**: 일정 확인

## 🔄 문서 업데이트 이력

### 최근 업데이트 (진행 중)
- **2024-01-XX**: 통합 가이드 문서 생성
- **2024-01-XX**: 백엔드 아키텍처 정책 추가
- **2024-01-XX**: 파일 모듈 조직화 규칙 추가
- **2024-01-XX**: 메인 README 업데이트

## 🎯 사용법

### AI 어시스턴트 활용 가이드
1. **작업 시작 전**: 관련 문서들을 먼저 참조하여 정책과 규칙 확인
2. **개발 중**: 정책 위반이 없는지 체크리스트 확인
3. **작업 완료 후**: 린터 에러 확인 및 정책 준수 검증

### 개발자 활용 가이드
1. **새 기능 개발**: 01→03→08 순서로 문서 참조
2. **UI 작업**: 02→09→10 순서로 가이드라인 확인
3. **백엔드 작업**: 13→14→03 순서로 구조 파악

---

**💡 Tip**: 이 문서는 모든 프로젝트 정보의 중앙 허브입니다. 
작업 시작 전 반드시 관련 문서를 확인하여 일관성 있는 개발을 진행하세요.

### 📚 추가 정책 문서
- **[18_utility_functions_policy.md](./18_utility_functions_policy.md)** - 유틸리티 함수 정책 및 재사용 가이드라인
- **[19_frontend_backend_integration_plan.md](./19_frontend_backend_integration_plan.md)** - 프론트엔드-백엔드 통합 계획
- **[20_layout_template_policy.md](./20_layout_template_policy.md)** - 레이아웃 템플릿 정책 및 사용 가이드
- **[21_extraction_api_documentation.md](./21_extraction_api_documentation.md)** - 추출 API 서비스 문서화

### 📊 최신 구현 보고서
- **[17_final_implementation_summary.md](./17_final_implementation_summary.md)** - 최종 구현 완료 보고서
- **[16_policy_violation_and_efficiency_review.md](./16_policy_violation_and_efficiency_review.md)** - 정책 위반 및 효율성 검토