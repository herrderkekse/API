from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    password: str
    is_admin: bool = False

class UserUpdate(UserBase):
    cash: Optional[float] = None

class UserResponse(UserBase):
    uid: int
    cash: float
    creation_time: datetime
    is_admin: bool

    class Config:
        orm_mode = True