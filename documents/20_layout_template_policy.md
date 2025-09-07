# 레이아웃 템플릿 정책

## 📋 업데이트 이력
**최종 업데이트**: 2025-01-27  
**현재 상태**: 레이아웃 템플릿 시스템 구축 완료, 정책 검증 완료

### 주요 변경사항
1. **레이아웃 정책 검증 완료** - 모든 페이지가 정책에 따라 올바르게 구현됨
2. **섹션 템플릿 재사용 확인** - MultiSectionLayout.Section, SectionContainer 컴포넌트 활용
3. **디자인 토큰 준수 확인** - CSS 변수 기반 스타일링, 하드코딩 값 없음
4. **App.js 파일 크기 개선 방안 수립** - 1,697줄 → 모듈화 계획

## 🎯 목적
일관된 페이지 레이아웃을 위한 표준화된 템플릿 시스템 구축

## 🏗️ 레이아웃 템플릿 분류

### 1. FullPageLayout (전체 페이지 레이아웃)
**용도**: 섹션이 없는 단일 콘텐츠 페이지
**구조**: 헤더 + 서브헤더 + 전체 콘텐츠 영역
**예시**: 웰컴 페이지, 대시보드, 설정 페이지

```javascript
<FullPageLayout
  header={<Header />}
  subHeader={<SubHeader breadcrumb={['홈']} />}
  content={<WelcomeContent />}
/>
```

### 2. MultiSectionLayout (멀티 섹션 레이아웃)
**용도**: 여러 섹션으로 나뉜 작업 페이지
**구조**: 헤더 + 서브헤더 + 3개 섹션 (1:2:1 비율)
**예시**: 데이터 추출 설정 페이지

```javascript
<MultiSectionLayout
  header={<Header />}
  subHeader={<SubHeader breadcrumb={['설정', '데이터 추출']} />}
  section1={<FileUploadSection />}
  section2={<TableDataSection />}
  section3={<KeySettingsSection />}
  sectionRatios={[1, 2, 1]}
/>
```

**중요**: MultiSectionLayout은 자체적으로 헤더와 서브헤더를 포함하는 완전한 페이지 레이아웃입니다.

### 3. TwoColumnLayout (2컬럼 레이아웃)
**용도**: 좌우 2개 영역으로 나뉜 페이지
**구조**: 헤더 + 서브헤더 + 2개 컬럼
**예시**: 비교 페이지, 상세 정보 페이지, 추출 테스트 페이지

```javascript
<TwoColumnLayout
  header={<Header />}
  subHeader={<SubHeader breadcrumb={['데이터마이닝', '추출 테스트']} />}
  leftColumn={<ExtractionTestPage />}
  rightColumn={<div></div>}
  leftRatio={1}
  rightRatio={0}
/>
```

**중요**: TwoColumnLayout은 자체적으로 헤더와 서브헤더를 포함하는 완전한 페이지 레이아웃입니다.

## 🎨 디자인 토큰 기반 스타일링

### 색상 시스템
```css
/* 배경 색상 */
--color-background: #F9FAFB;        /* 기본 배경 */
--color-surface: #FFFFFF;           /* 카드/패널 배경 */
--color-primary: #6B7280;           /* 메인 색상 */
--color-accent: #F97316;            /* 포인트 색상 */

/* 텍스트 색상 */
--color-text: #111827;              /* 기본 텍스트 */
--color-text-secondary: #6B7280;    /* 보조 텍스트 */
--color-text-inverse: #FFFFFF;      /* 역색 텍스트 */
```

### 간격 시스템 (8px 기준)
```css
--spacing-1: 4px;      /* xs */
--spacing-2: 8px;      /* sm */
--spacing-3: 12px;     /* md-sm */
--spacing-4: 16px;     /* md */
--spacing-6: 24px;     /* lg */
--spacing-8: 32px;     /* xl */
--spacing-12: 48px;    /* 2xl */
```

### 타이포그래피
```css
/* 폰트 크기 */
--font-size-xs: 12px;
--font-size-sm: 14px;
--font-size-base: 16px;
--font-size-lg: 18px;
--font-size-xl: 20px;
--font-size-2xl: 24px;
--font-size-3xl: 32px;

/* 폰트 두께 */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

## 📐 레이아웃 구조 규칙

### 1. 헤더 구조
- **메인 헤더**: 항상 `<Header />` 컴포넌트 사용
- **서브 헤더**: `<SubHeader breadcrumb={[...]} />` 사용
- **브레드크럼**: 페이지 계층 구조 표시

### 2. 콘텐츠 영역
- **전체 높이 활용**: `height: calc(100vh - var(--header-height) - var(--sub-header-height))`
- **스크롤 처리**: 콘텐츠 영역 내부에서만 스크롤
- **반응형**: 모바일에서 자동 조정

### 3. 컴포넌트 재사용성
- **표준 컴포넌트**: Header, SubHeader, Button, Card 등
- **토큰 기반**: 하드코딩된 값 금지
- **일관성**: 동일한 역할의 컴포넌트는 동일한 스타일

## 🚫 금지 사항

### 1. 하드코딩 금지
- 색상값 직접 입력 금지
- 크기/간격 직접 입력 금지
- 폰트 크기 직접 입력 금지

### 2. 인라인 스타일 금지
- `style={{}}` 사용 금지
- CSS 클래스 기반 스타일링만 허용

### 3. 컴포넌트 중복 구현 금지
- 기존 컴포넌트 무시하고 직접 코딩 금지
- 재사용 가능한 컴포넌트 우선 사용

## ✅ 사용 예시

### 웰컴 페이지
```javascript
const WelcomePage = () => (
  <FullPageLayout
    header={<Header />}
    subHeader={<SubHeader breadcrumb={['홈']} />}
    content={
      <div className="welcome-content">
        <h1>건강검진 데이터 추출 시스템</h1>
        <p>PDF 표에서 키-값 관계를 설정하여 자동 데이터 추출</p>
        <Button variant="primary">시작하기</Button>
      </div>
    }
  />
);
```

### 데이터 추출 설정 페이지
```javascript
const DataExtractionPage = () => (
  <MultiSectionLayout
    header={<Header />}
    subHeader={<SubHeader breadcrumb={['설정', '데이터 추출']} />}
    section1={<FileUploadSection />}
    section2={<TableDataSection />}
    section3={<KeySettingsSection />}
  />
);
```

## 📱 반응형 규칙

### 브레이크포인트
- **Desktop**: 1200px+
- **Tablet**: 768px - 1199px
- **Mobile**: 767px 이하

### 모바일 대응
- 폰트 크기 자동 축소
- 간격 자동 조정
- 세로 스택 레이아웃 전환
- 터치 친화적 버튼 크기

## 📊 현재 구현 상태 검증 (2025-01-27)

### ✅ 정책 준수 확인 완료

#### 1. 페이지별 레이아웃 사용법
- **설정 페이지**: `MultiSectionLayout` (3섹션, 1:2:1 비율) ✅
- **테스트 페이지**: `MultiSectionLayout` (2섹션, 1:1:0 비율) ✅  
- **웰컴 페이지**: `FullPageLayout` ✅

#### 2. 섹션 템플릿 재사용
- `MultiSectionLayout.Section` 컴포넌트 활용 ✅
- `SectionContainer` 컴포넌트 활용 ✅
- `|` 주황색 처리 자동 적용 ✅
- `responsive-font-compact-lg` 클래스 적용 ✅

#### 3. 디자인 토큰 준수
- CSS 변수 기반 스타일링 ✅
- 하드코딩된 값 사용 안함 ✅
- 색상/간격/폰트 토큰 사용 ✅

### 🔧 App.js 파일 크기 개선 방안

**현재 상태**: 1,697줄 (매우 큰 파일)

**개선 계획**:
1. **페이지별 컴포넌트 분리**
   - `DataExtractionPage.js`
   - `ExtractionTestPage.js` 
   - `WelcomePage.js`

2. **섹션 콘텐츠 컴포넌트 분리**
   - `FileUploadSection.js`
   - `TableDataSection.js`
   - `KeySelectionSection.js`

3. **훅 분리**
   - `useFileManagement.js`
   - `useAnalysis.js`
   - `useTemplateManagement.js`

4. **상수 분리**
   - `constants/menuItems.js`
   - `constants/apiEndpoints.js`

이 정책에 따라 모든 페이지 레이아웃을 구현해야 합니다.
