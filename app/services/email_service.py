"""
Email service for sending notifications to customers.

This service uses aiosmtplib for async email sending and Jinja2 for HTML templates.
It follows the same pattern as CompensationService (static methods, no database access).
"""
import logging
import os
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Optional

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails using SMTP with HTML templates."""

    # Set up Jinja2 template environment (loads HTML templates)
    # Templates are in app/templates/emails/
    template_dir = Path(__file__).parent.parent / "templates" / "emails"
    jinja_env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml'])  # Security: auto-escape HTML
    )

    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML version of the email
            text_content: Plain text version (optional, falls back to stripped HTML)

        Returns:
            True if email sent successfully, False otherwise
        """
        # Check if notifications are enabled
        if not config.NOTIFICATIONS_ENABLED:
            logger.info(f"Notifications disabled. Would have sent email to {to_email}: {subject}")
            return True

        # Validate SMTP credentials are configured
        if not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
            logger.error("SMTP credentials not configured. Cannot send email.")
            return False

        try:
            # Create email message
            message = EmailMessage()
            message["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Set both HTML and plain text content
            # Email clients that don't support HTML will show the plain text version
            if text_content:
                message.set_content(text_content)  # Plain text version
            message.add_alternative(html_content, subtype='html')  # HTML version

            # Connect to SMTP server and send
            # aiosmtplib is the async version of smtplib
            # Gmail port 587 requires STARTTLS (not implicit TLS)
            await aiosmtplib.send(
                message,
                hostname=config.SMTP_HOST,
                port=config.SMTP_PORT,
                username=config.SMTP_USERNAME,
                password=config.SMTP_PASSWORD,
                start_tls=True,  # Use STARTTLS for port 587
                use_tls=False,   # Don't use implicit TLS
            )

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def render_template(template_name: str, context: Dict) -> str:
        """
        Render an HTML email template with given context.

        Args:
            template_name: Name of template file (e.g., 'claim_submitted.html')
            context: Dictionary of variables to pass to template

        Returns:
            Rendered HTML string
        """
        try:
            template = EmailService.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            raise

    @staticmethod
    async def send_claim_submitted_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        flight_number: str,
        airline: str,
        magic_link_token: Optional[str] = None
    ) -> bool:
        """
        Send confirmation email when a claim is submitted.

        Args:
            customer_email: Customer's email address
            customer_name: Customer's full name
            claim_id: UUID of the claim
            flight_number: Flight number (e.g., "LH123")
            airline: Airline name
            magic_link_token: Optional magic link token for passwordless access

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending claim submitted email to {customer_email}")

        try:
            # Prepare data for the template
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            magic_link_url = None
            if magic_link_token:
                magic_link_url = f"{frontend_url}/auth/magic-link?token={magic_link_token}&claim_id={claim_id}"

            context = {
                "customer_name": customer_name,
                "claim_id": claim_id,
                "flight_number": flight_number,
                "airline": airline,
                "magic_link_url": magic_link_url,
            }

            # Render HTML template
            html_content = EmailService.render_template("claim_submitted.html", context)

            # Plain text fallback
            text_content = f"""
Hello {customer_name},

Thank you for submitting your flight compensation claim!

Claim Details:
- Claim ID: {claim_id}
- Flight: {airline} {flight_number}

We have received your claim and will review it shortly. You will receive email updates as your claim progresses.

Best regards,
{config.SMTP_FROM_NAME}
            """.strip()

            # Send the email
            return await EmailService.send_email(
                to_email=customer_email,
                subject=f"Claim Submitted - {airline} {flight_number}",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error(f"Failed to send claim submitted email: {str(e)}")
            return False

    @staticmethod
    async def send_status_update_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        old_status: str,
        new_status: str,
        flight_number: str,
        airline: str,
        change_reason: Optional[str] = None,
        compensation_amount: Optional[float] = None
    ) -> bool:
        """
        Send email when claim status changes.

        Args:
            customer_email: Customer's email address
            customer_name: Customer's full name
            claim_id: UUID of the claim
            old_status: Previous status
            new_status: New status
            flight_number: Flight number
            airline: Airline name
            change_reason: Reason for status change (optional)
            compensation_amount: Compensation amount if approved (optional)

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending status update email to {customer_email}: {old_status} -> {new_status}")

        try:
            # Prepare data for the template
            context = {
                "customer_name": customer_name,
                "claim_id": claim_id,
                "old_status": old_status.replace("_", " ").title(),
                "new_status": new_status.replace("_", " ").title(),
                "flight_number": flight_number,
                "airline": airline,
                "change_reason": change_reason,
                "compensation_amount": compensation_amount,
                "is_approved": new_status == "approved",
                "is_rejected": new_status == "rejected",
                "is_paid": new_status == "paid",
            }

            # Render HTML template
            html_content = EmailService.render_template("status_updated.html", context)

            # Plain text fallback
            compensation_text = f"\nCompensation Amount: €{compensation_amount}" if compensation_amount else ""
            reason_text = f"\nReason: {change_reason}" if change_reason else ""

            text_content = f"""
Hello {customer_name},

Your claim status has been updated!

Claim Details:
- Claim ID: {claim_id}
- Flight: {airline} {flight_number}
- Status: {new_status.replace('_', ' ').title()}{compensation_text}{reason_text}

Best regards,
{config.SMTP_FROM_NAME}
            """.strip()

            # Send the email
            return await EmailService.send_email(
                to_email=customer_email,
                subject=f"Claim Status Update - {new_status.replace('_', ' ').title()}",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error(f"Failed to send status update email: {str(e)}")
            return False

    @staticmethod
    async def send_document_rejected_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        document_type: str,
        rejection_reason: str,
        flight_number: str,
        airline: str
    ) -> bool:
        """
        Send email when a document is rejected and needs to be re-uploaded.

        Args:
            customer_email: Customer's email address
            customer_name: Customer's full name
            claim_id: UUID of the claim
            document_type: Type of document rejected (e.g., "boarding_pass")
            rejection_reason: Why the document was rejected
            flight_number: Flight number
            airline: Airline name

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending document rejected email to {customer_email}")

        try:
            # Prepare data for the template
            context = {
                "customer_name": customer_name,
                "claim_id": claim_id,
                "document_type": document_type.replace("_", " ").title(),
                "rejection_reason": rejection_reason,
                "flight_number": flight_number,
                "airline": airline,
            }

            # Render HTML template
            html_content = EmailService.render_template("document_rejected.html", context)

            # Plain text fallback
            text_content = f"""
Hello {customer_name},

We need you to re-upload a document for your claim.

Claim Details:
- Claim ID: {claim_id}
- Flight: {airline} {flight_number}

Document Issue:
- Document Type: {document_type.replace('_', ' ').title()}
- Reason: {rejection_reason}

Please log in to your account and upload a new version of this document.

Best regards,
{config.SMTP_FROM_NAME}
            """.strip()

            # Send the email
            return await EmailService.send_email(
                to_email=customer_email,
                subject=f"Document Re-upload Required - {document_type.replace('_', ' ').title()}",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error(f"Failed to send document rejected email: {str(e)}")
            return False
