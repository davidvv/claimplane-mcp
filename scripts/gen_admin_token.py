
import asyncio
import sys
import os
from uuid import UUID

# Add project root to path
sys.path.append(os.getcwd())
from app.database import AsyncSessionLocal
from app.services.auth_service import AuthService

async def create_token():
    async with AsyncSessionLocal() as session:
        user_id = UUID('fffff33a-9d83-47d3-89b8-e58b9398699e')
        token, _ = await AuthService.create_magic_link_token(
            session=session,
            user_id=user_id,
            ip_address="127.0.0.1",
            user_agent="Agent-Browser-Test"
        )
        await session.commit()
        print(f"TOKEN: {token}")

if __name__ == "__main__":
    asyncio.run(create_token())
