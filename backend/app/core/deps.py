from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.security import security
from app.core.permissions import permission_manager
from app.core.database import is_database_connected
from app.api.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = security.verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    logger.info(f"Debug: Database connected status: {is_database_connected()}")

    # Demo mode - return mock user
    if not is_database_connected():
        demo_users = {
            "admin": {
                "id": "demo_admin",
                "username": "admin",
                "email": "admin@demo.com",
                "full_name": "Demo Admin",
                "role": "admin",
                "status": "active",
                "is_active": True,
                "is_verified": True,
                "permissions": ["admin:*"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "login_count": 1,
                "failed_login_attempts": 0
            },
            "analyst": {
                "id": "demo_analyst",
                "username": "analyst",
                "email": "analyst@demo.com",
                "full_name": "Demo Analyst",
                "role": "security_analyst",
                "status": "active",
                "is_active": True,
                "is_verified": True,
                "permissions": ["vulnerability:read", "asset:read", "task:read"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "login_count": 1,
                "failed_login_attempts": 0
            },
            "demo": {
                "id": "demo_user",
                "username": "demo",
                "email": "demo@demo.com",
                "full_name": "Demo User",
                "role": "viewer",
                "status": "active",
                "is_active": True,
                "is_verified": True,
                "permissions": ["vulnerability:read", "asset:read"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "login_count": 1,
                "failed_login_attempts": 0
            }
        }

        logger.info(f"Demo mode: Looking for user '{username}' in demo users")
        if username in demo_users:
            # Create a mock User object with the necessary attributes
            class MockUser:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)

            logger.info(f"Demo mode: Returning mock user for '{username}'")
            return MockUser(demo_users[username])
        else:
            logger.warning(f"Demo mode: User '{username}' not found in demo users")
            raise credentials_exception

    # Only try to use database if connected
    logger.info(f"Database mode: Attempting to query User model for '{username}'")
    if is_database_connected():
        try:
            user = await User.find_one(User.username == username)
            if user is None:
                raise credentials_exception

            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Inactive user"
                )

            # Update last login
            user.last_login = datetime.utcnow()
            user.login_count += 1
            await user.save()

            return user
        except AttributeError as e:
            # User model not properly initialized, fall back to demo mode
            logger.warning(f"User model not initialized: {e}, using demo mode fallback")

    # Database not connected or User model not initialized, shouldn't reach here in demo mode
    logger.error("Reached end of get_current_user without returning a user")
    raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_permission(permission: str):
    """Dependency to require specific permission"""
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not permission_manager.has_permission(
            current_user.role,
            current_user.permissions,
            permission
        ):
            logger.warning(
                f"User {current_user.username} attempted to access {permission} "
                f"without permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user

    return permission_dependency


def require_role(allowed_roles: list):
    """Dependency to require specific role(s)"""
    async def role_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"User {current_user.username} with role {current_user.role} "
                f"attempted to access resource requiring {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role privileges"
            )
        return current_user

    return role_dependency


# Convenience dependencies
require_admin = require_role(["admin"])
require_analyst_or_admin = require_role(["security_analyst", "admin"])