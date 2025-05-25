from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DeviceResponse(BaseModel):
    id: int
    name: str
    type: str
    hourly_cost: float
    user_id: Optional[int] = None
    end_time: Optional[datetime] = None
    time_left: Optional[float] = None

    class Config:
        orm_mode = True

class DeviceStatusResponse(BaseModel):
    device_id: int
    running: bool
    end_time: Optional[datetime]
