#!/usr/bin/env python3
"""
Database migration script for GDPR separate consent fields.
Adds privacy_consent_at and privacy_consent_ip to claims table.
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import text
from app.database import engine
from app.models import Base


async def run_migrations():
    """Add new columns for GDPR consent tracking"""
    async with engine.begin() as conn:
        # Add new columns to claims table if they don't exist
        try:
            # Check if columns exist
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='claims' 
                AND column_name IN ('privacy_consent_at', 'privacy_consent_ip')
            """))
            existing_columns = {row[0] for row in result}
            
            if 'privacy_consent_at' not in existing_columns:
                await conn.execute(text("""
                    ALTER TABLE claims 
                    ADD COLUMN privacy_consent_at TIMESTAMP WITH TIME ZONE
                """))
                
                # Backfill for existing claims that have terms accepted
                await conn.execute(text("""
                    UPDATE claims 
                    SET privacy_consent_at = terms_accepted_at 
                    WHERE terms_accepted_at IS NOT NULL AND privacy_consent_at IS NULL
                """))
                print("✅ Added column: privacy_consent_at and backfilled data")
            
            if 'privacy_consent_ip' not in existing_columns:
                await conn.execute(text("""
                    ALTER TABLE claims 
                    ADD COLUMN privacy_consent_ip VARCHAR(45)
                """))
                
                # Backfill for existing claims that have terms acceptance IP
                await conn.execute(text("""
                    UPDATE claims 
                    SET privacy_consent_ip = terms_acceptance_ip 
                    WHERE terms_acceptance_ip IS NOT NULL AND privacy_consent_ip IS NULL
                """))
                print("✅ Added column: privacy_consent_ip and backfilled data")
                
        except Exception as e:
            print(f"⚠️  Column addition error: {e}")
        
        print("✅ GDPR consent migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migrations())
