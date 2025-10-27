#!/usr/bin/env python3
"""
User Microservice for SOC Platform
Handles user management, authentication, and authorization
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import jwt
import asyncpg
from pydantic import BaseModel, EmailStr
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_service import BaseMicroservice, ServiceConfig

# Security
security = HTTPBearer()

# Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "operator"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    permissions: List[str]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class UserService(BaseMicroservice):
    """User management microservice"""

    def __init__(self):
        config = ServiceConfig()
        config.service_name = "user-service"
        config.service_port = int(os.getenv("SERVICE_PORT", "8001"))
        super().__init__(config)

        self.jwt_secret = os.getenv("JWT_SECRET", "secret-key")
        self.jwt_algorithm = "HS256"
        self.access_token_expire = 3600  # 1 hour
        self.refresh_token_expire = 86400 * 7  # 7 days

    async def initialize(self):
        """Initialize user service"""
        # Create users table
        if self.db:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'operator',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    permissions TEXT[]
                )
            """)

            # Create indexes
            await self.db.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
            )
            await self.db.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
            )

            # Create sessions table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(500) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    async def cleanup(self):
        """Cleanup user service"""
        pass

    async def check_health(self) -> Dict[str, Any]:
        """Check user service health"""
        health = {"status": "healthy", "details": {}}

        # Check database
        if self.db:
            try:
                await self.db.execute("SELECT 1")
                health["details"]["database"] = "connected"
            except Exception as e:
                health["status"] = "unhealthy"
                health["details"]["database"] = f"error: {str(e)}"

        # Check cache
        if self.cache:
            try:
                await self.cache.set("health_check", "ok", 5)
                health["details"]["cache"] = "connected"
            except Exception:
                health["details"]["cache"] = "disconnected"

        return health

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def create_token(self, user_id: int, token_type: str = "access") -> str:
        """Create JWT token"""
        expire_delta = (
            self.access_token_expire
            if token_type == "access"
            else self.refresh_token_expire
        )

        payload = {
            "sub": str(user_id),
            "type": token_type,
            "exp": datetime.utcnow() + timedelta(seconds=expire_delta),
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )

            # Check if token exists in sessions
            session = await self.db.fetchrow(
                "SELECT * FROM sessions WHERE token = $1 AND expires_at > NOW()",
                token
            )

            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """Get current user from token"""
        token = credentials.credentials
        payload = await self.decode_token(token)

        user = await self.db.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            int(payload["sub"])
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return dict(user)

    def get_permissions_for_role(self, role: str) -> List[str]:
        """Get permissions for role"""
        permissions_map = {
            "admin": ["read", "write", "delete", "manage_users", "manage_system"],
            "security_analyst": ["read", "write", "manage_vulnerabilities", "run_scans"],
            "operator": ["read", "write"],
            "viewer": ["read"]
        }
        return permissions_map.get(role, ["read"])

    async def setup_routes(self):
        """Setup user service routes"""

        @self.app.post("/api/users/register", response_model=UserResponse)
        async def register(user_data: UserCreate):
            """Register new user"""
            # Check if user exists
            existing = await self.db.fetchrow(
                "SELECT id FROM users WHERE username = $1 OR email = $2",
                user_data.username,
                user_data.email
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists"
                )

            # Create user
            password_hash = self.hash_password(user_data.password)
            permissions = self.get_permissions_for_role(user_data.role)

            user = await self.db.fetchrow("""
                INSERT INTO users (username, email, password_hash, full_name, role, permissions)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """, user_data.username, user_data.email, password_hash,
                user_data.full_name, user_data.role, permissions)

            # Publish event
            await self.publish_event("user.created", {
                "user_id": user["id"],
                "username": user["username"],
                "role": user["role"]
            })

            # Cache user
            if self.cache:
                await self.cache.set(f"user:{user['id']}", dict(user), 3600)

            return UserResponse(**dict(user))

        @self.app.post("/api/users/login", response_model=TokenResponse)
        async def login(credentials: UserLogin):
            """User login"""
            # Get user
            user = await self.db.fetchrow(
                "SELECT * FROM users WHERE username = $1",
                credentials.username
            )

            if not user or not self.verify_password(credentials.password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            if not user["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled"
                )

            # Create tokens
            access_token = self.create_token(user["id"], "access")
            refresh_token = self.create_token(user["id"], "refresh")

            # Save session
            await self.db.execute("""
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES ($1, $2, $3)
            """, user["id"], access_token,
                datetime.utcnow() + timedelta(seconds=self.access_token_expire))

            # Update last login
            await self.db.execute(
                "UPDATE users SET last_login = $1 WHERE id = $2",
                datetime.utcnow(),
                user["id"]
            )

            # Publish event
            await self.publish_event("user.logged_in", {
                "user_id": user["id"],
                "username": user["username"]
            })

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire
            )

        @self.app.post("/api/users/logout")
        async def logout(current_user: Dict = Depends(self.get_current_user)):
            """User logout"""
            # Invalidate session
            await self.db.execute(
                "DELETE FROM sessions WHERE user_id = $1",
                current_user["id"]
            )

            # Clear cache
            if self.cache:
                await self.cache.delete(f"user:{current_user['id']}")

            # Publish event
            await self.publish_event("user.logged_out", {
                "user_id": current_user["id"],
                "username": current_user["username"]
            })

            return {"message": "Logged out successfully"}

        @self.app.get("/api/users/me", response_model=UserResponse)
        async def get_me(current_user: Dict = Depends(self.get_current_user)):
            """Get current user"""
            return UserResponse(**current_user)

        @self.app.get("/api/users/{user_id}", response_model=UserResponse)
        async def get_user(
            user_id: int,
            current_user: Dict = Depends(self.get_current_user)
        ):
            """Get user by ID"""
            # Check cache
            if self.cache:
                cached = await self.cache.get(f"user:{user_id}")
                if cached:
                    return UserResponse(**cached)

            # Get from database
            user = await self.db.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Cache result
            if self.cache:
                await self.cache.set(f"user:{user_id}", dict(user), 3600)

            return UserResponse(**dict(user))

        @self.app.get("/api/users", response_model=List[UserResponse])
        async def get_users(
            skip: int = 0,
            limit: int = 100,
            role: Optional[str] = None,
            is_active: Optional[bool] = None,
            current_user: Dict = Depends(self.get_current_user)
        ):
            """Get users list"""
            # Build query
            query = "SELECT * FROM users WHERE 1=1"
            params = []

            if role:
                params.append(role)
                query += f" AND role = ${len(params)}"

            if is_active is not None:
                params.append(is_active)
                query += f" AND is_active = ${len(params)}"

            query += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {skip}"

            # Execute query
            users = await self.db.fetch(query, *params)

            return [UserResponse(**dict(user)) for user in users]

        @self.app.put("/api/users/{user_id}", response_model=UserResponse)
        async def update_user(
            user_id: int,
            user_data: UserUpdate,
            current_user: Dict = Depends(self.get_current_user)
        ):
            """Update user"""
            # Check permissions
            if current_user["id"] != user_id and "manage_users" not in current_user["permissions"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )

            # Build update query
            updates = []
            params = []

            if user_data.email:
                params.append(user_data.email)
                updates.append(f"email = ${len(params)}")

            if user_data.full_name:
                params.append(user_data.full_name)
                updates.append(f"full_name = ${len(params)}")

            if user_data.role and "manage_users" in current_user["permissions"]:
                params.append(user_data.role)
                updates.append(f"role = ${len(params)}")

                # Update permissions
                permissions = self.get_permissions_for_role(user_data.role)
                params.append(permissions)
                updates.append(f"permissions = ${len(params)}")

            if user_data.is_active is not None and "manage_users" in current_user["permissions"]:
                params.append(user_data.is_active)
                updates.append(f"is_active = ${len(params)}")

            params.append(user_id)
            query = f"""
                UPDATE users
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ${len(params)}
                RETURNING *
            """

            user = await self.db.fetchrow(query, *params)

            # Invalidate cache
            if self.cache:
                await self.cache.delete(f"user:{user_id}")

            # Publish event
            await self.publish_event("user.updated", {
                "user_id": user_id,
                "updated_by": current_user["id"],
                "changes": user_data.dict(exclude_unset=True)
            })

            return UserResponse(**dict(user))

        @self.app.delete("/api/users/{user_id}")
        async def delete_user(
            user_id: int,
            current_user: Dict = Depends(self.get_current_user)
        ):
            """Delete user"""
            # Check permissions
            if "manage_users" not in current_user["permissions"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )

            # Delete user
            await self.db.execute("DELETE FROM users WHERE id = $1", user_id)

            # Invalidate cache
            if self.cache:
                await self.cache.delete(f"user:{user_id}")

            # Publish event
            await self.publish_event("user.deleted", {
                "user_id": user_id,
                "deleted_by": current_user["id"]
            })

            return {"message": "User deleted successfully"}

        @self.app.post("/api/users/refresh")
        async def refresh_token(refresh_token: str):
            """Refresh access token"""
            payload = await self.decode_token(refresh_token)

            if payload["type"] != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )

            # Create new access token
            access_token = self.create_token(int(payload["sub"]), "access")

            # Save session
            await self.db.execute("""
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES ($1, $2, $3)
            """, int(payload["sub"]), access_token,
                datetime.utcnow() + timedelta(seconds=self.access_token_expire))

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire
            )

        @self.app.get("/api/users/{user_id}/permissions")
        async def get_permissions(
            user_id: int,
            current_user: Dict = Depends(self.get_current_user)
        ):
            """Get user permissions"""
            user = await self.db.fetchrow(
                "SELECT permissions FROM users WHERE id = $1",
                user_id
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            return {"permissions": user["permissions"]}


if __name__ == "__main__":
    service = UserService()
    service.run()