import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.models.user import User

####################POST / ENDPOINT (CREATE USER)####################
@pytest.mark.asyncio
async def test_create_regular_user_success(test_app, test_session_factory):
    """Test that anyone can create a regular user account"""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/user",
            json={
                "name": "newuser",
                "password": "password123",
                "is_admin": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify user was created with correct data
        assert data["name"] == "newuser"
        assert data["cash"] == 0
        assert data["is_admin"] == False
        
        # Verify user exists in database
        async with test_session_factory() as session:
            result = await session.execute(select(User).where(User.name == "newuser"))
            user = result.scalars().first()
            assert user is not None
            assert user.name == "newuser"
            assert float(user.cash) == 0
            assert user.is_admin == False

@pytest.mark.asyncio
async def test_create_admin_user_unauthorized(test_app):
    """Test that non-admin users cannot create admin accounts"""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/user",
            json={
                "name": "newadmin",
                "password": "password123",
                "is_admin": True
            }
        )
        
        # Should be forbidden
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Only admins can create admin accounts" in data["detail"]

@pytest.mark.asyncio
async def test_create_admin_user_authorized(test_app, test_user, test_session_factory):
    """Test that admin users can create admin accounts"""
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
        
        # Create admin user using the admin endpoint
        response = await ac.post(
            "/user/admin",
            json={
                "name": "newadmin",
                "password": "password123",
                "is_admin": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify admin user was created with correct data
        assert data["name"] == "newadmin"
        assert data["is_admin"] == True

@pytest.mark.asyncio
async def test_create_user_duplicate_name(test_app, test_user):
    """Test that creating a user with an existing name fails"""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/user",
            json={
                "name": "testuser",  # Same as test_user
                "password": "password123",
                "is_admin": False
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Username already exists" in data["detail"]
