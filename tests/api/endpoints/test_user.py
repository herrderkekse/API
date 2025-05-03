import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.models.user import User
from app.core.auth import get_password_hash

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

@pytest.mark.asyncio
async def test_create_user_with_keycard(test_app, test_session_factory):
    """Test creating a user with key card and PIN"""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post(
            "/user",
            json={
                "name": "keycarduser",
                "password": "password123",
                "is_admin": False,
                "key_card_id": "keycard123",
                "pin": "4321"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify user was created with correct data
        assert data["name"] == "keycarduser"
        
        # Verify user exists in database with key card hash
        async with test_session_factory() as session:
            result = await session.execute(select(User).where(User.name == "keycarduser"))
            user = result.scalars().first()
            assert user is not None
            assert user.key_card_hash is not None
            assert user.pin_hash is not None
            
            # Test authentication with the key card
            from app.core.auth import verify_password, verify_password
            assert verify_password("keycard123", user.key_card_hash)
            assert verify_password("4321", user.pin_hash)

####################PATCH / ENDPOINT (UPDATE USER)####################
@pytest.mark.asyncio
async def test_update_user_add_keycard(test_app, test_user, test_session_factory):
    """Test adding key card to existing user"""
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Update user to add key card
        response = await ac.patch(
            f"/user/{test_user.uid}",
            json={
                "key_card_id": "newkeycard",
                "pin": "5555"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        # Verify key card was added
        async with test_session_factory() as session:
            result = await session.execute(select(User).where(User.uid == test_user.uid))
            user = result.scalars().first()
            assert user.key_card_hash is not None
            assert user.pin_hash is not None
            
            # Test authentication with the key card
            from app.core.auth import verify_password, verify_password
            assert verify_password("newkeycard", user.key_card_hash)
            assert verify_password("5555", user.pin_hash)
            
        # Test authentication with the key card
        keycard_login = await ac.post(
            "/auth/token/keycard",
            json={"key_card_id": "newkeycard", "pin": "5555"}
        )
        
        assert keycard_login.status_code == 200
        assert "access_token" in keycard_login.json()


####################POST /{uid}/keycard ENDPOINT (ADD KEYCARD)####################
@pytest.mark.asyncio
async def test_add_keycard_endpoint(test_app, test_user, test_session_factory):
    """Test the dedicated endpoint for adding a key card to a user"""
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Add key card using the dedicated endpoint
        response = await ac.post(
            f"/user/{test_user.uid}/keycard",
            json={
                "key_card_id": "dedicated_keycard",
                "pin": "1234"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "testuser"
        
        # Verify key card was added
        async with test_session_factory() as session:
            result = await session.execute(select(User).where(User.uid == test_user.uid))
            user = result.scalars().first()
            assert user.key_card_hash is not None
            assert user.pin_hash is not None
            
            # Test authentication with the key card
            from app.core.auth import verify_password
            assert verify_password("dedicated_keycard", user.key_card_hash)
            assert verify_password("1234", user.pin_hash)
        
        # Test authentication with the key card
        keycard_login = await ac.post(
            "/auth/token/keycard",
            json={"key_card_id": "dedicated_keycard", "pin": "1234"}
        )
        
        assert keycard_login.status_code == 200
        assert "access_token" in keycard_login.json()

@pytest.mark.asyncio
async def test_add_keycard_unauthorized(test_app, test_user, test_session_factory):
    """Test that users cannot add key cards to other users' accounts"""
    # Create another user
    async with test_session_factory() as session:
        other_user = User(
            name="otheruser",
            cash=100,
            hashed_password=get_password_hash("otherpassword"),
            is_admin=False
        )
        session.add(other_user)
        await session.commit()
        await session.refresh(other_user)
    
    # Login as test_user
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to add key card to other user's account
        response = await ac.post(
            f"/user/{other_user.uid}/keycard",
            json={
                "key_card_id": "unauthorized_keycard",
                "pin": "5678"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be forbidden
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Not authorized to modify this user" in data["detail"]

@pytest.mark.asyncio
async def test_add_keycard_admin_can_modify_others(test_app, test_user, test_session_factory):
    """Test that admin users can add key cards to other users' accounts"""
    # Create another user
    async with test_session_factory() as session:
        other_user = User(
            name="modifieduser",
            cash=100,
            hashed_password=get_password_hash("modifiedpassword"),
            is_admin=False
        )
        session.add(other_user)
        
        # Make test_user an admin
        result = await session.execute(select(User).where(User.uid == test_user.uid))
        user = result.scalars().first()
        user.is_admin = True
        
        await session.commit()
        await session.refresh(other_user)
    
    # Login as admin test_user
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Add key card to other user's account
        response = await ac.post(
            f"/user/{other_user.uid}/keycard",
            json={
                "key_card_id": "admin_added_keycard",
                "pin": "9999"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "modifieduser"
        
        # Verify key card was added
        async with test_session_factory() as session:
            result = await session.execute(select(User).where(User.uid == other_user.uid))
            user = result.scalars().first()
            assert user.key_card_hash is not None
            assert user.pin_hash is not None
            
            # Test authentication with the key card
            from app.core.auth import verify_password
            assert verify_password("admin_added_keycard", user.key_card_hash)
            assert verify_password("9999", user.pin_hash)

@pytest.mark.asyncio
async def test_add_keycard_missing_fields(test_app, test_user):
    """Test that both key card ID and PIN are required"""
    # Login to get token
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to add key card without PIN
        response = await ac.post(
            f"/user/{test_user.uid}/keycard",
            json={
                "key_card_id": "missing_pin_keycard",
                "pin": ""
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Both key card ID and PIN must be provided" in data["detail"]
        
        # Try to add key card without key card ID
        response = await ac.post(
            f"/user/{test_user.uid}/keycard",
            json={
                "key_card_id": "",
                "pin": "1234"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Both key card ID and PIN must be provided" in data["detail"]

####################DELETE /{uid}/keycard ENDPOINT (remove KEYCARD)####################
@pytest.mark.asyncio
async def test_remove_keycard(test_app, test_session_factory):
    """Test removing key card authentication from a user"""
    # Create a user with key card authentication
    async with test_session_factory() as session:
        user_with_keycard = User(
            name="keycardremovaluser",
            cash=100,
            hashed_password=get_password_hash("password123"),
            is_admin=False,
            key_card_hash=get_password_hash("keycard456"),
            pin_hash=get_password_hash("7890")
        )
        session.add(user_with_keycard)
        await session.commit()
        await session.refresh(user_with_keycard)
        
        user_id = user_with_keycard.uid
    
    # Login as the user
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "keycardremovaluser", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Remove key card authentication
        response = await ac.delete(
            f"/user/{user_id}/keycard",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "removed successfully" in data["message"]
        
        # Verify key card was removed
        async with test_session_factory() as session:
            result = await session.execute(select(User).where(User.uid == user_id))
            user = result.scalars().first()
            assert user.key_card_hash is None
            assert user.pin_hash is None
        
        # Verify user info shows has_keycard as false
        user_response = await ac.get(
            f"/user/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["has_keycard"] is False
        
        # Try to authenticate with removed key card
        keycard_login = await ac.post(
            "/auth/token/keycard",
            json={"key_card_id": "keycard456", "pin": "7890"}
        )
        
        assert keycard_login.status_code == 401

@pytest.mark.asyncio
async def test_remove_keycard_unauthorized(test_app, test_session_factory):
    """Test that users cannot remove key cards from other users' accounts"""
    # Create two users
    async with test_session_factory() as session:
        user_with_keycard = User(
            name="keycarduser2",
            cash=100,
            hashed_password=get_password_hash("password123"),
            is_admin=False,
            key_card_hash=get_password_hash("keycard789"),
            pin_hash=get_password_hash("1010")
        )
        
        other_user = User(
            name="otheruser2",
            cash=100,
            hashed_password=get_password_hash("otherpassword"),
            is_admin=False
        )
        
        session.add(user_with_keycard)
        session.add(other_user)
        await session.commit()
        await session.refresh(user_with_keycard)
        await session.refresh(other_user)
        
        keycard_user_id = user_with_keycard.uid
    
    # Login as other_user
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "otheruser2", "password": "otherpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to remove key card from user_with_keycard
        response = await ac.delete(
            f"/user/{keycard_user_id}/keycard",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be forbidden
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Not authorized to modify this user" in data["detail"]

@pytest.mark.asyncio
async def test_remove_nonexistent_keycard(test_app, test_user):
    """Test removing key card when user doesn't have one"""
    # Login as test_user (who doesn't have a key card)
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try to remove nonexistent key card
        response = await ac.delete(
            f"/user/{test_user.uid}/keycard",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "does not have key card authentication" in data["detail"]
