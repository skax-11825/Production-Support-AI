# GitHub 저장소 설정 가이드

현재 저장소가 Azure DevOps에 있어서 Vercel에서 직접 연결이 안 됩니다.
GitHub에 새 저장소를 만들어서 연결하는 방법입니다.

## 방법 1: GitHub에 새 저장소 만들기 (권장)

### 1단계: GitHub에서 저장소 생성

1. https://github.com 접속 및 로그인
2. 우측 상단 "+" 클릭 → "New repository"
3. 저장소 설정:
   - **Repository name**: `inform-note-agent` (원하는 이름)
   - **Description**: "Error Lense AI Agent with Dify Integration"
   - **Public** 또는 **Private** 선택
   - **Initialize this repository with** 체크 해제 (이미 코드가 있으므로)
4. "Create repository" 클릭

### 2단계: 로컬 코드를 GitHub에 푸시

터미널에서 실행:

```bash
cd "/Users/jeonghoon/Desktop/Project/Inform Note/Agent"

# GitHub 원격 저장소 추가 (위에서 만든 저장소 URL 사용)
git remote add github https://github.com/YOUR_USERNAME/inform-note-agent.git

# GitHub에 푸시
git push github main
```

**주의**: `YOUR_USERNAME`을 본인의 GitHub 사용자명으로 변경하세요.

### 3단계: Vercel에서 연결

1. Vercel 대시보드에서 "Add New Project"
2. 이제 GitHub 저장소가 보일 것입니다
3. 저장소 선택
4. **Root Directory**: `ai-agent-ui` 선택
5. "Deploy" 클릭

## 방법 2: Vercel CLI 사용 (GitHub 없이)

GitHub 없이 직접 배포하는 방법:

### 1단계: Vercel CLI 설치

```bash
npm install -g vercel
```

### 2단계: 로그인

```bash
vercel login
```

### 3단계: 배포

```bash
cd "/Users/jeonghoon/Desktop/Project/Inform Note/Agent/ai-agent-ui"
vercel
```

질문에 답변:
- Set up and deploy? → Yes
- Which scope? → 본인 계정 선택
- Link to existing project? → No
- Project name? → 원하는 이름 (예: inform-note-agent)
- Directory? → `./` (현재 디렉토리)
- Override settings? → No

### 4단계: 프로덕션 배포

```bash
vercel --prod
```

## 방법 3: GitLab 사용

GitLab도 Vercel에서 지원합니다:

1. https://gitlab.com 접속
2. 새 프로젝트 생성
3. 코드 푸시
4. Vercel에서 GitLab 연결

## 추천 방법

**방법 1 (GitHub)**을 추천합니다:
- ✅ Vercel과 완벽 통합
- ✅ 자동 배포 설정 쉬움
- ✅ 무료
- ✅ 가장 널리 사용됨

## 다음 단계

GitHub 저장소를 만들고 푸시한 후:
1. Vercel에서 저장소 선택
2. Root Directory: `ai-agent-ui` 선택
3. Deploy 클릭

완료!

