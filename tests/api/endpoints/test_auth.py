import pytest
from httpx import AsyncClient
from app.main import app

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
