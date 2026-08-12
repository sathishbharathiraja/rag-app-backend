import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_success(test_client: AsyncClient, db_session):
    # Ensure cleanup before test just in case
    from app.models.models import User
    from sqlalchemy.future import select
    result = await db_session.execute(select(User).where(User.username == "newuser_123"))
    user = result.scalars().first()
    if user:
        await db_session.delete(user)
        await db_session.commit()

    response = await test_client.post(
        "/api/register",
        json={"username": "newuser_123", "password": "securepassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Cleanup after test
    result = await db_session.execute(select(User).where(User.username == "newuser_123"))
    user = result.scalars().first()
    if user:
        await db_session.delete(user)
        await db_session.commit()

@pytest.mark.asyncio
async def test_register_duplicate(test_client: AsyncClient, test_user):
    # Try to register a user that already exists (test_user from conftest)
    response = await test_client.post(
        "/api/register",
        json={"username": "testuser_automated", "password": "anotherpassword"}
    )
    # Should return 400 Bad Request, NOT 500 Internal Server Error
    assert response.status_code == 400
    assert "Username already exists" in response.json()["detail"] or "already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient, test_user):
    response = await test_client.post(
        "/api/login",
        data={"username": "testuser_automated", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_invalid_password(test_client: AsyncClient, test_user):
    response = await test_client.post(
        "/api/login",
        data={"username": "testuser_automated", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
