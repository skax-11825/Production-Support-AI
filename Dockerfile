FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libaio1 \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Oracle Instant Client (기본/SDK) 설치
RUN curl -SLo instantclient-basic.zip https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linux.x64-23.4.0.0.0dbru.zip && \
    curl -SLo instantclient-sdk.zip https://download.oracle.com/otn_software/linux/instantclient/instantclient-sdk-linux.x64-23.4.0.0.0dbru.zip && \
    unzip instantclient-basic.zip && \
    unzip instantclient-sdk.zip && \
    rm instantclient-basic.zip instantclient-sdk.zip && \
    mv instantclient_23_4 /opt/oracle && \
    echo /opt/oracle > /etc/ld.so.conf.d/oracle-instantclient.conf && ldconfig

# Python 패키지 설치
ENV LD_LIBRARY_PATH=/opt/oracle:$LD_LIBRARY_PATH
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 실행 스크립트 권한 부여
RUN chmod +x docker-entrypoint.sh scripts/bootstrap_db.sh

# 포트 노출
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    SKIP_DB_BOOTSTRAP=0 \
    ORACLE_HOME=/opt/oracle

ENTRYPOINT ["./docker-entrypoint.sh"]

