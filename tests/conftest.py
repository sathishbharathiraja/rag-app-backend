import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import get_db
from app.models.models import Base, User
from app.core.security import get_password_hash
from app.core.config import settings

# Create a dedicated test engine with NullPool to avoid asyncio loop conflicts
test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    # We will hit the real database but clean up afterwards
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    # Ensure test user doesn't exist
    from sqlalchemy.future import select
    result = await db_session.execute(select(User).where(User.username == "testuser_automated"))
    user = result.scalars().first()
    if user:
        await db_session.delete(user)
        await db_session.commit()

    # Create new test user
    new_user = User(
        username="testuser_automated",
        password_hash=get_password_hash("testpass")
    )
    db_session.add(new_user)
    await db_session.commit()
    
    yield new_user
    
    # Cleanup
    await db_session.delete(new_user)
    await db_session.commit()

@pytest_asyncio.fixture(scope="function")
async def auth_token(test_client: AsyncClient, test_user):
    response = await test_client.post(
        "/api/login",
        data={"username": "testuser_automated", "password": "testpass"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]
