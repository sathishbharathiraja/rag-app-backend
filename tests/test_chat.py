import pytest
from httpx import AsyncClient
import os

@pytest.mark.asyncio
async def test_chat_without_session(test_client: AsyncClient, auth_token: str):
    # Test chatting without a session ID to ensure a new session is created
    response = await test_client.post(
        "/api/chat",
        json={"message": "Hello! Reply with exactly 'Hi'"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # The actual AI call will take place. If it succeeds without 500, we're good.
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    
@pytest.mark.asyncio
async def test_chat_unauthorized(test_client: AsyncClient):
    # Ensure hitting the chat endpoint without a token fails
    response = await test_client.post(
        "/api/chat",
        json={"message": "Hello!"}
    )
    assert response.status_code == 401
