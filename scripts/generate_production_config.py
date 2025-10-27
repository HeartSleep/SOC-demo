#!/usr/bin/env python3
"""
Production Environment Configuration Generator
Generates secure configuration for production deployment
"""
import os
import secrets
import string
import json
from pathlib import Path
from cryptography.fernet import Fernet
import hashlib
import base64


class ProductionConfigGenerator:
    """Generate secure production configuration"""

    def __init__(self, base_path="/Users/heart/Documents/Code/WEB/SOC"):
        self.base_path = Path(base_path)
        self.env_file = self.base_path / ".env.production"
        self.secrets_file = self.base_path / "secrets.json"

    def generate_secure_password(self, length=32):
        """Generate a cryptographically secure password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def generate_secret_key(self, length=64):
        """Generate a secure secret key"""
        return secrets.token_urlsafe(length)

    def generate_encryption_key(self):
        """Generate Fernet encryption key"""
        return Fernet.generate_key().decode()

    def generate_api_key(self):
        """Generate API key for external services"""
        return f"sk_{secrets.token_urlsafe(32)}"

    def create_production_env(self):
        """Create production .env file with secure defaults"""

        # Generate secure passwords and keys
        postgres_password = self.generate_secure_password()
        redis_password = self.generate_secure_password()
        jwt_secret = self.generate_secret_key()
        secret_key = self.generate_secret_key()
        csrf_secret = self.generate_secret_key()
        encryption_key = self.generate_encryption_key()

        production_config = f"""# Production Environment Configuration
# Generated securely - DO NOT COMMIT TO VERSION CONTROL

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# PostgreSQL Configuration
POSTGRES_USER=soc_prod_user
POSTGRES_PASSWORD={postgres_password}
POSTGRES_DB=soc_platform_prod
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://soc_prod_user:{postgres_password}@localhost:5432/soc_platform_prod

# PostgreSQL Backup Configuration
POSTGRES_BACKUP_ENABLED=true
POSTGRES_BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
POSTGRES_BACKUP_RETENTION_DAYS=30
POSTGRES_BACKUP_PATH=/var/backups/postgresql

# Redis Configuration
REDIS_PASSWORD={redis_password}
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://:{redis_password}@localhost:6379/0
REDIS_MAX_CONNECTIONS=100
REDIS_CONNECTION_TIMEOUT=5
REDIS_SOCKET_KEEPALIVE=true

# Application Security
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true

# CSRF Protection
CSRF_SECRET_KEY={csrf_secret}
CSRF_TOKEN_EXPIRE_MINUTES=60
CSRF_HEADER_NAME=X-CSRF-Token
CSRF_COOKIE_NAME=csrf_token
CSRF_COOKIE_SECURE=true
CSRF_COOKIE_HTTPONLY=true
CSRF_COOKIE_SAMESITE=strict

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_BURST=50
RATE_LIMIT_STORAGE=redis
LOGIN_RATE_LIMIT_PER_MINUTE=5
API_RATE_LIMIT_PER_HOUR=1000

# MFA/2FA Configuration
MFA_ENABLED=true
MFA_ISSUER_NAME=SOC_Security_Platform_Prod
MFA_QR_SIZE=256
MFA_BACKUP_CODES_COUNT=10
MFA_TIME_WINDOW=1

# Session Management
SESSION_LIFETIME_HOURS=8
SESSION_IDLE_TIMEOUT_MINUTES=30
SESSION_SECURE_COOKIE=true
SESSION_HTTPONLY=true
SESSION_SAMESITE=strict
MAX_SESSIONS_PER_USER=3

# Security Headers
SECURITY_HEADERS_ENABLED=true
HSTS_MAX_AGE=31536000
HSTS_INCLUDE_SUBDOMAINS=true
HSTS_PRELOAD=true
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
X_FRAME_OPTIONS=DENY
X_CONTENT_TYPE_OPTIONS=nosniff
REFERRER_POLICY=strict-origin-when-cross-origin

# SSL/TLS Configuration
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/soc-platform.crt
SSL_KEY_PATH=/etc/ssl/private/soc-platform.key
SSL_DH_PARAM_PATH=/etc/ssl/certs/dhparam.pem
SSL_PROTOCOLS=TLSv1.2,TLSv1.3
SSL_CIPHERS=ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS

# CORS Configuration
BACKEND_CORS_ORIGINS=["https://soc-platform.com","https://www.soc-platform.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=3600

# Celery Configuration
CELERY_BROKER_URL=redis://:{redis_password}@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:{redis_password}@localhost:6379/2
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# WebSocket Configuration
WS_MESSAGE_QUEUE=redis://:{redis_password}@localhost:6379/3
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=1000
WS_MAX_MESSAGE_SIZE=65536

# Database Connection Pool
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=false
DB_POOL_PRE_PING=true
DB_STATEMENT_TIMEOUT=30000

# Monitoring & Logging
LOGGING_ENABLED=true
LOG_DIR=/var/log/soc-platform
LOG_FILE_MAX_SIZE=100MB
LOG_FILE_BACKUP_COUNT=10
LOG_FORMAT=json
SENTRY_DSN=
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
METRICS_ENABLED=true

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@soc-platform.com
SMTP_FROM_NAME=SOC Security Platform

# File Upload Configuration
UPLOAD_DIR=/var/data/soc-platform/uploads
UPLOAD_MAX_SIZE=52428800  # 50MB
UPLOAD_ALLOWED_EXTENSIONS=.pdf,.doc,.docx,.txt,.json,.xml,.csv,.zip
UPLOAD_SCAN_ON_UPLOAD=true
UPLOAD_QUARANTINE_PATH=/var/data/soc-platform/quarantine

# Vulnerability Scanning Tools
SCANNING_ENABLED=true
MAX_CONCURRENT_SCANS=5
SCAN_TIMEOUT=600
SCAN_RESULTS_PATH=/var/data/soc-platform/scan-results
SCAN_QUEUE_TYPE=redis

# Nmap Configuration
NMAP_ENABLED=true
NMAP_PATH=/usr/bin/nmap
NMAP_SCRIPTS_PATH=/usr/share/nmap/scripts
NMAP_DEFAULT_ARGUMENTS=-sV -sC -O -A
NMAP_AGGRESSIVE_MODE=false
NMAP_MAX_RETRIES=2
NMAP_HOST_TIMEOUT=300

# Nuclei Configuration
NUCLEI_ENABLED=true
NUCLEI_PATH=/usr/local/bin/nuclei
NUCLEI_TEMPLATES_PATH=/var/data/nuclei-templates
NUCLEI_UPDATE_TEMPLATES=true
NUCLEI_SEVERITY_FILTER=medium,high,critical
NUCLEI_CONCURRENCY=25
NUCLEI_RATE_LIMIT=150
NUCLEI_BULK_SIZE=25
NUCLEI_TIMEOUT=10
NUCLEI_MAX_HOST_ERRORS=30

# OWASP ZAP Configuration
ZAP_ENABLED=true
ZAP_PATH=/opt/zaproxy/zap.sh
ZAP_PORT=8090
ZAP_API_KEY={self.generate_api_key()}
ZAP_TIMEOUT=3600
ZAP_MEMORY=2048m
ZAP_AJAX_SPIDER=true

# Metasploit Configuration
METASPLOIT_ENABLED=false
METASPLOIT_RPC_HOST=localhost
METASPLOIT_RPC_PORT=55553
METASPLOIT_RPC_USER=msf
METASPLOIT_RPC_PASS={self.generate_secure_password(24)}

# Shodan Integration
SHODAN_ENABLED=false
SHODAN_API_KEY=
SHODAN_RATE_LIMIT=1

# VirusTotal Integration
VIRUSTOTAL_ENABLED=false
VIRUSTOTAL_API_KEY=
VIRUSTOTAL_RATE_LIMIT=4

# Data Encryption
ENCRYPTION_ENABLED=true
ENCRYPTION_KEY={encryption_key}
ENCRYPT_SENSITIVE_DATA=true
ENCRYPT_PII=true
ENCRYPT_CREDENTIALS=true

# Audit Logging
AUDIT_LOG_ENABLED=true
AUDIT_LOG_PATH=/var/log/soc-platform/audit
AUDIT_LOG_RETENTION_DAYS=90
AUDIT_LOG_COMPRESSION=true
AUDIT_EVENTS=["login","logout","data_access","configuration_change","scan_initiated","vulnerability_found"]

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 3 * * *"
BACKUP_RETENTION_DAYS=30
BACKUP_ENCRYPTION=true
BACKUP_COMPRESSION=true
BACKUP_DESTINATION=/var/backups/soc-platform
BACKUP_REMOTE_ENABLED=false
BACKUP_REMOTE_TYPE=s3
BACKUP_REMOTE_BUCKET=
BACKUP_REMOTE_REGION=

# Performance Tuning
CACHE_ENABLED=true
CACHE_TTL=300
CACHE_MAX_SIZE=1000
RESPONSE_CACHE_ENABLED=true
QUERY_CACHE_ENABLED=true
STATIC_FILE_CACHE_ENABLED=true
CDN_ENABLED=false
CDN_URL=

# WAF Configuration
WAF_ENABLED=true
WAF_MODE=blocking
WAF_RULES_PATH=/etc/soc-platform/waf-rules
WAF_LOG_BLOCKED=true
WAF_RATE_LIMIT=100
WAF_GEO_BLOCKING=false
WAF_BLOCKED_COUNTRIES=[]

# API Security
API_KEY_REQUIRED=false
API_KEY_HEADER=X-API-Key
API_VERSION_HEADER=X-API-Version
API_DEPRECATION_HEADER=X-API-Deprecation-Date

# Compliance
COMPLIANCE_MODE=true
GDPR_ENABLED=true
HIPAA_ENABLED=false
PCI_DSS_ENABLED=false
SOC2_ENABLED=true
DATA_RETENTION_DAYS=365
DATA_ANONYMIZATION_ENABLED=true

# Feature Flags
FEATURE_ASYNC_SCANNING=true
FEATURE_AUTOMATED_PATCHING=false
FEATURE_THREAT_INTELLIGENCE=true
FEATURE_MACHINE_LEARNING=false
FEATURE_CLOUD_SCANNING=true
FEATURE_CONTAINER_SCANNING=true
FEATURE_API_SCANNING=true
FEATURE_MOBILE_APP_SCANNING=false

# Notification Channels
NOTIFICATION_EMAIL=true
NOTIFICATION_SMS=false
NOTIFICATION_SLACK=false
NOTIFICATION_WEBHOOK=true
NOTIFICATION_SEVERITY_THRESHOLD=medium

# Service Endpoints
ELASTICSEARCH_URL=http://localhost:9200
KIBANA_URL=http://localhost:5601
GRAFANA_URL=http://localhost:3000
PROMETHEUS_URL=http://localhost:9090
"""

        # Write production environment file
        with open(self.env_file, 'w') as f:
            f.write(production_config)

        # Set proper permissions (read/write for owner only)
        os.chmod(self.env_file, 0o600)

        # Generate secrets file for additional sensitive data
        secrets_data = {
            "database": {
                "master_password": postgres_password,
                "read_replica_password": self.generate_secure_password(),
                "backup_encryption_key": self.generate_encryption_key()
            },
            "redis": {
                "master_password": redis_password,
                "sentinel_password": self.generate_secure_password()
            },
            "api_keys": {
                "internal_api_key": self.generate_api_key(),
                "admin_api_key": self.generate_api_key(),
                "service_api_key": self.generate_api_key()
            },
            "encryption": {
                "master_key": encryption_key,
                "data_key": self.generate_encryption_key(),
                "backup_key": self.generate_encryption_key()
            },
            "tokens": {
                "jwt_secret": jwt_secret,
                "csrf_secret": csrf_secret,
                "webhook_secret": self.generate_secret_key()
            }
        }

        with open(self.secrets_file, 'w') as f:
            json.dump(secrets_data, f, indent=2)

        # Set proper permissions for secrets file
        os.chmod(self.secrets_file, 0o600)

        print(f"✅ Production configuration generated successfully!")
        print(f"   - Environment file: {self.env_file}")
        print(f"   - Secrets file: {self.secrets_file}")
        print("\n⚠️  IMPORTANT SECURITY NOTES:")
        print("   1. Never commit these files to version control")
        print("   2. Back up the secrets file securely")
        print("   3. Use a secrets management system in production")
        print("   4. Rotate all keys and passwords regularly")
        print("   5. Enable audit logging for all access")

        return {
            "env_file": str(self.env_file),
            "secrets_file": str(self.secrets_file),
            "postgres_password": postgres_password,
            "redis_password": redis_password
        }


if __name__ == "__main__":
    generator = ProductionConfigGenerator()
    config = generator.create_production_env()