# Ana Document AI 개발 스크립트

## 📋 개요
Ana Document AI 프로젝트의 개발 환경을 쉽게 관리할 수 있는 스크립트 모음입니다.

## 🚀 스크립트 목록

### 통합 관리 스크립트
- `start_dev.sh`: 백엔드와 프론트엔드를 각각 별도 터미널에서 시작
- `stop_dev.sh`: 모든 서비스를 한 번에 중지

### 개별 서비스 관리 (scripts 디렉토리)
- `backend_service.sh`: 백엔드 서비스 관리
- `frontend_service.sh`: 프론트엔드 서비스 관리

## 💻 사용법

### 개발 환경 시작
```bash
# 프로젝트 루트에서 실행
./scripts/start_dev.sh
```

이 명령어를 실행하면:
- 백엔드 서버가 새 터미널 탭에서 시작됩니다 (포트 9001)
- 프론트엔드 서버가 또 다른 터미널 탭에서 시작됩니다 (포트 9003)
- 각 서비스의 실시간 로그를 확인할 수 있습니다

### 개발 환경 중지
```bash
# 프로젝트 루트에서 실행
./scripts/stop_dev.sh
```

또는 각 터미널에서 `Ctrl+C`로 개별 중지

### 개별 서비스 관리

#### 백엔드 서비스
```bash
./scripts/backend_service.sh start    # 시작
./scripts/backend_service.sh stop     # 중지
./scripts/backend_service.sh restart  # 재시작
./scripts/backend_service.sh status   # 상태 확인
./scripts/backend_service.sh logs     # 로그 확인
```

#### 프론트엔드 서비스
```bash
./scripts/frontend_service.sh start    # 시작
./scripts/frontend_service.sh stop     # 중지
./scripts/frontend_service.sh restart  # 재시작
./scripts/frontend_service.sh status   # 상태 확인
./scripts/frontend_service.sh logs     # 로그 확인
```

## 🌐 서비스 URL

- **백엔드 API**: http://localhost:9001
- **프론트엔드**: http://localhost:9003

## 🛠️ 지원 환경

- **macOS**: Terminal 앱의 새 탭 사용
- **Linux**: gnome-terminal 사용
- **tmux**: 세션 기반 분할 터미널

## 📝 특징

1. **실시간 로그**: 각 서비스의 로그를 실시간으로 확인 가능
2. **별도 터미널**: 백엔드와 프론트엔드가 각각 독립된 터미널에서 실행
3. **안전한 종료**: 모든 관련 프로세스와 포트를 정리
4. **상태 확인**: 서비스 상태와 포트 사용 현황 확인 가능

## 🔧 문제 해결

### 포트 충돌 시
스크립트가 자동으로 기존 프로세스를 종료하고 포트를 정리합니다.

### 서비스 시작 실패 시
```bash
# 상태 확인
./scripts/backend_service.sh status
./scripts/frontend_service.sh status

# 로그 확인
./scripts/backend_service.sh logs
./scripts/frontend_service.sh logs
```

### 완전 정리가 필요한 경우
```bash
# 모든 서비스 중지 후
./scripts/stop_dev.sh

# 수동으로 프로세스 확인
lsof -i :9001  # 백엔드 포트
lsof -i :9003  # 프론트엔드 포트
```
