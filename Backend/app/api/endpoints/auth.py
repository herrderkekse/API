from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.session import get_db
from ...models.user import User
from ...core.auth import verify_password, create_access_token, get_current_user
from ...schemas.user import UserResponse, KeyCardAuth 

router = APIRouter()

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.name == form_data.username)
    )
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": str(user.uid)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.uid
    }

@router.post("/token/keycard")
async def login_with_keycard(auth_data: KeyCardAuth, db: AsyncSession = Depends(get_db)):
    """Authenticate using key card ID and PIN"""
    # Query all users since we can't directly query by hashed value
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    # Find user with matching key card hash
    user = next((u for u in users if u.key_card_hash and 
                verify_password(auth_data.key_card_id, u.key_card_hash)), None)
    
    if not user or not user.pin_hash or not verify_password(auth_data.pin, user.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid key card ID or PIN",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": str(user.uid)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.uid
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user._tojson()
