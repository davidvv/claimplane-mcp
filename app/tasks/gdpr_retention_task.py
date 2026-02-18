"""
Celery task for GDPR 7-year data retention automation (Work Package 359).
This task ensures compliance with GDPR Article 5.1.e (Storage Limitation).
"""
import logging
from datetime import datetime, timezone
from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.services.gdpr_service import GDPRService
from app.services.email_service import EmailService
from app.config import config
from app.tasks.draft_tasks import run_async

logger = logging.getLogger(__name__)

async def _run_retention_purge():
    """
    Identify and anonymize claims older than 7 years.
    Logic:
    1. Identify claims with updated_at < (now - 7 years)
    2. Ensure status is 'paid', 'rejected', 'withdrawn', 'closed', or 'abandoned'
    3. Skip claims marked with is_retention_locked or is_legal_proceeding
    4. Anonymize each claim surgicaly using GDPRService
    """
    from app.models import Claim
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Identify expired claims (7 years retention)
            expired_claims = await GDPRService.get_expired_claims(session, years=7)
            
            if not expired_claims:
                logger.info("GDPR Retention: No claims found eligible for 7-year purge.")
                return {"processed": 0, "errors": 0}

            logger.info(f"GDPR Retention: Found {len(expired_claims)} claims eligible for 7-year purge.")
            
            # Notify admin about the batch start
            if config.ADMIN_EMAIL:
                await EmailService.send_admin_alert(
                    config.ADMIN_EMAIL,
                    "GDPR Retention Purge Started",
                    f"Starting automated anonymization of {len(expired_claims)} claims older than 7 years."
                )

            processed_count = 0
            error_count = 0
            
            for claim in expired_claims:
                try:
                    # Surgeon-like anonymization of specific claim
                    await GDPRService.anonymize_specific_claim(
                        session, 
                        claim.id, 
                        reason="Automated 7-year retention policy compliance"
                    )
                    processed_count += 1
                    logger.info(f"GDPR Retention: Successfully anonymized claim {claim.id}")
                except Exception as e:
                    logger.error(f"GDPR Retention: Failed to anonymize claim {claim.id}: {str(e)}")
                    error_count += 1

            # Commit all changes at once for this batch
            await session.commit()
            
            # Final report for logs and admin
            summary_msg = (
                f"GDPR 7-year retention purge completed.\n"
                f"Total eligible: {len(expired_claims)}\n"
                f"Successfully anonymized: {processed_count}\n"
                f"Errors encountered: {error_count}"
            )
            logger.info(summary_msg)
            
            if config.ADMIN_EMAIL:
                await EmailService.send_admin_alert(
                    config.ADMIN_EMAIL,
                    "GDPR Retention Purge Report",
                    summary_msg
                )
                
            return {"total_eligible": len(expired_claims), "processed": processed_count, "errors": error_count}

        except Exception as e:
            logger.error(f"GDPR Retention: Fatal error during purge process: {str(e)}")
            if config.ADMIN_EMAIL:
                await EmailService.send_admin_alert(
                    config.ADMIN_EMAIL,
                    "GDPR Retention Purge FAILED",
                    f"Critical error during retention purge: {str(e)}"
                )
            raise


@celery_app.task(
    name="run_retention_purge",
    bind=True,
    max_retries=1,
    default_retry_delay=3600
)
def run_retention_purge(self):
    """
    Monthly task for GDPR data retention compliance (Article 5.1.e).
    Scheduled via Celery Beat in celery_app.py.
    """
    logger.info("Starting scheduled GDPR retention purge task")
    try:
        # We use run_async helper to execute the async logic in synchronous Celery worker
        result = run_async(_run_retention_purge())
        return result
    except Exception as e:
        logger.error(f"Retention purge task failed with retry: {str(e)}")
        raise self.retry(exc=e)
