"""Claim repository for data access operations."""
from typing import Optional, List
from uuid import UUID
from datetime import date

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