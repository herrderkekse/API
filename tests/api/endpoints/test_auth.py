import pytest
from httpx import AsyncClient
from app.main import app
from jose import jwt
from app.config import settings

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
