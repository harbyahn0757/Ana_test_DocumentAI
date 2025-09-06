# 색상 시스템 명세서

## 🎨 공식 색상 팔레트

### ⚠️ 중요: 색상 사용 규칙
**이 문서에 명시된 색상만 사용해야 합니다. 다른 색상은 절대 사용 금지입니다.**

## 📋 승인된 색상 목록

### 1. 메인 색상 (회색 계열)
```css
/* 주 회색 색상 */
--color-primary: #6B7280;        /* 기본 회색 */
--color-primary-dark: #4B5563;   /* 진한 회색 */
--color-primary-light: #9CA3AF;  /* 밝은 회색 */
```

### 2. 포인트 색상 (주황 계열)
```css
/* 주 주황 색상 */
--color-accent: #F97316;         /* 기본 주황 */
--color-accent-dark: #EA580C;    /* 진한 주황 */
--color-accent-light: #FB923C;   /* 밝은 주황 */
--color-accent-pale: #FEF3E2;    /* 연한 주황 배경 */
```

### 3. 배경 및 표면 색상 (무채색)
```css
/* 배경 색상 */
--color-background: #F9FAFB;     /* 기본 배경 (밝은 회색) */
--color-surface: #FFFFFF;        /* 카드/패널 배경 (흰색) */
--color-border: #E5E7EB;         /* 테두리 색상 */
--color-border-light: #F3F4F6;   /* 밝은 테두리 */
```

### 4. 텍스트 색상 (회색 계열)
```css
/* 텍스트 색상 */
--color-text: #111827;           /* 기본 텍스트 (짙은 회색) */
--color-text-secondary: #6B7280; /* 보조 텍스트 (회색) */
--color-text-muted: #9CA3AF;     /* 비활성 텍스트 (밝은 회색) */
--color-text-inverse: #FFFFFF;   /* 역전 텍스트 (흰색) */
```

### 5. 특수 기능 색상
```css
/* 건강검진 시스템 전용 색상 */
--color-anchor: #3B82F6;         /* 앵커(기준점) - 파란색 */
--color-anchor-bg: #EFF6FF;      /* 앵커 배경 */
--color-value: #F97316;          /* 값 - 주황색 (accent와 동일) */
--color-value-bg: #FEF3E2;       /* 값 배경 (accent-pale와 동일) */
--color-selected: #10B981;       /* 선택됨 - 초록색 */
--color-selected-bg: #ECFDF5;    /* 선택됨 배경 */
```

### 6. 상태 색상 (시스템 피드백용)
```css
/* 상태 표시 색상 */
--color-success: #10B981;        /* 성공 - 초록색 */
--color-warning: #F59E0B;        /* 경고 - 노랑색 */
--color-error: #EF4444;          /* 오류 - 빨간색 */
--color-info: #3B82F6;           /* 정보 - 파란색 */
```

## 🚫 사용 금지 사항

### 색상 사용 금지
다음 색상들은 **절대 사용하지 않습니다**:
- 보라색 계열 (purple, violet, indigo)
- 분홍색 계열 (pink, magenta)
- 사용자 정의 그라데이션 (단, 헤더의 기본 그라데이션 제외)
- RGB/HSL로 직접 지정한 색상
- 브랜드 컬러가 아닌 임의의 색상

### 이모티콘 사용 금지
**모든 이모티콘 사용을 금지합니다**:
- 📊, 🎯, ⚙️, 💾, 📄, 📁 등 모든 유니코드 이모티콘
- 텍스트 내용, 버튼 레이블, 제목, 플레이스홀더 등 어디에도 사용 불가
- 아이콘이 필요한 경우 SVG 또는 아이콘 폰트 사용
- 순수 텍스트만 사용하여 깔끔하고 전문적인 인터페이스 구현

## 📏 색상 사용 가이드라인

### 1. 버튼 색상 적용
```css
/* Primary 버튼 - 주황색 (주요 액션) */
.btn--primary {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text-inverse);
}

/* Secondary 버튼 - 회색 (보조 액션) */
.btn--secondary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-inverse);
}
```

### 2. 상태 표시 색상
```css
/* 성공 상태 */
.status--success {
  color: var(--color-success);
  background: var(--color-selected-bg);
}

/* 경고 상태 */
.status--warning {
  color: var(--color-warning);
  background: #FEF3E2; /* warning의 연한 배경 */
}

/* 오류 상태 */
.status--error {
  color: var(--color-error);
  background: #FEE2E2; /* error의 연한 배경 */
}
```

### 3. 그리드 셀 색상 (건강검진 시스템)
```css
/* 일반 셀 */
.cell-normal {
  background: var(--color-surface);
  border-color: var(--color-border);
  color: var(--color-text);
}

/* 앵커 셀 (기준점) */
.cell-anchor {
  background: var(--color-anchor-bg);
  border-color: var(--color-anchor);
  color: var(--color-anchor);
}

/* 값 셀 (데이터) */
.cell-value {
  background: var(--color-value-bg);
  border-color: var(--color-value);
  color: var(--color-value);
}

/* 선택된 셀 */
.cell-selected {
  background: var(--color-selected-bg);
  border-color: var(--color-selected);
  color: var(--color-selected);
}
```

## 🎯 색상 사용 우선순위

1. **메인 액션**: 주황색 (accent)
2. **보조 액션**: 회색 (primary) 
3. **배경**: 흰색/밝은 회색
4. **텍스트**: 짙은 회색
5. **특수 기능**: 파란색(앵커), 초록색(선택)

## ✅ 색상 검증 체크리스트

코드 작성 시 다음을 확인하세요:

- [ ] CSS 변수만 사용했는가? (var(--color-*))
- [ ] 하드코딩된 색상값 없는가? (#123456, rgb(), hsl() 등)
- [ ] 승인된 색상 목록에 있는 색상인가?
- [ ] 색상 조합이 접근성 기준을 만족하는가?
- [ ] 브랜드 아이덴티티와 일치하는가?

## 🔧 개발자 참고사항

### CSS 변수 우선 사용
```css
/* ✅ 올바른 사용 */
color: var(--color-accent);
background: var(--color-surface);

/* ❌ 잘못된 사용 */
color: #F97316;
background: white;
```

### 새로운 색상이 필요한 경우
1. 기존 색상으로 해결 가능한지 먼저 검토
2. 불가능한 경우 이 문서에 추가 후 사용
3. 팀 리뷰를 통한 승인 과정 거치기

이 색상 시스템을 통해 일관성 있고 전문적인 UI를 구축합니다.
