# 디자인 가이드라인

## 📋 업데이트 이력
**최종 업데이트**: 2025-01-XX  
**현재 상태**: 디자인 토큰 시스템 구축 완료, 컴포넌트 상수화 진행 중

### 주요 변경사항
1. **디자인 토큰 시스템 도입** (design-tokens.css)
2. **이모티콘 완전 제거** - 전문적인 UI 구현
3. **색상 시스템 정책 수립** - 승인된 색상만 사용
4. **동적 반응형 레이아웃** - 2:1 비율, 화면 높이 기준 조정
5. **컴포넌트 상수화** - 재사용 가능한 디자인 시스템

## 🎨 디자인 시스템

### 색상 팔레트

#### 주요 색상
- **메인 색상**: 회색 계열 (#6B7280, #4B5563, #374151)
- **포인트 색상**: 주황 (#F97316, #EA580C, #FB923C)
- **배경 색상**: 
  - 기본 배경: #F9FAFB
  - 카드 배경: #FFFFFF
  - 어두운 배경: #F3F4F6

#### 상태 색상
- **성공**: #10B981 (Green)
- **경고**: #F59E0B (Amber)
- **오류**: #EF4444 (Red)
- **정보**: #3B82F6 (Blue)

#### 텍스트 색상
- **기본 텍스트**: #111827
- **보조 텍스트**: #6B7280
- **비활성 텍스트**: #9CA3AF
- **링크**: #F97316 (주황)

### 타이포그래피

#### 폰트 패밀리
```css
font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 
             'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

#### 폰트 크기 스케일
- **h1**: 32px (2rem) - 페이지 제목
- **h2**: 24px (1.5rem) - 섹션 제목
- **h3**: 20px (1.25rem) - 하위 섹션 제목
- **body**: 16px (1rem) - 기본 텍스트
- **small**: 14px (0.875rem) - 보조 텍스트
- **caption**: 12px (0.75rem) - 캡션

#### 폰트 두께
- **Light**: 300
- **Regular**: 400
- **Medium**: 500
- **Semibold**: 600
- **Bold**: 700

### 여백 시스템

#### 스페이싱 스케일 (8px 기준)
```css
--spacing-1: 8px;
--spacing-2: 16px;
--spacing-3: 24px;
--spacing-4: 32px;
--spacing-5: 40px;
--spacing-6: 48px;
```

#### 컴포넌트별 여백
- **카드 패딩**: 24px
- **버튼 패딩**: 12px 24px
- **입력 필드 패딩**: 12px 16px
- **섹션 간격**: 32px

### 모서리 반경

- **작은 요소**: 4px (버튼, 입력 필드)
- **카드**: 8px
- **모달**: 12px
- **이미지**: 6px

### 그림자

#### 카드 그림자
```css
box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 
            0 1px 2px 0 rgba(0, 0, 0, 0.06);
```

#### 호버 그림자
```css
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 
            0 2px 4px -1px rgba(0, 0, 0, 0.06);
```

#### 포커스 그림자
```css
box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
```

## 🔧 디자인 토큰 시스템

### 상수화된 디자인 값
모든 디자인 요소는 `design-tokens.css`에서 상수로 관리됩니다.

#### 색상 토큰
```css
/* 메인 색상 */
--color-primary: #6B7280;
--color-accent: #F97316;
--color-background: #F9FAFB;
--color-surface: #FFFFFF;

/* 특수 기능 색상 */
--color-anchor: #3B82F6;        /* 앵커(기준점) */
--color-value: #F97316;         /* 값 */
--color-selected: #10B981;      /* 선택됨 */
```

#### 타이포그래피 토큰
```css
/* 폰트 크기 - 8px 기준 스케일 */
--font-size-xs: 12px;
--font-size-sm: 14px;
--font-size-base: 16px;
--font-size-lg: 18px;
--font-size-xl: 20px;
--font-size-2xl: 24px;

/* 폰트 두께 */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

#### 간격 토큰
```css
/* 8px 기준 간격 시스템 */
--spacing-1: 4px;      /* xs */
--spacing-2: 8px;      /* sm */
--spacing-4: 16px;     /* md */
--spacing-6: 24px;     /* lg */
--spacing-8: 32px;     /* xl */
--spacing-12: 48px;    /* 2xl */
```

#### 크기 토큰
```css
/* 컴포넌트 높이 */
--height-sm: 32px;
--height-md: 40px;
--height-lg: 48px;
--height-xl: 56px;

/* 버튼 전용 높이 */
--button-height-sm: var(--height-sm);
--button-height-md: var(--height-lg);
--button-height-lg: var(--height-xl);
```

#### 레이아웃 토큰
```css
/* 화면 높이 기준 */
--header-height: 80px;
--control-panel-height: 120px;
--available-height: calc(100vh - var(--header-height) - var(--control-panel-height));

/* 그리드 비율 */
--grid-ratio-left: 2fr;
--grid-ratio-right: 1fr;
```

### 사용 규칙
1. **상수만 사용**: 하드코딩된 값 금지
2. **토큰 우선**: CSS 변수를 통한 일관성 유지
3. **계층적 명명**: 의미 기반 네이밍 시스템

## 🚫 금지 사항

### 1. 이모티콘 사용 금지
- 모든 UI 텍스트에서 이모티콘 제거 완료
- 아이콘 필요시 SVG 또는 아이콘 폰트 사용
- 전문적이고 깔끔한 인터페이스 유지

### 2. 비승인 색상 사용 금지
- `documents/09_color_system_specification.md` 참조
- 하드코딩된 색상값 사용 금지
- CSS 변수만 사용

### 3. 임의의 크기/간격 사용 금지
- 디자인 토큰에 정의된 값만 사용
- 8px 기준 간격 시스템 준수

## 🧩 컴포넌트 디자인

### 컴포넌트 상수화 원칙
1. **재사용성**: 모든 컴포넌트는 토큰 기반
2. **일관성**: 동일한 역할의 컴포넌트는 동일한 스타일
3. **확장성**: 새로운 변형 추가 시에도 토큰 활용

### 버튼

#### 기본 버튼 (Primary)
```css
background: #F97316;
color: white;
border: none;
padding: 12px 24px;
border-radius: 6px;
font-weight: 500;
transition: all 0.2s ease;

&:hover {
  background: #EA580C;
  transform: translateY(-1px);
}

&:active {
  transform: translateY(0);
}
```

#### 보조 버튼 (Secondary)
```css
background: #6B7280;
color: white;
border: none;
padding: 12px 24px;
border-radius: 6px;
font-weight: 500;

&:hover {
  background: #4B5563;
}
```

#### 외곽선 버튼 (Outline)
```css
background: transparent;
color: #F97316;
border: 2px solid #F97316;
padding: 10px 22px;
border-radius: 6px;
font-weight: 500;

&:hover {
  background: #F97316;
  color: white;
}
```

### 입력 필드

```css
border: 2px solid #D1D5DB;
border-radius: 6px;
padding: 12px 16px;
font-size: 16px;
transition: border-color 0.2s ease;

&:focus {
  border-color: #F97316;
  outline: none;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

&:disabled {
  background: #F3F4F6;
  color: #9CA3AF;
}
```

### 카드

```css
background: white;
border-radius: 8px;
padding: 24px;
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
border: 1px solid #E5E7EB;
```

### 그리드 셀

#### 일반 셀
```css
border: 1px solid #E5E7EB;
padding: 8px 12px;
background: white;
transition: all 0.2s ease;

&:hover {
  background: #F3F4F6;
  cursor: pointer;
}
```

#### 선택된 셀
```css
background: #FEF3E2;
border-color: #F97316;
color: #EA580C;
font-weight: 500;
```

#### 기준값 셀
```css
background: #EFF6FF;
border-color: #3B82F6;
color: #1D4ED8;
```

## 📱 반응형 디자인

### 동적 레이아웃 시스템
현재 구현된 반응형 시스템은 화면 크기에 따라 동적으로 조정됩니다.

#### 레이아웃 비율
```css
/* 데스크톱 (1200px+) */
.work-area__content {
  grid-template-columns: var(--grid-ratio-left) var(--grid-ratio-right); /* 2fr 1fr */
  height: var(--available-height);
}

/* 중간 화면 (1024px-1200px) */
.work-area__content {
  grid-template-columns: 3fr 2fr; /* 비율 조정 */
}

/* 태블릿/모바일 (< 1024px) */
.work-area__content {
  grid-template-columns: 1fr; /* 세로 스택 */
  height: auto;
}
```

#### 화면 높이 기반 레이아웃
```css
/* 화면을 벗어나지 않는 높이 계산 */
--available-height: calc(100vh - var(--header-height) - var(--control-panel-height));

/* 패널 높이 제어 */
.panel-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-body {
  flex: 1;
  overflow-y: auto; /* 내용 많을 때 스크롤 */
}
```

### 브레이크포인트 토큰
```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

### 반응형 원칙
1. **화면 밖으로 나가지 않음**: 뷰포트 높이 기준 계산
2. **비율 유지**: 화면 크기에 따른 동적 비율 조정
3. **콘텐츠 우선**: 모바일에서는 관계설정이 상단에 위치
4. **스크롤 최적화**: 개별 패널 내 스크롤로 전체 레이아웃 보존

### 브레이크포인트별 변화
- **Desktop (1200px+)**: 2:1 비율, 전체 화면 높이 활용
- **Large (1024px-1200px)**: 3:2 비율, 사이드바 너비 조정
- **Tablet (768px-1024px)**: 세로 스택, 자동 높이
- **Mobile (< 768px)**: 컴팩트 레이아웃, 폰트/간격 조정

### 레이아웃 조정

#### 모바일 (< 768px)
- 사이드바를 하단 탭으로 변경
- 그리드를 세로 스크롤로 변경
- 카드 패딩 축소 (16px)
- 폰트 크기 조정

#### 태블릿 (768px - 1024px)
- 2단 레이아웃 유지
- 그리드 열 수 조정
- 버튼 크기 약간 증가

#### 데스크톱 (> 1024px)
- 최대 너비 제한 (1200px)
- 3단 레이아웃 가능
- 전체 기능 표시

## 🎯 사용자 경험 원칙

### 1. 직관성
- 명확한 아이콘과 레이블 사용
- 일관된 색상 코딩
- 예상 가능한 인터랙션

### 2. 피드백
- 로딩 상태 표시
- 성공/실패 메시지
- 호버 효과로 상호작용 가능성 표시

### 3. 효율성
- 키보드 단축키 지원
- 드래그 앤 드롭 기능
- 일괄 선택/해제 옵션

### 4. 오류 방지
- 입력 검증 및 실시간 피드백
- 확인 대화상자 (삭제 등)
- 되돌리기 기능

## 🏗️ 컴포넌트 라이브러리

### 기본 컴포넌트
- Button
- Input
- Select
- Card
- Modal
- Toast
- Loading
- Grid

### 복합 컴포넌트
- FileSelector
- TableGrid
- RelationshipEditor
- ProgressBar
- TabPanel

## 🎨 테마 시스템

### CSS 변수 정의
```css
:root {
  /* Colors */
  --color-primary: #F97316;
  --color-primary-dark: #EA580C;
  --color-secondary: #6B7280;
  --color-background: #F9FAFB;
  --color-surface: #FFFFFF;
  --color-text: #111827;
  --color-text-secondary: #6B7280;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* Borders */
  --border-radius: 6px;
  --border-width: 2px;
  --border-color: #E5E7EB;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

### 다크 모드 (향후 지원)
```css
[data-theme="dark"] {
  --color-background: #111827;
  --color-surface: #1F2937;
  --color-text: #F9FAFB;
  --color-text-secondary: #D1D5DB;
  --border-color: #374151;
}
```

## ✅ 접근성 가이드라인

### 키보드 네비게이션
- Tab 순서 논리적 배치
- Enter/Space로 버튼 활성화
- 방향키로 그리드 네비게이션

### 시각적 접근성
- 충분한 색상 대비 (WCAG AA 기준)
- 색상 외의 정보 전달 방법 제공
- 적절한 폰트 크기 유지

### 스크린 리더 지원
- 의미 있는 alt 텍스트
- aria-label 속성 사용
- heading 구조 체계적 구성

---

## 📊 현재 구현 상황 (2025-09-04 기준)

### ✅ 완료된 항목
1. **디자인 토큰 시스템** - `design-tokens.css` 구축 완료
2. **색상 시스템 정책** - 승인된 색상만 사용하도록 제한
3. **이모티콘 제거** - 모든 UI에서 이모티콘 완전 제거
4. **기본 레이아웃** - 헤더, 컨트롤 패널, 작업 영역 구조 완성
5. **반응형 시스템** - 동적 2:1 비율, 화면 높이 기준 레이아웃
6. **Button 컴포넌트** - 토큰 기반 재사용 가능한 버튼
7. **MainLayout 컴포넌트** - 전체 앱 레이아웃 구조

### 🔄 진행 중인 항목
1. **기존 컴포넌트 토큰화** - 모든 컴포넌트를 디자인 토큰 기반으로 전환
2. **테이블 그리드 컴포넌트** - 셀 선택, 앵커/값 색상 코딩
3. **관계 설정 UI** - 키 관리, 앵커/값 설정 인터랙션

### 📋 다음 단계
1. **Input/Select 컴포넌트** 토큰화
2. **Card 컴포넌트** 재사용성 강화
3. **테이블 그리드** 핵심 기능 구현
4. **백엔드 API** 연동

### 🎯 품질 기준 달성도
- **색상**: 승인된 CSS 변수만 사용 ✅
- **이모티콘**: 완전 제거 ✅  
- **폰트**: Pretendard 적용 ✅
- **간격**: 8px 기준 시스템 ✅
- **반응형**: 화면 밖으로 나가지 않음 ✅
- **재사용성**: 컴포넌트 토큰화 🔄

### 📝 관련 문서
- `documents/09_color_system_specification.md` - 색상 사용 정책
- `documents/06_folder_structure_policy.md` - 폴더 구조 정책
- `frontend/src/shared/styles/design-tokens.css` - 디자인 토큰 정의
