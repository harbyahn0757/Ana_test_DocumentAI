#!/bin/bash

# Ana Document AI 개발 환경 시작 스크립트
# 백엔드와 프론트엔드를 각각 별도 터미널에서 실행하며 실시간 로그 표시

PROJECT_DIR="/Users/harby/0_workspace/PEERNINE/Plot_Code/Ana_test_DocumentAI"
BACKEND_SCRIPT="$PROJECT_DIR/scripts/backend_service.sh"
FRONTEND_SCRIPT="$PROJECT_DIR/scripts/frontend_service.sh"

echo "Ana Document AI 개발 환경을 시작합니다..."
echo "프로젝트 디렉토리: $PROJECT_DIR"

# 스크립트 파일 존재 확인
if [ ! -f "$BACKEND_SCRIPT" ]; then
    echo "오류: 백엔드 서비스 스크립트를 찾을 수 없습니다: $BACKEND_SCRIPT"
    exit 1
fi

if [ ! -f "$FRONTEND_SCRIPT" ]; then
    echo "오류: 프론트엔드 서비스 스크립트를 찾을 수 없습니다: $FRONTEND_SCRIPT"
    exit 1
fi

# macOS에서 터미널 앱을 사용하여 새 탭에서 스크립트 실행
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS 터미널에서 서비스들을 시작합니다..."
    
    # 백엔드 서비스를 새 터미널 탭에서 시작 (실시간 로그 포함)
    echo "백엔드 서비스 시작 중..."
    osascript -e "
        tell application \"Terminal\"
            activate
            do script \"cd '$PROJECT_DIR' && echo '=== Ana Document AI 백엔드 서버 ===' && '$BACKEND_SCRIPT' start\"
        end tell
    "
    
    sleep 3
    
    # 프론트엔드 서비스를 새 터미널 탭에서 시작 (실시간 로그 포함)
    echo "프론트엔드 서비스 시작 중..."
    osascript -e "
        tell application \"Terminal\"
            do script \"cd '$PROJECT_DIR' && echo '=== Ana Document AI 프론트엔드 서버 ===' && '$FRONTEND_SCRIPT' start\"
        end tell
    "
    
    echo "✅ 백엔드와 프론트엔드 서비스가 각각 별도 터미널 탭에서 시작되었습니다."
    echo ""
    echo "서비스 URL:"
    echo "- 백엔드 API: http://localhost:9001"
    echo "- 프론트엔드: http://localhost:9003"
    echo ""
    echo "서비스 중지:"
    echo "- 각 터미널에서 Ctrl+C를 누르거나"
    echo "- 통합 중지: ./scripts/stop_dev.sh"
    echo "- 개별 중지:"
    echo "  * 백엔드: $BACKEND_SCRIPT stop"
    echo "  * 프론트엔드: $FRONTEND_SCRIPT stop"

# Linux/WSL에서 gnome-terminal 사용
elif command -v gnome-terminal &> /dev/null; then
    echo "Linux 환경에서 서비스들을 시작합니다..."
    
    # 백엔드 서비스 시작 (실시간 로그 포함)
    echo "백엔드 서비스 시작 중..."
    gnome-terminal --tab --title="Ana Backend" -- bash -c "cd '$PROJECT_DIR' && echo '=== Ana Document AI 백엔드 서버 ===' && '$BACKEND_SCRIPT' start; exec bash"
    
    sleep 3
    
    # 프론트엔드 서비스 시작 (실시간 로그 포함)
    echo "프론트엔드 서비스 시작 중..."
    gnome-terminal --tab --title="Ana Frontend" -- bash -c "cd '$PROJECT_DIR' && echo '=== Ana Document AI 프론트엔드 서버 ===' && '$FRONTEND_SCRIPT' start; exec bash"
    
    echo "✅ 백엔드와 프론트엔드 서비스가 각각 별도 터미널 탭에서 시작되었습니다."

# tmux 환경
elif command -v tmux &> /dev/null; then
    echo "tmux 환경에서 서비스들을 시작합니다..."
    
    # tmux 세션 생성
    SESSION_NAME="ana-dev"
    
    # 기존 세션이 있으면 종료
    tmux has-session -t $SESSION_NAME 2>/dev/null && tmux kill-session -t $SESSION_NAME
    
    # 새 세션 생성
    tmux new-session -d -s $SESSION_NAME -c "$PROJECT_DIR"
    
    # 백엔드 창 (실시간 로그 포함)
    tmux rename-window -t $SESSION_NAME:0 'Backend'
    tmux send-keys -t $SESSION_NAME:0 "echo '=== Ana Document AI 백엔드 서버 ===' && '$BACKEND_SCRIPT' start" C-m
    
    # 프론트엔드 창 생성 (실시간 로그 포함)
    tmux new-window -t $SESSION_NAME -n 'Frontend' -c "$PROJECT_DIR"
    tmux send-keys -t $SESSION_NAME:1 "echo '=== Ana Document AI 프론트엔드 서버 ===' && '$FRONTEND_SCRIPT' start" C-m
    
    # 상태 표시 창 생성
    tmux new-window -t $SESSION_NAME -n 'Status' -c "$PROJECT_DIR"
    tmux send-keys -t $SESSION_NAME:2 "echo '=== Ana Document AI 서비스 상태 ===' && echo 'Backend: http://localhost:9001' && echo 'Frontend: http://localhost:9003' && echo '' && echo '서비스 중지: ./scripts/stop_dev.sh' && echo '세션 종료: tmux kill-session -t $SESSION_NAME'" C-m
    
    # 첫 번째 창으로 이동
    tmux select-window -t $SESSION_NAME:0
    
    # 세션에 연결
    tmux attach-session -t $SESSION_NAME
    
    echo "✅ tmux 세션 '$SESSION_NAME'에서 서비스들이 시작되었습니다."
    echo "세션 재연결: tmux attach-session -t $SESSION_NAME"
    echo "세션 종료: tmux kill-session -t $SESSION_NAME"

else
    echo "지원되는 터미널 환경을 찾을 수 없습니다."
    echo "수동으로 다음 명령어를 각각 별도 터미널에서 실행하세요:"
    echo ""
    echo "터미널 1 (백엔드):"
    echo "cd '$PROJECT_DIR' && '$BACKEND_SCRIPT' start"
    echo ""
    echo "터미널 2 (프론트엔드):"
    echo "cd '$PROJECT_DIR' && '$FRONTEND_SCRIPT' start"
    exit 1
fi
