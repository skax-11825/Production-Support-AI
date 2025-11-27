# Dify HTTP 노드 연결 가이드

## 현재 서버 상태
- **서버 주소**: `http://localhost:8001` (로컬 테스트용)
- **배포 주소**: 배포 환경에 따라 변경 필요
- **헬스 체크**: `GET /health`
- **질문-답변 API**: `POST /ask`

## Dify HTTP 노드 설정 방법

### 1. Dify 워크플로우에서 HTTP 노드 추가
1. Dify 워크플로우 편집기에서 **HTTP Request** 노드를 추가합니다
2. 노드 설정을 엽니다

### 2. HTTP 노드 설정

#### 기본 설정
- **Method**: `POST`
- **URL**: 
  - 로컬 테스트: `http://localhost:8001/ask`
  - 배포 환경: `https://your-domain.com/ask` (실제 배포 주소로 변경)

#### Headers 설정
```
Content-Type: application/json
```

#### Body 설정 (JSON)
```json
{
  "question": "{{#question#}}",
  "context": "{{#context#}}"
}
```

또는 Dify 변수 사용:
- `question`: 사용자 질문 변수
- `context`: (선택사항) 추가 컨텍스트 변수

### 3. 응답 처리

#### 응답 형식
```json
{
  "answer": "답변 내용",
  "question": "원본 질문",
  "success": true
}
```

#### Dify에서 응답 사용
- `{{#response.answer#}}`: 답변 내용 추출
- `{{#response.success#}}`: 성공 여부 확인

### 4. 테스트 예시

#### 간단한 테스트
```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "시스템 상태를 알려줘",
    "context": "테스트"
  }'
```

#### 예상 응답
```json
{
  "answer": "요약된 오케스트레이션 처리 흐름...",
  "question": "시스템 상태를 알려줘",
  "success": true
}
```

## 엔드포인트 상세

### POST /ask
질문을 받아 답변을 제공하는 메인 엔드포인트

**Request Body:**
```json
{
  "question": "string (필수)",
  "context": "string (선택사항)"
}
```

**Response:**
```json
{
  "answer": "string",
  "question": "string",
  "success": boolean
}
```

### GET /health
서버 상태 확인 엔드포인트

**Response:**
```json
{
  "status": "healthy" | "unhealthy",
  "database_connected": boolean,
  "dify_enabled": boolean
}
```

## 주의사항

1. **포트 변경**: 현재 로컬에서는 8001 포트를 사용 중입니다. 배포 시 포트를 확인하세요.
2. **HTTPS**: 배포 환경에서는 HTTPS를 사용해야 할 수 있습니다.
3. **인증**: 필요시 API 키나 토큰 인증을 추가할 수 있습니다.
4. **타임아웃**: Dify HTTP 노드의 타임아웃 설정을 충분히 길게 설정하세요 (30초 이상 권장).

## 문제 해결

### 연결 실패 시
1. 서버가 실행 중인지 확인: `curl http://localhost:8001/health`
2. 방화벽 설정 확인
3. Dify에서 접근 가능한 주소인지 확인 (로컬호스트는 외부에서 접근 불가)

### 응답 형식 오류
- 응답이 JSON 형식인지 확인
- `Content-Type: application/json` 헤더 확인


