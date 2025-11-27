# ngrok 설정 가이드 (초보자용)

## ngrok이 뭔가요?
ngrok은 로컬 컴퓨터에서 실행 중인 서버를 인터넷을 통해 접근할 수 있게 해주는 도구입니다.
마치 "터널"을 만들어서 원격 서버(Dify)가 로컬 컴퓨터에 접근할 수 있게 해줍니다.

## 1단계: ngrok 계정 만들기

1. 웹 브라우저를 엽니다
2. 다음 주소로 이동합니다: https://dashboard.ngrok.com/signup
3. 이메일 주소를 입력하고 계정을 만듭니다 (무료입니다)
4. 이메일 인증을 완료합니다

## 2단계: authtoken 받기

1. 로그인 후 다음 주소로 이동합니다: https://dashboard.ngrok.com/get-started/your-authtoken
2. 화면에 표시된 "Your Authtoken"을 복사합니다
   - 예: `2abc123def456ghi789jkl012mno345pq_6r7s8t9u0v1w2x3y4z5`

## 3단계: authtoken 설정하기

터미널에서 다음 명령어를 실행합니다:
```bash
export PATH="$HOME/bin:$PATH"
ngrok config add-authtoken <여기에_복사한_authtoken_붙여넣기>
```

예시:
```bash
ngrok config add-authtoken 2abc123def456ghi789jkl012mno345pq_6r7s8t9u0v1w2x3y4z5
```

성공하면 "Authtoken saved to configuration file" 메시지가 나타납니다.

## 4단계: ngrok 실행하기

로컬 서버(포트 8001)를 외부에 노출:
```bash
export PATH="$HOME/bin:$PATH"
ngrok http 8001
```

실행하면 다음과 같은 화면이 나타납니다:
```
ngrok

Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.33.1
Region                        Asia Pacific (ap)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8001

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**중요**: `Forwarding` 줄에 있는 `https://abc123.ngrok-free.app` 주소를 복사하세요!
이 주소가 외부에서 접근 가능한 주소입니다.

## 5단계: Dify HTTP 노드에 주소 입력

1. Dify 워크플로우 편집기로 돌아갑니다
2. HTTP 요청 노드의 URL을 다음과 같이 변경합니다:
   - 기존: `http://localhost:8001/ask`
   - 변경: `https://abc123.ngrok-free.app/ask` (ngrok에서 받은 주소 사용)

## 주의사항

⚠️ **ngrok 무료 버전의 제한사항:**
- ngrok을 종료하면 주소가 변경됩니다
- 매번 실행할 때마다 새로운 주소가 생성됩니다
- 세션이 2시간 후 자동 종료될 수 있습니다

💡 **해결책:**
- ngrok을 계속 실행 상태로 유지하세요
- 주소가 변경되면 Dify HTTP 노드의 URL도 업데이트해야 합니다
- 더 안정적인 사용을 원하면 ngrok 유료 플랜을 사용하거나 Azure에 배포하는 것을 고려하세요

## 문제 해결

### ngrok이 실행되지 않아요
- authtoken을 제대로 설정했는지 확인하세요
- `ngrok config add-authtoken` 명령어를 다시 실행해보세요

### 주소가 계속 바뀌어요
- ngrok 무료 버전의 제한사항입니다
- ngrok을 종료하지 않고 계속 실행 상태로 유지하세요

### 연결이 안 돼요
- 로컬 서버(포트 8001)가 실행 중인지 확인하세요
- ngrok이 정상적으로 실행 중인지 확인하세요

