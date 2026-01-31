import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_constraints():
    """
    Remove NOT NULL constraints from backup plaintext columns.
    """
    # Use localhost if running from host
    db_url = config.DATABASE_URL.replace("db:5432", "localhost:5432")
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        logger.info("Fixing backup column constraints...")
        
        # 1. CUSTOMERS
        logger.info("Fixing customers table...")
        await conn.execute(text("ALTER TABLE customers ALTER COLUMN email_plaintext DROP NOT NULL"))
        await conn.execute(text("ALTER TABLE customers ALTER COLUMN first_name_plaintext DROP NOT NULL"))
        await conn.execute(text("ALTER TABLE customers ALTER COLUMN last_name_plaintext DROP NOT NULL"))

        # 2. PASSENGERS
        logger.info("Fixing passengers table...")
        await conn.execute(text("ALTER TABLE passengers ALTER COLUMN first_name_plaintext DROP NOT NULL"))
        await conn.execute(text("ALTER TABLE passengers ALTER COLUMN last_name_plaintext DROP NOT NULL"))

        logger.info("Constraints fixed successfully.")

if __name__ == "__main__":
    asyncio.run(fix_constraints())
