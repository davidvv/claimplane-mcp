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
    """Helper function to run async code in Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        # Clean up any pending tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        # Run one more iteration to handle cancellations
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        # Close the loop
        loop.close()
        # Reset event loop to None to prevent reuse
        asyncio.set_event_loop(None)


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
    airline: str,
    magic_link_token: Optional[str] = None
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
        magic_link_token: Optional magic link token for passwordless access

    Usage:
        # In your router, call it like this:
        send_claim_submitted_email.delay(
            customer_email="john@example.com",
            customer_name="John Doe",
            claim_id="123e4567-e89b-12d3-a456-426614174000",
            flight_number="LH123",
            airline="Lufthansa",
            magic_link_token="abc123..."
        )
    """
    logger.info(f"Task started: Sending claim submitted email to {customer_email}")

    try:
        # Attach POA if it exists
        attachments = []
        
        # We need to fetch the POA file from storage/db.
        # Since this is a synchronous function calling run_async, we need to do the fetching inside an async block
        # OR we can do it here if we had synchronous access.
        # Let's delegate the fetching to a helper function that runs inside run_async.
        
        async def fetch_poa_and_send():
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from app.config import config
            from app.repositories.file_repository import FileRepository
            from app.services.file_service import FileService
            from app.models import ClaimFile
            from uuid import UUID

            # Create session to find POA
            engine = create_async_engine(config.DATABASE_URL, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            poa_attachment = None
            
            async with async_session() as session:
                try:
                    file_repo = FileRepository(session)
                    # Find POA file for this claim
                    files = await file_repo.get_by_claim_id(UUID(claim_id))
                    poa_file = next((f for f in files if f.document_type == ClaimFile.DOCUMENT_POWER_OF_ATTORNEY), None)
                    
                    if poa_file:
                        # Fetch content
                        file_service = FileService(session)
                        # We need a user_id to download, but as a system task we might need to bypass or use the owner's ID
                        # Let's use the owner's ID (poa_file.customer_id)
                        content, _ = await file_service.download_file(str(poa_file.id), str(poa_file.customer_id))
                        
                        poa_attachment = {
                            "filename": poa_file.original_filename or "Power_of_Attorney.pdf",
                            "content": content,
                            "mime_type": "application/pdf"
                        }
                        logger.info(f"Found POA for claim {claim_id}, attaching to email")
                except Exception as e:
                    logger.warning(f"Failed to fetch POA for email: {e}")
                
            # Send email
            return await EmailService.send_claim_submitted_email(
                customer_email=customer_email,
                customer_name=customer_name,
                claim_id=claim_id,
                flight_number=flight_number,
                airline=airline,
                magic_link_token=magic_link_token,
                attachments=[poa_attachment] if poa_attachment else None
            )

        success = run_async(fetch_poa_and_send())

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


@celery_app.task(
    name="send_magic_link_login_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_magic_link_login_email(
    self,
    customer_email: str,
    customer_name: str,
    magic_link_token: str,
    ip_address: Optional[str] = None
):
    """
    Celery task: Send magic link email for passwordless login.

    Args:
        self: Task instance
        customer_email: Customer's email address
        customer_name: Customer's full name
        magic_link_token: Magic link token for authentication
        ip_address: IP address where the request originated

    Usage:
        send_magic_link_login_email.delay(
            customer_email="john@example.com",
            customer_name="John Doe",
            magic_link_token="abc123...",
            ip_address="192.168.1.1"
        )
    """
    logger.info(f"Task started: Sending magic link login email to {customer_email}")

    try:
        success = run_async(
            EmailService.send_magic_link_login_email(
                customer_email=customer_email,
                customer_name=customer_name,
                magic_link_token=magic_link_token,
                ip_address=ip_address
            )
        )

        if success:
            logger.info(f"Task completed: Magic link login email sent successfully to {customer_email}")
            return {"status": "success", "email": customer_email}
        else:
            logger.error(f"Task failed: Magic link login email failed for {customer_email}")
            raise Exception(f"Email sending failed for {customer_email}")

    except Exception as exc:
        logger.error(f"Task error: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# Example: How to check task status
# If you save the result: task_result = send_claim_submitted_email.delay(...)
# You can check status: task_result.status (PENDING, STARTED, SUCCESS, FAILURE, RETRY)
# Get result: task_result.get(timeout=10)  # Wait up to 10 seconds for result


# Phase 6: AeroDataBox Flight Data Backfill Task

@celery_app.task(
    name="backfill_flight_data",
    bind=True,
    max_retries=1,  # Only retry once if the entire task fails
    time_limit=3600  # 1 hour timeout for the entire task
)
def backfill_flight_data(
    self,
    batch_size: int = 50,
    admin_user_id: Optional[str] = None
):
    """
    Celery task: Backfill flight data for existing claims without verification.

    This task processes claims in batches to avoid overwhelming the API quota.
    It respects quota limits and stops if the emergency brake is triggered (>95%).

    **Cost Control**:
    - Each claim consumes 2 API credits (TIER 2 endpoint)
    - Free tier: 600 credits/month = 300 claims/month
    - Pro tier: 3000 credits/month = 1500 claims/month
    - Uses 24-hour cache to avoid duplicate API calls

    **Usage**:
        # Backfill 50 claims (default batch)
        backfill_flight_data.delay()

        # Backfill 100 claims
        backfill_flight_data.delay(batch_size=100)

        # Backfill with admin tracking
        backfill_flight_data.delay(
            batch_size=50,
            admin_user_id="123e4567-e89b-12d3-a456-426614174000"
        )

    Args:
        self: Task instance
        batch_size: Number of claims to process in this run (default: 50)
        admin_user_id: Optional admin user ID who triggered the backfill

    Returns:
        Dict with backfill statistics:
        - total_processed: Number of claims processed
        - verified_count: Number successfully verified
        - failed_count: Number that failed verification
        - api_credits_used: Total API credits consumed
        - quota_exceeded: Whether quota was exceeded during processing
    """
    from uuid import UUID
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.config import config
    from app.repositories.flight_data_repository import FlightDataRepository
    from app.repositories.claim_repository import ClaimRepository
    from app.services.flight_data_service import FlightDataService
    from app.services.quota_tracking_service import QuotaTrackingService

    logger.info(
        f"Task started: Backfilling flight data for up to {batch_size} claims "
        f"(triggered_by={admin_user_id or 'system'})"
    )

    # Statistics tracking
    stats = {
        "total_processed": 0,
        "verified_count": 0,
        "failed_count": 0,
        "api_credits_used": 0,
        "quota_exceeded": False,
        "errors": []
    }

    async def _backfill_claims():
        """Async function to process claims."""
        # Create async database session
        engine = create_async_engine(config.DATABASE_URL, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            try:
                flight_repo = FlightDataRepository(session)
                claim_repo = ClaimRepository(session)

                # Get claims without flight data
                claims = await flight_repo.get_claims_without_flight_data(limit=batch_size)

                if not claims:
                    logger.info("No claims found without flight data. Backfill complete.")
                    return stats

                logger.info(f"Found {len(claims)} claims to backfill")

                # Process each claim
                for idx, claim in enumerate(claims, 1):
                    try:
                        # Check quota before each API call
                        quota_available = await QuotaTrackingService.check_quota_available(session)

                        if not quota_available:
                            logger.warning(
                                f"API quota exceeded (>95%) after processing {idx-1} claims. "
                                f"Stopping backfill."
                            )
                            stats["quota_exceeded"] = True
                            break

                        logger.info(
                            f"Processing claim {idx}/{len(claims)}: {claim.id} "
                            f"(flight {claim.flight_number} on {claim.departure_date})"
                        )

                        # Verify and enrich claim
                        enriched_data = await FlightDataService.verify_and_enrich_claim(
                            session=session,
                            claim=claim,
                            user_id=UUID(admin_user_id) if admin_user_id else None,
                            force_refresh=False  # Use cache if available
                        )

                        stats["total_processed"] += 1
                        stats["api_credits_used"] += enriched_data.get("api_credits_used", 0)

                        # Update claim with verified data
                        if enriched_data.get("verified"):
                            logger.info(
                                f"Claim {claim.id} verified: "
                                f"compensation={enriched_data.get('compensation_amount')} EUR, "
                                f"cached={enriched_data.get('cached')}"
                            )

                            # Update claim fields
                            if enriched_data.get("compensation_amount") is not None:
                                claim.calculated_compensation = enriched_data["compensation_amount"]

                            if enriched_data.get("distance_km") is not None:
                                claim.flight_distance_km = enriched_data["distance_km"]

                            if enriched_data.get("delay_hours") is not None:
                                claim.delay_hours = enriched_data["delay_hours"]

                            await session.commit()
                            stats["verified_count"] += 1

                        else:
                            logger.warning(
                                f"Claim {claim.id} not verified: "
                                f"source={enriched_data.get('verification_source')}"
                            )
                            stats["failed_count"] += 1

                    except Exception as e:
                        logger.error(
                            f"Failed to process claim {claim.id}: {str(e)}",
                            exc_info=True
                        )
                        stats["failed_count"] += 1
                        stats["errors"].append({
                            "claim_id": str(claim.id),
                            "error": str(e)
                        })
                        # Continue with next claim - don't fail entire batch
                        continue

                # Final commit for any pending changes
                await session.commit()

                logger.info(
                    f"Backfill complete: processed={stats['total_processed']}, "
                    f"verified={stats['verified_count']}, "
                    f"failed={stats['failed_count']}, "
                    f"credits_used={stats['api_credits_used']}"
                )

                return stats

            except Exception as e:
                logger.error(f"Backfill task failed: {str(e)}", exc_info=True)
                await session.rollback()
                raise

            finally:
                await engine.dispose()

    try:
        # Run the async backfill function
        result_stats = run_async(_backfill_claims())

        logger.info(f"Task completed: Backfill statistics: {result_stats}")

        return result_stats

    except Exception as exc:
        logger.error(f"Task error: {str(exc)}", exc_info=True)
        # Retry the task once after 5 minutes if it fails
        raise self.retry(exc=exc, countdown=300)
