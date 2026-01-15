"""Drop and recreate all database tables for Phase 3."""
import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.database import engine, Base
from app.models import *  # Import all models

async def recreate_tables():
    """Drop all tables and recreate them."""
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("All tables dropped.")

    print("Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(recreate_tables())
