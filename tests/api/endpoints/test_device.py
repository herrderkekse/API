import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from sqlalchemy import text, select
from app.main import app
from app.models.device import Device
from app.models.user import User
from app.config import DEVICES


####################GET /all ENDPOINT####################
@pytest.mark.asyncio
async def test_get_all_devices(test_app, test_user, test_session_factory):
    # Create some test devices in the database
    async with test_session_factory() as session:
        # Create some test devices in the database
        devices = []
        for i in range(1, 4):  # Create 3 test devices
            device = Device(
                id=i,
                name=f"Test Device {i}",
                type="test",
                hourly_cost=10.0,
                user_id=None,
                end_time=None
            )
            session.add(device)
            devices.append(device)
        
        # Add one device that's currently in use
        active_device = Device(
            id=4,
            name="Active Test Device",
            type="test",
            hourly_cost=10.0,
            user_id=test_user.uid,
            end_time=datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        session.add(active_device)
        devices.append(active_device)
        
        await session.commit()
    
    # First login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Then use token to get all devices
        response = await ac.get(
            "/device/all",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify we got all devices
        assert len(data) == len(devices)
        
        # Check that device properties are correct
        device_ids = [d["id"] for d in data]
        assert set(device_ids) == {1, 2, 3, 4}
        
        # Check the active device has correct data
        active_device_data = next(d for d in data if d["id"] == 4)
        assert active_device_data["user_id"] == test_user.uid
        assert "end_time" in active_device_data
        assert "time_left" in active_device_data
        assert active_device_data["time_left"] > 0

@pytest.mark.asyncio
async def test_get_all_devices_unauthorized(test_app):
    # Try to get devices without authentication
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.get("/device/all")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_get_all_devices_empty(test_app, test_user, test_session_factory):
    # Clear any devices from previous tests
    async with test_session_factory() as session:
        await session.execute(text("DELETE FROM device"))
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Get all devices when none exist
        response = await ac.get(
            "/device/all",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty array
        assert isinstance(data, list)
        assert len(data) == 0

####################POST /start ENDPOINT####################
@pytest.mark.asyncio
async def test_start_device_success(test_app, test_user, test_session_factory):
    # Ensure we have a device to start
    device_id = 1
    initial_cash = 100.0
    duration_minutes = 30
    hourly_cost = 10.0
    expected_cost = (hourly_cost * duration_minutes) / 60
    
    async with test_session_factory() as session:
        # First clear any existing devices
        await session.execute(text("DELETE FROM device"))
        
        # Create a test device
        device = Device(
            id=device_id,
            name="Test Device",
            type="test",
            hourly_cost=hourly_cost,
            user_id=None,
            end_time=None
        )
        session.add(device)
        
        # Ensure user has enough cash
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        user = result.scalars().first()
        user.cash = initial_cash  # Ensure enough cash for the test
        
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Start the device
        response = await ac.post(
            f"/device/start/{device_id}",
            json={
                "user_id": test_user.uid,
                "duration_minutes": duration_minutes
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify device is now running
        assert data["id"] == device_id
        assert data["user_id"] == test_user.uid
        assert "end_time" in data
        assert data["time_left"] > 0
        
        # Verify device state in database
        async with test_session_factory() as session:
            result = await session.execute(select(Device).where(Device.id == device_id))
            updated_device = result.scalars().first()
            assert updated_device.user_id == test_user.uid
            assert updated_device.end_time is not None
            
            # Ensure end_time has timezone info before comparing
            if updated_device.end_time.tzinfo is None:
                end_time = updated_device.end_time.replace(tzinfo=timezone.utc)
            else:
                end_time = updated_device.end_time
                
            # Check that end_time is approximately duration_minutes in the future
            time_diff = (end_time - datetime.now(timezone.utc)).total_seconds() / 60
            assert duration_minutes - 1 <= time_diff <= duration_minutes + 1
            
            # Verify user's cash was deducted correctly
            user_result = await session.execute(select(User).where(User.uid == test_user.uid))
            updated_user = user_result.scalars().first()
            expected_remaining = round(initial_cash - expected_cost, 2)
            assert updated_user.cash == expected_remaining

@pytest.mark.asyncio
async def test_start_device_invalid_id(test_app, test_user):
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to start a device with invalid ID
        invalid_device_id = 999
        response = await ac.post(
            f"/device/start/{invalid_device_id}",
            json={
                "user_id": test_user.uid,
                "duration_minutes": 30
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid device ID" in data["detail"]

@pytest.mark.asyncio
async def test_start_device_invalid_duration(test_app, test_user):
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to start a device with invalid duration
        device_id = 1
        response = await ac.post(
            f"/device/start/{device_id}",
            json={
                "user_id": test_user.uid,
                "duration_minutes": 0  # Invalid duration
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Duration must be positive" in data["detail"]

@pytest.mark.asyncio
async def test_start_device_already_in_use(test_app, test_user, test_session_factory):
    # Set up a device that's already in use
    device_id = 2
    async with test_session_factory() as session:
        # Create a device that's already in use
        device = Device(
            id=device_id,
            name="Busy Device",
            type="test",
            hourly_cost=10.0,
            user_id=test_user.uid,
            end_time=datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        session.add(device)
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to start the device that's already in use
        response = await ac.post(
            f"/device/start/{device_id}",
            json={
                "user_id": test_user.uid,
                "duration_minutes": 30
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Device is currently in use" in data["detail"]

@pytest.mark.asyncio
async def test_start_device_insufficient_funds(test_app, test_user, test_session_factory):
    # Set up a device and user with insufficient funds
    device_id = 3
    async with test_session_factory() as session:
        # First clear any existing devices with this ID
        await session.execute(text(f"DELETE FROM device WHERE id = {device_id}"))
        
        # Create a test device
        device = Device(
            id=device_id,
            name="Expensive Device",
            type="test",
            hourly_cost=1000.0,  # Very expensive device
            user_id=None,
            end_time=None
        )
        session.add(device)
        
        # Set user's cash to a low amount
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        user = result.scalars().first()
        user.cash = 1.0  # Not enough for the device
        
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to start the device with insufficient funds
        response = await ac.post(
            f"/device/start/{device_id}",
            json={
                "user_id": test_user.uid,
                "duration_minutes": 60
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Insufficient funds" in data["detail"]

####################POST /stop ENDPOINT####################
@pytest.mark.asyncio
async def test_stop_device_success(test_app, test_user, test_session_factory):
    # Set up a device that's in use
    device_id = 1
    async with test_session_factory() as session:
        # First clear any existing devices
        await session.execute(text("DELETE FROM device"))
        
        # Create a test device that's in use
        device = Device(
            id=device_id,
            name="Test Device",
            type="test",
            hourly_cost=10.0,
            user_id=test_user.uid,
            end_time=datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        session.add(device)
        
        # Make test user an admin to stop the device
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        user = result.scalars().first()
        user.is_admin = True
        
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Stop the device
        response = await ac.post(
            f"/device/stop/{device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "device" in data
        assert "refund_amount" in data
        assert data["message"] == "Device stopped successfully"
        assert data["device"]["id"] == device_id
        assert data["device"]["user_id"] is None
        assert data["device"]["end_time"] is None
        
        # Verify device state in database
        async with test_session_factory() as session:
            result = await session.execute(select(Device).where(Device.id == device_id))
            updated_device = result.scalars().first()
            assert updated_device.user_id is None
            assert updated_device.end_time is None

@pytest.mark.asyncio
async def test_stop_device_not_admin(test_app, test_user, test_session_factory):
    # Set up a device that's in use
    device_id = 1
    async with test_session_factory() as session:
        # First clear any existing devices
        await session.execute(text("DELETE FROM device"))
        
        # Create a test device that's in use
        device = Device(
            id=device_id,
            name="Test Device",
            type="test",
            hourly_cost=10.0,
            user_id=test_user.uid,
            end_time=datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        session.add(device)
        
        # Ensure user is not an admin
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        user = result.scalars().first()
        user.is_admin = False
        
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to stop the device as non-admin
        response = await ac.post(
            f"/device/stop/{device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be forbidden for non-admin users
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Not enough permissions" in data["detail"]

@pytest.mark.asyncio
async def test_stop_device_invalid_id(test_app, test_user, test_session_factory):
    # Make test user an admin
    async with test_session_factory() as session:
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        user = result.scalars().first()
        user.is_admin = True
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to stop a device with invalid ID
        invalid_device_id = 999
        response = await ac.post(
            f"/device/stop/{invalid_device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid device ID" in data["detail"]

@pytest.mark.asyncio
async def test_stop_device_not_running(test_app, test_user, test_session_factory):
    # Set up a device that's not in use
    device_id = 1
    async with test_session_factory() as session:
        # First clear any existing devices
        await session.execute(text("DELETE FROM device"))
        
        # Create a test device that's not in use
        device = Device(
            id=device_id,
            name="Test Device",
            type="test",
            hourly_cost=10.0,
            user_id=None,
            end_time=None
        )
        session.add(device)
        
        # Make test user an admin
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        user = result.scalars().first()
        user.is_admin = True
        
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to stop a device that's not running
        response = await ac.post(
            f"/device/stop/{device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Device is not running" in data["detail"]

@pytest.mark.asyncio
async def test_stop_device_refund(test_app, test_user, test_session_factory):
    # Set up a device that's in use
    device_id = 1
    duration_minutes = 30
    initial_cash = 100.0
    hourly_cost = 10.0
    
    async with test_session_factory() as session:
        # First clear any existing devices
        await session.execute(text("DELETE FROM device"))
        
        # Create a test device that's in use
        device = Device(
            id=device_id,
            name="Test Device",
            type="test",
            hourly_cost=hourly_cost,
            user_id=test_user.uid,
            end_time=datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        )
        session.add(device)
        
        # Set user's initial cash and make them admin
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        user = result.scalars().first()
        user.cash = initial_cash
        user.is_admin = True
        
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Stop the device
        response = await ac.post(
            f"/device/stop/{device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify refund amount is returned in response
        assert "refund_amount" in data
        refund_amount = data["refund_amount"]
        print(data)
        assert refund_amount > 0
        
        # Calculate expected refund (approximately)
        # hourly_cost * (duration_minutes / 60) is the total cost
        # The refund should be close to this amount since we just started the device
        expected_refund = round((hourly_cost * duration_minutes) / 60, 2)
        # Allow for a small difference due to time elapsed during the test
        assert abs(refund_amount - expected_refund) < 1.0
        
    # Verify user's cash was updated in the database
    async with test_session_factory() as session:
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        updated_user = result.scalars().first()
        expected_cash = initial_cash + refund_amount
        assert updated_user.cash == expected_cash


####################GET /{device_id} ENDPOINT####################
@pytest.mark.asyncio
async def test_get_device_success(test_app, test_user, test_session_factory):
    # Set up a test device
    device_id = 1
    async with test_session_factory() as session:
        # First clear any existing devices
        await session.execute(text("DELETE FROM device"))
        
        # Create a test device
        device = Device(
            id=device_id,
            name="Test Device",
            type="test",
            hourly_cost=10.0,
            user_id=None,
            end_time=None
        )
        session.add(device)
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Get the device
        response = await ac.get(
            f"/device/{device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify device properties
        assert data["id"] == device_id
        assert data["name"] == "Test Device"
        assert data["type"] == "test"
        assert data["hourly_cost"] == 10.0
        assert data["user_id"] is None
        assert data["end_time"] is None
        assert "time_left" in data
        assert data["time_left"] == 0

@pytest.mark.asyncio
async def test_get_device_running(test_app, test_user, test_session_factory):
    # Set up a device that's in use
    device_id = 2
    async with test_session_factory() as session:
        # First clear any existing devices with this ID
        await session.execute(text(f"DELETE FROM device WHERE id = {device_id}"))
        
        # Create a test device that's in use
        device = Device(
            id=device_id,
            name="Running Device",
            type="test",
            hourly_cost=10.0,
            user_id=test_user.uid,
            end_time=datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        session.add(device)
        await session.commit()
    
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Get the device
        response = await ac.get(
            f"/device/{device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify device properties
        assert data["id"] == device_id
        assert data["name"] == "Running Device"
        assert data["type"] == "test"
        assert data["hourly_cost"] == 10.0
        assert data["user_id"] == test_user.uid
        assert "end_time" in data
        assert "time_left" in data
        assert data["time_left"] > 0

@pytest.mark.asyncio
async def test_get_device_invalid_id(test_app, test_user):
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to get a device with invalid ID
        invalid_device_id = 999
        response = await ac.get(
            f"/device/{invalid_device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid device ID" in data["detail"]

@pytest.mark.asyncio
async def test_get_device_unauthorized(test_app):
    # Try to get a device without authentication
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.get("/device/1")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Not authenticated"
