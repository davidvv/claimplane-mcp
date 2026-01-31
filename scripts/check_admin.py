
import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
sys.path.append(os.getcwd())
from app.config import config
from app.utils.db_encryption import generate_blind_index

async def check_admin():
    # Use localhost if running from host
    db_url = config.DATABASE_URL.replace("db:5432", "localhost:5432")
    engine = create_async_engine(db_url)
    email = 'vences.david@icloud.com'
    email_idx = generate_blind_index(email)
    
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT id, role FROM customers WHERE email_idx = :email_idx"), {"email_idx": email_idx})
        user = result.fetchone()
        if user:
            print(f"ADMIN_EXISTS: {user[0]} Role: {user[1]}")
            if user[1] != 'superadmin':
                print("Updating role to superadmin...")
                await conn.execute(text("UPDATE customers SET role = 'superadmin' WHERE id = :id"), {"id": user[0]})
                print("Role updated.")
        else:
            print("ADMIN_NOT_FOUND")

if __name__ == "__main__":
    asyncio.run(check_admin())
