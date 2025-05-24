import asyncio
from fastapi import APIRouter, Depends, WebSocket, HTTPException, status
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.logging import get_transaction_logger


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

from ...database.session import get_db
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

transaction_logger = get_transaction_logger()

@router.get("/all", response_model=List[DeviceResponse])
async def get_all_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Device))
    devices = result.scalars().all()
    
    # Update status for each device
    for device in devices:
        await _update_device_status(db, device)
    await db.commit()
    
    return [device._tojson() for device in devices]

@router.post("/start/{device_id}", response_model=DeviceResponse)
async def start_device(
    device_id: int,
    request: DeviceStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    
    return await _handle_device_start(
        db, 
        device_id, 
        request.user_id, 
        request.duration_minutes
    )

@router.post("/stop/{device_id}")
async def stop_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not 1 <= device_id <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID"
        )
    
    # Get device to check permissions
    device = await _get_device_with_status_update(db, device_id)
    
    # Allow both admins and the user who started the device to stop it
    if not current_user.is_admin and device.user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to stop this device"
        )
    
    return await _handle_device_stop(db, device_id)

@router.websocket("/ws/timeleft/{device_id}")
async def time_ws_endpoint(websocket: WebSocket, device_id: int):
    # Validate device_id before accepting the connection
    if not 1 <= device_id <= 5:
        await websocket.close(code=1003, reason="Invalid device ID")
        return
    
    await websocket.accept()
    
    # Add connection to tracking
    if device_id not in time_ws_connections:
        time_ws_connections[device_id] = set()
    time_ws_connections[device_id].add(websocket)

    try:
        while True:
            db_generator = get_db()
            session = await anext(db_generator)
            
            try:
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
            finally:
                try:
                    await db_generator.asend(None)
                except StopAsyncIteration:
                    pass
                
            await asyncio.sleep(1)
    finally:
        # Remove connection when client disconnects
        if device_id in time_ws_connections:
            time_ws_connections[device_id].remove(websocket)
            if not time_ws_connections[device_id]:
                del time_ws_connections[device_id]

@router.websocket("/ws/status/{device_id}")
async def device_status_ws_endpoint(websocket: WebSocket, device_id: int):
    # Validate device_id before accepting the connection
    if not 1 <= device_id <= 5:
        await websocket.close(code=1003, reason="Invalid device ID")
        return
    
    await websocket.accept()

    # Add connection to tracking
    if device_id not in status_ws_connections:
        status_ws_connections[device_id] = set()
    status_ws_connections[device_id].add(websocket)

    try:
        last_status = None
        while True:
            db_generator = get_db()
            session = await anext(db_generator)
            
            try:
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
            finally:
                try:
                    await db_generator.asend(None)
                except StopAsyncIteration:
                    pass
                        
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not 1 <= device_id <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID"
        )
    
    device = await _get_device_with_status_update(db, device_id)
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
    
    # Use device's hourly_cost if available, otherwise use from config
    hourly_cost = device.hourly_cost if hasattr(device, 'hourly_cost') and device.hourly_cost is not None else device_config["hourly_cost"]
    cost = (hourly_cost * duration_minutes) / 60
    
    # Convert user.cash to float for comparison
    if float(user.cash) < cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds"
        )
    
    # Log the transaction before deducting money
    old_balance = float(user.cash)
    new_balance = round(old_balance - cost, 2)
    transaction_logger.transaction(
        f"DEVICE_PAYMENT: User {user_id} ({user.name}) paid {cost} for device {device_id} ({device.name}) "
        f"for {duration_minutes} minutes. Balance changed from {old_balance} to {new_balance}"
    )
    
    # Deduct the cost from user's balance
    user.cash = new_balance
    
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
    
    # Ensure end_time has timezone info
    if device.end_time.tzinfo is None:
        end_time = device.end_time.replace(tzinfo=timezone.utc)
    else:
        end_time = device.end_time
    
    time_left = max(0, (end_time - datetime.now(timezone.utc)).total_seconds() / 60)  # in minutes
    if time_left <= 0:
        return 0.0
    
    # Use the device's own hourly_cost if available, otherwise get from config
    if hasattr(device, 'hourly_cost') and device.hourly_cost is not None:
        hourly_cost = device.hourly_cost
    else:
        device_config = _get_device_config(device.id)
        hourly_cost = device_config["hourly_cost"]
    
    # Calculate refund amount and round to 2 decimal places (cents)
    refund_amount = round((hourly_cost * time_left) / 60, 2)
    
    # Update user's cash balance
    user = await _get_user(session, device.user_id)
    old_balance = float(user.cash)
    new_balance = round(old_balance + refund_amount, 2)
    
    # Log the refund transaction
    transaction_logger.transaction(
        f"DEVICE_REFUND: User {device.user_id} ({user.name}) refunded {refund_amount} from device {device.id} "
        f"({device.name}) for {time_left:.2f} minutes. Balance changed from {old_balance} to {new_balance}"
    )
    
    user.cash = new_balance
    
    # Don't commit here, let the calling function handle the commit
    # to maintain transaction integrity
    
    return refund_amount
