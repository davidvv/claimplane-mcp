"""
Celery tasks for claim notifications.

These tasks run in the background, separate from the main API.
When you call task_name.delay(), the task is added to the Redis queue,
and a Celery worker picks it up and executes it asynchronously.

This is important for:
1. Not blocking API responses (emails can take 1-2 seconds to send)
2. Automatic retries if email sending fails
3. Better user experience (instant API response)
"""
import logging
import asyncio
from typing import Optional

from app.celery_app import celery_app
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Helper function to run async code in Celery tasks.

    Celery doesn't natively support async/await, so we need to create
    an event loop to run our async EmailService methods.
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@celery_app.task(
    name="send_claim_submitted_email",
    bind=True,  # Gives us access to the task instance (for retries)
    max_retries=3,  # Retry up to 3 times if it fails
    default_retry_delay=60  # Wait 60 seconds between retries
)
def send_claim_submitted_email(
    self,
    customer_email: str,
    customer_name: str,
    claim_id: str,
    flight_number: str,
    airline: str
):
    """
    Celery task: Send email when a claim is submitted.

    Args:
        self: Task instance (automatically provided by Celery when bind=True)
        customer_email: Customer's email address
        customer_name: Customer's full name
        claim_id: UUID of the claim
        flight_number: Flight number (e.g., "LH123")
        airline: Airline name

    Usage:
        # In your router, call it like this:
        send_claim_submitted_email.delay(
            customer_email="john@example.com",
            customer_name="John Doe",
            claim_id="123e4567-e89b-12d3-a456-426614174000",
            flight_number="LH123",
            airline="Lufthansa"
        )
    """
    logger.info(f"Task started: Sending claim submitted email to {customer_email}")

    try:
        # Call the async EmailService method
        success = run_async(
            EmailService.send_claim_submitted_email(
                customer_email=customer_email,
                customer_name=customer_name,
                claim_id=claim_id,
                flight_number=flight_number,
                airline=airline
            )
        )

        if success:
            logger.info(f"Task completed: Email sent successfully to {customer_email}")
            return {"status": "success", "email": customer_email}
        else:
            logger.error(f"Task failed: Email sending failed for {customer_email}")
            # Retry the task automatically
            raise Exception(f"Email sending failed for {customer_email}")

    except Exception as exc:
        logger.error(f"Task error: {str(exc)}")
        # Retry the task with exponential backoff
        # First retry after 60 seconds, then 120, then 240
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="send_status_update_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_status_update_email(
    self,
    customer_email: str,
    customer_name: str,
    claim_id: str,
    old_status: str,
    new_status: str,
    flight_number: str,
    airline: str,
    change_reason: Optional[str] = None,
    compensation_amount: Optional[float] = None
):
    """
    Celery task: Send email when claim status changes.

    Args:
        self: Task instance
        customer_email: Customer's email address
        customer_name: Customer's full name
        claim_id: UUID of the claim
        old_status: Previous status
        new_status: New status
        flight_number: Flight number
        airline: Airline name
        change_reason: Reason for status change (optional)
        compensation_amount: Compensation amount if approved (optional)

    Usage:
        send_status_update_email.delay(
            customer_email="john@example.com",
            customer_name="John Doe",
            claim_id="123e4567-e89b-12d3-a456-426614174000",
            old_status="submitted",
            new_status="approved",
            flight_number="LH123",
            airline="Lufthansa",
            change_reason="All documents verified",
            compensation_amount=600.00
        )
    """
    logger.info(f"Task started: Sending status update email to {customer_email} ({old_status} -> {new_status})")

    try:
        success = run_async(
            EmailService.send_status_update_email(
                customer_email=customer_email,
                customer_name=customer_name,
                claim_id=claim_id,
                old_status=old_status,
                new_status=new_status,
                flight_number=flight_number,
                airline=airline,
                change_reason=change_reason,
                compensation_amount=compensation_amount
            )
        )

        if success:
            logger.info(f"Task completed: Status update email sent successfully to {customer_email}")
            return {"status": "success", "email": customer_email, "new_status": new_status}
        else:
            logger.error(f"Task failed: Status update email failed for {customer_email}")
            raise Exception(f"Email sending failed for {customer_email}")

    except Exception as exc:
        logger.error(f"Task error: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="send_document_rejected_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_document_rejected_email(
    self,
    customer_email: str,
    customer_name: str,
    claim_id: str,
    document_type: str,
    rejection_reason: str,
    flight_number: str,
    airline: str
):
    """
    Celery task: Send email when a document is rejected.

    Args:
        self: Task instance
        customer_email: Customer's email address
        customer_name: Customer's full name
        claim_id: UUID of the claim
        document_type: Type of document rejected (e.g., "boarding_pass")
        rejection_reason: Why the document was rejected
        flight_number: Flight number
        airline: Airline name

    Usage:
        send_document_rejected_email.delay(
            customer_email="john@example.com",
            customer_name="John Doe",
            claim_id="123e4567-e89b-12d3-a456-426614174000",
            document_type="boarding_pass",
            rejection_reason="Image is blurry and unreadable",
            flight_number="LH123",
            airline="Lufthansa"
        )
    """
    logger.info(f"Task started: Sending document rejected email to {customer_email}")

    try:
        success = run_async(
            EmailService.send_document_rejected_email(
                customer_email=customer_email,
                customer_name=customer_name,
                claim_id=claim_id,
                document_type=document_type,
                rejection_reason=rejection_reason,
                flight_number=flight_number,
                airline=airline
            )
        )

        if success:
            logger.info(f"Task completed: Document rejected email sent successfully to {customer_email}")
            return {"status": "success", "email": customer_email, "document_type": document_type}
        else:
            logger.error(f"Task failed: Document rejected email failed for {customer_email}")
            raise Exception(f"Email sending failed for {customer_email}")

    except Exception as exc:
        logger.error(f"Task error: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# Example: How to check task status
# If you save the result: task_result = send_claim_submitted_email.delay(...)
# You can check status: task_result.status (PENDING, STARTED, SUCCESS, FAILURE, RETRY)
# Get result: task_result.get(timeout=10)  # Wait up to 10 seconds for result
