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
    async def send_magic_link_login_email(
        customer_email: str,
        customer_name: str,
        magic_link_token: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Send magic link email for passwordless login.

        Args:
            customer_email: Customer's email address
            customer_name: Customer's full name
            magic_link_token: Magic link token for authentication
            ip_address: IP address where the request originated

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending magic link login email to {customer_email}")

        try:
            # Prepare data for the template
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            magic_link_url = f"{frontend_url}/auth/magic-link?token={magic_link_token}"

            from datetime import datetime
            context = {
                "customer_name": customer_name,
                "magic_link_url": magic_link_url,
                "ip_address": ip_address or "Unknown",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            }

            # Render HTML template
            html_content = EmailService.render_template("magic_link_login.html", context)

            # Plain text fallback
            text_content = f"""
Hello {customer_name},

You requested a magic link to access your account.

Click this link to securely log in:
{magic_link_url}

This link is valid for 48 hours and can only be used once.

Security Information:
- IP Address: {ip_address or "Unknown"}
- Time: {context['timestamp']}

If you didn't request this, you can safely ignore this email.

Best regards,
{config.SMTP_FROM_NAME}
            """.strip()

            # Send the email
            return await EmailService.send_email(
                to_email=customer_email,
                subject="Your Secure Login Link",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error(f"Failed to send magic link login email: {str(e)}")
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

    # =========================================================================
    # Draft Reminder Emails (Phase 7 - Workflow v2)
    # =========================================================================

    @staticmethod
    async def send_draft_reminder_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        flight_number: str,
        airline: str,
        magic_link_token: str,
        reminder_number: int
    ) -> bool:
        """
        Send reminder email for abandoned draft claims.

        Args:
            customer_email: Customer's email address
            customer_name: Customer's first name or "there"
            claim_id: UUID of the draft claim
            flight_number: Flight number
            airline: Airline name
            magic_link_token: Token to resume the claim
            reminder_number: Which reminder this is (1=30min, 2=day5, 3=day8)

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending draft reminder #{reminder_number} to {customer_email}")

        try:
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            resume_url = f"{frontend_url}/auth/magic-link?token={magic_link_token}&claim_id={claim_id}&resume=true"

            # Different messaging based on reminder number
            if reminder_number == 1:
                subject = f"Continue Your Claim - {airline} {flight_number}"
                headline = "Don't forget to complete your claim!"
                message = "You started a compensation claim but didn't finish. Your potential compensation is just a few steps away."
                urgency = ""
            elif reminder_number == 2:
                subject = f"Your Claim is Waiting - {airline} {flight_number}"
                headline = "Your claim is still waiting for you"
                message = "It's been a few days since you started your compensation claim. We're keeping your progress saved."
                urgency = "Complete it soon to get the compensation you deserve."
            else:  # reminder_number == 3
                subject = f"Last Chance - Complete Your Claim for {airline} {flight_number}"
                headline = "Your claim will expire soon"
                message = "This is your final reminder. Your draft claim will be deleted in a few days if not completed."
                urgency = "Act now to claim your compensation!"

            context = {
                "customer_name": customer_name,
                "claim_id": claim_id,
                "flight_number": flight_number,
                "airline": airline,
                "resume_url": resume_url,
                "headline": headline,
                "message": message,
                "urgency": urgency,
                "reminder_number": reminder_number,
            }

            # Try to render template, fall back to plain text if template doesn't exist
            try:
                html_content = EmailService.render_template("draft_reminder.html", context)
            except Exception:
                # Fallback HTML
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">{headline}</h2>
                    <p>Hello {customer_name},</p>
                    <p>{message}</p>
                    <p><strong>Flight:</strong> {airline} {flight_number}</p>
                    {"<p style='color: #dc2626; font-weight: bold;'>" + urgency + "</p>" if urgency else ""}
                    <p style="margin: 30px 0;">
                        <a href="{resume_url}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                            Complete My Claim
                        </a>
                    </p>
                    <p style="color: #666; font-size: 12px;">
                        If the button doesn't work, copy this link: {resume_url}
                    </p>
                </body>
                </html>
                """

            text_content = f"""
Hello {customer_name},

{headline}

{message}

Flight: {airline} {flight_number}
{urgency}

Click this link to continue your claim:
{resume_url}

Best regards,
{config.SMTP_FROM_NAME}
            """.strip()

            return await EmailService.send_email(
                to_email=customer_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error(f"Failed to send draft reminder email: {str(e)}")
            return False

    @staticmethod
    async def send_draft_expired_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        flight_number: str,
        can_still_submit: bool = True
    ) -> bool:
        """
        Send email when a draft claim has expired/been deleted.

        Args:
            customer_email: Customer's email address
            customer_name: Customer's first name or "there"
            claim_id: UUID of the expired claim
            flight_number: Flight number
            can_still_submit: Whether customer can start a new claim

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending draft expired email to {customer_email}")

        try:
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            new_claim_url = f"{frontend_url}/claim/new"

            context = {
                "customer_name": customer_name,
                "claim_id": claim_id,
                "flight_number": flight_number,
                "can_still_submit": can_still_submit,
                "new_claim_url": new_claim_url,
            }

            # Fallback HTML (no template needed for this simple email)
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #666;">Your Draft Claim Has Expired</h2>
                <p>Hello {customer_name},</p>
                <p>Your draft claim for flight {flight_number} has expired and been removed from our system.</p>
                <p>We respect your privacy and have deleted all data associated with this incomplete claim.</p>
                {"<p>If you still want to claim compensation, you can start a new claim anytime:</p><p><a href='" + new_claim_url + "' style='background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;'>Start New Claim</a></p>" if can_still_submit else ""}
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    This is an automated message. We won't contact you again about this claim.
                </p>
            </body>
            </html>
            """

            text_content = f"""
Hello {customer_name},

Your draft claim for flight {flight_number} has expired and been removed from our system.

We respect your privacy and have deleted all data associated with this incomplete claim.

{"You can start a new claim anytime at: " + new_claim_url if can_still_submit else ""}

This is an automated message. We won't contact you again about this claim.

Best regards,
{config.SMTP_FROM_NAME}
            """.strip()

            return await EmailService.send_email(
                to_email=customer_email,
                subject=f"Draft Claim Expired - {flight_number}",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error(f"Failed to send draft expired email: {str(e)}")
            return False

    @staticmethod
    async def send_final_reminder_email(
        customer_email: str,
        customer_name: str,
        claim_id: str,
        flight_number: str
    ) -> bool:
        """
        Send final reminder to multi-claim users (45 days after draft creation).

        This is the last email we send, letting them know we won't bother them anymore.

        Args:
            customer_email: Customer's email address
            customer_name: Customer's first name or "there"
            claim_id: UUID of the draft claim
            flight_number: Flight number

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending final reminder email to {customer_email}")

        try:
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            new_claim_url = f"{frontend_url}/claim/new"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #666;">Final Reminder</h2>
                <p>Hello {customer_name},</p>
                <p>We noticed you started a claim for flight {flight_number} but never completed it.</p>
                <p>This is our final reminder - we won't send any more emails about this claim.</p>
                <p>If you'd still like to claim compensation for your disrupted flight, you can start fresh anytime:</p>
                <p style="margin: 20px 0;">
                    <a href="{new_claim_url}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                        Start New Claim
                    </a>
                </p>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Thank you for considering our service. We wish you smooth travels!
                </p>
            </body>
            </html>
            """

            text_content = f"""
Hello {customer_name},

We noticed you started a claim for flight {flight_number} but never completed it.

This is our final reminder - we won't send any more emails about this claim.

If you'd still like to claim compensation, you can start fresh anytime:
{new_claim_url}

Thank you for considering our service. We wish you smooth travels!

Best regards,
{config.SMTP_FROM_NAME}
            """.strip()

            return await EmailService.send_email(
                to_email=customer_email,
                subject=f"Final Reminder - Flight Compensation Claim",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error(f"Failed to send final reminder email: {str(e)}")
            return False

    @staticmethod
    async def send_admin_alert(
        recipient_email: str,
        subject: str,
        message: str
    ) -> bool:
        """
        Send a generic alert email to an administrator.

        Args:
            recipient_email: Admin's email address
            subject: Alert subject
            message: Alert message body (plain text or simple HTML)

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending admin alert to {recipient_email}: {subject}")

        try:
            # Simple HTML wrapper
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #d32f2f;">System Alert</h2>
                <p><strong>Subject:</strong> {subject}</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #d32f2f; margin: 20px 0;">
                    {message.replace(chr(10), '<br>')}
                </div>
                <p style="color: #666; font-size: 12px;">
                    EasyAirClaim System Notification
                </p>
            </body>
            </html>
            """

            return await EmailService.send_email(
                to_email=recipient_email,
                subject=f"[Admin Alert] {subject}",
                html_content=html_content,
                text_content=message
            )

        except Exception as e:
            logger.error(f"Failed to send admin alert: {str(e)}")
            return False
