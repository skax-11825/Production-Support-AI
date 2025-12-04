# Inform Note 프론트엔드 UI

Dify AI와 연동된 반도체 공정 데이터 조회 시스템의 웹 UI입니다.

## 기능

- 💬 **자연어 질의-응답**: Dify AI를 통한 자연어 질의 처리
- 📊 **데이터 시각화**: 조회된 데이터를 테이블 형태로 표시
- ⚙️ **설정 관리**: Dify API Key 및 서버 URL 설정
- 🔍 **시스템 상태 확인**: API 서버 및 Dify 연결 상태 모니터링

## 사용 방법

### 1. 기본 사용

1. `index.html` 파일을 웹 브라우저에서 엽니다.
2. 사이드바에서 Dify API Key를 입력하고 저장합니다.
3. 채팅창에 질문을 입력하고 전송합니다.

### 2. 설정

#### Dify API 설정
- **Dify API Base URL**: Dify API의 기본 URL (기본값: `https://api.dify.ai/v1`)
- **Dify API Key**: Dify에서 발급받은 API Key (`app-xxxxxxxx` 형식)
- **API 서버 URL**: FastAPI 서버의 URL (기본값: `http://localhost:8000`)

#### Dify API Key 발급 방법
1. Dify 웹사이트에 로그인
2. 애플리케이션 설정으로 이동
3. API Keys 섹션에서 새 API Key 생성
4. 생성된 Key를 복사하여 UI에 입력

### 3. 질문 예시

- "ETCH 공정의 에러 코드 통계를 보여줘"
- "최근 PM 이력을 조회해줘"
- "특정 장비의 상세 내역을 검색해줘"
- "2024년 1월부터 3월까지의 에러 코드별 통계를 보여줘"

## 시스템 아키텍처

```
[웹 브라우저 (이 UI)]
    ↓ HTTP Request
[Dify AI]
    ↓ HTTP Request
[FastAPI Server (main.py)]
    ↓ SQL Query
[Oracle Database]
```

## 파일 구조

```
frontend/
├── index.html      # 메인 HTML 파일
├── styles.css      # 스타일시트
├── app.js          # JavaScript 애플리케이션 로직
└── README.md       # 이 파일
```

## 로컬 서버 실행 (선택사항)

CORS 문제를 피하기 위해 로컬 서버를 사용할 수 있습니다:

### Python HTTP 서버
```bash
cd frontend
python3 -m http.server 8080
```

그 다음 브라우저에서 `http://localhost:8080` 접속

### Node.js HTTP 서버
```bash
cd frontend
npx http-server -p 8080
```

## 주의사항

1. **CORS 설정**: FastAPI 서버의 CORS 설정이 모든 origin을 허용하도록 설정되어 있어야 합니다. (현재 설정됨)
2. **Dify 워크플로우**: Dify에서 이 FastAPI 서버를 Tool로 등록해야 합니다.
3. **API 서버 실행**: FastAPI 서버가 실행 중이어야 합니다.

## Dify 워크플로우 설정

Dify에서 이 시스템을 사용하려면:

1. Dify 워크플로우 생성
2. HTTP Request 노드 추가
3. FastAPI 서버의 엔드포인트를 Tool로 등록:
   - `/lookup/ids` - ID 조회
   - `/api/v1/informnote/stats/error-code` - 에러 코드 통계
   - `/api/v1/informnote/history/pm` - PM 이력
   - `/api/v1/informnote/search` - 상세 검색
4. LLM 노드에서 이 Tool들을 사용하도록 설정

## 문제 해결

### Dify 연결 실패
- API Key가 올바른지 확인
- Dify API Base URL이 올바른지 확인
- 네트워크 연결 확인

### API 서버 연결 실패
- FastAPI 서버가 실행 중인지 확인 (`http://localhost:8000/health`)
- API 서버 URL이 올바른지 확인
- CORS 설정 확인

### 데이터가 표시되지 않음
- Dify 워크플로우에서 FastAPI 서버를 Tool로 등록했는지 확인
- Dify 응답 형식이 올바른지 확인

## 향후 개선 사항

- [ ] React 기반으로 마이그레이션
- [ ] 실시간 스트리밍 응답 지원
- [ ] 대화 기록 저장 및 불러오기
- [ ] 차트 및 그래프 시각화
- [ ] 다국어 지원

