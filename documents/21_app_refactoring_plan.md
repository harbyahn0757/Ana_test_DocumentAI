# App.js 리팩터링 계획

## 📋 개요
현재 App.js 파일이 1,697줄로 매우 크므로 모듈화를 통한 개선 방안을 제시합니다.

## 🎯 목표
- App.js 파일 크기 1,697줄 → 300줄 이하로 축소
- 재사용 가능한 컴포넌트 분리
- 유지보수성 향상
- 코드 가독성 개선

## 📊 현재 상태 분석

### App.js 파일 구성 요소
1. **상수 정의** (약 50줄)
   - MENU_ITEMS
   - API_ENDPOINTS
   - 기타 상수들

2. **상태 관리** (약 200줄)
   - useState 훅들
   - useEffect 훅들
   - 이벤트 핸들러들

3. **페이지 콘텐츠** (약 1,200줄)
   - section1Content (설정 페이지)
   - section2Content (설정 페이지)
   - section3Content (설정 페이지)
   - extractionTestSection1Content (테스트 페이지)
   - extractionTestSection2Content (테스트 페이지)

4. **렌더링 로직** (약 200줄)
   - renderPageContent 함수
   - 메인 컴포넌트 구조

5. **기타** (약 47줄)
   - import 문들
   - export 문들

## 🔧 리팩터링 계획

### 1단계: 상수 분리
**파일**: `frontend/src/constants/`

#### `menuItems.js`
```javascript
export const MENU_ITEMS = [
  {
    id: 'home',
    label: '홈',
    icon: 'HOME',
    isActive: false
  },
  // ... 나머지 메뉴 아이템들
];
```

#### `apiEndpoints.js`
```javascript
export const API_ENDPOINTS = {
  FILES: {
    LIST: '/api/v1/files/list',
    SAMPLES: '/api/v1/files/samples',
    DOWNLOAD: '/api/v1/files/{file_id}/download'
  },
  ANALYSIS: {
    START: '/api/v1/analysis/start',
    STATUS: '/api/v1/analysis/status/{analysis_id}',
    RESULTS: '/api/v1/analysis/results/{analysis_id}'
  },
  // ... 나머지 엔드포인트들
};
```

### 2단계: 커스텀 훅 분리
**파일**: `frontend/src/hooks/`

#### `useFileManagement.js`
```javascript
export const useFileManagement = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // 파일 관련 로직들...
  
  return {
    selectedFiles,
    setSelectedFiles,
    files,
    setFiles,
    loading,
    // ... 기타 반환값들
  };
};
```

#### `useAnalysis.js`
```javascript
export const useAnalysis = () => {
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // 분석 관련 로직들...
  
  return {
    analysisResults,
    setAnalysisResults,
    isAnalyzing,
    setIsAnalyzing,
    // ... 기타 반환값들
  };
};
```

#### `useTemplateManagement.js`
```javascript
export const useTemplateManagement = () => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  
  // 템플릿 관련 로직들...
  
  return {
    templates,
    setTemplates,
    selectedTemplate,
    setSelectedTemplate,
    // ... 기타 반환값들
  };
};
```

### 3단계: 페이지 컴포넌트 분리
**파일**: `frontend/src/pages/`

#### `DataExtractionPage.js`
```javascript
import React from 'react';
import MultiSectionLayout from '../shared/components/layout/MultiSectionLayout';
import FileUploadSection from '../components/sections/FileUploadSection';
import TableDataSection from '../components/sections/TableDataSection';
import KeySelectionSection from '../components/sections/KeySelectionSection';

const DataExtractionPage = ({ 
  section1Content, 
  section2Content, 
  section3Content 
}) => {
  return (
    <MultiSectionLayout
      header={<Header />}
      subHeader={<SubHeader breadcrumb={['설정', '데이터 추출']} />}
      section1={section1Content}
      section2={section2Content}
      section3={section3Content}
      sectionRatios={[1, 2, 1]}
    />
  );
};

export default DataExtractionPage;
```

#### `ExtractionTestPage.js`
```javascript
import React from 'react';
import MultiSectionLayout from '../shared/components/layout/MultiSectionLayout';

const ExtractionTestPage = ({ 
  section1Content, 
  section2Content 
}) => {
  return (
    <MultiSectionLayout
      header={<Header />}
      subHeader={<SubHeader breadcrumb={['데이터마이닝', '추출 테스트']} />}
      section1={section1Content}
      section2={section2Content}
      section3={null}
      sectionRatios={[1, 1, 0]}
    />
  );
};

export default ExtractionTestPage;
```

### 4단계: 섹션 컴포넌트 분리
**파일**: `frontend/src/components/sections/`

#### `FileUploadSection.js`
```javascript
import React from 'react';
import MultiSectionLayout from '../../shared/components/layout/MultiSectionLayout';
import SectionContainer from '../../shared/components/ui/SectionContainer';

const FileUploadSection = ({ 
  selectedFiles, 
  setSelectedFiles, 
  files, 
  loading 
}) => {
  return (
    <MultiSectionLayout.Section title="파일 업로드 & 처리" className="responsive-font-compact-lg">
      <div className="vertical-sections">
        {/* 파일 업로드 섹션 */}
        <SectionContainer 
          title="파일 업로드"
          border="none"
          background="none"
          padding="sm"
        >
          {/* 파일 업로드 로직 */}
        </SectionContainer>
        
        {/* 파일 목록 섹션 */}
        <SectionContainer 
          title="| 파일 목록"
          border="none"
          background="none"
          padding="sm"
        >
          {/* 파일 목록 로직 */}
        </SectionContainer>
        
        {/* 분석 설정 섹션 */}
        <SectionContainer 
          title="| 분석 설정"
          border="none"
          background="none"
          padding="sm"
        >
          {/* 분석 설정 로직 */}
        </SectionContainer>
      </div>
    </MultiSectionLayout.Section>
  );
};

export default FileUploadSection;
```

#### `TableDataSection.js`
```javascript
import React from 'react';
import MultiSectionLayout from '../../shared/components/layout/MultiSectionLayout';
import SectionContainer from '../../shared/components/ui/SectionContainer';

const TableDataSection = ({ 
  analysisResults, 
  selectedFiles, 
  keyMappings 
}) => {
  return (
    <MultiSectionLayout.Section 
      title="테이블 데이터" 
      className="responsive-font-compact-lg"
      headerActions={
        <div className="table-actions">
          <Button 
            variant="primary" 
            size="lg"
            onClick={handleStartAnalysis}
            disabled={selectedFiles.length === 0 || isAnalyzing}
          >
            {isAnalyzing ? '분석 중...' : '분석 시작'}
          </Button>
        </div>
      }
    >
      <div className="vertical-sections">
        {/* 분석 결과 섹션 */}
        <SectionContainer 
          title="| 분석결과"
          border="none"
          background="none"
          padding="sm"
        >
          {/* 분석 결과 로직 */}
        </SectionContainer>
        
        {/* 앵커/값 설정 섹션 */}
        <SectionContainer 
          title="| 앵커/값 설정"
          border="none"
          background="none"
          padding="sm"
        >
          {/* 앵커/값 설정 로직 */}
        </SectionContainer>
      </div>
    </MultiSectionLayout.Section>
  );
};

export default TableDataSection;
```

#### `KeySelectionSection.js`
```javascript
import React from 'react';
import MultiSectionLayout from '../../shared/components/layout/MultiSectionLayout';
import SectionContainer from '../../shared/components/ui/SectionContainer';

const KeySelectionSection = ({ 
  keyMappings, 
  setKeyMappings, 
  templates, 
  selectedTemplate 
}) => {
  return (
    <MultiSectionLayout.Section 
      title="키 선택" 
      className="responsive-font-compact-lg"
      headerActions={
        <div className="key-actions">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowTemplateSaveModal(true)}
          >
            템플릿 저장
          </Button>
        </div>
      }
    >
      <div className="vertical-sections">
        {/* 템플릿 선택 섹션 */}
        <SectionContainer 
          title="템플릿 선택"
          border="none"
          background="none"
          padding="sm"
        >
          {/* 템플릿 선택 로직 */}
        </SectionContainer>
        
        {/* 관계 설정 상태 섹션 */}
        <SectionContainer 
          title="| 관계설정상태"
          border="none"
          background="none"
          padding="sm"
        >
          {/* 관계 설정 상태 로직 */}
        </SectionContainer>
      </div>
    </MultiSectionLayout.Section>
  );
};

export default KeySelectionSection;
```

### 5단계: 리팩터링된 App.js
```javascript
import React, { useState, useEffect } from 'react';
import { SidebarLayout } from './shared/components/layout';
import { Header, SubHeader, Sidebar } from './shared/components';
import { MENU_ITEMS } from './constants/menuItems';
import { useFileManagement } from './hooks/useFileManagement';
import { useAnalysis } from './hooks/useAnalysis';
import { useTemplateManagement } from './hooks/useTemplateManagement';
import DataExtractionPage from './pages/DataExtractionPage';
import ExtractionTestPage from './pages/ExtractionTestPage';
import WelcomePage from './pages/WelcomePage';
import './App.css';

function App() {
  // 커스텀 훅 사용
  const fileManagement = useFileManagement();
  const analysis = useAnalysis();
  const templateManagement = useTemplateManagement();
  
  // 앱 상태
  const [activeMenu, setActiveMenu] = useState('home');
  
  // 페이지 렌더링
  const renderPageContent = () => {
    switch (activeMenu) {
      case 'data-extraction':
        return (
          <DataExtractionPage
            section1Content={<FileUploadSection {...fileManagement} />}
            section2Content={<TableDataSection {...analysis} />}
            section3Content={<KeySelectionSection {...templateManagement} />}
          />
        );
      case 'extraction-test':
        return (
          <ExtractionTestPage
            section1Content={<ExtractionTestSection1 {...fileManagement} />}
            section2Content={<ExtractionTestSection2 {...templateManagement} />}
          />
        );
      default:
        return <WelcomePage />;
    }
  };

  return (
    <SidebarLayout
      sidebar={<Sidebar menuItems={MENU_ITEMS} activeMenu={activeMenu} onMenuChange={setActiveMenu} />}
      content={renderPageContent()}
    />
  );
}

export default App;
```

## 📈 예상 효과

### 파일 크기 개선
- **App.js**: 1,697줄 → 300줄 (82% 감소)
- **전체 코드**: 더 작고 관리하기 쉬운 모듈들로 분산

### 유지보수성 향상
- 각 컴포넌트의 책임이 명확해짐
- 독립적인 테스트 가능
- 재사용성 증대

### 개발 효율성 향상
- 병렬 개발 가능
- 코드 충돌 감소
- 디버깅 용이성 증대

## 🚀 구현 순서

1. **1단계**: 상수 분리 (1일)
2. **2단계**: 커스텀 훅 분리 (2일)
3. **3단계**: 페이지 컴포넌트 분리 (2일)
4. **4단계**: 섹션 컴포넌트 분리 (3일)
5. **5단계**: App.js 리팩터링 (1일)

**총 예상 기간**: 9일

## ⚠️ 주의사항

1. **점진적 리팩터링**: 한 번에 모든 것을 바꾸지 말고 단계별로 진행
2. **테스트**: 각 단계마다 기능이 정상 작동하는지 확인
3. **백업**: 리팩터링 전 현재 상태 백업
4. **문서화**: 변경사항을 문서에 기록

이 계획에 따라 App.js 파일을 모듈화하여 유지보수성과 가독성을 크게 향상시킬 수 있습니다.
