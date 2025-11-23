"""
Test script to verify email notifications are working.
This will submit a test claim and trigger the email notification.
"""
import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import ClaimRepository
from app.tasks.claim_tasks import send_claim_submitted_email


async def test_email_notification():
    """Test email notification by creating a claim and triggering email."""

    print("=" * 60)
    print("Testing Email Notification System")
    print("=" * 60)

    # Test data
    test_customer_id = "3c3e7ea6-9c48-4da2-b8fa-1d04b62f2f3b"  # Your test user
    test_email = "idavidvv+AEC@gmail.com"
    test_name = "David Test"

    print(f"\n1. Creating test claim for: {test_email}")

    # Create a test claim
    async for session in get_db():
        claim_repo = ClaimRepository(session)

        claim = await claim_repo.create_claim(
            customer_id=test_customer_id,
            flight_number="TEST123",
            airline="Test Airlines",
            departure_date=datetime.now() - timedelta(days=5),
            departure_airport="MAD",
            arrival_airport="JFK",
            incident_type="delay",
            notes="This is a test claim to verify email notifications"
        )

        print(f"✓ Claim created with ID: {claim.id}")

        # Queue the email task
        print(f"\n2. Queueing email notification task...")

        result = send_claim_submitted_email.delay(
            customer_email=test_email,
            customer_name=test_name,
            claim_id=str(claim.id),
            flight_number=claim.flight_number,
            airline=claim.airline
        )

        print(f"✓ Email task queued with ID: {result.id}")
        print(f"✓ Task status: {result.status}")

        print("\n" + "=" * 60)
        print("Email notification test completed!")
        print("=" * 60)
        print(f"\nCheck your email: {test_email}")
        print("The email should arrive within a few seconds.")
        print("\nIf you don't receive it, check:")
        print("1. Spam/Junk folder")
        print("2. Celery worker logs for errors")
        print("3. SMTP credentials in .env file")
        print("\nTo monitor the task:")
        print(f"- Task ID: {result.id}")
        print("- Check Celery worker output for task completion")

        break


if __name__ == "__main__":
    print("\nStarting email notification test...\n")
    asyncio.run(test_email_notification())
