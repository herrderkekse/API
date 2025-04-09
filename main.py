# main.py
import asyncio
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import FastAPI, WebSocket, Request
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Float, Integer, String, DateTime, select
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from typing import Dict, Optional

# FastAPI setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="HTML")

# Database setup
DATABASE_URL = "mysql+aiomysql://admin:password@localhost:3306/waschplan"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "user"
    uid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))  #maximum length of 255 characters
    cash = Column(Float)
    creation_time = Column(DateTime, default=datetime.now(timezone.utc))

    def _tojson(self):
        return {"uid": self.uid, "name": self.name, "cash": self.cash, "creation_time": self.creation_time}

# Device model
class Device(Base):
    __tablename__ = "device"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)  # NULL when device is free
    end_time = Column(DateTime, nullable=True)  # NULL when device is not running
    
    def _tojson(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "end_time": self.end_time
        }

@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/user")
async def create_user(name: str):
    async with AsyncSessionLocal() as session:
        new_user = User(name=name, cash=0)
        session.add(new_user)
        await session.commit()
        return {"uid": new_user._tojson()}
    
@app.get("/user")
async def get_user(uid: int):
    if not isinstance(uid, int):
        return {"error": "Invalid UID"}
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if user:
            return user._tojson()
        else:
            return {"error": "User not found"}

@app.delete("/user")
async def delete_user(uid: int):
    if not isinstance(uid, int):
        return {"error": "Invalid UID"}
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if user:
            await session.delete(user)
            await session.commit()
            return {"message": "User deleted successfully"}
        else:
            return {"error": "User not found"}

@app.patch("/user")
async def update_user(uid: int, name: str = None, cash: float = None):
    if not isinstance(uid, int):
        return {"error": "Invalid UID"}
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if user:
            if name:
                user.name = name
            if cash is not None:
                user.cash = cash
            await session.commit()
            return user._tojson()
        else:
            return {"error": "User not found"}


@app.post("/device/start")
async def start_device(device_id: int, user_id: int, duration_minutes: int):
    if not 1 <= device_id <= 5:
        return {"error": "Invalid device ID"}
    if duration_minutes <= 0:
        return {"error": "Duration must be positive"}
    
    async with AsyncSessionLocal() as session:
        # Check if user exists
        user_result = await session.execute(select(User).where(User.uid == user_id))
        user = user_result.scalars().first()
        if not user:
            return {"error": "Invalid user ID"}
        
        # Check if device exists
        result = await session.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        
        if not device:
            # First time setup - create device
            device = Device(id=device_id)
            session.add(device)
        elif device.end_time and device.end_time.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            return {"error": "Device is currently in use"}
            
        # Start the device
        device.user_id = user_id
        device.end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        await session.commit()
        return device._tojson()


@app.get("/device")
async def get_device(device_id: int):
    if not 1 <= device_id <= 5:
        return {"error": "Invalid device ID"}
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        
        if not device:
            return {"error": "Device not found"}
        
        return device._tojson()


@app.get("/devices")
async def get_all_devices():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device))
        devices = result.scalars().all()
        return [device._tojson() for device in devices]


@app.websocket("/timeleft")
async def time_ws_endpoint(websocket: WebSocket, device_id: int):
    await websocket.accept()
    if not isinstance(device_id, int) or device_id < 1 or device_id > 5:
        await websocket.close(code=1003, reason="Invalid device ID")
        return

    while True:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Device).where(Device.id == device_id))
            device = result.scalars().first()
            
            if not device or not device.end_time:
                await websocket.send_json({"device_id": device_id, "time_left": 0, "status": "idle"})
            else:
                # Make sure end_time is timezone-aware
                if device.end_time.tzinfo is None:
                    device.end_time = device.end_time.replace(tzinfo=timezone.utc)
                
                time_left = (device.end_time - datetime.now(timezone.utc)).total_seconds()
                if time_left <= 0:
                    # Reset device
                    device.user_id = None
                    device.end_time = None
                    await session.commit()
                    await websocket.send_json({"device_id": device_id, "time_left": 0, "status": "idle"})
                else:
                    await websocket.send_json({
                        "device_id": device_id,
                        "time_left": round(time_left),
                        "status": "running",
                        "user_id": device.user_id
                    })
                    
        await asyncio.sleep(1)


