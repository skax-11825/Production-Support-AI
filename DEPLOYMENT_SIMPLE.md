# 배포 가이드 (간단 버전)

## 목표
- 다른 사람들이 각자의 Dify API Key와 URL을 사용해서 에이전트를 사용할 수 있도록 함
- 모든 기능이 정상 작동해야 함
- 코드 변경 시 자동 반영

## 전체 구조

```
[다른 사용자들]
    ↓ 브라우저 접속
[Vercel에 배포된 UI]
    ↓ 각자 설정한 Dify API 호출
[각자의 Dify 워크플로우]
    ↓ Tool 호출
[Ngrok을 통한 당신의 FastAPI 서버]
    ↓ SQL 쿼리
[당신의 로컬 Oracle DB]
```

## 배포 방법

### 1단계: Vercel에 배포 (5분)

1. **Vercel 계정 생성**
   - https://vercel.com 접속
   - GitHub 계정으로 로그인

2. **프로젝트 연결**
   - "Add New Project" 클릭
   - GitHub 저장소 선택
   - **Root Directory**: `ai-agent-ui` 선택 ⚠️ 중요!
   - Framework는 자동으로 Next.js 감지됨
   - "Deploy" 클릭

3. **배포 완료**
   - 약 2-3분 후 배포 완료
   - 배포된 URL 확인 (예: `https://your-project.vercel.app`)

### 2단계: 당신의 로컬 서버 설정

```bash
# FastAPI 서버 실행
cd "/Users/jeonghoon/Desktop/Project/Inform Note/Agent"
python main.py

# 다른 터미널에서 Ngrok 실행
ngrok http 8000
```

Ngrok URL 확인 (예: `https://xxxx-xxxx.ngrok-free.dev`)

### 3단계: 사용자 가이드 제공

사용자들에게 다음을 알려주세요:

1. **배포된 URL 접속**
   - 예: `https://your-project.vercel.app/error-lense`

2. **설정 버튼 클릭** (채팅창 우측 상단)

3. **각자의 정보 입력**
   - **Dify API Base URL**: 각자의 Dify 서버 URL
     - 예: `https://api.dify.ai/v1`
     - 또는: `https://their-dify-server.com/v1`
   - **Dify API Key**: 각자의 Dify API Key
   - **API 서버 URL**: 당신의 Ngrok URL (모든 사용자가 동일)
     - 예: `https://xxxx-xxxx.ngrok-free.dev`

4. **저장 후 사용**
   - "저장" 클릭
   - "확인" 버튼으로 연결 상태 확인
   - 채팅창에서 질문 입력

## 코드 업데이트 시

### 자동 배포 (GitHub 푸시만 하면 됨)

```bash
# 코드 수정 후
git add .
git commit -m "Update UI"
git push
```

- Vercel이 자동으로 감지하여 재배포
- 약 1-2분 후 사용자들이 새로고침하면 최신 버전 사용 가능

## 중요 사항

### ✅ 장점
- **무료**: Vercel 무료 플랜으로 충분
- **자동 배포**: GitHub 푸시만 하면 자동 반영
- **사용자별 설정**: 각자의 Dify API Key 사용 가능
- **모든 기능 사용 가능**: 설정만 하면 바로 사용

### ⚠️ 주의사항
- **Ngrok URL 변경**: Ngrok 재시작 시 URL이 변경되면 사용자들에게 새 URL 알려줘야 함
- **FastAPI 서버**: 항상 실행 중이어야 함
- **Oracle DB**: 로컬에서 접근 가능해야 함

## Ngrok URL 고정 (선택사항)

Ngrok 무료 플랜은 URL이 변경되므로, 고정 URL이 필요하면:
- Ngrok 유료 플랜 ($8/월) - 고정 URL 제공
- 또는 사용자들에게 URL 변경 시 알림

## 요약

1. ✅ Vercel에 배포 (무료, 5분)
2. ✅ 로컬 FastAPI + Ngrok 실행
3. ✅ 사용자들이 각자 설정 입력
4. ✅ GitHub 푸시 시 자동 배포

이제 다른 사람들이 각자의 Dify 설정으로 에이전트를 사용할 수 있습니다!

