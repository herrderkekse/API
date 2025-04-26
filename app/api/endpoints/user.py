from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy import select
from typing import List

from ...database.session import AsyncSessionLocal
from ...models.user import User
from ...schemas.user import UserCreate, UserUpdate, UserResponse
from ...core.auth import get_current_user, get_admin_user, get_password_hash

router = APIRouter()

@router.get("/all", response_model=List[UserResponse])
async def get_all_users(): #TODO: make admin only
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [user._tojson() for user in users]

@router.get("/{uid}", response_model=UserResponse)
async def get_user(
    uid: int,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin and current_user.uid != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user._tojson()

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user)
):
    async with AsyncSessionLocal() as session:
        # Check if username already exists
        result = await session.execute(select(User).where(User.name == user_data.name))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
            
        new_user = User(
            name=user_data.name,
            cash=0,
            hashed_password=get_password_hash(user_data.password),
            is_admin=user_data.is_admin
        )
        session.add(new_user)
        await session.commit()
        return new_user._tojson()

@router.delete("/{uid}")
async def delete_user(uid: int, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.uid != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if user:
            await session.delete(user)
            await session.commit()
            return {"message": "User deleted successfully"}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.patch("/{uid}")
async def update_user(uid: int, user_data: UserUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.uid != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        if user_data.name:
            user.name = user_data.name
        if user_data.cash is not None:
            user.cash = user_data.cash
            
        await session.commit()
        return user._tojson()
