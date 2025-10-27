from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.database import Base
import uuid
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SECURITY_ANALYST = "security_analyst"
    OPERATOR = "operator"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base):
    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Basic info
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Role and Status
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False, index=True)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False, index=True)

    # Profile
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)

    # Permissions
    permissions = Column(ARRAY(String), server_default='{}', nullable=False)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)

    # Security
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # MFA/2FA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    backup_codes = Column(ARRAY(String), server_default='{}', nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_role', 'role'),
        Index('idx_user_status', 'status'),
        Index('idx_user_created_at', 'created_at'),
    )

    def dict_safe(self) -> dict:
        """Return user dict without sensitive data"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "status": self.status.value if isinstance(self.status, UserStatus) else self.status,
            "avatar_url": self.avatar_url,
            "phone": self.phone,
            "department": self.department,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "mfa_enabled": self.mfa_enabled,
        }