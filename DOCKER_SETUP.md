# Docker Oracle DB 연결 가이드

## Docker Oracle 컨테이너 확인

현재 실행 중인 Oracle 컨테이너:
- 컨테이너 이름: `oracle`
- 이미지: `gvenzl/oracle-free`
- 포트: `1521:1521`

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# Oracle 데이터베이스 설정 (Docker)
ORACLE_USER=system
ORACLE_PASSWORD=your_password
ORACLE_DSN=localhost:1521/FREEPDB1
```

### gvenzl/oracle-free 이미지 기본 설정

이 이미지의 경우 일반적으로:
- **기본 사용자**: `system` 또는 컨테이너 실행 시 설정한 사용자
- **Service Name**: `FREEPDB1` (플러그 가능 데이터베이스)
- **포트**: `1521`

### DSN 형식 확인 방법

Docker 컨테이너에서 Service Name 확인:
```bash
docker exec oracle sqlplus -s system/your_password <<EOF
SELECT name FROM v\$pdbs;
EXIT;
EOF
```

또는:
```bash
docker exec oracle lsnrctl status
```

### 일반적인 DSN 형식

1. **Service Name 사용** (권장):
   ```
   ORACLE_DSN=localhost:1521/FREEPDB1
   ```

2. **SID 사용**:
   ```
   ORACLE_DSN=localhost:1521/XE
   ```

3. **TNS 형식** (tnsnames.ora 사용 시):
   ```
   ORACLE_DSN=ORCL
   ```

## 연결 테스트

연결 테스트 스크립트 실행:
```bash
python test_connection.py
```

성공하면 다음과 같은 출력이 표시됩니다:
```
==================================================
Oracle DB 연결 테스트
==================================================
DSN: localhost:1521/FREEPDB1
User: system
Password: ********
--------------------------------------------------
✓ 연결 풀 생성 성공
✓ 데이터베이스 연결 성공!
✓ 현재 사용자: SYSTEM
✓ 데이터베이스 이름: FREE
==================================================
연결 테스트 완료!
```

## 문제 해결

### 1. 연결 오류: ORA-12541: TNS:no listener
**원인**: Oracle 리스너가 실행되지 않음
**해결**:
```bash
# 컨테이너 상태 확인
docker ps

# 컨테이너 재시작
docker restart oracle

# 리스너 상태 확인
docker exec oracle lsnrctl status
```

### 2. 연결 오류: ORA-01017: invalid username/password
**원인**: 잘못된 사용자명 또는 비밀번호
**해결**:
- `.env` 파일의 `ORACLE_USER`와 `ORACLE_PASSWORD` 확인
- Docker 컨테이너 실행 시 설정한 비밀번호와 일치하는지 확인

### 3. 연결 오류: ORA-12514: TNS:listener does not currently know of service
**원인**: 잘못된 Service Name 또는 SID
**해결**:
```bash
# Service Name 확인
docker exec oracle sqlplus -s system/your_password <<EOF
SELECT name FROM v\$pdbs;
EXIT;
EOF

# 또는 SID 확인
docker exec oracle echo $ORACLE_SID
```

### 4. Oracle Instant Client 필요 오류
**원인**: `oracledb` 라이브러리가 Thin 모드로 작동하지 않음
**해결**:
- `oracledb` 2.0 이상은 기본적으로 Thin 모드를 사용하므로 추가 설치 불필요
- 만약 오류가 발생하면: `pip install --upgrade oracledb`

## Docker 컨테이너 관리 명령어

```bash
# 컨테이너 상태 확인
docker ps | grep oracle

# 컨테이너 로그 확인
docker logs oracle

# 컨테이너 재시작
docker restart oracle

# 컨테이너 중지
docker stop oracle

# 컨테이너 시작
docker start oracle

# SQL*Plus로 직접 연결 테스트
docker exec -it oracle sqlplus system/your_password@FREEPDB1
```

## API 서버 실행

연결이 확인되면 API 서버를 실행하세요:
```bash
python main.py
```

서버 실행 후 헬스 체크:
```bash
curl http://localhost:8000/health
```

응답 예시:
```json
{
  "status": "healthy",
  "database_connected": true
}
```

