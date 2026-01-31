
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import engine

async def add_columns():
    """Add account lockout columns to the customers table."""
    async with engine.begin() as conn:
        print("Checking for existing columns...")
        # Check if columns already exist
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='customers' AND column_name IN ('failed_login_attempts', 'locked_until')"
        ))
        existing_columns = [row[0] for row in result.fetchall()]
        
        if 'failed_login_attempts' not in existing_columns:
            print("Adding failed_login_attempts column...")
            await conn.execute(text(
                "ALTER TABLE customers ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"
            ))
        
        if 'locked_until' not in existing_columns:
            print("Adding locked_until column...")
            await conn.execute(text(
                "ALTER TABLE customers ADD COLUMN locked_until TIMESTAMP WITH TIME ZONE"
            ))
            
        print("Done.")

if __name__ == "__main__":
    asyncio.run(add_columns())
