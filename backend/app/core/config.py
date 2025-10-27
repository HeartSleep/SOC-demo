from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # App settings
    APP_NAME: str = "SOC Security Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security - JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Security - CSRF
    CSRF_SECRET_KEY: str = "csrf-secret-key-change-in-production"
    CSRF_TOKEN_EXPIRE_MINUTES: int = 60

    # Security - Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100

    # Security - MFA/2FA
    MFA_ENABLED: bool = False
    MFA_ISSUER_NAME: str = "SOC_Security_Platform"

    # Database - PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://soc_admin:soc_secure_password_2024@localhost:5432/soc_platform"
    POSTGRES_USER: str = "soc_admin"
    POSTGRES_PASSWORD: str = "soc_secure_password_2024"
    POSTGRES_DB: str = "soc_platform"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Database - Connection Pool
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = "redis123456"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True

    # WebSocket
    WS_MESSAGE_QUEUE: str = "redis://localhost:6379/3"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080"
    ]

    # External APIs
    FOFA_API_EMAIL: Optional[str] = None
    FOFA_API_KEY: Optional[str] = None

    # File Upload
    UPLOAD_DIR: str = "data/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "data/logs"

    # Scanning Configuration
    MAX_CONCURRENT_SCANS: int = 10
    SCAN_TIMEOUT: int = 300  # 5 minutes
    NMAP_PATH: str = "/usr/bin/nmap"

    # Vulnerability Detection
    XRAY_PATH: Optional[str] = None
    NUCLEI_PATH: Optional[str] = None


settings = Settings()