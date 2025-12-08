#!/usr/bin/env python3
"""
Send admin credentials via email using the app's email service.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.email_service import EmailService


async def send_credentials_email(email: str, password: str, first_name: str):
    """Send admin credentials via email."""

    subject = "EasyAirClaim - Your Superadmin Credentials"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2563eb;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                background-color: #f9fafb;
                padding: 30px;
                border: 1px solid #e5e7eb;
                border-radius: 0 0 5px 5px;
            }}
            .credentials {{
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #2563eb;
            }}
            .credential-item {{
                margin: 10px 0;
            }}
            .credential-label {{
                font-weight: bold;
                color: #6b7280;
            }}
            .credential-value {{
                font-family: monospace;
                background-color: #f3f4f6;
                padding: 5px 10px;
                border-radius: 3px;
                display: inline-block;
                margin-top: 5px;
            }}
            .warning {{
                background-color: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .button {{
                display: inline-block;
                background-color: #2563eb;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                color: #6b7280;
                font-size: 12px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 EasyAirClaim Superadmin Access</h1>
        </div>
        <div class="content">
            <p>Hello {first_name},</p>

            <p>Your superadmin account for EasyAirClaim has been created successfully. Below are your login credentials:</p>

            <div class="credentials">
                <div class="credential-item">
                    <div class="credential-label">Email:</div>
                    <div class="credential-value">{email}</div>
                </div>
                <div class="credential-item">
                    <div class="credential-label">Password:</div>
                    <div class="credential-value">{password}</div>
                </div>
                <div class="credential-item">
                    <div class="credential-label">Role:</div>
                    <div class="credential-value">Superadmin</div>
                </div>
            </div>

            <div class="warning">
                <strong>⚠️ Security Notice:</strong>
                <ul style="margin: 10px 0;">
                    <li>This is a testing environment, but please keep these credentials secure</li>
                    <li>Change your password after first login</li>
                    <li>Never share these credentials with anyone</li>
                    <li>Delete this email after saving your credentials securely</li>
                </ul>
            </div>

            <p style="text-align: center;">
                <a href="https://eac.dvvcloud.work/auth" class="button">Login to EasyAirClaim</a>
            </p>

            <p><strong>Your Superadmin Capabilities:</strong></p>
            <ul>
                <li>Full access to admin dashboard</li>
                <li>Manage all claims and customer data</li>
                <li>Review and approve documents</li>
                <li>Promote other users to admin roles</li>
                <li>Access system analytics and reports</li>
            </ul>

            <p>If you have any questions or need assistance, please don't hesitate to reach out.</p>

            <p>Best regards,<br>
            <strong>EasyAirClaim System</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email from EasyAirClaim Testing Environment</p>
            <p>Cloudflare Tunnel: https://eac.dvvcloud.work</p>
        </div>
    </body>
    </html>
    """

    # Plain text version
    text_body = f"""
EasyAirClaim - Your Superadmin Credentials

Hello {first_name},

Your superadmin account for EasyAirClaim has been created successfully.

Login Credentials:
------------------
Email: {email}
Password: {password}
Role: Superadmin

Login URL: https://eac.dvvcloud.work/auth

SECURITY NOTICE:
- This is a testing environment, but please keep these credentials secure
- Change your password after first login
- Never share these credentials with anyone
- Delete this email after saving your credentials securely

Your Superadmin Capabilities:
- Full access to admin dashboard
- Manage all claims and customer data
- Review and approve documents
- Promote other users to admin roles
- Access system analytics and reports

Best regards,
EasyAirClaim System

---
This is an automated email from EasyAirClaim Testing Environment
Cloudflare Tunnel: https://eac.dvvcloud.work
    """

    try:
        success = await EmailService.send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

        if success:
            print(f"✅ Email sent successfully to {email}")
            print(f"\nCredentials have been sent via email.")
            print(f"\n📧 Please check your inbox at: {email}")
            print(f"\nNote: The email may take a few moments to arrive.")
            print(f"      Check your spam folder if you don't see it in your inbox.")
        else:
            print(f"❌ Failed to send email to {email}")
            print(f"\nFalling back to console output:")
            print(f"\n{'='*60}")
            print(f"SUPERADMIN CREDENTIALS")
            print(f"{'='*60}")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Login URL: https://eac.dvvcloud.work/auth")
            print(f"{'='*60}")

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print(f"\nFalling back to console output:")
        print(f"\n{'='*60}")
        print(f"SUPERADMIN CREDENTIALS")
        print(f"{'='*60}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Login URL: https://eac.dvvcloud.work/auth")
        print(f"{'='*60}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Send admin credentials via email")
    parser.add_argument('--email', required=True, help='Admin email address')
    parser.add_argument('--password', required=True, help='Admin password')
    parser.add_argument('--first-name', required=True, help='First name')

    args = parser.parse_args()

    await send_credentials_email(args.email, args.password, args.first_name)


if __name__ == "__main__":
    asyncio.run(main())
