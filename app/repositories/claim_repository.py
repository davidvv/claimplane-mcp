"""Claim repository for data access operations."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models import Claim, Customer
from app.repositories.base import BaseRepository


class ClaimRepository(BaseRepository[Claim]):
    """Repository for Claim model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Claim, session)
    
    async def get_by_customer_id(self, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Claim]:
        """Get all claims for a specific customer."""
        return await self.get_all_by_field('customer_id', customer_id, skip, limit)
    
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Claim]:
        """Get claims by status."""
        return await self.get_all_by_field('status', status, skip, limit)
    
    async def get_by_incident_type(self, incident_type: str, skip: int = 0, limit: int = 100) -> List[Claim]:
        """Get claims by incident type."""
        return await self.get_all_by_field('incident_type', incident_type, skip, limit)
    
    async def get_by_flight_number(self, flight_number: str, skip: int = 0, limit: int = 100) -> List[Claim]:
        """Get claims by flight number."""
        return await self.get_all_by_field('flight_number', flight_number.upper(), skip, limit)
    
    async def get_by_date_range(self, start_date: date, end_date: date, skip: int = 0, limit: int = 100) -> List[Claim]:
        """Get claims within a date range."""
        stmt = select(Claim).where(
            and_(
                Claim.departure_date >= start_date,
                Claim.departure_date <= end_date
            )
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_pending_claims(self, skip: int = 0, limit: int = 100) -> List[Claim]:
        """Get claims that are pending review (submitted or under_review)."""
        stmt = select(Claim).where(
            Claim.status.in_([Claim.STATUS_SUBMITTED, Claim.STATUS_UNDER_REVIEW])
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_claims_with_compensation(self, skip: int = 0, limit: int = 100) -> List[Claim]:
        """Get claims that have compensation amount set."""
        stmt = select(Claim).where(
            Claim.compensation_amount.is_not(None)
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create_claim(self, customer_id: UUID, flight_number: str, airline: str,
                          departure_date: date, departure_airport: str, arrival_airport: str,
                          incident_type: str, notes: Optional[str] = None,
                          booking_reference: Optional[str] = None,
                          ticket_number: Optional[str] = None,
                          terms_accepted_at: Optional[str] = None,
                          terms_acceptance_ip: Optional[str] = None) -> Claim:
        """Create a new claim with all required fields."""
        return await self.create(
            customer_id=customer_id,
            flight_number=flight_number.upper(),
            airline=airline,
            departure_date=departure_date,
            departure_airport=departure_airport.upper(),
            arrival_airport=arrival_airport.upper(),
            incident_type=incident_type,
            notes=notes,
            booking_reference=booking_reference.upper() if booking_reference else None,
            ticket_number=ticket_number,
            terms_accepted_at=terms_accepted_at,
            terms_acceptance_ip=terms_acceptance_ip
        )
    
    async def update_claim(self, claim_id: UUID, allow_null_values: bool = False, **kwargs) -> Optional[Claim]:
        """Update claim information.
        
        Args:
            claim_id: UUID of the claim to update
            allow_null_values: If True, None values will be set to null. If False, None values are filtered out.
            **kwargs: Fields to update
        """
        claim = await self.get_by_id(claim_id)
        if not claim:
            return None
        
        if allow_null_values:
            # For PUT operations: allow None values to be set to null
            update_data = kwargs
        else:
            # For PATCH operations: filter out None values to avoid overwriting with null
            update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return claim
        
        return await self.update(claim, **update_data)
    
    async def update_claim_status(self, claim_id: UUID, status: str, notes: Optional[str] = None) -> Optional[Claim]:
        """Update claim status and optionally notes."""
        claim = await self.get_by_id(claim_id)
        if not claim:
            return None
        
        update_data = {'status': status}
        if notes is not None:
            update_data['notes'] = notes
        
        return await self.update(claim, **update_data)
    
    async def update_compensation(self, claim_id: UUID, amount: float, currency: str = "EUR") -> Optional[Claim]:
        """Update claim compensation amount."""
        claim = await self.get_by_id(claim_id)
        if not claim:
            return None
        
        return await self.update(claim, compensation_amount=amount, currency=currency)
    
    async def get_claims_summary(self) -> dict:
        """Get summary statistics for claims."""
        # This could be expanded with more complex aggregations
        total_claims = await self.count()
        
        stmt = select(Claim.status, func.count(Claim.id)).group_by(Claim.status)
        result = await self.session.execute(stmt)
        status_counts = dict(result.all())
        
        return {
            'total_claims': total_claims,
            'status_breakdown': status_counts
        }

    # =========================================================================
    # Draft Workflow Methods (Phase 7 - Workflow v2)
    # =========================================================================

    async def create_draft_claim(
        self,
        customer_id: UUID,
        flight_number: str,
        airline: str,
        departure_date: date,
        departure_airport: str,
        arrival_airport: str,
        incident_type: str,
        compensation_amount: Optional[float] = None,
        currency: str = "EUR",
        current_step: int = 2
    ) -> Claim:
        """Create a draft claim (status=draft, no terms acceptance yet)."""
        return await self.create(
            customer_id=customer_id,
            flight_number=flight_number.upper(),
            airline=airline,
            departure_date=departure_date,
            departure_airport=departure_airport.upper(),
            arrival_airport=arrival_airport.upper(),
            incident_type=incident_type,
            status=Claim.STATUS_DRAFT,
            compensation_amount=compensation_amount,
            currency=currency,
            current_step=current_step,
            reminder_count=0
        )

    async def get_stale_drafts(
        self,
        minutes_inactive: int = 30,
        max_reminders: int = 0
    ) -> List[Claim]:
        """Get draft claims that have been inactive for specified minutes.

        Args:
            minutes_inactive: Minutes since last activity
            max_reminders: Maximum reminder count (get drafts with <= this count)

        Returns:
            List of stale draft claims
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes_inactive)

        stmt = select(Claim).where(
            and_(
                Claim.status == Claim.STATUS_DRAFT,
                func.coalesce(Claim.last_activity_at, Claim.submitted_at) < cutoff_time,
                Claim.reminder_count <= max_reminders
            )
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_drafts_for_reminder(
        self,
        days_old: int,
        reminder_count: int
    ) -> List[Claim]:
        """Get draft claims that need a specific reminder.

        Args:
            days_old: Minimum age of draft in days
            reminder_count: Exact reminder count to match

        Returns:
            List of draft claims needing this reminder
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        stmt = select(Claim).where(
            and_(
                Claim.status == Claim.STATUS_DRAFT,
                Claim.submitted_at < cutoff_date,  # submitted_at is creation time for drafts
                Claim.reminder_count == reminder_count
            )
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_expired_drafts(self, days_old: int = 11) -> List[Claim]:
        """Get draft claims that are past expiration for cleanup.

        Args:
            days_old: Minimum age of draft in days for expiration

        Returns:
            List of expired draft claims
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        stmt = select(Claim).where(
            and_(
                Claim.status == Claim.STATUS_DRAFT,
                Claim.submitted_at < cutoff_date
            )
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def increment_reminder_count(self, claim_id: UUID) -> Optional[Claim]:
        """Increment the reminder count for a claim."""
        claim = await self.get_by_id(claim_id)
        if not claim:
            return None

        claim.reminder_count = (claim.reminder_count or 0) + 1
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def update_activity(self, claim_id: UUID) -> Optional[Claim]:
        """Update last_activity_at timestamp for a claim."""
        claim = await self.get_by_id(claim_id)
        if not claim:
            return None

        claim.last_activity_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def update_passengers(self, claim_id: UUID, passengers_data: List[dict]) -> None:
        """Update the list of passengers for a claim (replaces existing list)."""
        from app.models import Passenger
        
        # Delete existing passengers
        stmt = select(Passenger).where(Passenger.claim_id == claim_id)
        result = await self.session.execute(stmt)
        existing_passengers = result.scalars().all()
        for p in existing_passengers:
            await self.session.delete(p)
        
        # Add new passengers
        for p_data in passengers_data:
            new_p = Passenger(
                claim_id=claim_id,
                first_name=p_data.get('first_name'),
                last_name=p_data.get('last_name'),
                ticket_number=p_data.get('ticket_number'),
                email=p_data.get('email')
            )
            self.session.add(new_p)
        
        await self.session.flush()

    async def finalize_draft(
        self,
        claim_id: UUID,
        notes: Optional[str] = None,
        booking_reference: Optional[str] = None,
        ticket_number: Optional[str] = None,
        terms_accepted_at: Optional[datetime] = None,
        terms_acceptance_ip: Optional[str] = None
    ) -> Optional[Claim]:
        """Finalize a draft claim to submitted status."""
        claim = await self.get_by_id(claim_id)
        if not claim:
            return None

        if claim.status != Claim.STATUS_DRAFT:
            raise ValueError(f"Claim {claim_id} is not a draft (status: {claim.status})")

        claim.status = Claim.STATUS_SUBMITTED
        claim.notes = notes
        claim.booking_reference = booking_reference.upper() if booking_reference else None
        claim.ticket_number = ticket_number
        claim.terms_accepted_at = terms_accepted_at or datetime.utcnow()
        claim.terms_acceptance_ip = terms_acceptance_ip
        claim.submitted_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(claim)
        return claim