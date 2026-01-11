"""Quota tracking service for AeroDataBox API usage monitoring.

This service provides:
- Track every API call (credits used, endpoint, response time)
- Update quota status in database
- Send multi-tier alerts (80%, 90%, 95%)
- Emergency brake at 95% usage
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.models import APIUsageTracking, APIQuotaStatus, Customer
from app.services.email_service import EmailService
from app.exceptions import AeroDataBoxQuotaExceededError

logger = logging.getLogger(__name__)


class QuotaTrackingService:
    """Service for tracking and monitoring AeroDataBox API quota usage."""

    API_PROVIDER = "aerodatabox"

    @classmethod
    async def track_api_call(
        cls,
        session: AsyncSession,
        endpoint: str,
        tier_level: str,
        credits_used: int,
        http_status: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        triggered_by_user_id: Optional[UUID] = None,
        claim_id: Optional[UUID] = None
    ) -> APIUsageTracking:
        """
        Track an API call in the database.

        Args:
            session: Database session
            endpoint: API endpoint called (e.g., "/flights/number/BA123/2024-01-15")
            tier_level: API tier (e.g., "TIER_2")
            credits_used: Number of credits consumed (e.g., 2 for TIER_2)
            http_status: HTTP status code
            response_time_ms: Response time in milliseconds
            error_message: Error message if call failed
            triggered_by_user_id: User who triggered the call
            claim_id: Associated claim ID

        Returns:
            Created APIUsageTracking record
        """
        # Create tracking record
        tracking = APIUsageTracking(
            api_provider=cls.API_PROVIDER,
            endpoint=endpoint,
            tier_level=tier_level,
            credits_used=credits_used,
            http_status=http_status,
            response_time_ms=response_time_ms,
            error_message=error_message,
            triggered_by_user_id=triggered_by_user_id,
            claim_id=claim_id
        )

        session.add(tracking)
        await session.flush()  # Get ID without committing

        logger.info(
            f"Tracked API call: {endpoint} ({tier_level}, {credits_used} credits, "
            f"status={http_status}, time={response_time_ms}ms)"
        )

        # Update quota status
        await cls._update_quota_status(session, credits_used)

        return tracking

    @classmethod
    async def _update_quota_status(cls, session: AsyncSession, credits_used: int):
        """
        Update quota status and check for alerts.

        Args:
            session: Database session
            credits_used: Credits consumed by this API call
        """
        # Get or create quota status for current billing period
        quota_status = await cls.get_or_create_quota_status(session)

        # Increment credits used
        quota_status.credits_used += credits_used
        quota_status.last_updated = datetime.now(timezone.utc)

        # Check if quota exceeded (emergency brake at 95%)
        if quota_status.usage_percentage >= 95:
            quota_status.is_quota_exceeded = True
            logger.critical(
                f"API quota EXCEEDED: {quota_status.credits_used}/{quota_status.total_credits_allowed} "
                f"({quota_status.usage_percentage}%)"
            )

        await session.flush()

        # Check and send alerts
        await cls._check_and_send_alerts(session, quota_status)

        logger.info(
            f"Updated quota: {quota_status.credits_used}/{quota_status.total_credits_allowed} "
            f"({quota_status.usage_percentage}%)"
        )

    @classmethod
    async def get_or_create_quota_status(cls, session: AsyncSession) -> APIQuotaStatus:
        """
        Get existing quota status or create new one for current billing period.

        Args:
            session: Database session

        Returns:
            APIQuotaStatus for current billing period
        """
        # Get existing quota status
        result = await session.execute(
            select(APIQuotaStatus)
            .where(APIQuotaStatus.api_provider == cls.API_PROVIDER)
            .limit(1)
        )
        quota_status = result.scalar_one_or_none()

        # Get current time
        now = datetime.now(timezone.utc)

        # Check if we need to create new billing period
        if quota_status is None or now > quota_status.period_end:
            # Calculate billing period (monthly from 1st to last day of month)
            period_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

            # Calculate last day of month
            if now.month == 12:
                period_end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
            else:
                period_end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)

            if quota_status is None:
                # Create new quota status
                logger.info(f"Creating new quota status for {cls.API_PROVIDER}")
                quota_status = APIQuotaStatus(
                    api_provider=cls.API_PROVIDER,
                    period_start=period_start,
                    period_end=period_end,
                    total_credits_allowed=config.AERODATABOX_MONTHLY_QUOTA,
                    credits_used=0
                )
                session.add(quota_status)
            else:
                # Reset for new billing period
                logger.info(
                    f"Resetting quota status for new billing period: "
                    f"{period_start.date()} to {period_end.date()}"
                )
                quota_status.period_start = period_start
                quota_status.period_end = period_end
                quota_status.credits_used = 0
                quota_status.alert_80_sent = False
                quota_status.alert_80_sent_at = None
                quota_status.alert_90_sent = False
                quota_status.alert_90_sent_at = None
                quota_status.alert_95_sent = False
                quota_status.alert_95_sent_at = None
                quota_status.is_quota_exceeded = False

            await session.flush()

        return quota_status

    @classmethod
    async def check_quota_available(cls, session: AsyncSession) -> bool:
        """
        Check if API quota is available (not exceeded).

        Emergency brake: Blocks API calls when quota > 95%.

        Args:
            session: Database session

        Returns:
            True if quota available, False if exceeded (>95%)
        """
        quota_status = await cls.get_or_create_quota_status(session)

        if quota_status.is_quota_exceeded or quota_status.usage_percentage >= 95:
            logger.warning(
                f"API quota BLOCKED: {quota_status.credits_used}/{quota_status.total_credits_allowed} "
                f"({quota_status.usage_percentage}%)"
            )
            return False

        return True

    @classmethod
    async def _check_and_send_alerts(cls, session: AsyncSession, quota_status: APIQuotaStatus):
        """
        Check quota thresholds and send alerts to admins.

        Alerts at: 80%, 90%, 95%

        Args:
            session: Database session
            quota_status: Current quota status
        """
        # 95% CRITICAL alert
        if quota_status.should_send_alert_95:
            await cls._send_quota_alert(session, quota_status, 95)
            quota_status.alert_95_sent = True
            quota_status.alert_95_sent_at = datetime.now(timezone.utc)
            await session.flush()

        # 90% URGENT alert
        elif quota_status.should_send_alert_90:
            await cls._send_quota_alert(session, quota_status, 90)
            quota_status.alert_90_sent = True
            quota_status.alert_90_sent_at = datetime.now(timezone.utc)
            await session.flush()

        # 80% WARNING alert
        elif quota_status.should_send_alert_80:
            await cls._send_quota_alert(session, quota_status, 80)
            quota_status.alert_80_sent = True
            quota_status.alert_80_sent_at = datetime.now(timezone.utc)
            await session.flush()

    @classmethod
    async def _send_quota_alert(cls, session: AsyncSession, quota_status: APIQuotaStatus, threshold: int):
        """
        Send quota alert email to all admin users.

        Args:
            session: Database session
            quota_status: Current quota status
            threshold: Alert threshold (80, 90, or 95)
        """
        # Get all admin users
        result = await session.execute(
            select(Customer)
            .where(Customer.role.in_([Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]))
            .where(Customer.is_active == True)
        )
        admins = result.scalars().all()

        if not admins:
            logger.warning("No admin users found to send quota alert")
            return

        # Determine alert level
        if threshold >= 95:
            alert_level = "CRITICAL"
            subject = "🚨 CRITICAL: AeroDataBox API Quota Exceeded (95%)"
            action = "IMMEDIATE ACTION REQUIRED: API calls are now BLOCKED. Upgrade to Pro tier or wait for quota reset."
        elif threshold >= 90:
            alert_level = "URGENT"
            subject = "⚠️ URGENT: AeroDataBox API Quota at 90%"
            action = "Upgrade to Pro tier ($5/month) recommended to avoid service interruption."
        else:  # 80%
            alert_level = "WARNING"
            subject = "⚡ WARNING: AeroDataBox API Quota at 80%"
            action = "Review usage patterns and consider upgrading to Pro tier if needed."

        # Prepare email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #{'dc3545' if threshold >= 95 else 'ffc107' if threshold >= 90 else 'fd7e14'}; border-radius: 8px;">
                <h2 style="color: #{'dc3545' if threshold >= 95 else 'ffc107' if threshold >= 90 else 'fd7e14'};">
                    {alert_level}: API Quota Alert
                </h2>

                <p><strong>Your AeroDataBox API quota has reached {threshold}% usage.</strong></p>

                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Current Usage</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Credits Used:</strong> {quota_status.credits_used:,} / {quota_status.total_credits_allowed:,}</li>
                        <li><strong>Credits Remaining:</strong> {quota_status.credits_remaining:,}</li>
                        <li><strong>Usage Percentage:</strong> {quota_status.usage_percentage}%</li>
                        <li><strong>Billing Period:</strong> {quota_status.period_start.date()} to {quota_status.period_end.date()}</li>
                    </ul>
                </div>

                <div style="background-color: #{'fff3cd' if threshold < 95 else 'f8d7da'}; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Action Required</h3>
                    <p>{action}</p>
                </div>

                <h3>Recommendations</h3>
                <ul>
                    <li><strong>Upgrade to Pro Tier:</strong> $5/month for 3,000 API calls (10x more)</li>
                    <li><strong>Review Usage:</strong> Check which claims are consuming credits</li>
                    <li><strong>Enable Caching:</strong> Ensure Redis caching is working (reduces duplicate calls)</li>
                    {f'<li><strong>Manual Verification:</strong> Claims will use manual verification until quota resets on {(quota_status.period_end + timedelta(days=1)).date()}</li>' if threshold >= 95 else ''}
                </ul>

                <p style="margin-top: 30px; font-size: 12px; color: #666;">
                    This is an automated alert from ClaimPlane API Quota Monitoring.<br>
                    Login to admin dashboard to view detailed usage statistics.
                </p>
            </div>
        </body>
        </html>
        """

        # Send email to all admins
        for admin in admins:
            try:
                success = await EmailService.send_email(
                    to_email=admin.email,
                    subject=subject,
                    html_content=html_content,
                    text_content=f"AeroDataBox API quota alert: {threshold}% usage ({quota_status.credits_used}/{quota_status.total_credits_allowed} credits)"
                )

                if success:
                    logger.info(f"Sent {threshold}% quota alert to admin: {admin.email}")
                else:
                    logger.error(f"Failed to send {threshold}% quota alert to admin: {admin.email}")

            except Exception as e:
                logger.error(f"Error sending quota alert to {admin.email}: {str(e)}", exc_info=True)

    @classmethod
    async def get_quota_status(cls, session: AsyncSession) -> Dict[str, Any]:
        """
        Get current quota status.

        Args:
            session: Database session

        Returns:
            Quota status dictionary
        """
        quota_status = await cls.get_or_create_quota_status(session)

        return {
            "api_provider": quota_status.api_provider,
            "period_start": quota_status.period_start.isoformat(),
            "period_end": quota_status.period_end.isoformat(),
            "total_credits_allowed": quota_status.total_credits_allowed,
            "credits_used": quota_status.credits_used,
            "credits_remaining": quota_status.credits_remaining,
            "usage_percentage": quota_status.usage_percentage,
            "is_quota_exceeded": quota_status.is_quota_exceeded,
            "alerts": {
                "alert_80_sent": quota_status.alert_80_sent,
                "alert_80_sent_at": quota_status.alert_80_sent_at.isoformat() if quota_status.alert_80_sent_at else None,
                "alert_90_sent": quota_status.alert_90_sent,
                "alert_90_sent_at": quota_status.alert_90_sent_at.isoformat() if quota_status.alert_90_sent_at else None,
                "alert_95_sent": quota_status.alert_95_sent,
                "alert_95_sent_at": quota_status.alert_95_sent_at.isoformat() if quota_status.alert_95_sent_at else None
            },
            "last_updated": quota_status.last_updated.isoformat()
        }

    @classmethod
    async def get_usage_statistics(cls, session: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """
        Get API usage statistics for the last N days.

        Args:
            session: Database session
            days: Number of days to analyze

        Returns:
            Usage statistics dictionary
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get total calls and credits
        result = await session.execute(
            select(
                func.count(APIUsageTracking.id).label("total_calls"),
                func.sum(APIUsageTracking.credits_used).label("total_credits"),
                func.avg(APIUsageTracking.response_time_ms).label("avg_response_time"),
                func.max(APIUsageTracking.response_time_ms).label("max_response_time")
            )
            .where(APIUsageTracking.api_provider == cls.API_PROVIDER)
            .where(APIUsageTracking.timestamp >= cutoff_date)
        )
        stats = result.one()

        # Get usage by day
        result = await session.execute(
            select(
                func.date(APIUsageTracking.timestamp).label("date"),
                func.count(APIUsageTracking.id).label("calls"),
                func.sum(APIUsageTracking.credits_used).label("credits")
            )
            .where(APIUsageTracking.api_provider == cls.API_PROVIDER)
            .where(APIUsageTracking.timestamp >= cutoff_date)
            .group_by(func.date(APIUsageTracking.timestamp))
            .order_by(func.date(APIUsageTracking.timestamp))
        )
        daily_usage = [
            {
                "date": row.date.isoformat(),
                "calls": row.calls,
                "credits": row.credits
            }
            for row in result.all()
        ]

        # Get usage by endpoint
        result = await session.execute(
            select(
                APIUsageTracking.endpoint,
                func.count(APIUsageTracking.id).label("calls"),
                func.sum(APIUsageTracking.credits_used).label("credits")
            )
            .where(APIUsageTracking.api_provider == cls.API_PROVIDER)
            .where(APIUsageTracking.timestamp >= cutoff_date)
            .group_by(APIUsageTracking.endpoint)
            .order_by(func.sum(APIUsageTracking.credits_used).desc())
            .limit(10)
        )
        endpoint_usage = [
            {
                "endpoint": row.endpoint,
                "calls": row.calls,
                "credits": row.credits
            }
            for row in result.all()
        ]

        return {
            "period_days": days,
            "total_calls": stats.total_calls or 0,
            "total_credits": stats.total_credits or 0,
            "avg_response_time_ms": round(stats.avg_response_time, 2) if stats.avg_response_time else 0,
            "max_response_time_ms": stats.max_response_time or 0,
            "daily_usage": daily_usage,
            "top_endpoints": endpoint_usage
        }
