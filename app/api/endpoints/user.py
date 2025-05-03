from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy import select
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.session import get_db
from ...models.user import User
from ...schemas.user import KeyCardAuth, UserCreate, UserUpdate, UserResponse
from ...core.auth import get_current_user, get_admin_user, get_password_hash

router = APIRouter()

@router.get("/all", response_model=List[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db)): #TODO: make admin only
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [user._tojson() for user in users]

@router.get("/{uid}", response_model=UserResponse)
async def get_user(
    uid: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_admin and current_user.uid != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
        
    result = await db.execute(select(User).where(User.uid == uid))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user._tojson()

@router.post("/admin", response_model=UserResponse)
async def create_admin_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    return await _createUser(user_data, db)

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # this is only for creating regular users. Only admins can create admin users
    if user_data.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create admin accounts"
        )
    
    return await _createUser(user_data, db)

@router.delete("/{uid}")
async def delete_user(
    uid: int, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_admin and current_user.uid != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
        
    result = await db.execute(select(User).where(User.uid == uid))
    user = result.scalars().first()
    if user:
        await db.delete(user)
        await db.commit()
        return {"message": "User deleted successfully"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@router.patch("/{uid}", response_model=UserResponse)
async def update_user(
    uid: int, 
    user_data: UserUpdate, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get the user to update
    result = await db.execute(select(User).where(User.uid == uid))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only allow users to update their own account unless they're an admin
    if current_user.uid != uid and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields if provided
    if user_data.name is not None:
        user.name = user_data.name
    
    if user_data.cash is not None:
        user.cash = user_data.cash
    
    # Update key card info if provided
    if user_data.key_card_id is not None:
        user.key_card_hash = get_password_hash(user_data.key_card_id) if user_data.key_card_id else None
    
    if user_data.pin is not None:
        user.pin_hash = get_password_hash(user_data.pin) if user_data.pin else None
        
    await db.commit()
    return user._tojson()

@router.post("/{uid}/keycard", response_model=UserResponse)
async def add_keycard(
    uid: int,
    keycard_data: KeyCardAuth,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a key card and PIN to a user account"""
    # Get the user to update
    result = await db.execute(select(User).where(User.uid == uid))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only allow users to update their own account unless they're an admin
    if current_user.uid != uid and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this user"
        )
    
    # Both key card ID and PIN must be provided
    if not keycard_data.key_card_id or not keycard_data.pin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both key card ID and PIN must be provided"
        )
    
    # Update key card and PIN
    user.key_card_hash = get_password_hash(keycard_data.key_card_id)
    user.pin_hash = get_password_hash(keycard_data.pin)
    
    await db.commit()
    return user._tojson()


# Helper functions
async def _createUser(user_data: UserCreate, db: AsyncSession):
    
    # Check if username already exists
    result = await db.execute(select(User).where(User.name == user_data.name))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    new_user = User(
        name=user_data.name,
        cash=0,
        hashed_password=get_password_hash(user_data.password),
        is_admin=user_data.is_admin,
        key_card_hash=get_password_hash(user_data.key_card_id) if user_data.key_card_id else None,
        pin_hash=get_password_hash(user_data.pin) if user_data.pin else None
    )
    db.add(new_user)
    await db.commit()
    return new_user._tojson()
