"""Reset password for a user in the database."""
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import config
from app.models import Customer
from app.services.password_service import PasswordService

async def reset_password():
    email = "idavidvv@gmail.com"
    new_password = "Welcome123!"

    # Create async engine
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Find the user
        stmt = select(Customer).where(Customer.email == email)
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            print(f"❌ User with email {email} not found!")
            return

        # Hash the new password
        new_hash = PasswordService.hash_password(new_password)

        print(f"✅ User found: {customer.email} (ID: {customer.id})")
        print(f"   Old hash: {customer.password_hash[:50]}...")
        print(f"   New hash: {new_hash[:50]}...")

        # Update the password
        customer.password_hash = new_hash
        await session.commit()

        print(f"✅ Password updated successfully!")
        print(f"   Email: {email}")
        print(f"   New password: {new_password}")

if __name__ == "__main__":
    asyncio.run(reset_password())
