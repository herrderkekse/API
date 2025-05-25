from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    password: str
    is_admin: bool = False
    key_card_id: Optional[str] = None
    pin: Optional[str] = None

class UserUpdate(UserBase):
    name: Optional[str] = None
    cash: Optional[float] = None
    key_card_id: Optional[str] = None
    pin: Optional[str] = None

class UserResponse(UserBase):
    uid: int
    cash: float
    creation_time: datetime
    is_admin: bool
    has_keycard: bool = False  # Add this field to indicate if key card auth is available

    class Config:
        orm_mode = True

class KeyCardAuth(BaseModel):
    key_card_id: str
    pin: str
