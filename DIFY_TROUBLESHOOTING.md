# Dify API 연결 문제 해결 가이드

## 현재 상황
- API 서버 (Ngrok): ✅ 정상 작동
- Dify 연결: ❌ 인증 실패 (401 에러)

## 가능한 원인 및 해결 방법

### 1. API Key 문제 (가장 가능성 높음)

**가능한 원인:**
- API Key가 잘못 복사되었거나 수정됨
- API Key에 보이지 않는 공백이나 특수문자 포함
- API Key가 만료되었거나 삭제됨
- API Key가 다른 애플리케이션에 연결됨

**해결 방법:**
1. Dify 대시보드에서 **새로운 API Key를 발급**받으세요
2. API Key를 **직접 복사-붙여넣기**하세요 (수동 입력 금지)
3. API Key 미리보기 기능(눈 아이콘)을 사용하여 정확히 복사되었는지 확인하세요
4. API Key 앞뒤에 공백이 없는지 확인하세요

### 2. Dify 애플리케이션 미게시 상태

**가능한 원인:**
- Dify 애플리케이션이 "게시(Published)" 상태가 아님
- 워크플로우가 게시되지 않음

**해결 방법:**
1. Dify 대시보드에서 애플리케이션 상태 확인
2. 애플리케이션이 **"게시"** 상태인지 확인
3. 사용 중인 워크플로우가 **게시**되었는지 확인
4. 워크플로우에 오류가 없는지 확인

### 3. Dify API Base URL 문제

**현재 URL:** `http://ai-platform-deploy.koreacentral.cloudapp.azure.com/v1`

**가능한 원인:**
- URL 끝에 슬래시가 있거나 없음
- `/v1` 경로가 올바르지 않음
- HTTP vs HTTPS 문제
- 엔드포인트 경로가 다름

**해결 방법:**
1. Dify 서버 관리자에게 정확한 API Base URL 확인
2. 다음 형식들을 시도해보세요:
   - `http://ai-platform-deploy.koreacentral.cloudapp.azure.com/v1`
   - `http://ai-platform-deploy.koreacentral.cloudapp.azure.com/v1/`
   - `https://ai-platform-deploy.koreacentral.cloudapp.azure.com/v1` (HTTPS 시도)
3. Dify 서버의 API 문서 확인

### 4. Dify 서버 접근 제한 설정

**가능한 원인:**
- Dify 서버가 특정 IP만 허용하도록 설정됨
- Vercel 서버의 IP가 화이트리스트에 없음
- Azure 방화벽이 요청을 차단함
- CORS 설정 문제

**해결 방법:**
1. Dify 서버 관리자에게 Vercel IP 범위를 허용 목록에 추가 요청
2. Azure 방화벽 설정에서 Vercel IP 허용
3. 임시로 IP 제한을 해제하고 테스트
4. Dify 서버의 CORS 설정 확인

### 5. Authorization 헤더 형식 문제

**현재 형식:** `Bearer {API_KEY}`

**가능한 원인:**
- 자체 호스팅 Dify 서버가 다른 인증 방식을 사용
- 헤더 이름이 다를 수 있음 (예: `X-API-Key`)

**해결 방법:**
1. Dify 서버 관리자에게 인증 방식 확인
2. Dify API 문서에서 정확한 헤더 형식 확인
3. 서버 로그에서 기대하는 헤더 형식 확인

### 6. 네트워크 연결 문제

**가능한 원인:**
- Vercel에서 Azure로의 네트워크 연결 문제
- 타임아웃
- 방화벽 차단

**해결 방법:**
1. Vercel 서버 로그 확인
2. 네트워크 타임아웃 설정 확인
3. Azure 방화벽 로그 확인

## 디버깅 방법

### 1. 브라우저 개발자 도구 확인
1. 브라우저에서 F12를 눌러 개발자 도구 열기
2. Network 탭에서 `/api/dify` 요청 확인
3. 요청 헤더와 응답 확인

### 2. Vercel 로그 확인
1. Vercel 대시보드에서 Functions 로그 확인
2. `[Dify Proxy]`로 시작하는 로그 메시지 확인
3. 실제 서버 응답 내용 확인

### 3. Dify 서버 로그 확인
1. Dify 서버 관리자에게 로그 확인 요청
2. 인증 실패 원인 확인
3. 요청이 서버에 도달했는지 확인

### 4. 수동 테스트 (curl)
```bash
# API Key를 YOUR_API_KEY로 교체
curl -X POST http://ai-platform-deploy.koreacentral.cloudapp.azure.com/v1/chat-messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {},
    "query": "테스트",
    "response_mode": "blocking",
    "user": "test-user"
  }'
```

## 체크리스트

다음 항목들을 순서대로 확인하세요:

- [ ] API Key가 Dify 대시보드에서 새로 발급받은 것인가?
- [ ] API Key를 직접 복사-붙여넣기했는가? (수동 입력하지 않았는가?)
- [ ] API Key 앞뒤에 공백이 없는가?
- [ ] Dify 애플리케이션이 "게시" 상태인가?
- [ ] 워크플로우가 게시되었는가?
- [ ] Dify API Base URL이 정확한가?
- [ ] Dify 서버 관리자에게 접근 제한 설정을 확인했는가?
- [ ] Vercel 로그에서 실제 에러 메시지를 확인했는가?
- [ ] Dify 서버 로그를 확인했는가?

## 추가 도움

문제가 계속되면 다음 정보를 수집하여 공유하세요:
1. Vercel 로그의 `[Dify Proxy]` 메시지 전체
2. 브라우저 개발자 도구의 Network 탭 스크린샷
3. Dify 서버 로그 (가능한 경우)
4. Dify API 문서 링크 (자체 호스팅인 경우)

