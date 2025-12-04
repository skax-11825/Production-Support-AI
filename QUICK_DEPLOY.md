# 빠른 배포 가이드

## 문제: Vercel에서 저장소를 찾을 수 없음

현재 저장소가 Azure DevOps에 있어서 Vercel에서 직접 연결이 안 됩니다.

## 해결 방법: GitHub에 푸시하기

### 1. GitHub 저장소 만들기

1. https://github.com → 로그인
2. 우측 상단 "+" → "New repository"
3. 이름 입력 (예: `inform-note-agent`)
4. **Initialize 체크 해제** (코드가 이미 있으므로)
5. "Create repository" 클릭

### 2. GitHub에 코드 푸시

터미널에서 실행:

```bash
cd "/Users/jeonghoon/Desktop/Project/Inform Note/Agent"

# GitHub 원격 저장소 추가
git remote add github https://github.com/YOUR_USERNAME/inform-note-agent.git

# GitHub에 푸시
git push github main
```

**⚠️ 중요**: `YOUR_USERNAME`을 본인의 GitHub 사용자명으로 변경하세요!

### 3. Vercel에서 연결

1. Vercel → "Add New Project"
2. 이제 GitHub 저장소가 보입니다!
3. 저장소 선택
4. **Root Directory**: `ai-agent-ui` 선택 ⚠️ 중요!
5. "Deploy" 클릭

## 완료!

이제 배포가 시작됩니다. 2-3분 후 배포된 URL을 받을 수 있습니다.

## 자동 배포 설정

앞으로는 GitHub에 푸시하면 자동으로 배포됩니다:

```bash
git add .
git commit -m "Update"
git push github main
```

→ Vercel이 자동으로 재배포합니다!

