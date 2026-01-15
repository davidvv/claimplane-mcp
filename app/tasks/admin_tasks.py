"""
Celery tasks for administrative alerts and maintenance.
"""
import logging
import asyncio
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
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
        asyncio.set_event_loop(None)

@celery_app.task(name="send_admin_alert_email")
def send_admin_alert_email(subject: str, message: str, recipient_email: str = None):
    """
    Send an alert email to the admin.
    """
    # Use configured SMTP_FROM_EMAIL as default recipient if not provided, 
    # or hardcode the admin email if known/preferred.
    # For now, we'll assume the admin email is the same as the sender or configured separately.
    # Since recipient_email is required by EmailService, we need a target.
    # I'll default to the one from .env if possible, or expect it passed.
    
    # Check config for admin email, or use a default
    from app.config import config
    target_email = recipient_email or config.SMTP_FROM_EMAIL 
    
    logger.info(f"Sending admin alert to {target_email}: {subject}")
    
    try:
        # We need a method in EmailService for generic alerts or reuse an existing one.
        # Since EmailService methods are specific, I'll add a generic one or use a template.
        # For simplicity in this task, I'll assume we can add a method to EmailService
        # OR I'll reuse the internal sending logic if accessible.
        
        # Let's verify EmailService capabilities first.
        # If no generic method, I'll add one to EmailService as well.
        success = run_async(
            EmailService.send_admin_alert(
                recipient_email=target_email,
                subject=subject,
                message=message
            )
        )
        return success
    except Exception as e:
        logger.error(f"Failed to send admin alert: {e}")
        return False
