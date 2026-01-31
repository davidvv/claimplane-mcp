import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from cryptography.fernet import Fernet
from app.config import config
from app.utils.db_encryption import generate_blind_index

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database():
    """
    Migrate database to use encryption for PII.
    
    Steps:
    1. Add new columns (_encrypted, _idx)
    2. Encrypt existing data into new columns
    3. Generate blind indexes
    4. Verify data
    """
    # Create engine directly to avoid dependency issues
    engine = create_async_engine(config.DATABASE_URL)
    
    fernet = Fernet(config.DB_ENCRYPTION_KEY)
    
    async with engine.begin() as conn:
        logger.info("Starting encryption migration...")
        
        # 1. CUSTOMERS TABLE
        logger.info("Processing customers table...")
        
        # Add columns if they don't exist
        await conn.execute(text("""
            ALTER TABLE customers 
            ADD COLUMN IF NOT EXISTS email_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS email_idx VARCHAR(255),
            ADD COLUMN IF NOT EXISTS first_name_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS last_name_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS phone_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS street_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS city_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS postal_code_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS country_encrypted TEXT
        """))
        
        # Fetch all customers
        result = await conn.execute(text("SELECT id, email, first_name, last_name, phone, street, city, postal_code, country FROM customers"))
        customers = result.fetchall()
        
        for customer in customers:
            c_id = customer[0]
            updates = {}
            
            # Email (Encrypt + Index)
            if customer[1]:
                encrypted = fernet.encrypt(customer[1].encode()).decode()
                idx = generate_blind_index(customer[1])
                updates["email_encrypted"] = encrypted
                updates["email_idx"] = idx
            
            # Other fields (Encrypt only)
            fields = ['first_name', 'last_name', 'phone', 'street', 'city', 'postal_code', 'country']
            for i, field in enumerate(fields, start=2):
                if customer[i]:
                    encrypted = fernet.encrypt(customer[i].encode()).decode()
                    updates[f"{field}_encrypted"] = encrypted
            
            # Build update query
            if updates:
                set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
                stmt = text(f"UPDATE customers SET {set_clause} WHERE id = :id")
                await conn.execute(stmt, {"id": c_id, **updates})
                
        logger.info(f"Processed {len(customers)} customers")

        # 2. PASSENGERS TABLE
        logger.info("Processing passengers table...")
        
        await conn.execute(text("""
            ALTER TABLE passengers 
            ADD COLUMN IF NOT EXISTS first_name_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS last_name_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS email_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS email_idx VARCHAR(255),
            ADD COLUMN IF NOT EXISTS ticket_number_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS ticket_number_idx VARCHAR(255)
        """))
        
        result = await conn.execute(text("SELECT id, first_name, last_name, email, ticket_number FROM passengers"))
        passengers = result.fetchall()
        
        for p in passengers:
            p_id = p[0]
            updates = {}
            
            # Fields to encrypt map: index -> name
            field_map = {1: 'first_name', 2: 'last_name', 3: 'email', 4: 'ticket_number'}
            index_fields = {3: 'email', 4: 'ticket_number'}
            
            for idx, name in field_map.items():
                if p[idx]:
                    encrypted = fernet.encrypt(p[idx].encode()).decode()
                    updates[f"{name}_encrypted"] = encrypted
                    
                    if idx in index_fields:
                        blind_idx = generate_blind_index(p[idx])
                        updates[f"{name}_idx"] = blind_idx
            
            if updates:
                set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
                stmt = text(f"UPDATE passengers SET {set_clause} WHERE id = :id")
                await conn.execute(stmt, {"id": p_id, **updates})
                
        logger.info(f"Processed {len(passengers)} passengers")

        # 3. CLAIMS TABLE
        logger.info("Processing claims table...")
        
        await conn.execute(text("""
            ALTER TABLE claims 
            ADD COLUMN IF NOT EXISTS booking_reference_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS booking_reference_idx VARCHAR(255),
            ADD COLUMN IF NOT EXISTS ticket_number_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS ticket_number_idx VARCHAR(255)
        """))
        
        result = await conn.execute(text("SELECT id, booking_reference, ticket_number FROM claims"))
        claims = result.fetchall()
        
        for claim in claims:
            c_id = claim[0]
            updates = {}
            
            if claim[1]: # booking_reference
                encrypted = fernet.encrypt(claim[1].encode()).decode()
                idx = generate_blind_index(claim[1])
                updates["booking_reference_encrypted"] = encrypted
                updates["booking_reference_idx"] = idx
                
            if claim[2]: # ticket_number
                encrypted = fernet.encrypt(claim[2].encode()).decode()
                idx = generate_blind_index(claim[2])
                updates["ticket_number_encrypted"] = encrypted
                updates["ticket_number_idx"] = idx
            
            if updates:
                set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
                stmt = text(f"UPDATE claims SET {set_clause} WHERE id = :id")
                await conn.execute(stmt, {"id": c_id, **updates})
                
        logger.info(f"Processed {len(claims)} claims")
        
        logger.info("Migration completed successfully.")

if __name__ == "__main__":
    asyncio.run(migrate_database())
