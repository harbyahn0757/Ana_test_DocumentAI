#!/bin/bash

# Ana Document AI 개발 환경 중지 스크립트
# 백엔드와 프론트엔드 서비스를 모두 중지

PROJECT_DIR="/Users/harby/0_workspace/PEERNINE/Plot_Code/Ana_test_DocumentAI"
BACKEND_SCRIPT="$PROJECT_DIR/scripts/backend_service.sh"
FRONTEND_SCRIPT="$PROJECT_DIR/scripts/frontend_service.sh"

echo "Ana Document AI 개발 환경을 중지합니다..."

# 백엔드 서비스 중지
if [ -f "$BACKEND_SCRIPT" ]; then
    echo "백엔드 서비스 중지 중..."
    "$BACKEND_SCRIPT" stop
    if [ $? -eq 0 ]; then
        echo "✅ 백엔드 서비스가 중지되었습니다."
    else
        echo "⚠️ 백엔드 서비스 중지 중 오류가 발생했습니다."
    fi
else
    echo "경고: 백엔드 서비스 스크립트를 찾을 수 없습니다: $BACKEND_SCRIPT"
fi

sleep 1

# 프론트엔드 서비스 중지
if [ -f "$FRONTEND_SCRIPT" ]; then
    echo "프론트엔드 서비스 중지 중..."
    "$FRONTEND_SCRIPT" stop
    if [ $? -eq 0 ]; then
        echo "✅ 프론트엔드 서비스가 중지되었습니다."
    else
        echo "⚠️ 프론트엔드 서비스 중지 중 오류가 발생했습니다."
    fi
else
    echo "경고: 프론트엔드 서비스 스크립트를 찾을 수 없습니다: $FRONTEND_SCRIPT"
fi

# tmux 세션이 있으면 종료
if command -v tmux &> /dev/null; then
    SESSION_NAME="ana-dev"
    if tmux has-session -t $SESSION_NAME 2>/dev/null; then
        echo "tmux 세션 '$SESSION_NAME' 종료 중..."
        tmux kill-session -t $SESSION_NAME
        echo "✅ tmux 세션이 종료되었습니다."
    fi
fi

# 추가 프로세스 정리 (혹시 남아있을 수 있는 프로세스들)
echo "잔여 프로세스 정리 중..."

# 포트 9001, 9003 사용 프로세스 확인 및 정리
for port in 9001 9003; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "포트 $port 사용 프로세스 정리 중..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
    fi
done

# uvicorn, react-scripts 프로세스 정리
pkill -f "uvicorn app.main" 2>/dev/null
pkill -f "react-scripts" 2>/dev/null
pkill -f "npm.*start" 2>/dev/null

echo ""
echo "🎉 모든 Ana Document AI 서비스가 정상적으로 중지되었습니다."
echo ""
echo "서비스 재시작: ./scripts/start_dev.sh"
