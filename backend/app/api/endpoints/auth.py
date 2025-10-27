from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import security
from app.core.config import settings
from app.core.deps import get_current_active_user, require_admin
from app.core.permissions import permission_manager
from app.core.database import is_database_connected
from app.api.models.user import User, UserRole, UserStatus
from app.api.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    Token, PasswordChange
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin)
):
    """Register a new user (Admin only)"""

    # Check if user already exists
    existing_user = await User.find_one(
        {"$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ]}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )

    # Create new user
    hashed_password = security.get_password_hash(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        phone=user_data.phone,
        department=user_data.department,
        permissions=permission_manager.get_role_permissions(user_data.role),
        created_at=datetime.utcnow()
    )

    await new_user.insert()

    logger.info(f"New user created: {new_user.username} by {current_user.username}")

    return UserResponse(**new_user.dict())


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """User login"""

    # Check if database is connected
    if not is_database_connected():
        # Demo mode - accept any credentials matching demo users
        demo_users = {
            "admin": {"password": "admin", "role": UserRole.ADMIN},
            "analyst": {"password": "analyst", "role": UserRole.SECURITY_ANALYST},
            "demo": {"password": "demo", "role": UserRole.VIEWER}
        }

        demo_user = demo_users.get(user_credentials.username)
        if not demo_user or demo_user["password"] != user_credentials.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Create access token for demo user
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user_credentials.username}, expires_delta=access_token_expires
        )

        # Create demo user response
        demo_user_data = {
            "id": f"demo_{user_credentials.username}",
            "username": user_credentials.username,
            "email": f"{user_credentials.username}@demo.com",
            "full_name": f"Demo {user_credentials.username.title()}",
            "role": demo_user["role"],
            "status": UserStatus.ACTIVE,
            "is_active": True,
            "is_verified": True,
            "permissions": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "login_count": 1,
            "failed_login_attempts": 0
        }

        logger.info(f"Demo user {user_credentials.username} logged in successfully")

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**demo_user_data)
        )

    user = await User.find_one(User.username == user_credentials.username)

    if not user or not security.verify_password(
        user_credentials.password, user.hashed_password
    ):
        # Check for failed login attempts
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            await user.save()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until}"
        )

    # Check if user is active
    if not user.is_active or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active"
        )

    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    user.login_count += 1
    await user.save()

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    logger.info(f"User {user.username} logged in successfully")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**user.dict())
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """OAuth2 compatible token endpoint"""
    return await login(UserLogin(
        username=form_data.username,
        password=form_data.password
    ))


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse(**current_user.dict())


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user profile"""

    # Users can only update certain fields for themselves
    allowed_fields = ["full_name", "phone", "department"]

    for field, value in user_update.dict(exclude_unset=True).items():
        if field in allowed_fields and value is not None:
            setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()
    await current_user.save()

    logger.info(f"User {current_user.username} updated their profile")

    return UserResponse(**current_user.dict())


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """Change user password"""

    # Verify current password
    if not security.verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update password
    current_user.hashed_password = security.get_password_hash(
        password_data.new_password
    )
    current_user.updated_at = datetime.utcnow()
    await current_user.save()

    logger.info(f"User {current_user.username} changed their password")

    return {"message": "Password updated successfully"}


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin)
):
    """List all users (Admin only)"""

    users = await User.find().skip(skip).limit(limit).to_list()
    return [UserResponse(**user.dict()) for user in users]


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin)
):
    """Update user (Admin only)"""

    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    for field, value in user_update.dict(exclude_unset=True).items():
        if value is not None:
            setattr(user, field, value)

    # Update permissions when role changes
    if user_update.role:
        user.permissions = permission_manager.get_role_permissions(user_update.role)

    user.updated_at = datetime.utcnow()
    user.updated_by = current_user.username
    await user.save()

    logger.info(f"User {user.username} updated by {current_user.username}")

    return UserResponse(**user.dict())


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    """Delete user (Admin only)"""

    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Don't allow deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    await user.delete()

    logger.info(f"User {user.username} deleted by {current_user.username}")

    return {"message": "User deleted successfully"}