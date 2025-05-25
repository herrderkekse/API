
import pytest
import json
import asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.device import Device
from app.models.user import User
from app.core.auth import get_password_hash

@pytest.mark.asyncio
async def test_timeleft_websocket_valid_device(test_app, test_session_factory, capsys):
    """Test the /ws/timeleft/{device_id} WebSocket endpoint with a valid device ID."""
    device_id = 1
    
    # Set up a user and device in the database
    async with test_session_factory() as session:
        # Create a test user with sufficient funds
        test_user = User(
            name="websocket_test_user",
            cash=100.0,
            hashed_password=get_password_hash("password"),
            is_admin=False
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        # Create a device
        device = Device(
            id=device_id,
            name="Test Device",
            type="test",
            hourly_cost=10.0
        )
        session.add(device)
        await session.commit()
    
    # Start the device using the API
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        # Login to get token
        login_response = await ac.post(
            "/auth/token",
            data={"username": "websocket_test_user", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Start the device
        duration_minutes = 30
        response = await ac.post(
            f"/device/start/{device_id}",
            json={
                "user_id": test_user.uid,
                "duration_minutes": duration_minutes
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        # Directly update the device in the database to ensure it's running
        async with test_session_factory() as session:
            result = await session.execute(select(Device).where(Device.id == device_id))
            device = result.scalars().first()
            if not device:
                device = Device(
                    id=device_id,
                    user_id=test_user.uid,
                    end_time=datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
                )
                session.add(device)
            else:
                device.user_id = test_user.uid
                device.end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
            await session.commit()

    # Create a test client for WebSocket
    client = TestClient(test_app)
    
    # Connect to the WebSocket
    with client.websocket_connect(f"/device/ws/timeleft/{device_id}") as websocket:
        # Receive the first message
        data = json.loads(websocket.receive_text())
        
        # Verify the device_id is correct
        assert data["device_id"] == device_id
        
        # Wait briefly and receive another update
        await asyncio.sleep(1.2)
        
        # Receive the next update
        data = json.loads(websocket.receive_text())
        
        # Verify we're still getting the correct device_id
        assert data["device_id"] == device_id

@pytest.mark.parametrize("invalid_id", [
    "abc",  # Non-numeric ID
    "0",    # Out of range (too low)
    "6",    # Out of range (too high)
])
@pytest.mark.asyncio
async def test_timeleft_websocket_invalid_device_id_formats(test_app, invalid_id):
    """Test the /ws/timeleft/{device_id} WebSocket endpoint with various invalid device ID formats."""
    # Create a test client for WebSocket
    client = TestClient(test_app)
    
    # Try to connect with an invalid device ID
    with pytest.raises(Exception):
        with client.websocket_connect(f"/device/ws/timeleft/{invalid_id}") as websocket:
            # This should fail before we can receive any data
            pass

@pytest.mark.parametrize("invalid_id", [
    "abc",  # Non-numeric ID
    "0",    # Out of range (too low)
    "6",    # Out of range (too high)
])
@pytest.mark.asyncio
async def test_status_websocket_invalid_device_id_formats(test_app, invalid_id):
    """Test the /ws/status/{device_id} WebSocket endpoint with various invalid device ID formats."""
    # Create a test client for WebSocket
    client = TestClient(test_app)
    
    # Try to connect with an invalid device ID
    with pytest.raises(Exception):
        with client.websocket_connect(f"/device/ws/status/{invalid_id}") as websocket:
            # This should fail before we can receive any data
            pass
