import pytest
from httpx import AsyncClient
from app.main import app
from jose import jwt
from app.config import settings
from app.core.auth import get_password_hash, get_password_hash

@pytest.mark.asyncio
async def test_login_success(test_app, test_user):  # test_user is passed in by pytest
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data

@pytest.mark.asyncio
async def test_login_invalid_credentials(test_app, test_user):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Incorrect username or password"

@pytest.mark.asyncio
async def test_login_nonexistent_user(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/token",
            data={"username": "nonexistentuser", "password": "anypassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Incorrect username or password"

@pytest.mark.asyncio
async def test_get_current_user_info(test_app, test_user):
    # First login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Then use token to get current user info
        response = await ac.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "testuser"
        assert data["uid"] == test_user.uid
        assert "cash" in data
        assert "is_admin" in data

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalidtoken"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid authentication credentials"

@pytest.mark.asyncio
async def test_token_validation(test_app, test_user):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Decode token and verify payload
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "sub" in payload
        assert int(payload["sub"]) == test_user.uid
        assert "exp" in payload

@pytest.mark.asyncio
async def test_login_with_keycard_success(test_app, test_session_factory):
    # Create a user with key card and PIN
    async with test_session_factory() as session:
        from app.models.user import User
        
        test_user_with_keycard = User(
            name="keycarduser",
            cash=100,
            hashed_password=get_password_hash("testpassword"),
            is_admin=False,
            key_card_hash=get_password_hash("1234567890"),
            pin_hash=get_password_hash("1234")
        )
        session.add(test_user_with_keycard)
        await session.commit()
        await session.refresh(test_user_with_keycard)
    
    # Test key card authentication
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/token/keycard",
            json={"key_card_id": "1234567890", "pin": "1234"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        
        # Verify token contains correct user ID
        payload = jwt.decode(data["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "sub" in payload
        assert int(payload["sub"]) == test_user_with_keycard.uid

@pytest.mark.asyncio
async def test_login_with_keycard_invalid_pin(test_app, test_session_factory):
    # Create a user with key card and PIN
    async with test_session_factory() as session:
        from app.models.user import User
        
        test_user_with_keycard = User(
            name="keycarduser2",
            cash=100,
            hashed_password=get_password_hash("testpassword"),
            is_admin=False,
            key_card_hash=get_password_hash("0987654321"),
            pin_hash=get_password_hash("5678")
        )
        session.add(test_user_with_keycard)
        await session.commit()
    
    # Test with invalid PIN
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/token/keycard",
            json={"key_card_id": "0987654321", "pin": "wrong"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid key card ID or PIN"

@pytest.mark.asyncio
async def test_login_with_keycard_invalid_card(test_app, test_session_factory):
    # Test with invalid key card ID
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/token/keycard",
            json={"key_card_id": "nonexistent", "pin": "1234"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid key card ID or PIN"

@pytest.mark.asyncio
async def test_user_with_keycard_can_use_password(test_app, test_session_factory):
    # Create a user with both password and key card
    async with test_session_factory() as session:
        from app.models.user import User
        
        test_dual_auth_user = User(
            name="dualuser",
            cash=100,
            hashed_password=get_password_hash("dualpassword"),
            is_admin=False,
            key_card_hash=get_password_hash("dualcard123"),
            pin_hash=get_password_hash("9999")
        )
        session.add(test_dual_auth_user)
        await session.commit()
    
    # Test regular password login still works
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/token",
            data={"username": "dualuser", "password": "dualpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
