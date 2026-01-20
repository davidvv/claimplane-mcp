"""
Celery tasks for draft claim management and abandoned cart recovery.

These tasks run on a schedule (Celery Beat) to:
1. Send reminders to users who abandoned their claims
2. Clean up expired draft claims
3. Track analytics events
"""
import logging
import asyncio
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.services.email_service import EmailService
from app.database import AsyncSessionLocal

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


async def _send_draft_reminder_30min():
    """Find drafts inactive for 30 min and send first reminder."""
    from app.repositories import ClaimRepository, CustomerRepository, ClaimEventRepository
    from app.models import ClaimEvent
    from app.services.auth_service import AuthService
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    import os

    from app.config import config

    # Create a fresh engine and session factory for this event loop
    DATABASE_URL = config.DATABASE_URL
    engine = create_async_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    session = SessionLocal()
    try:
        claim_repo = ClaimRepository(session)
        customer_repo = CustomerRepository(session)
        event_repo = ClaimEventRepository(session)

        # Get drafts inactive for 30+ minutes with no reminders sent
        stale_drafts = await claim_repo.get_stale_drafts(
            minutes_inactive=30,
            max_reminders=0
        )

        sent_count = 0
        for claim in stale_drafts:
            try:
                customer = await customer_repo.get_by_id(claim.customer_id)
                if not customer:
                    continue

                # Create magic link for resuming
                magic_token, _ = await AuthService.create_magic_link_token(
                    session=session,
                    user_id=customer.id,
                    claim_id=claim.id,
                    ip_address=None,
                    user_agent="DraftReminderTask"
                )

                # Send reminder email
                await EmailService.send_draft_reminder_email(
                    customer_email=customer.email,
                    customer_name=customer.first_name or "there",
                    claim_id=str(claim.id),
                    flight_number=claim.flight_number,
                    airline=claim.airline,
                    magic_link_token=magic_token,
                    reminder_number=1
                )

                # Increment reminder count
                await claim_repo.increment_reminder_count(claim.id)

                # Log analytics event
                await event_repo.log_event(
                    event_type=ClaimEvent.EVENT_REMINDER_SENT,
                    claim_id=claim.id,
                    customer_id=customer.id,
                    event_data={"reminder_number": 1, "trigger": "30_min_inactive"}
                )

                sent_count += 1
                logger.info(f"Sent 30-min reminder for draft {claim.id} to {customer.email}")

            except Exception as e:
                logger.error(f"Failed to send 30-min reminder for draft {claim.id}: {e}")

        await session.commit()
        return sent_count
    finally:
        await session.close()
        await engine.dispose()


async def _send_draft_reminder_day(days: int, reminder_number: int):
    """Send reminder for drafts that are N days old."""
    from app.repositories import ClaimRepository, CustomerRepository, ClaimEventRepository
    from app.models import ClaimEvent
    from app.services.auth_service import AuthService
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    import os

    from app.config import config

    # Create a fresh engine and session factory for this event loop
    DATABASE_URL = config.DATABASE_URL
    engine = create_async_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    session = SessionLocal()
    try:
        claim_repo = ClaimRepository(session)
        customer_repo = CustomerRepository(session)
        event_repo = ClaimEventRepository(session)

        # Get drafts that are N days old with correct reminder count
        drafts = await claim_repo.get_drafts_for_reminder(
            days_old=days,
            reminder_count=reminder_number - 1  # Has received (reminder_number - 1) reminders
        )

        sent_count = 0
        for claim in drafts:
            try:
                customer = await customer_repo.get_by_id(claim.customer_id)
                if not customer:
                    continue

                # Create magic link for resuming
                magic_token, _ = await AuthService.create_magic_link_token(
                    session=session,
                    user_id=customer.id,
                    claim_id=claim.id,
                    ip_address=None,
                    user_agent=f"DraftReminderTask_Day{days}"
                )

                # Send reminder email
                await EmailService.send_draft_reminder_email(
                    customer_email=customer.email,
                    customer_name=customer.first_name or "there",
                    claim_id=str(claim.id),
                    flight_number=claim.flight_number,
                    airline=claim.airline,
                    magic_link_token=magic_token,
                    reminder_number=reminder_number
                )

                # Increment reminder count
                await claim_repo.increment_reminder_count(claim.id)

                # Log analytics event
                await event_repo.log_event(
                    event_type=ClaimEvent.EVENT_REMINDER_SENT,
                    claim_id=claim.id,
                    customer_id=customer.id,
                    event_data={"reminder_number": reminder_number, "trigger": f"day_{days}"}
                )

                sent_count += 1
                logger.info(f"Sent day-{days} reminder for draft {claim.id} to {customer.email}")

            except Exception as e:
                logger.error(f"Failed to send day-{days} reminder for draft {claim.id}: {e}")

        await session.commit()
        return sent_count
    finally:
        await session.close()
        await engine.dispose()


async def _cleanup_expired_drafts():
    """Delete drafts older than configured retention (default 11 days)."""
    from app.repositories import ClaimRepository, CustomerRepository, ClaimEventRepository, FileRepository
    from app.models import ClaimEvent, Claim
    from app.services.nextcloud_service import nextcloud_service
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    import os

    from app.config import config

    # Create a fresh engine and session factory for this event loop
    DATABASE_URL = config.DATABASE_URL
    engine = create_async_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    session = SessionLocal()
    try:
        claim_repo = ClaimRepository(session)
        customer_repo = CustomerRepository(session)
        event_repo = ClaimEventRepository(session)
        file_repo = FileRepository(session)

        # Get drafts older than configured retention period
        retention_days = config.DRAFT_RETENTION_DAYS
        expired_drafts = await claim_repo.get_expired_drafts(days_old=retention_days)

        deleted_count = 0
        notified_count = 0

        for claim in expired_drafts:
            try:
                customer = await customer_repo.get_by_id(claim.customer_id)
                if not customer:
                    continue

                # Check if customer has other claims
                all_claims = await claim_repo.get_by_customer_id(customer.id)
                other_claims = [c for c in all_claims if c.id != claim.id and c.status != Claim.STATUS_DRAFT]
                has_other_claims = len(other_claims) > 0

                # Check if customer has accepted terms (has submitted claims before)
                has_accepted_terms = customer.is_email_verified or len(other_claims) > 0

                if has_other_claims or has_accepted_terms:
                    # Don't delete customer - just mark claim as abandoned and notify
                    claim.status = "abandoned"  # Custom status for abandoned drafts
                    
                    # Delete files from Nextcloud to reclaim storage
                    claim_files = await file_repo.get_by_claim_id(claim.id)
                    for file in claim_files:
                        try:
                            if file.storage_path:
                                await nextcloud_service.delete_file(file.storage_path)
                        except Exception as file_err:
                            logger.error(f"Failed to delete Nextcloud file {file.id} for abandoned draft {claim.id}: {file_err}")

                    await event_repo.log_event(
                        event_type=ClaimEvent.EVENT_CLAIM_ABANDONED,
                        claim_id=claim.id,
                        customer_id=customer.id,
                        event_data={"has_other_claims": has_other_claims, "action": "marked_abandoned", "files_deleted": len(claim_files)}
                    )

                    # Send notification that we won't bother them anymore
                    await EmailService.send_draft_expired_email(
                        customer_email=customer.email,
                        customer_name=customer.first_name or "there",
                        claim_id=str(claim.id),
                        flight_number=claim.flight_number,
                        can_still_submit=True  # They can start a new claim anytime
                    )
                    notified_count += 1
                    logger.info(f"Marked draft {claim.id} as abandoned (customer has other claims)")

                else:
                    # New account, never accepted terms - safe to delete completely
                    # Log event before deletion
                    await event_repo.log_event(
                        event_type=ClaimEvent.EVENT_CLAIM_DELETED,
                        claim_id=claim.id,
                        customer_id=customer.id,
                        event_data={"reason": "expired_draft", "days_old": retention_days}
                    )

                    # Send goodbye email
                    await EmailService.send_draft_expired_email(
                        customer_email=customer.email,
                        customer_name=customer.first_name or "there",
                        claim_id=str(claim.id),
                        flight_number=claim.flight_number,
                        can_still_submit=True
                    )

                    # Delete files from Nextcloud before deleting claim
                    claim_files = await file_repo.get_by_claim_id(claim.id)
                    files_deleted = 0
                    for file in claim_files:
                        try:
                            if file.storage_path:
                                await nextcloud_service.delete_file(file.storage_path)
                                files_deleted += 1
                        except Exception as file_err:
                            logger.error(f"Failed to delete Nextcloud file {file.id} for draft {claim.id}: {file_err}")

                    if files_deleted > 0:
                        logger.info(f"Deleted {files_deleted} files from Nextcloud for draft {claim.id}")

                    # Delete claim
                    await claim_repo.delete(claim)

                    # Delete customer (if they have no other data)
                    await customer_repo.delete(customer)

                    deleted_count += 1
                    logger.info(f"Deleted expired draft {claim.id} and customer {customer.id}")

            except Exception as e:
                logger.error(f"Failed to process expired draft {claim.id}: {e}")

        await session.commit()
        return {"deleted": deleted_count, "notified": notified_count}
    finally:
        await session.close()
        await engine.dispose()


async def _send_final_reminder():
    """Send final reminder to multi-claim users 45 days after draft creation."""
    from app.repositories import ClaimRepository, CustomerRepository, ClaimEventRepository
    from app.models import ClaimEvent
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    import os

    from app.config import config

    # Create a fresh engine and session factory for this event loop
    DATABASE_URL = config.DATABASE_URL
    engine = create_async_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    session = SessionLocal()
    try:
        claim_repo = ClaimRepository(session)
        customer_repo = CustomerRepository(session)
        event_repo = ClaimEventRepository(session)

        # Get abandoned claims that are 45 days old with reminder_count = 4
        # (meaning they got the day-11 notification but not the final one)
        drafts = await claim_repo.get_drafts_for_reminder(
            days_old=45,
            reminder_count=4
        )

        sent_count = 0
        for claim in drafts:
            try:
                customer = await customer_repo.get_by_id(claim.customer_id)
                if not customer:
                    continue

                # Send final reminder email
                await EmailService.send_final_reminder_email(
                    customer_email=customer.email,
                    customer_name=customer.first_name or "there",
                    claim_id=str(claim.id),
                    flight_number=claim.flight_number
                )

                # Increment reminder count to mark as done
                await claim_repo.increment_reminder_count(claim.id)

                # Log analytics event
                await event_repo.log_event(
                    event_type=ClaimEvent.EVENT_REMINDER_SENT,
                    claim_id=claim.id,
                    customer_id=customer.id,
                    event_data={"reminder_number": 5, "trigger": "final_reminder_45_days"}
                )

                sent_count += 1
                logger.info(f"Sent final reminder for draft {claim.id} to {customer.email}")

            except Exception as e:
                logger.error(f"Failed to send final reminder for draft {claim.id}: {e}")

        await session.commit()
        return sent_count
    finally:
        await session.close()
        await engine.dispose()


# ============================================================================
# Celery Tasks
# ============================================================================


@celery_app.task(
    name="send_draft_reminder_30min",
    bind=True,
    max_retries=2,
    default_retry_delay=300
)
def send_draft_reminder_30min(self):
    """Task: Send reminders to drafts inactive for 30 minutes."""
    logger.info("Starting 30-min draft reminder task")
    try:
        count = run_async(_send_draft_reminder_30min())
        logger.info(f"30-min reminder task completed: sent {count} reminders")
        return {"sent": count}
    except Exception as e:
        logger.error(f"30-min reminder task failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    name="send_draft_reminder_day5",
    bind=True,
    max_retries=2,
    default_retry_delay=3600
)
def send_draft_reminder_day5(self):
    """Task: Send reminders to drafts 5 days old."""
    logger.info("Starting day-5 draft reminder task")
    try:
        count = run_async(_send_draft_reminder_day(days=5, reminder_number=2))
        logger.info(f"Day-5 reminder task completed: sent {count} reminders")
        return {"sent": count}
    except Exception as e:
        logger.error(f"Day-5 reminder task failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    name="send_draft_reminder_day8",
    bind=True,
    max_retries=2,
    default_retry_delay=3600
)
def send_draft_reminder_day8(self):
    """Task: Send reminders to drafts 8 days old."""
    logger.info("Starting day-8 draft reminder task")
    try:
        count = run_async(_send_draft_reminder_day(days=8, reminder_number=3))
        logger.info(f"Day-8 reminder task completed: sent {count} reminders")
        return {"sent": count}
    except Exception as e:
        logger.error(f"Day-8 reminder task failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    name="cleanup_expired_drafts",
    bind=True,
    max_retries=2,
    default_retry_delay=3600
)
def cleanup_expired_drafts(self):
    """Task: Clean up drafts older than 11 days."""
    logger.info("Starting expired drafts cleanup task")
    try:
        result = run_async(_cleanup_expired_drafts())
        logger.info(f"Cleanup task completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    name="send_final_reminder",
    bind=True,
    max_retries=2,
    default_retry_delay=3600
)
def send_final_reminder(self):
    """Task: Send final reminder to multi-claim users (45 days)."""
    logger.info("Starting final reminder task")
    try:
        count = run_async(_send_final_reminder())
        logger.info(f"Final reminder task completed: sent {count} reminders")
        return {"sent": count}
    except Exception as e:
        logger.error(f"Final reminder task failed: {e}")
        raise self.retry(exc=e)
