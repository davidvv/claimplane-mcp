"""Delete a user account from the database."""
import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import Customer, RefreshToken

async def delete_user():
    email = "idavidvv@gmail.com"

    # Use localhost since we're running locally
    database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/flight_claim"

    # Create async engine
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            # First, find the user to get their ID
            from sqlalchemy import select
            stmt = select(Customer).where(Customer.email == email)
            result = await session.execute(stmt)
            customer = result.scalar_one_or_none()

            if not customer:
                print(f"❌ User with email {email} not found!")
                return

            user_id = customer.id
            print(f"Found user: {customer.email} (ID: {user_id})")

            # Delete refresh tokens first (foreign key constraint)
            delete_tokens = delete(RefreshToken).where(RefreshToken.user_id == user_id)
            result = await session.execute(delete_tokens)
            print(f"Deleted {result.rowcount} refresh tokens")

            # Delete the customer
            delete_customer = delete(Customer).where(Customer.email == email)
            result = await session.execute(delete_customer)
            print(f"Deleted {result.rowcount} customer record")

        print(f"✅ Successfully deleted user: {email}")

if __name__ == "__main__":
    asyncio.run(delete_user())
