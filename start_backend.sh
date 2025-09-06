#!/bin/bash

# 가상환경 활성화 및 백엔드 서버 시작 스크립트
cd /Users/harby/0_workspace/PEERNINE/Plot_Code/Ana_test_DocumentAI
source .venv/bin/activate
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
