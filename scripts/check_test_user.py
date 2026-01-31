
import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.config import config

async def check_user():
    # Use localhost if running from host
    db_url = config.DATABASE_URL.replace("db:5432", "localhost:5432")
    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, email_plaintext FROM customers WHERE email_plaintext = 'idavidvv@gmail.com'"))
        user = result.fetchone()
        if user:
            print(f"USER_EXISTS: {user[0]}")
        else:
            print("USER_NOT_FOUND")

if __name__ == "__main__":
    asyncio.run(check_user())
