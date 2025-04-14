from fastapi.middleware.cors import CORSMiddleware
import asyncio
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, WebSocket, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Float, Integer, String, DateTime, Boolean, select
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from typing import Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from config.devices import DEVICES

# FastAPI setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Create initial admin user if no users exist
        result = await session.execute(select(User))
        if not result.scalars().first():
            admin_user = User(
                name="admin",
                cash=0,
                hashed_password=pwd_context.hash("admin"),
                is_admin=True
            )
            session.add(admin_user)
            
        # Update or create devices based on config
        for device_config in DEVICES:
            result = await session.execute(
                select(Device).where(Device.id == device_config["id"])
            )
            device = result.scalars().first()
            
            if device:
                # Update existing device
                device.name = device_config["name"]
                device.type = device_config["type"]
            else:
                # Create new device
                device = Device(
                    id=device_config["id"],
                    name=device_config["name"],
                    type=device_config["type"]
                )
                session.add(device)
        
        # Remove devices that are no longer in config
        result = await session.execute(select(Device))
        existing_devices = result.scalars().all()
        config_device_ids = [d["id"] for d in DEVICES]
        
        for device in existing_devices:
            if device.id not in config_device_ids:
                await session.delete(device)
        
        await session.commit()
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="HTML")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: In production, replace with frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "mysql+aiomysql://admin:password@localhost:3306/waschplan" #TODO: Change this
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Auth configuration
SECRET_KEY = "your-secret-key-here"  # TODO: Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User model
class User(Base):
    __tablename__ = "user"
    uid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    cash = Column(Float)
    creation_time = Column(DateTime, default=datetime.now(timezone.utc))
    hashed_password = Column(String(255))
    is_admin = Column(Boolean, default=False)

    def _tojson(self):
        return {
            "uid": self.uid,
            "name": self.name,
            "cash": self.cash,
            "creation_time": self.creation_time,
            "is_admin": self.is_admin
        }

# Device model
class Device(Base):
    __tablename__ = "device"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    user_id = Column(Integer, nullable=True)  # NULL when device is free
    end_time = Column(DateTime, nullable=True)  # NULL when device is not running
    
    def _tojson(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "user_id": self.user_id,
            "end_time": self.end_time,
            "time_left": (self.end_time.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds() if self.end_time else 0
        }

@app.get("/test", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid: int = payload.get("sub")
        if uid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if user is None:
            raise credentials_exception
        return user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.name == form_data.username)
        )
        user = result.scalars().first()
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    access_token = jwt.encode(
        {"sub": str(user.uid), "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.uid
    }


class UserCreate(BaseModel):
    name: str
    password: str
    is_admin: bool = False

@app.post("/user")
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
            hashed_password=pwd_context.hash(user_data.password),
            is_admin=user_data.is_admin
        )
        session.add(new_user)
        await session.commit()
        return new_user._tojson()
    
@app.get("/user")
async def get_user(uid: int, current_user: User = Depends(get_current_user)):
    if not isinstance(uid, int):
        return {"error": "Invalid UID"}
    if not current_user.is_admin and current_user.uid != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if user:
            return user._tojson()
        else:
            return {"error": "User not found"}

@app.delete("/user")
async def delete_user(uid: int, current_user: User = Depends(get_current_user)):
    if not isinstance(uid, int):
        return {"error": "Invalid UID"}
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
        else:
            return {"error": "User not found"}

@app.patch("/user")
async def update_user(
    uid: int, 
    name: str = None, 
    cash: float = None, 
    current_user: User = Depends(get_current_user)
):
    if not isinstance(uid, int):
        return {"error": "Invalid UID"}
    if not current_user.is_admin and current_user.uid != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
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
            # Device is in use - check if it's the same user trying to add time
            if device.user_id != user_id:
                return {"error": "Device is currently in use by another user"}
            # Add time to existing session
            device.end_time = device.end_time.replace(tzinfo=timezone.utc) + timedelta(minutes=duration_minutes)
        else:
            # Start the device
            device.user_id = user_id
            device.end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
            
        await session.commit()
        return device._tojson()

@app.get("/device")
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user)
):
    if not 1 <= device_id <= 5:
        return {"error": "Invalid device ID"}
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        
        if not device:
            return {"error": "Device not found"}
        
        if device.end_time:
            # Make sure end_time is timezone-aware
            if device.end_time.tzinfo is None:
                device.end_time = device.end_time.replace(tzinfo=timezone.utc)
            
            time_left = max(0, (device.end_time - datetime.now(timezone.utc)).total_seconds())
            if time_left <= 0:
                # Reset device
                device.user_id = None
                device.end_time = None
                await session.commit()
        
        return device._tojson()

@app.get("/devices")
async def get_all_devices():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device))
        devices = result.scalars().all()
        
        for device in devices:
            if device.end_time:
                # Make sure end_time is timezone-aware
                if device.end_time.tzinfo is None:
                    device.end_time = device.end_time.replace(tzinfo=timezone.utc)
                
                time_left = max(0, (device.end_time - datetime.now(timezone.utc)).total_seconds())
                if time_left <= 0:
                    # Reset device
                    device.user_id = None
                    device.end_time = None
        
        await session.commit()
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

@app.get("/users")
#async def get_all_users(current_user: User = Depends(get_admin_user)): #TODO: make admin only
async def get_all_users():
    """Get all users. Only accessible by admin users."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [user._tojson() for user in users]

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

