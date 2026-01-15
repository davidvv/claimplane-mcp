"""Create a test user with known credentials for testing."""
import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from passlib.context import CryptContext
from sqlalchemy import select
from app.database import get_db
from app.models import Customer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """Create test user with credentials from test_login.json."""
    async for session in get_db():
        # Check if user already exists
        result = await session.execute(
            select(Customer).where(Customer.email == "idavidvv@gmail.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User idavidvv@gmail.com already exists. Updating password...")
            # Update password
            existing_user.password_hash = pwd_context.hash("Welcome123!")
            await session.commit()
            print("Password updated successfully!")
        else:
            print("Creating new user idavidvv@gmail.com...")
            # Create new user
            new_user = Customer(
                email="idavidvv@gmail.com",
                password_hash=pwd_context.hash("Welcome123!"),
                first_name="Test",
                last_name="User",
                phone="1234567890",
                role="customer",
                is_active=True,
                is_email_verified=True
            )
            session.add(new_user)
            await session.commit()
            print("User created successfully!")

        print("\nTest credentials:")
        print("  Email: idavidvv@gmail.com")
        print("  Password: Welcome123!")
        break

if __name__ == "__main__":
    asyncio.run(create_test_user())
