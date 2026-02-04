#!/usr/bin/env python3
"""
Admin User Creation Script

This script creates admin or superadmin users for the ClaimPlane platform.
Use this to create the first admin users who can then manage the system.

Usage:
    # Interactive mode (recommended):
    python scripts/create_admin_user.py

    # Command-line mode:
    python scripts/create_admin_user.py --email admin@example.com --password SecurePass123! --role admin

    # Create superadmin:
    python scripts/create_admin_user.py --email superadmin@example.com --password SecurePass123! --role superadmin

Requirements:
    - Database must be accessible (check DATABASE_URL in .env)
    - ClaimPlane conda environment must be activated
    - Run from project root directory

Security Notes:
    - Passwords must meet minimum requirements (12+ chars, upper, lower, digit, special)
    - Passwords are hashed using bcrypt before storage
    - Never commit passwords to version control
    - Use strong, unique passwords for production

Role Types:
    - customer: Regular user (can submit claims)
    - admin: Can manage claims, review documents, update statuses
    - superadmin: Full system access (can promote other users)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import config
from app.models import Customer
from app.services.auth_service import AuthService


async def create_admin_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone: str = None,
    role: str = Customer.ROLE_ADMIN
) -> Customer:
    """
    Create an admin or superadmin user.

    Args:
        email: User's email address (must be unique)
        password: Plain text password (will be hashed)
        first_name: User's first name
        last_name: User's last name
        phone: Optional phone number
        role: User role ('admin' or 'superadmin')

    Returns:
        Created Customer instance

    Raises:
        ValueError: If email already exists or validation fails
    """
    # Create async engine
    engine = create_async_engine(
        config.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if email already exists
        stmt = select(Customer).where(Customer.email == email)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError(f"User with email {email} already exists (ID: {existing_user.id}, Role: {existing_user.role})")

        # Validate role
        if role not in Customer.ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of: {', '.join(Customer.ROLES)}")

        # Create user using AuthService
        user = await AuthService.register_user(
            session=session,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )

        # Mark email as verified (admins don't need email verification)
        user.is_email_verified = True

        await session.commit()
        await session.refresh(user)

        print(f"\n✅ Success! {role.capitalize()} user created:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.first_name} {user.last_name}")
        print(f"   Role: {user.role}")
        print(f"   Active: {user.is_active}")
        print(f"   Email Verified: {user.is_email_verified}")

        return user


async def interactive_create_admin():
    """Interactive mode for creating admin users."""
    print("=" * 60)
    print("ClaimPlane - Admin User Creation")
    print("=" * 60)
    print()

    # Get user input
    print("Enter admin user details:")
    print()

    email = input("Email address: ").strip()
    if not email or '@' not in email:
        print("❌ Error: Invalid email address")
        sys.exit(1)

    first_name = input("First name: ").strip()
    if not first_name:
        print("❌ Error: First name is required")
        sys.exit(1)

    last_name = input("Last name: ").strip()
    if not last_name:
        print("❌ Error: Last name is required")
        sys.exit(1)

    phone = input("Phone (optional, press Enter to skip): ").strip() or None

    # Role selection
    print("\nSelect role:")
    print("  1. Admin (can manage claims and documents)")
    print("  2. Superadmin (full system access)")
    role_choice = input("Enter choice (1 or 2): ").strip()

    if role_choice == "1":
        role = Customer.ROLE_ADMIN
    elif role_choice == "2":
        role = Customer.ROLE_SUPERADMIN
    else:
        print("❌ Error: Invalid choice. Must be 1 or 2")
        sys.exit(1)

    # Password input (visible)
    print("\nPassword requirements:")
    print("  - At least 12 characters")
    print("  - Contains uppercase letter")
    print("  - Contains lowercase letter")
    print("  - Contains digit")
    print("  - Contains special character")
    print()

    password = input("Password: ").strip()
    password_confirm = input("Confirm password: ").strip()

    if password != password_confirm:
        print("❌ Error: Passwords do not match")
        sys.exit(1)

    if len(password) < 12:
        print("❌ Error: Password must be at least 12 characters")
        sys.exit(1)

    # Confirmation
    print("\n" + "-" * 60)
    print("Review details:")
    print(f"  Email: {email}")
    print(f"  Name: {first_name} {last_name}")
    print(f"  Phone: {phone or 'N/A'}")
    print(f"  Role: {role}")
    print("-" * 60)

    confirm = input("\nCreate this user? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)

    # Create user
    try:
        await create_admin_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )
        print("\n✨ Admin user created successfully!")
        print(f"\nYou can now login at the admin dashboard with:")
        print(f"  Email: {email}")
        print(f"  Password: [the password you just entered]")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create admin users for ClaimPlane",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended):
  python scripts/create_admin_user.py

  # Command-line mode:
  python scripts/create_admin_user.py --email admin@example.com --password "SecurePass123!" --first-name John --last-name Doe --role admin

  # Create superadmin:
  python scripts/create_admin_user.py --email superadmin@example.com --password "SuperSecure456!" --first-name Jane --last-name Admin --role superadmin
        """
    )

    parser.add_argument('--email', help='Admin email address')
    parser.add_argument('--password', help='Admin password (use quotes if contains special chars)')
    parser.add_argument('--first-name', help='First name')
    parser.add_argument('--last-name', help='Last name')
    parser.add_argument('--phone', help='Phone number (optional)')
    parser.add_argument('--role', choices=['admin', 'superadmin'], default='admin', help='User role')

    args = parser.parse_args()

    # If no arguments provided, use interactive mode
    if not any([args.email, args.password, args.first_name, args.last_name]):
        await interactive_create_admin()
        return

    # Validate all required args are present for CLI mode
    if not all([args.email, args.password, args.first_name, args.last_name]):
        parser.error("In CLI mode, --email, --password, --first-name, and --last-name are required")

    # Create user in CLI mode
    try:
        await create_admin_user(
            email=args.email,
            password=args.password,
            first_name=args.first_name,
            last_name=args.last_name,
            phone=args.phone,
            role=args.role
        )
        print("\n✨ Admin user created successfully!")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
