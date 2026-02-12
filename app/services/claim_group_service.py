"""Service layer for claim group management."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClaimGroup, ClaimGroupNote, Claim, Customer
from app.schemas import (
    ClaimGroupCreateSchema,
    ClaimGroupNoteCreateSchema,
    BulkActionSchema
)


class ClaimGroupService:
    """Service for managing claim groups."""
    
    @staticmethod
    async def create_claim_group(
        db: AsyncSession,
        account_holder_id: UUID,
        data: ClaimGroupCreateSchema
    ) -> ClaimGroup:
        """Create a new claim group."""
        claim_group = ClaimGroup(
            account_holder_id=account_holder_id,
            flight_number=data.flight_number.upper(),
            flight_date=data.flight_date,
            group_name=data.group_name or f"Group - {data.flight_number}"
        )
        db.add(claim_group)
        await db.commit()
        await db.refresh(claim_group)
        return claim_group
    
    @staticmethod
    async def get_claim_group(
        db: AsyncSession,
        group_id: UUID
    ) -> Optional[ClaimGroup]:
        """Get a claim group by ID."""
        result = await db.execute(
            select(ClaimGroup).where(ClaimGroup.id == group_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_claim_group_with_claims(
        db: AsyncSession,
        group_id: UUID
    ) -> Optional[ClaimGroup]:
        """Get a claim group with all associated claims."""
        result = await db.execute(
            select(ClaimGroup)
            .where(ClaimGroup.id == group_id)
            .outerjoin(Claim, Claim.claim_group_id == ClaimGroup.id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_customer_claim_groups(
        db: AsyncSession,
        customer_id: UUID
    ) -> List[ClaimGroup]:
        """Get all claim groups for a customer."""
        result = await db.execute(
            select(ClaimGroup)
            .where(ClaimGroup.account_holder_id == customer_id)
            .order_by(ClaimGroup.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_claim_group_summary(
        db: AsyncSession,
        group_id: UUID
    ) -> dict:
        """Get summary statistics for a claim group."""
        # Get the group
        group = await ClaimGroupService.get_claim_group(db, group_id)
        if not group:
            return None
        
        # Get all claims in the group
        result = await db.execute(
            select(Claim).where(Claim.claim_group_id == group_id)
        )
        claims = result.scalars().all()
        
        # Calculate totals
        total_claims = len(claims)
        total_compensation = sum(
            c.compensation_amount for c in claims 
            if c.compensation_amount
        )
        
        # Count by status
        status_counts = {}
        for claim in claims:
            status_counts[claim.status] = status_counts.get(claim.status, 0) + 1
        
        return {
            "id": group.id,
            "group_name": group.group_name,
            "flight_number": group.flight_number,
            "flight_date": group.flight_date,
            "total_claims": total_claims,
            "total_compensation": total_compensation,
            "status_summary": status_counts,
            "created_at": group.created_at,
            "updated_at": group.updated_at
        }
    
    @staticmethod
    async def confirm_consent(
        db: AsyncSession,
        group_id: UUID,
        ip_address: Optional[str] = None
    ) -> ClaimGroup:
        """Confirm consent for filing claims on behalf of others."""
        group = await ClaimGroupService.get_claim_group(db, group_id)
        if not group:
            raise ValueError("Claim group not found")
        
        group.consent_confirmed = True
        group.consent_confirmed_at = datetime.utcnow()
        group.consent_ip_address = ip_address
        
        await db.commit()
        await db.refresh(group)
        return group
    
    @staticmethod
    async def add_claim_to_group(
        db: AsyncSession,
        claim_id: UUID,
        group_id: UUID
    ) -> Claim:
        """Add a claim to a group."""
        # Get the claim
        result = await db.execute(
            select(Claim).where(Claim.id == claim_id)
        )
        claim = result.scalar_one_or_none()
        
        if not claim:
            raise ValueError("Claim not found")
        
        # Get the group
        group = await ClaimGroupService.get_claim_group(db, group_id)
        if not group:
            raise ValueError("Claim group not found")
        
        # Validate same flight
        if (claim.flight_number != group.flight_number or 
            claim.departure_date != group.flight_date):
            raise ValueError("All claims in a group must have the same flight number and date")
        
        claim.claim_group_id = group_id
        await db.commit()
        await db.refresh(claim)
        return claim
    
    @staticmethod
    async def validate_unique_passengers(
        db: AsyncSession,
        group_id: UUID
    ) -> bool:
        """Validate that all passengers in a group are unique."""
        result = await db.execute(
            select(Claim)
            .where(Claim.claim_group_id == group_id)
            .outerjoin(Claim.passengers)
        )
        claims = result.scalars().all()
        
        # Extract passenger names from all claims
        passengers = []
        for claim in claims:
            for passenger in claim.passengers:
                passenger_key = f"{passenger.first_name.lower()}_{passenger.last_name.lower()}"
                if passenger_key in passengers:
                    return False
                passengers.append(passenger_key)
        
        return True


class ClaimGroupNoteService:
    """Service for managing claim group notes."""
    
    @staticmethod
    async def create_note(
        db: AsyncSession,
        group_id: UUID,
        admin_id: UUID,
        data: ClaimGroupNoteCreateSchema
    ) -> ClaimGroupNote:
        """Create a new note for a claim group."""
        note = ClaimGroupNote(
            claim_group_id=group_id,
            admin_id=admin_id,
            note_text=data.note_text
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note
    
    @staticmethod
    async def get_group_notes(
        db: AsyncSession,
        group_id: UUID
    ) -> List[ClaimGroupNote]:
        """Get all notes for a claim group."""
        result = await db.execute(
            select(ClaimGroupNote)
            .where(ClaimGroupNote.claim_group_id == group_id)
            .order_by(ClaimGroupNote.created_at.desc())
        )
        return result.scalars().all()


class ClaimGroupAdminService:
    """Service for admin claim group operations."""
    
    @staticmethod
    async def get_all_claim_groups(
        db: AsyncSession,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        account_holder_id: Optional[UUID] = None,
        flight_number: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClaimGroup]:
        """Get all claim groups with optional filters."""
        query = select(ClaimGroup)
        
        if account_holder_id:
            query = query.where(ClaimGroup.account_holder_id == account_holder_id)
        
        if flight_number:
            query = query.where(ClaimGroup.flight_number.ilike(f"%{flight_number}%"))
        
        if date_from:
            query = query.where(ClaimGroup.flight_date >= date_from)
        
        if date_to:
            query = query.where(ClaimGroup.flight_date <= date_to)
        
        # Note: Status filtering requires joining with claims and aggregating
        # This is handled separately in the endpoint
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def bulk_update_claims(
        db: AsyncSession,
        group_id: UUID,
        data: BulkActionSchema,
        admin_id: UUID
    ) -> dict:
        """Perform bulk action on all claims in a group."""
        from app.services.claim_service import ClaimService
        
        # Get all claims in the group
        result = await db.execute(
            select(Claim).where(Claim.claim_group_id == group_id)
        )
        claims = result.scalars().all()
        
        if not claims:
            raise ValueError("No claims found in this group")
        
        updated_count = 0
        errors = []
        
        for claim in claims:
            try:
                if data.action == "approve_all":
                    await ClaimService.approve_claim(
                        db, claim.id, admin_id, 
                        calculated_compensation=claim.calculated_compensation
                    )
                elif data.action == "reject_all":
                    await ClaimService.reject_claim(
                        db, claim.id, admin_id, 
                        rejection_reason=data.rejection_reason
                    )
                elif data.action == "request_info_all":
                    # Set status to under_review to request more info
                    claim.status = Claim.STATUS_UNDER_REVIEW
                
                updated_count += 1
            except Exception as e:
                errors.append({
                    "claim_id": str(claim.id),
                    "error": str(e)
                })
        
        await db.commit()
        
        return {
            "success": len(errors) == 0,
            "total_claims": len(claims),
            "updated_count": updated_count,
            "errors": errors
        }
