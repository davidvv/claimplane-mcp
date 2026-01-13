"""Claim event repository for analytics data access operations."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models import ClaimEvent
from app.repositories.base import BaseRepository


class ClaimEventRepository(BaseRepository[ClaimEvent]):
    """Repository for ClaimEvent model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ClaimEvent, session)

    async def log_event(
        self,
        event_type: str,
        claim_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ClaimEvent:
        """Log a claim workflow event.

        Args:
            event_type: Type of event (from ClaimEvent.EVENT_TYPES)
            claim_id: Optional claim UUID
            customer_id: Optional customer UUID
            event_data: Optional JSON data specific to the event
            ip_address: Client IP address
            user_agent: Client user agent string
            session_id: Browser session ID

        Returns:
            Created ClaimEvent instance
        """
        return await self.create(
            event_type=event_type,
            claim_id=claim_id,
            customer_id=customer_id,
            event_data=event_data,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )

    async def get_by_claim_id(
        self,
        claim_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClaimEvent]:
        """Get all events for a specific claim."""
        return await self.get_all_by_field('claim_id', claim_id, skip, limit)

    async def get_by_customer_id(
        self,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClaimEvent]:
        """Get all events for a specific customer."""
        return await self.get_all_by_field('customer_id', customer_id, skip, limit)

    async def get_by_event_type(
        self,
        event_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClaimEvent]:
        """Get all events of a specific type."""
        return await self.get_all_by_field('event_type', event_type, skip, limit)

    async def get_claim_timeline(self, claim_id: UUID) -> List[ClaimEvent]:
        """Get chronological event timeline for a claim."""
        stmt = select(ClaimEvent).where(
            ClaimEvent.claim_id == claim_id
        ).order_by(ClaimEvent.created_at.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_events_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None
    ) -> List[ClaimEvent]:
        """Get events within a date range, optionally filtered by type."""
        conditions = [
            ClaimEvent.created_at >= start_date,
            ClaimEvent.created_at <= end_date
        ]

        if event_type:
            conditions.append(ClaimEvent.event_type == event_type)

        stmt = select(ClaimEvent).where(
            and_(*conditions)
        ).order_by(ClaimEvent.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_funnel_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get conversion funnel statistics.

        Returns count of each event type for funnel analysis.
        """
        conditions = []
        if start_date:
            conditions.append(ClaimEvent.created_at >= start_date)
        if end_date:
            conditions.append(ClaimEvent.created_at <= end_date)

        stmt = select(
            ClaimEvent.event_type,
            func.count(ClaimEvent.id)
        ).group_by(ClaimEvent.event_type)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return dict(result.all())

    async def get_drop_off_analysis(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze where users drop off in the claim process.

        Returns step-by-step conversion rates.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        funnel_stats = await self.get_funnel_stats(start_date=start_date)

        # Calculate conversion rates
        drafts = funnel_stats.get(ClaimEvent.EVENT_DRAFT_CREATED, 0)
        step_completed = funnel_stats.get(ClaimEvent.EVENT_STEP_COMPLETED, 0)
        submitted = funnel_stats.get(ClaimEvent.EVENT_CLAIM_SUBMITTED, 0)
        abandoned = funnel_stats.get(ClaimEvent.EVENT_CLAIM_ABANDONED, 0)

        return {
            'period_days': days,
            'drafts_created': drafts,
            'steps_completed': step_completed,
            'claims_submitted': submitted,
            'claims_abandoned': abandoned,
            'conversion_rate': round(submitted / drafts * 100, 2) if drafts > 0 else 0,
            'abandonment_rate': round(abandoned / drafts * 100, 2) if drafts > 0 else 0,
        }

    async def get_reminder_effectiveness(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze effectiveness of reminder emails."""
        start_date = datetime.utcnow() - timedelta(days=days)

        funnel_stats = await self.get_funnel_stats(start_date=start_date)

        reminders_sent = funnel_stats.get(ClaimEvent.EVENT_REMINDER_SENT, 0)
        reminders_clicked = funnel_stats.get(ClaimEvent.EVENT_REMINDER_CLICKED, 0)
        claims_resumed = funnel_stats.get(ClaimEvent.EVENT_CLAIM_RESUMED, 0)

        return {
            'period_days': days,
            'reminders_sent': reminders_sent,
            'reminders_clicked': reminders_clicked,
            'claims_resumed': claims_resumed,
            'click_rate': round(reminders_clicked / reminders_sent * 100, 2) if reminders_sent > 0 else 0,
            'resume_rate': round(claims_resumed / reminders_clicked * 100, 2) if reminders_clicked > 0 else 0,
        }
