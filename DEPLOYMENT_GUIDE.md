# 배포 가이드

이 문서는 Error Lense UI를 다른 사람들이 사용할 수 있도록 배포하는 방법을 설명합니다.

## 전체 구조

```
[사용자들]
    ↓ 브라우저 접속
[Vercel 배포된 Next.js UI]
    ↓ 각자 설정한 Dify API 호출
[각자의 Dify 워크플로우]
    ↓ Tool 호출
[Ngrok 터널을 통한 FastAPI 서버]
    ↓ SQL 쿼리
[로컬 Oracle DB]
```

## 1단계: Vercel에 배포 (무료)

### 1.1 Vercel 계정 생성
1. https://vercel.com 접속
2. GitHub 계정으로 로그인 (또는 이메일로 가입)

### 1.2 프로젝트 연결
1. Vercel 대시보드에서 "Add New Project" 클릭
2. GitHub 저장소 선택
3. 프로젝트 설정:
   - **Root Directory**: `ai-agent-ui` 선택
   - **Framework Preset**: Next.js (자동 감지)
   - **Build Command**: `npm run build` (기본값)
   - **Output Directory**: `.next` (기본값)

### 1.3 배포 설정
- **Environment Variables**: 필요 없음 (사용자별 설정은 localStorage 사용)
- **Deploy**: "Deploy" 클릭

### 1.4 자동 배포 설정
- GitHub에 푸시하면 자동으로 배포됨
- Vercel이 자동으로 감지하여 재배포

## 2단계: FastAPI 서버 및 Ngrok 설정

### 2.1 FastAPI 서버 실행
```bash
cd "/Users/jeonghoon/Desktop/Project/Inform Note/Agent"
python main.py
# 또는
./start_server.sh
```

### 2.2 Ngrok 터널 시작
```bash
cd "/Users/jeonghoon/Desktop/Project/Inform Note/Agent"
./start_ngrok.sh
```

또는 직접 실행:
```bash
ngrok http 8000
```

### 2.3 Ngrok URL 확인
- Ngrok 대시보드: http://localhost:4040
- 또는 터미널에서 표시되는 URL 확인
- 예: `https://xxxx-xxxx-xxxx.ngrok-free.dev`

## 3단계: 사용자 가이드

### 3.1 사용자 접속
1. 배포된 Vercel URL로 접속
   - 예: `https://your-project.vercel.app/error-lense`

### 3.2 설정 방법
1. 채팅창 우측 상단의 설정 아이콘 클릭
2. 다음 정보 입력:
   - **Dify API Base URL**: 각자의 Dify 서버 URL
     - 예: `https://api.dify.ai/v1`
     - 또는 자체 호스팅: `https://your-dify-server.com/v1`
   - **Dify API Key**: 각자의 Dify API Key
   - **API 서버 URL**: Ngrok URL (모든 사용자가 공유)
     - 예: `https://xxxx-xxxx-xxxx.ngrok-free.dev`
3. "저장" 클릭
4. "확인" 버튼으로 연결 상태 확인

### 3.3 사용 시작
- 설정 완료 후 채팅창에서 질문 입력
- 각자의 Dify 워크플로우가 실행됨

## 4단계: 코드 업데이트 및 자동 배포

### 4.1 코드 수정
```bash
# 로컬에서 코드 수정
cd "/Users/jeonghoon/Desktop/Project/Inform Note/Agent/ai-agent-ui"
# 파일 수정...
```

### 4.2 GitHub에 푸시
```bash
cd "/Users/jeonghoon/Desktop/Project/Inform Note/Agent"
git add .
git commit -m "Update UI"
git push
```

### 4.3 자동 배포
- Vercel이 자동으로 변경사항 감지
- 약 1-2분 내에 자동 배포 완료
- 사용자들은 새로고침하면 최신 버전 사용 가능

## 대안: 다른 배포 옵션

### Netlify (무료)
1. https://netlify.com 접속
2. GitHub 저장소 연결
3. Build settings:
   - Build command: `cd ai-agent-ui && npm install && npm run build`
   - Publish directory: `ai-agent-ui/.next`

### GitHub Pages (정적 사이트)
- Next.js는 정적 사이트로 빌드 필요
- `next export` 사용 (Next.js 13+에서는 `output: 'export'`)

## 주의사항

### Ngrok 제한사항
- 무료 플랜: 세션당 2시간, 재시작 시 URL 변경
- 해결책:
  1. Ngrok 계정 업그레이드 (고정 URL)
  2. 또는 자동 재시작 스크립트 사용

### CORS 설정
- FastAPI 서버의 CORS 설정이 모든 origin을 허용하는지 확인
- 현재 설정: `allow_origins=["*"]` (이미 설정됨)

### 보안 고려사항
- API Key는 사용자 브라우저의 localStorage에 저장
- 서버에 전송되지 않으므로 안전함
- 하지만 HTTPS 사용 권장 (Vercel은 기본 HTTPS)

## 문제 해결

### 배포 실패
- Vercel 로그 확인
- `npm run build` 로컬에서 테스트
- TypeScript 오류 확인 (`ignoreBuildErrors: true` 설정됨)

### Ngrok 연결 실패
- Ngrok 세션 확인: http://localhost:4040
- FastAPI 서버가 실행 중인지 확인
- 포트 8000이 열려있는지 확인

### 사용자 연결 실패
- Dify API URL 확인
- API Key 유효성 확인
- 브라우저 콘솔에서 오류 확인

## 비용

- **Vercel**: 무료 플랜 (개인 프로젝트)
  - 대역폭: 100GB/월
  - 빌드 시간: 100시간/월
- **Ngrok**: 무료 플랜
  - 세션당 2시간
  - 고정 URL은 유료 ($8/월)

## 요약

1. ✅ Vercel에 배포 (무료, 자동 배포)
2. ✅ FastAPI 서버 로컬 실행 + Ngrok 터널
3. ✅ 사용자별 설정 (localStorage)
4. ✅ GitHub 푸시 시 자동 배포

이 구조로 다른 사람들이 각자의 Dify 설정으로 에이전트를 사용할 수 있습니다!

