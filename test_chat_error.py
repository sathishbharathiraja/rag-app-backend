import asyncio
from app.api.chat import chat, ChatRequest
from app.core.database import AsyncSessionLocal
from app.models.models import User

async def main():
    async with AsyncSessionLocal() as db:
        user = User(id=1, username="test")
        req = ChatRequest(message="test query", session_id=None)
        try:
            res = await chat(req, db, user)
            print("Chat success:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("Chat crashed:", e)

asyncio.run(main())
