import asyncio
from app.core.database import engine, Base
from app.models import models

async def main():
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database recreated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
