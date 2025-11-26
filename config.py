"""
데이터베이스 및 애플리케이션 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Oracle DB 설정
    ORACLE_USER: str
    ORACLE_PASSWORD: str
    ORACLE_DSN: str  # 예: "localhost:1521/XEPDB1" 또는 "localhost:1521/XE"
    
    # 애플리케이션 설정
    APP_NAME: str = "Question Answer API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Dify AI 설정 (선택 사항)
    DIFY_API_BASE: Optional[str] = None  # 예: "http://.../v1"
    DIFY_API_KEY: Optional[str] = None   # 예: "app-xxxxxxxx"
    DIFY_USER_ID: str = "oracle-agent-user"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 전역 설정 인스턴스
settings = Settings()

