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

async def swap_columns():
    """
    Swap encrypted columns with original columns to complete migration.
    """
    engine = create_async_engine(config.DATABASE_URL)
    
    async with engine.begin() as conn:
        logger.info("Starting column swap...")
        
        # 1. CUSTOMERS
        logger.info("Swapping customer columns...")
        customer_fields = ['email', 'first_name', 'last_name', 'phone', 'street', 'city', 'postal_code', 'country']
        
        for field in customer_fields:
            # Rename original to _plaintext (backup)
            await conn.execute(text(f"ALTER TABLE customers RENAME COLUMN {field} TO {field}_plaintext"))
            # Rename encrypted to original name
            await conn.execute(text(f"ALTER TABLE customers RENAME COLUMN {field}_encrypted TO {field}"))
            # Set constraints if needed (e.g. NOT NULL for email/names)
            if field in ['email', 'first_name', 'last_name']:
                 # Note: Encrypted columns are nullable by default in my migration script, 
                 # but original might have been NOT NULL. 
                 # We should enforce NOT NULL if original was.
                 pass 

        # 2. PASSENGERS
        logger.info("Swapping passenger columns...")
        passenger_fields = ['first_name', 'last_name', 'email', 'ticket_number']
        
        for field in passenger_fields:
            await conn.execute(text(f"ALTER TABLE passengers RENAME COLUMN {field} TO {field}_plaintext"))
            await conn.execute(text(f"ALTER TABLE passengers RENAME COLUMN {field}_encrypted TO {field}"))

        # 3. CLAIMS
        logger.info("Swapping claim columns...")
        claim_fields = ['booking_reference', 'ticket_number']
        
        for field in claim_fields:
            await conn.execute(text(f"ALTER TABLE claims RENAME COLUMN {field} TO {field}_plaintext"))
            await conn.execute(text(f"ALTER TABLE claims RENAME COLUMN {field}_encrypted TO {field}"))
            
        logger.info("Column swap completed successfully.")

if __name__ == "__main__":
    asyncio.run(swap_columns())
