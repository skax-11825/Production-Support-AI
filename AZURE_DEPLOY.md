# Azure 배포 가이드

## 배포 방법

### 방법 1: Azure Container Instances (ACI) 사용

#### 1. Azure CLI 로그인
```bash
az login
```

#### 2. 리소스 그룹 생성 (없는 경우)
```bash
az group create --name question-answer-api-rg --location koreacentral
```

#### 3. Azure Container Registry (ACR) 생성
```bash
az acr create --resource-group question-answer-api-rg \
  --name questionanswerapiacr \
  --sku Basic
```

#### 4. 이미지 빌드 및 푸시
```bash
# ACR에 로그인
az acr login --name questionanswerapiacr

# 이미지 빌드 및 푸시
az acr build --registry questionanswerapiacr \
  --image question-answer-api:latest .
```

#### 5. Container Instance 배포
```bash
az container create \
  --resource-group question-answer-api-rg \
  --name question-answer-api \
  --image questionanswerapiacr.azurecr.io/question-answer-api:latest \
  --registry-login-server questionanswerapiacr.azurecr.io \
  --registry-username questionanswerapiacr \
  --registry-password <ACR_PASSWORD> \
  --dns-name-label question-answer-api \
  --ports 8000 \
  --environment-variables \
    ORACLE_USER=system \
    ORACLE_PASSWORD=oracle \
    ORACLE_DSN=your-oracle-host:1521/FREEPDB1 \
    DIFY_API_BASE=https://ai-platform-deploy.koreacentral.cloudapp.azure.com:3000/v1 \
    DIFY_API_KEY=your-dify-api-key \
    DIFY_USER_ID=chaejh@sk.com \
    DEBUG=False
```

### 방법 2: Azure App Service 사용

#### 1. Docker 이미지 준비 (위의 ACR 단계 참고)

#### 2. App Service 배포
```bash
az webapp create \
  --resource-group question-answer-api-rg \
  --plan question-answer-api-plan \
  --name question-answer-api-app \
  --deployment-container-image-name questionanswerapiacr.azurecr.io/question-answer-api:latest

# 환경 변수 설정
az webapp config appsettings set \
  --resource-group question-answer-api-rg \
  --name question-answer-api-app \
  --settings \
    ORACLE_USER=system \
    ORACLE_PASSWORD=oracle \
    ORACLE_DSN=your-oracle-host:1521/FREEPDB1 \
    DIFY_API_BASE=https://ai-platform-deploy.koreacentral.cloudapp.azure.com:3000/v1 \
    DIFY_API_KEY=your-dify-api-key \
    DIFY_USER_ID=chaejh@sk.com \
    DEBUG=False \
    WEBSITES_PORT=8000
```

### 방법 3: 같은 Azure 환경의 VM/컨테이너에 배포

Dify가 실행 중인 Azure 환경과 같은 네트워크에 배포하면 내부 IP로 접근 가능합니다.

#### 내부 네트워크 접근 URL 형식
```
http://<내부-IP>:8000/ask
또는
http://<서비스-이름>:8000/ask
```

## Dify HTTP 노드 설정

배포 후 Dify HTTP 노드에서 사용할 URL:

### Azure Container Instances 사용 시
```
http://question-answer-api.koreacentral.azurecontainer.io/ask
```

### Azure App Service 사용 시
```
https://question-answer-api-app.azurewebsites.net/ask
```

### 같은 네트워크 내부 접근 시
```
http://<내부-IP>:8000/ask
또는
http://question-answer-api:8000/ask  (서비스 이름 사용)
```

## 환경 변수 설정

배포 시 다음 환경 변수를 설정해야 합니다:

- `ORACLE_USER`: Oracle DB 사용자명
- `ORACLE_PASSWORD`: Oracle DB 비밀번호
- `ORACLE_DSN`: Oracle DB 연결 문자열 (Azure 내부 네트워크 주소 사용)
- `DIFY_API_BASE`: Dify API 기본 URL
- `DIFY_API_KEY`: Dify API 키
- `DIFY_USER_ID`: Dify 사용자 ID
- `DEBUG`: False (프로덕션)

## Oracle DB 연결

Azure에 배포된 Oracle DB에 연결하려면:
- Azure 내부 네트워크의 Oracle DB 주소 사용
- 또는 Azure Database for Oracle 사용 시 연결 문자열 사용

## 테스트

배포 후 헬스 체크:
```bash
curl http://<배포-URL>/health
```

질문 API 테스트:
```bash
curl -X POST http://<배포-URL>/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "테스트 질문",
    "context": ""
  }'
```

