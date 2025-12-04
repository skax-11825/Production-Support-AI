# 배포 가이드 (간단 버전)

## 빠른 시작

### 1. Vercel에 배포

1. https://vercel.com 접속 및 로그인
2. "Add New Project" 클릭
3. GitHub 저장소 선택
4. **Root Directory**: `ai-agent-ui` 선택
5. "Deploy" 클릭

### 2. Ngrok 설정 (로컬 서버용)

```bash
# FastAPI 서버 실행
python main.py

# 다른 터미널에서 Ngrok 실행
ngrok http 8000
```

### 3. 사용자 설정

배포된 URL로 접속 후:
1. 설정 버튼 클릭
2. Dify API 정보 입력
3. API 서버 URL에 Ngrok URL 입력
4. 저장 후 사용

## 자동 배포

GitHub에 푸시하면 Vercel이 자동으로 배포합니다.

```bash
git add .
git commit -m "Update"
git push
```

## 배포 URL 확인

Vercel 대시보드에서 배포된 URL 확인:
- 예: `https://your-project.vercel.app`

