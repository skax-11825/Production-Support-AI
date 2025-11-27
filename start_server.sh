#!/bin/bash

# API 서버 자동 실행 스크립트

cd /Users/jeonghoon/Desktop/Project/Inform\ Note/Agent

# 가상환경 활성화 및 서버 실행
/Users/jeonghoon/Desktop/Project/Inform\ Note/Agent/venv/bin/python3.12 -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='info')" >> /tmp/question-answer-api.log 2>&1

