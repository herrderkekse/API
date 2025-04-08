# main.py
import time
import asyncio
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import FastAPI, WebSocket, Request
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Float, Integer, String, DateTime, select
import datetime
from contextlib import asynccontextmanager

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
    creation_time = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    def _tojson(self):
        return {"uid": self.uid, "name": self.name, "cash": self.cash, "creation_time": self.creation_time}


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


