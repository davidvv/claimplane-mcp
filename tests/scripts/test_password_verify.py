"""Test password verification to debug login issue."""
import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import config
from app.models import Customer
from app.services.password_service import PasswordService

async def test_password():
    # Create async engine
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get the user
        stmt = select(Customer).where(Customer.email == "idavidvv@gmail.com")
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            print("❌ User not found!")
            return

        print(f"✅ User found: {customer.email}")
        print(f"   User ID: {customer.id}")
        print(f"   Is Active: {customer.is_active}")
        print(f"   Has password hash: {bool(customer.password_hash)}")
        print(f"   Password hash (first 50 chars): {customer.password_hash[:50] if customer.password_hash else 'None'}...")

        # Test password verification
        test_password = "Welcome123!"
        print(f"\nTesting password: '{test_password}'")

        try:
            is_valid = PasswordService.verify_password(test_password, customer.password_hash)
            print(f"Password verification result: {is_valid}")

            if is_valid:
                print("✅ Password verification PASSED!")
            else:
                print("❌ Password verification FAILED!")

                # Try to hash the same password and compare
                new_hash = PasswordService.hash_password(test_password)
                print(f"\nNew hash of same password: {new_hash[:50]}...")
                is_valid_new = PasswordService.verify_password(test_password, new_hash)
                print(f"New hash verification: {is_valid_new}")
        except Exception as e:
            print(f"❌ Exception during verification: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_password())
