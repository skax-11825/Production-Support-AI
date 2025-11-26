========================================
질문-답변 API 서버 실행 가이드
========================================

이 실행 파일은 Oracle 데이터베이스와 연동된 질문-답변 API 서버입니다.

## 시작하기

1. .env 파일 설정
   - 이 실행 파일과 같은 폴더에 .env 파일을 생성하세요
   - 다음 내용을 입력하세요:

   ORACLE_USER=system
   ORACLE_PASSWORD=oracle
   ORACLE_DSN=localhost:1521/FREEPDB1

   (Docker Oracle DB 사용 시 위 설정을 사용하세요)

2. 실행 파일 실행
   - Windows: question-answer-api.exe 더블클릭
   - macOS: 터미널에서 ./question-answer-api 실행

3. 서버 접속
   - 브라우저에서 http://localhost:8000/docs 접속
   - API 문서에서 서버 사용법을 확인할 수 있습니다

## 서버 중지

서버를 중지하려면:
- 명령줄 창에서 Ctrl+C (Windows/Linux) 또는 Cmd+C (macOS)를 누르세요

## 문제 해결

1. "데이터베이스 연결 실패" 오류
   - Oracle 데이터베이스가 실행 중인지 확인
   - .env 파일의 연결 정보가 올바른지 확인
   - Docker를 사용하는 경우: docker ps로 컨테이너 상태 확인

2. "포트가 이미 사용 중" 오류
   - 다른 프로그램이 8000번 포트를 사용 중일 수 있습니다
   - 다른 포트를 사용하려면 코드를 수정해야 합니다

3. 추가 도움말
   - BUILD_GUIDE.md 파일 참고
   - DOCKER_SETUP.md 파일 참고 (Docker 사용 시)

## API 사용 예시

### 질문하기
POST http://localhost:8000/ask
Content-Type: application/json

{
  "question": "현재 시간은 몇 시인가요?",
  "context": null
}

### 헬스 체크
GET http://localhost:8000/health

========================================
문의사항이 있으면 개발자에게 연락하세요.
========================================

