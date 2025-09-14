#!/bin/bash

# Ana Document AI 프론트엔드 서비스 관리 스크립트
# 사용법: ./frontend_service.sh [start|stop|restart|status|logs]

FRONTEND_DIR="frontend"
FRONTEND_PORT=9003
FRONTEND_PID_FILE="$FRONTEND_DIR/logs/frontend.pid"
FRONTEND_LOG_FILE="$FRONTEND_DIR/logs/frontend.log"
FRONTEND_ERROR_LOG_FILE="$FRONTEND_DIR/logs/frontend_error.log"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 포트 사용 확인 함수
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 포트 사용 중
    else
        return 1  # 포트 사용 안함
    fi
}

# 포트 사용 프로세스 종료 함수
kill_port_process() {
    local port=$1
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            log_info "포트 $port 사용 프로세스 종료 시도 ($attempt/$max_attempts)..."
            lsof -ti:$port | xargs kill -9 2>/dev/null
            sleep 2
            
            if ! check_port $port; then
                log_success "포트 $port이 정리되었습니다."
                return 0
            fi
        else
            log_success "포트 $port이 이미 정리되어 있습니다."
            return 0
        fi
        
        attempt=$((attempt + 1))
    done
    
    log_error "포트 $port 정리에 실패했습니다."
    return 1
}

# 프론트엔드 시작 함수
start_frontend() {
    log_info "Ana Document AI 프론트엔드 서버 시작..."
    
    # 포트 9003 사용 상태 체크
    log_info "포트 $FRONTEND_PORT 사용 상태 체크 중..."
    if check_port $FRONTEND_PORT; then
        log_warning "포트 $FRONTEND_PORT이 이미 사용 중입니다."
        kill_port_process $FRONTEND_PORT
    fi
    
    # 기존 React 프로세스 체크 및 종료
    log_info "기존 React 프로세스 체크 및 종료 중..."
    pkill -f "react-scripts" 2>/dev/null
    pkill -f "npm.*start" 2>/dev/null
    
    # PID 파일 제거
    if [ -f "$FRONTEND_PID_FILE" ]; then
        rm -f "$FRONTEND_PID_FILE"
        log_info "기존 PID 파일 제거됨"
    fi
    
    # 로그 디렉토리 생성
    mkdir -p "$FRONTEND_DIR/logs"
    
    # 프론트엔드 디렉토리로 이동
    cd "$FRONTEND_DIR" || {
        log_error "프론트엔드 디렉토리로 이동할 수 없습니다: $FRONTEND_DIR"
        exit 1
    }
    
    # npm 의존성 확인
    if [ ! -d "node_modules" ]; then
        log_info "npm 의존성 설치 중..."
        npm install
    fi
    
    # 포트 완전 해제 확인
    if check_port $FRONTEND_PORT; then
        log_error "포트 $FRONTEND_PORT이 여전히 사용 중입니다."
        exit 1
    fi
    
    log_success "포트 $FRONTEND_PORT이 정리되었습니다. 서버 시작 중..."
    
    # 프론트엔드 서버 시작 (실시간 로그)
    log_info "프론트엔드 서버 시작 중... (실시간 로그 출력)"
    log_info "종료하려면 Ctrl+C를 누르세요"
    echo "----------------------------------------"
    
    # 실시간 로그와 함께 서버 시작
    PORT=$FRONTEND_PORT npm start
}

# 프론트엔드 중지 함수
stop_frontend() {
    log_info "Ana Document AI 프론트엔드 서버 중지..."
    
    # PID 파일에서 프로세스 ID 읽기
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            log_info "프론트엔드 프로세스 종료 중 (PID: $FRONTEND_PID)..."
            kill $FRONTEND_PID
            sleep 3
            
            # 강제 종료 확인
            if ps -p $FRONTEND_PID > /dev/null 2>&1; then
                log_warning "프로세스가 종료되지 않아 강제 종료합니다..."
                kill -9 $FRONTEND_PID
            fi
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi
    
    # React 관련 프로세스 모두 종료
    pkill -f "react-scripts" 2>/dev/null
    pkill -f "npm.*start" 2>/dev/null
    
    # 포트 정리
    kill_port_process $FRONTEND_PORT
    
    log_success "프론트엔드 서버가 중지되었습니다."
}

# 프론트엔드 재시작 함수
restart_frontend() {
    log_info "Ana Document AI 프론트엔드 서버 재시작..."
    stop_frontend
    sleep 2
    start_frontend
}

# 프론트엔드 상태 확인 함수
status_frontend() {
    log_info "Ana Document AI 프론트엔드 서버 상태 확인..."
    
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            log_success "프론트엔드 서버가 실행 중입니다 (PID: $FRONTEND_PID)"
            if check_port $FRONTEND_PORT; then
                log_success "포트 $FRONTEND_PORT 사용 중"
            else
                log_warning "포트 $FRONTEND_PORT 사용 안함"
            fi
        else
            log_warning "PID 파일은 있지만 프로세스가 실행되지 않습니다."
            rm -f "$FRONTEND_PID_FILE"
        fi
    else
        log_warning "프론트엔드 서버가 실행되지 않습니다."
    fi
}

# 로그 확인 함수
logs_frontend() {
    log_info "프론트엔드 로그 확인..."
    
    if [ -f "$FRONTEND_LOG_FILE" ]; then
        log_info "=== 일반 로그 ==="
        tail -n 50 "$FRONTEND_LOG_FILE"
    fi
    
    if [ -f "$FRONTEND_ERROR_LOG_FILE" ]; then
        log_info "=== 에러 로그 ==="
        tail -n 20 "$FRONTEND_ERROR_LOG_FILE"
    fi
}

# 메인 함수
main() {
    case "$1" in
        start)
            start_frontend
            ;;
        stop)
            stop_frontend
            ;;
        restart)
            restart_frontend
            ;;
        status)
            status_frontend
            ;;
        logs)
            logs_frontend
            ;;
        *)
            echo "사용법: $0 {start|stop|restart|status|logs}"
            echo ""
            echo "명령어:"
            echo "  start   - 프론트엔드 서버 시작"
            echo "  stop    - 프론트엔드 서버 중지"
            echo "  restart - 프론트엔드 서버 재시작"
            echo "  status  - 프론트엔드 서버 상태 확인"
            echo "  logs    - 프론트엔드 로그 확인"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"
