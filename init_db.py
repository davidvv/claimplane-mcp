#!/usr/bin/env python3
"""
Database initialization script for Flight Claim System
Creates all tables defined in the models
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base
from app.models import Customer, Claim
from app.config import settings

async def init_database():
    """Initialize the database by creating all tables"""
    try:
        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=True)
        
        # Create all tables
        async with engine.begin() as conn:
            print("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_database())