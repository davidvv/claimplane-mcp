"""
Celery tasks for account management notifications (Phase 4).

These tasks send emails for account changes like email updates,
password changes, and account deletion requests.
"""
import logging
import asyncio

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
    name="send_email_change_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_email_change_notification(
    self,
    old_email: str,
    new_email: str,
    user_name: str
):
    """
    Celery task: Send notification when email address is changed.

    Args:
        old_email: Previous email address
        new_email: New email address
        user_name: User's full name
    """
    try:
        logger.info(f"Sending email change notification to {old_email} and {new_email}")

        # Send to old email (security notification)
        run_async(
            EmailService.send_email(
                to_email=old_email,
                subject="Email Address Changed - ClaimPlane",
                html_content=f"""
                <h2>Email Address Changed</h2>
                <p>Hello {user_name},</p>
                <p>This is to notify you that the email address for your ClaimPlane account
                has been changed from <strong>{old_email}</strong> to <strong>{new_email}</strong>.</p>
                <p>If you did not make this change, please contact our support team immediately.</p>
                <p>All future communications will be sent to your new email address.</p>
                <p>For security reasons, you have been logged out of all devices and will need to
                log in again with your new email address.</p>
                <br>
                <p>Best regards,<br>The ClaimPlane Team</p>
                """
            )
        )

        # Send to new email (confirmation)
        run_async(
            EmailService.send_email(
                to_email=new_email,
                subject="Welcome to Your New Email - ClaimPlane",
                html_content=f"""
                <h2>Email Address Updated Successfully</h2>
                <p>Hello {user_name},</p>
                <p>Your ClaimPlane account email has been successfully updated to this address.</p>
                <p>You can now use <strong>{new_email}</strong> to log in to your account.</p>
                <p>For security reasons, you have been logged out of all devices. Please log in
                again with your new email address.</p>
                <br>
                <p>Best regards,<br>The ClaimPlane Team</p>
                """
            )
        )

        logger.info(f"Email change notification sent successfully")

    except Exception as exc:
        logger.error(f"Failed to send email change notification: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="send_password_change_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_password_change_notification(
    self,
    email: str,
    user_name: str
):
    """
    Celery task: Send notification when password is changed.

    Args:
        email: User's email address
        user_name: User's full name
    """
    try:
        logger.info(f"Sending password change notification to {email}")

        run_async(
            EmailService.send_email(
                to_email=email,
                subject="Password Changed - ClaimPlane",
                html_content=f"""
                <h2>Password Changed Successfully</h2>
                <p>Hello {user_name},</p>
                <p>This is to confirm that your ClaimPlane account password has been changed.</p>
                <p>If you did not make this change, please contact our support team immediately
                as your account may be compromised.</p>
                <p>For security reasons, you have been logged out of all devices and will need to
                log in again with your new password.</p>
                <br>
                <p><strong>Security Tip:</strong> Make sure to use a strong, unique password and
                never share it with anyone.</p>
                <br>
                <p>Best regards,<br>The ClaimPlane Team</p>
                """
            )
        )

        logger.info(f"Password change notification sent successfully")

    except Exception as exc:
        logger.error(f"Failed to send password change notification: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="send_account_deletion_request_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_account_deletion_request_notification(
    self,
    email: str,
    user_name: str,
    deletion_request_id: str
):
    """
    Celery task: Send confirmation when account deletion is requested.

    Args:
        email: User's email address
        user_name: User's full name
        deletion_request_id: ID of the deletion request
    """
    try:
        logger.info(f"Sending account deletion request confirmation to {email}")

        run_async(
            EmailService.send_email(
                to_email=email,
                subject="Account Deletion Request Received - ClaimPlane",
                html_content=f"""
                <h2>Account Deletion Request Received</h2>
                <p>Hello {user_name},</p>
                <p>We have received your request to delete your ClaimPlane account.</p>
                <p><strong>What happens next:</strong></p>
                <ul>
                    <li>Your account has been deactivated and you can no longer log in</li>
                    <li>Our team will review your request within 2-3 business days</li>
                    <li>If you have any open claims, we may contact you to resolve them first</li>
                    <li>Once approved, your personal data will be permanently deleted within 30 days</li>
                    <li>Some information may be retained for legal compliance (up to 7 years for financial records)</li>
                </ul>
                <p><strong>Changed your mind?</strong> Contact our support team at support@claimplane.com
                with your deletion request ID: <strong>{deletion_request_id}</strong></p>
                <p>We're sorry to see you go. If there's anything we could have done better,
                please let us know by replying to this email.</p>
                <br>
                <p>Best regards,<br>The ClaimPlane Team</p>
                """
            )
        )

        logger.info(f"Account deletion request confirmation sent successfully")

    except Exception as exc:
        logger.error(f"Failed to send account deletion request confirmation: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="send_account_deletion_admin_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_account_deletion_admin_notification(
    self,
    customer_email: str,
    customer_name: str,
    customer_id: str,
    reason: str,
    open_claims_count: int,
    total_claims_count: int,
    deletion_request_id: str
):
    """
    Celery task: Notify admins about account deletion request.

    Args:
        customer_email: Customer's email address
        customer_name: Customer's full name
        customer_id: Customer's ID
        reason: Deletion reason
        open_claims_count: Number of open claims
        total_claims_count: Total number of claims
        deletion_request_id: ID of the deletion request
    """
    try:
        logger.info(f"Sending account deletion admin notification for customer {customer_id}")

        # Send to admin email (from config)
        from app.config import config
        admin_email = config.ADMIN_EMAIL or "admin@claimplane.com"

        run_async(
            EmailService.send_email(
                to_email=admin_email,
                subject=f"[ACTION REQUIRED] Account Deletion Request - {customer_name}",
                html_content=f"""
                <h2>New Account Deletion Request</h2>
                <p>A customer has requested account deletion. Please review and process:</p>

                <h3>Customer Information</h3>
                <ul>
                    <li><strong>Name:</strong> {customer_name}</li>
                    <li><strong>Email:</strong> {customer_email}</li>
                    <li><strong>Customer ID:</strong> {customer_id}</li>
                    <li><strong>Request ID:</strong> {deletion_request_id}</li>
                </ul>

                <h3>Account Status</h3>
                <ul>
                    <li><strong>Open Claims:</strong> {open_claims_count}</li>
                    <li><strong>Total Claims:</strong> {total_claims_count}</li>
                    <li><strong>Account Status:</strong> Blacklisted (cannot log in)</li>
                </ul>

                <h3>Deletion Reason</h3>
                <p>{reason}</p>

                <h3>Action Required</h3>
                <ol>
                    <li>Review the deletion request in the admin panel</li>
                    <li>Check if there are any open claims that need resolution</li>
                    <li>If open claims exist, contact the customer to close them</li>
                    <li>Once cleared, approve the deletion request</li>
                    <li>Follow the GDPR data deletion workflow to remove all customer data</li>
                </ol>

                <p><strong>Important:</strong> The customer's account has been blacklisted and
                they can no longer log in. Please process this request within 2-3 business days.</p>

                <br>
                <p>ClaimPlane Admin System</p>
                """
            )
        )

        logger.info(f"Account deletion admin notification sent successfully")

    except Exception as exc:
        logger.error(f"Failed to send account deletion admin notification: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="send_account_deletion_approval_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_account_deletion_approval_notification(
    self,
    email: str,
    customer_name: str,
    notes: str
):
    """
    Celery task: Send notification when deletion request is approved.

    Args:
        email: Customer's email address
        customer_name: Customer's full name
        notes: Admin notes about the approval
    """
    try:
        logger.info(f"Sending deletion approval notification to {email}")

        run_async(
            EmailService.send_email(
                to_email=email,
                subject="Account Deletion Approved - ClaimPlane",
                html_content=f"""
                <h2>Account Deletion Request Approved</h2>
                <p>Hello {customer_name},</p>
                <p>Your account deletion request has been reviewed and approved.</p>
                <p><strong>What happens next:</strong></p>
                <ul>
                    <li>Your personal data will be permanently deleted within 30 days</li>
                    <li>Your account is currently deactivated and you cannot log in</li>
                    <li>Claim records will be anonymized but retained for legal compliance (7 years)</li>
                    <li>Uploaded files will be permanently deleted</li>
                    <li>This action is irreversible once completed</li>
                </ul>
                <p><strong>Admin Notes:</strong></p>
                <blockquote style="border-left: 4px solid #3b82f6; padding-left: 1em; margin: 1em 0;">
                    {notes}
                </blockquote>
                <p>If you have any questions, please contact our support team at support@claimplane.com.</p>
                <br>
                <p>Best regards,<br>The ClaimPlane Team</p>
                """
            )
        )

        logger.info("Deletion approval notification sent successfully")

    except Exception as exc:
        logger.error(f"Failed to send deletion approval notification: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="send_account_deletion_rejection_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_account_deletion_rejection_notification(
    self,
    email: str,
    customer_name: str,
    rejection_reason: str
):
    """
    Celery task: Send notification when deletion request is rejected.

    Args:
        email: Customer's email address
        customer_name: Customer's full name
        rejection_reason: Reason for rejection
    """
    try:
        logger.info(f"Sending deletion rejection notification to {email}")

        run_async(
            EmailService.send_email(
                to_email=email,
                subject="Account Deletion Request Update - ClaimPlane",
                html_content=f"""
                <h2>Account Deletion Request Update</h2>
                <p>Hello {customer_name},</p>
                <p>We have reviewed your account deletion request. Unfortunately, we cannot process your
                deletion at this time for the following reason:</p>
                <blockquote style="border-left: 4px solid #e74c3c; padding-left: 1em; margin: 1em 0; color: #e74c3c;">
                    {rejection_reason}
                </blockquote>
                <p><strong>Your account has been reactivated</strong> and you can now log in again using
                your email and password.</p>
                <p>If you still wish to delete your account after resolving the above issue, you can
                submit a new deletion request from your account settings.</p>
                <p>If you have any questions or need assistance, please contact our support team at
                support@claimplane.com.</p>
                <br>
                <p>Best regards,<br>The ClaimPlane Team</p>
                """
            )
        )

        logger.info("Deletion rejection notification sent successfully")

    except Exception as exc:
        logger.error(f"Failed to send deletion rejection notification: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="send_account_deletion_completed_admin_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_account_deletion_completed_admin_notification(
    self,
    admin_email: str,
    customer_email: str,
    deletion_summary: dict
):
    """
    Celery task: Notify admin when deletion is completed.

    Args:
        admin_email: Admin's email address
        customer_email: Customer's email address
        deletion_summary: Summary of deletion operation
    """
    try:
        logger.info(f"Sending deletion completion notification to admin {admin_email}")

        from app.config import config
        admin_email_target = config.ADMIN_EMAIL or admin_email

        run_async(
            EmailService.send_email(
                to_email=admin_email_target,
                subject=f"Account Deletion Completed - {customer_email}",
                html_content=f"""
                <h2>Account Deletion Completed</h2>
                <p>A customer account deletion has been processed:</p>
                <h3>Deletion Summary</h3>
                <ul>
                    <li><strong>Customer Email:</strong> {customer_email}</li>
                    <li><strong>Files Deleted:</strong> {deletion_summary.get('files_deleted', 0)}</li>
                    <li><strong>Files Failed:</strong> {deletion_summary.get('files_failed', 0)}</li>
                    <li><strong>Claims Anonymized:</strong> {deletion_summary.get('claims_anonymized', 0)}</li>
                    <li><strong>Started:</strong> {deletion_summary.get('deletion_started_at', 'N/A')}</li>
                    <li><strong>Completed:</strong> {deletion_summary.get('deletion_completed_at', 'N/A')}</li>
                </ul>
                {f'''
                <h3>Errors</h3>
                <ul>
                    {"".join(f"<li>{error}</li>" for error in deletion_summary.get('errors', []))}
                </ul>
                ''' if deletion_summary.get('errors') else ''}
                <p>The customer account has been permanently anonymized and can no longer be used.</p>
                <p>Claims have been retained for legal compliance (7 years) but all personal data has been removed.</p>
                <br>
                <p>ClaimPlane Admin System</p>
                """
            )
        )

        logger.info("Deletion completion admin notification sent successfully")

    except Exception as exc:
        logger.error(f"Failed to send deletion completion admin notification: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
