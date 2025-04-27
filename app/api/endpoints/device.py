import asyncio
from fastapi import APIRouter, Depends, WebSocket, HTTPException, status
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set
from pydantic import BaseModel

# Store WebSocket connections
time_ws_connections: Dict[int, Set[WebSocket]] = {}
status_ws_connections: Dict[int, Set[WebSocket]] = {}

async def broadcast_device_update(device_id: int, data: dict):
    """Broadcast update to all WebSocket clients for a specific device"""
    if device_id in time_ws_connections:
        dead_connections = set()
        for websocket in time_ws_connections[device_id]:
            try:
                await websocket.send_json(data)
            except RuntimeError:  # Connection already closed
                dead_connections.add(websocket)
        
        # Clean up dead connections
        time_ws_connections[device_id] -= dead_connections

async def broadcast_status_update(device_id: int, data: dict):
    """Broadcast status update to all status WebSocket clients for a specific device"""
    if device_id in status_ws_connections:
        dead_connections = set()
        for websocket in status_ws_connections[device_id]:
            try:
                await websocket.send_json(data)
            except RuntimeError:  # Connection already closed
                dead_connections.add(websocket)
        
        # Clean up dead connections
        status_ws_connections[device_id] -= dead_connections

from ...database.session import AsyncSessionLocal
from ...models.device import Device
from ...models.user import User
from ...schemas.device import DeviceResponse
from ...core.auth import get_current_user, get_admin_user
from ...config import DEVICES

# Add this class for request validation
class DeviceStartRequest(BaseModel):
    user_id: int
    duration_minutes: int

router = APIRouter()


@router.get("/all", response_model=List[DeviceResponse])
async def get_all_devices(current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device))
        devices = result.scalars().all()
        
        # Update status for each device
        for device in devices:
            await _update_device_status(session, device)
        await session.commit()
        
        return [device._tojson() for device in devices]

@router.post("/start/{device_id}", response_model=DeviceResponse)
async def start_device(
    device_id: int,
    request: DeviceStartRequest,
    current_user: User = Depends(get_current_user)
):
    if not 1 <= device_id <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID"
        )
    if request.duration_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be positive"
        )
    
    async with AsyncSessionLocal() as session:
        return await _handle_device_start(
            session, 
            device_id, 
            request.user_id, 
            request.duration_minutes
        )

@router.post("/stop/{device_id}")
async def stop_device(
    device_id: int,
    current_user: User = Depends(get_admin_user)
):
    if not 1 <= device_id <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID"
        )
    
    async with AsyncSessionLocal() as session:
        return await _handle_device_stop(session, device_id)

@router.websocket("/ws/timeleft/{device_id}")
async def time_ws_endpoint(websocket: WebSocket, device_id: int):
    await websocket.accept()
    if not isinstance(device_id, int) or device_id < 1 or device_id > 5:
        await websocket.close(code=1003, reason="Invalid device ID")
        return

    # Add connection to tracking
    if device_id not in time_ws_connections:
        time_ws_connections[device_id] = set()
    time_ws_connections[device_id].add(websocket)

    try:
        while True:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Device).where(Device.id == device_id))
                device = result.scalars().first()
                
                response_data = {
                    "device_id": device_id,
                    "time_left": 0,
                    "status": "idle",
                    "user_id": None
                }
                
                if device and device.end_time:
                    if device.end_time.tzinfo is None:
                        device.end_time = device.end_time.replace(tzinfo=timezone.utc)
                    
                    time_left = (device.end_time - datetime.now(timezone.utc)).total_seconds()
                    if time_left <= 0:
                        device.user_id = None
                        device.end_time = None
                        await session.commit()
                    else:
                        response_data.update({
                            "time_left": round(time_left),
                            "status": "running",
                            "user_id": device.user_id
                        })
                
                await websocket.send_json(response_data)
            await asyncio.sleep(1)
    finally:
        # Remove connection when client disconnects
        if device_id in time_ws_connections:
            time_ws_connections[device_id].remove(websocket)
            if not time_ws_connections[device_id]:
                del time_ws_connections[device_id]

@router.websocket("/ws/status/{device_id}")
async def device_status_ws_endpoint(websocket: WebSocket, device_id: int):
    await websocket.accept()
    if not isinstance(device_id, int) or device_id < 1 or device_id > 5:
        await websocket.close(code=1003, reason="Invalid device ID")
        return

    # Add connection to tracking
    if device_id not in status_ws_connections:
        status_ws_connections[device_id] = set()
    status_ws_connections[device_id].add(websocket)

    try:
        last_status = None
        while True:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Device).where(Device.id == device_id))
                device = result.scalars().first()
                
                if not device or not device.end_time:
                    current_status = False
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
                        current_status = False
                    else:
                        current_status = True
                
                # Only send update if status has changed
                if current_status != last_status:
                    response = {
                        "device_id": device_id,
                        "running": current_status
                    }
                    if current_status:
                        response["end_time"] = device.end_time.isoformat()
                    await websocket.send_json(response)
                    last_status = current_status
                        
            await asyncio.sleep(1)
    finally:
        # Remove connection when client disconnects
        if device_id in status_ws_connections:
            status_ws_connections[device_id].remove(websocket)
            if not status_ws_connections[device_id]:
                del status_ws_connections[device_id]

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user)
):
    if not 1 <= device_id <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID"
        )
    
    async with AsyncSessionLocal() as session:
        device = await _get_device_with_status_update(session, device_id)
        return device._tojson()

# Helper functions
async def _get_device_with_status_update(session, device_id):
    result = await session.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    await _update_device_status(session, device)
    return device

async def _update_device_status(session, device):
    if device.end_time:
        if device.end_time.tzinfo is None:
            device.end_time = device.end_time.replace(tzinfo=timezone.utc)
        
        time_left = max(0, (device.end_time - datetime.now(timezone.utc)).total_seconds())
        if time_left <= 0:
            device.user_id = None
            device.end_time = None
            await session.commit()

async def _handle_device_start(session, device_id, user_id, duration_minutes):
    user = await _get_user(session, user_id)
    device = await _get_or_create_device(session, device_id)
    device_config = _get_device_config(device_id)
    
    cost = (device_config["hourly_cost"] * duration_minutes) / 60
    if user.cash < cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds"
        )
    
    await _update_device_time(session, device, user_id, duration_minutes)
    return device._tojson()

async def _handle_device_stop(session, device_id):
    device = await _get_device_with_status_update(session, device_id)
    
    if not device.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device is not running"
        )
    
    refund = await _process_refund(session, device)
    
    device.user_id = None
    device.end_time = None
    await session.commit()
    
    # Create response data
    response = {
        "message": "Device stopped successfully",
        "device": device._tojson(),
        "refund_amount": refund
    }
    
    # Broadcast updates to all connected WebSocket clients
    await broadcast_device_update(device_id, {
        "device_id": device_id,
        "time_left": 0,
        "status": "idle",
        "user_id": None
    })

    # Broadcast status update
    await broadcast_status_update(device_id, {
        "device_id": device_id,
        "running": False
    })
    
    return response

async def _get_user(session, user_id: int) -> User:
    result = await session.execute(select(User).where(User.uid == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

async def _get_or_create_device(session, device_id: int) -> Device:
    result = await session.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    
    if not device:
        device = Device(id=device_id)
        session.add(device)
        await session.commit()
    
    await _update_device_status(session, device)
    return device

def _get_device_config(device_id: int) -> dict:
    device_config = next((device for device in DEVICES if device["id"] == device_id), None)
    if not device_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device configuration not found"
        )
    return device_config

async def _update_device_time(session, device: Device, user_id: int, duration_minutes: int):
    if device.end_time and device.end_time > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device is currently in use"
        )
    
    device.user_id = user_id
    device.end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    await session.commit()

async def _process_refund(session, device: Device) -> float:
    if not device.end_time or not device.user_id:
        return 0.0
    
    time_left = max(0, (device.end_time - datetime.now(timezone.utc)).total_seconds() / 60)  # in minutes
    if time_left <= 0:
        return 0.0
    
    device_config = _get_device_config(device.id)
    refund_amount = (device_config["hourly_cost"] * time_left) / 60
    
    # Update user's cash balance
    user = await _get_user(session, device.user_id)
    user.cash += refund_amount
    await session.commit()
    
    return round(refund_amount, 2)
