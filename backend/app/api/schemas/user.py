from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.api.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.VIEWER
    phone: Optional[str] = None
    department: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    permissions: Optional[List[str]] = None


class UserResponse(UserBase):
    id: str
    status: UserStatus
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime]
    login_count: int
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None
    permissions: List[str] = []


class PasswordChange(BaseModel):
    current_password: str
    new_password: str