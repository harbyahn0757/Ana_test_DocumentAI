#!/bin/bash

# Ana Document AI 백엔드 서비스 관리 스크립트

PROJECT_DIR="/Users/harby/0_workspace/PEERNINE/Plot_Code/Ana_test_DocumentAI"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/.venv"
PID_FILE="$BACKEND_DIR/backend.pid"
LOG_FILE="$BACKEND_DIR/logs/backend.log"
ERROR_LOG="$BACKEND_DIR/logs/backend.error.log"

start() {
    echo "Ana Document AI 백엔드 서버 시작..."
    
    # 1. 포트 9001 사용 중인 프로세스 체크 및 종료
    echo "포트 9001 사용 상태 체크 중..."
    PORT_PROCESSES=$(lsof -t -i:9001 2>/dev/null)
    if [ ! -z "$PORT_PROCESSES" ]; then
        echo "포트 9001을 사용 중인 프로세스 발견. 종료 중..."
        echo "$PORT_PROCESSES" | xargs kill -9 2>/dev/null
        sleep 2
    fi
    
    # 2. uvicorn 프로세스 강제 종료
    echo "기존 uvicorn 프로세스 체크 및 종료 중..."
    pkill -f "uvicorn app.main" 2>/dev/null
    sleep 1
    
    # 3. PID 파일 정리
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
        echo "기존 PID 파일 제거됨"
    fi
    
    # 4. 로그 디렉토리 생성
    mkdir -p "$BACKEND_DIR/logs"
    
    # 5. 포트가 완전히 해제되었는지 재확인
    sleep 1
    if lsof -i:9001 >/dev/null 2>&1; then
        echo "경고: 포트 9001이 아직 사용 중입니다. 5초 대기 후 재시도..."
        sleep 5
        if lsof -i:9001 >/dev/null 2>&1; then
            echo "오류: 포트 9001을 해제할 수 없습니다"
            return 1
        fi
    fi
    
    echo "포트 9001이 정리되었습니다. 서버 시작 중..."
    
    # 6. 백엔드 서버 시작 (실시간 로그 출력)
    cd "$BACKEND_DIR"
    echo "백엔드 서버 시작 중... (실시간 로그 출력)"
    echo "종료하려면 Ctrl+C를 누르세요"
    echo "----------------------------------------"
    
    # 실시간 로그와 함께 서버 시작
    "$VENV_DIR/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
    
    # 8. 시작 확인
    sleep 3
    if ps -p $! > /dev/null 2>&1; then
        echo "서버가 정상적으로 실행 중입니다"
    else
        echo "서버 시작에 실패했습니다. 에러 로그를 확인하세요:"
        tail -10 "$ERROR_LOG"
        return 1
    fi
}

stop() {
    echo "Ana Document AI 백엔드 서버 중지..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            rm -f "$PID_FILE"
            echo "백엔드 서버가 중지되었습니다"
        else
            echo "백엔드 서버가 실행되고 있지 않습니다"
            rm -f "$PID_FILE"
        fi
    else
        echo "PID 파일을 찾을 수 없습니다"
        # uvicorn 프로세스 강제 종료
        pkill -f "uvicorn app.main"
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "백엔드 서버가 실행 중입니다 (PID: $PID)"
            # 포트 확인
            if lsof -i :9001 > /dev/null 2>&1; then
                echo "포트 9001이 사용 중입니다"
            else
                echo "포트 9001이 사용되지 않고 있습니다"
            fi
        else
            echo "백엔드 서버가 실행되고 있지 않습니다"
            rm -f "$PID_FILE"
        fi
    else
        echo "백엔드 서버가 실행되고 있지 않습니다"
    fi
}

restart() {
    stop
    sleep 2
    start
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "로그 파일을 찾을 수 없습니다: $LOG_FILE"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "사용법: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
