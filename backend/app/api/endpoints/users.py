from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_database
from app.core.deps import get_current_user
from app.core.security import security as security_manager
from app.api.models.user import User

router = APIRouter()
security = HTTPBearer()


class UserCreate(BaseModel):
    email: str
    username: str
    full_name: str
    password: str
    role: str = "viewer"
    is_active: bool = True


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = 1,
    size: int = 20,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all users with filtering and pagination"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check if database is connected
    db = await get_database()

    if not db:
        # Demo mode - return mock users
        from datetime import datetime
        mock_users = [
            UserResponse(
                id="1",
                email="admin@soc.com",
                username="admin",
                full_name="System Administrator",
                role="admin",
                is_active=True,
                created_at=datetime.now().isoformat(),
                last_login=datetime.now().isoformat()
            )
        ]

        # Apply filters to mock data
        filtered_users = mock_users
        if role:
            filtered_users = [u for u in filtered_users if u.role == role]
        if is_active is not None:
            filtered_users = [u for u in filtered_users if u.is_active == is_active]
        if search:
            search_lower = search.lower()
            filtered_users = [u for u in filtered_users if
                            search_lower in u.username.lower() or
                            search_lower in u.email.lower() or
                            search_lower in u.full_name.lower()]

        # Apply pagination
        start = (page - 1) * size
        end = start + size
        paginated_users = filtered_users[start:end]

        return UserListResponse(
            items=paginated_users,
            total=len(filtered_users),
            page=page,
            size=size,
            pages=(len(filtered_users) + size - 1) // size
        )

    # Production mode with database
    query = User.find()

    # Apply filters
    if role:
        query = query.find(User.role == role)
    if is_active is not None:
        query = query.find(User.is_active == is_active)
    if search:
        query = query.find({
            "$or": [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"full_name": {"$regex": search, "$options": "i"}}
            ]
        })

    # Get total count
    total = await query.count()

    # Apply pagination
    skip = (page - 1) * size
    users = await query.skip(skip).limit(size).to_list()

    # Convert to response format
    user_responses = []
    for user in users:
        user_responses.append(UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None
        ))

    return UserListResponse(
        items=user_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )

    # Check if user already exists
    existing_user = await User.find_one(
        {"$or": [{"email": user_data.email}, {"username": user_data.username}]}
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    # Create new user
    from datetime import datetime

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=security_manager.get_password_hash(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active,
        created_at=datetime.utcnow()
    )

    await new_user.create()

    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        username=new_user.username,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat(),
        last_login=None
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID"""
    # Users can view their own profile, admins can view any
    if str(current_user.id) != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a user"""
    # Users can update their own profile (except role), admins can update any
    if str(current_user.id) != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Non-admin users cannot change role
    if str(current_user.id) == user_id and current_user.role != "admin":
        if user_data.role is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role"
            )

    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    if "password" in update_data:
                update_data["hashed_password"] = security_manager.get_password_hash(update_data.pop("password"))

    if update_data:
        await user.update({"$set": update_data})

    # Refresh user data
    updated_user = await User.get(user_id)

    return UserResponse(
        id=str(updated_user.id),
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at.isoformat(),
        last_login=updated_user.last_login.isoformat() if updated_user.last_login else None
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )

    # Cannot delete yourself
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await user.delete()


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Activate a user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can activate users"
        )

    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await user.update({"$set": {"is_active": True}})
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deactivate a user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can deactivate users"
        )

    # Cannot deactivate yourself
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await user.update({"$set": {"is_active": False}})
    return {"message": "User deactivated successfully"}


@router.get("/me/profile", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )


@router.put("/me/profile", response_model=UserResponse)
async def update_my_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    # Users cannot change their own role
    update_data = profile_data.dict(exclude_unset=True, exclude={"role"})

    if "password" in update_data:
                update_data["hashed_password"] = security_manager.get_password_hash(update_data.pop("password"))

    if update_data:
        await current_user.update({"$set": update_data})

    # Refresh user data
    updated_user = await User.get(str(current_user.id))

    return UserResponse(
        id=str(updated_user.id),
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at.isoformat(),
        last_login=updated_user.last_login.isoformat() if updated_user.last_login else None
    )