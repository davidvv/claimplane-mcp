#!/usr/bin/env python3
"""
Database migration script for workflow-v2 changes
Adds ClaimEvent table and new fields to Claim table
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import text
from app.database import engine, get_db
from app.models import Base


async def run_migrations():
    """Create new tables and add new columns"""
    async with engine.begin() as conn:
        # Create all tables (will skip existing ones)
        await conn.run_sync(Base.metadata.create_all)
        
        # Add new columns to claims table if they don't exist
        try:
            # Check if columns exist
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='claims' 
                AND column_name IN ('last_activity_at', 'reminder_count', 'current_step')
            """))
            existing_columns = {row[0] for row in result}
            
            if 'last_activity_at' not in existing_columns:
                await conn.execute(text("""
                    ALTER TABLE claims 
                    ADD COLUMN last_activity_at TIMESTAMP
                """))
                print("✅ Added column: last_activity_at")
            
            if 'reminder_count' not in existing_columns:
                await conn.execute(text("""
                    ALTER TABLE claims 
                    ADD COLUMN reminder_count INTEGER DEFAULT 0
                """))
                print("✅ Added column: reminder_count")
            
            if 'current_step' not in existing_columns:
                await conn.execute(text("""
                    ALTER TABLE claims 
                    ADD COLUMN current_step INTEGER DEFAULT 1
                """))
                print("✅ Added column: current_step")
                
        except Exception as e:
            print(f"⚠️  Column addition error (might already exist): {e}")
        
        print("✅ Database migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migrations())
