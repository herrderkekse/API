import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User
from app.core.auth import get_password_hash
from app.database.session import get_db
from app.main import app

# Test database URL - use in-memory SQLite for tests
# TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared"

@pytest_asyncio.fixture
async def test_app(test_session_factory):
    # Override get_db dependency
    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)



@pytest_asyncio.fixture
async def test_user(test_session_factory):
    async with test_session_factory() as session:
        test_user = User(
            name="testuser",
            cash=100,
            hashed_password=get_password_hash("testpassword"),
            is_admin=False
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        return test_user
