"""Admin claim repository with advanced filtering and bulk operations."""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date

from sqlalchemy import select, func, and_, or_, desc, asc, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Claim, Customer, ClaimFile, ClaimNote, ClaimStatusHistory
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AdminClaimRepository(BaseRepository[Claim]):
    """Repository for admin claim operations with advanced querying."""

    def __init__(self, session: AsyncSession):
        super().__init__(Claim, session)

    async def get_claims_with_details(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        airline: Optional[str] = None,
        incident_type: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "submitted_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get claims with filtering, sorting, and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            airline: Filter by airline
            incident_type: Filter by incident type
            assigned_to: Filter by assigned reviewer
            date_from: Filter by departure date from
            date_to: Filter by departure date to
            search: Search in customer name, email, flight number, claim ID
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            Dictionary with claims and pagination info
        """
        # Build base query with eager loading
        query = select(Claim).options(
            selectinload(Claim.customer),
            selectinload(Claim.files),
            selectinload(Claim.assignee),
            selectinload(Claim.reviewer)
        )

        # Apply filters
        filters = []

        if status:
            filters.append(Claim.status == status)

        if airline:
            filters.append(Claim.airline.ilike(f"%{airline}%"))

        if incident_type:
            filters.append(Claim.incident_type == incident_type)

        if assigned_to:
            filters.append(Claim.assigned_to == assigned_to)

        if date_from:
            filters.append(Claim.departure_date >= date_from)

        if date_to:
            filters.append(Claim.departure_date <= date_to)

        # Search functionality
        if search:
            # Join with Customer for searching customer details
            query = query.join(Customer)
            search_filters = or_(
                Claim.flight_number.ilike(f"%{search}%"),
                Customer.first_name.ilike(f"%{search}%"),
                Customer.last_name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                func.cast(Claim.id, String).ilike(f"%{search}%")
            )
            filters.append(search_filters)

        if filters:
            query = query.where(and_(*filters))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Claim, sort_by, Claim.submitted_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        claims = result.scalars().all()

        return {
            "claims": claims,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": (skip + limit) < total,
            "has_prev": skip > 0
        }

    async def get_claim_with_full_details(self, claim_id: UUID) -> Optional[Claim]:
        """
        Get a single claim with all related data loaded.

        Args:
            claim_id: Claim ID

        Returns:
            Claim with all relationships loaded, or None
        """
        query = select(Claim).where(Claim.id == claim_id).options(
            selectinload(Claim.customer),
            selectinload(Claim.files),
            selectinload(Claim.assignee),
            selectinload(Claim.reviewer),
            selectinload(Claim.claim_notes).selectinload(ClaimNote.author),  # Load note authors
            selectinload(Claim.status_history).selectinload(ClaimStatusHistory.changed_by_user)  # Load status change users
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_claims_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Claim]:
        """
        Get claims by status with customer info loaded.

        Args:
            status: Claim status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of claims
        """
        query = select(Claim).where(Claim.status == status).options(
            selectinload(Claim.customer)
        ).order_by(desc(Claim.submitted_at)).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_claims_for_reviewer(
        self,
        reviewer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Claim]:
        """
        Get claims assigned to a specific reviewer.

        Args:
            reviewer_id: Reviewer user ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of claims
        """
        query = select(Claim).where(Claim.assigned_to == reviewer_id).options(
            selectinload(Claim.customer),
            selectinload(Claim.files)
        ).order_by(desc(Claim.assigned_at)).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get analytics summary for admin dashboard.

        Returns:
            Dictionary with analytics data
        """
        # Count by status
        status_counts = {}
        for status_type in Claim.STATUS_TYPES:
            count_query = select(func.count()).where(Claim.status == status_type)
            result = await self.session.execute(count_query)
            status_counts[status_type] = result.scalar()

        # Total claims
        total_query = select(func.count(Claim.id))
        total_result = await self.session.execute(total_query)
        total_claims = total_result.scalar()

        # Total compensation approved
        compensation_query = select(func.sum(Claim.compensation_amount)).where(
            Claim.status.in_([Claim.STATUS_APPROVED, Claim.STATUS_PAID])
        )
        compensation_result = await self.session.execute(compensation_query)
        total_compensation = compensation_result.scalar() or 0

        # Average compensation
        avg_compensation_query = select(func.avg(Claim.compensation_amount)).where(
            Claim.compensation_amount.isnot(None)
        )
        avg_result = await self.session.execute(avg_compensation_query)
        avg_compensation = avg_result.scalar() or 0

        # Claims by airline
        airline_query = select(
            Claim.airline,
            func.count(Claim.id).label('count')
        ).group_by(Claim.airline).order_by(desc('count')).limit(10)
        airline_result = await self.session.execute(airline_query)
        claims_by_airline = {row.airline: row.count for row in airline_result}

        # Claims by incident type
        incident_query = select(
            Claim.incident_type,
            func.count(Claim.id).label('count')
        ).group_by(Claim.incident_type)
        incident_result = await self.session.execute(incident_query)
        claims_by_incident = {row.incident_type: row.count for row in incident_result}

        return {
            "total_claims": total_claims,
            "pending_review": status_counts.get("submitted", 0) + status_counts.get("under_review", 0),
            "approved": status_counts.get("approved", 0),
            "rejected": status_counts.get("rejected", 0),
            "total_compensation": float(total_compensation),
            "avg_processing_time_hours": 0,  # TODO: Implement processing time calculation
            "claims_by_status": status_counts,
            "claims_by_airline": claims_by_airline,
            "claims_by_incident_type": claims_by_incident
        }

    async def bulk_update_status(
        self,
        claim_ids: List[UUID],
        new_status: str,
        changed_by: UUID,
        change_reason: Optional[str] = None
    ) -> int:
        """
        Bulk update status for multiple claims.

        Note: This is a simplified version. For production, use the
        ClaimWorkflowService for each claim to maintain audit trail.

        Args:
            claim_ids: List of claim IDs to update
            new_status: New status to set
            changed_by: User ID making the change
            change_reason: Reason for the change

        Returns:
            Number of claims updated
        """
        from sqlalchemy import update

        # Update claims
        stmt = update(Claim).where(Claim.id.in_(claim_ids)).values(
            status=new_status,
            updated_at=datetime.utcnow()
        )
        result = await self.session.execute(stmt)

        # Create status history entries for each claim
        for claim_id in claim_ids:
            # Get the claim to know previous status
            claim = await self.get_by_id(claim_id)
            if claim:
                history = ClaimStatusHistory(
                    claim_id=claim_id,
                    previous_status=claim.status,
                    new_status=new_status,
                    changed_by=changed_by,
                    change_reason=change_reason or f"Bulk status update"
                )
                self.session.add(history)

        await self.session.flush()

        logger.info(f"Bulk updated {result.rowcount} claims to status '{new_status}' by user {changed_by}")
        return result.rowcount

    async def bulk_assign(
        self,
        claim_ids: List[UUID],
        assigned_to: UUID,
        assigned_by: UUID
    ) -> int:
        """
        Bulk assign claims to a reviewer.

        Args:
            claim_ids: List of claim IDs to assign
            assigned_to: User ID to assign to
            assigned_by: User ID making the assignment

        Returns:
            Number of claims assigned
        """
        from sqlalchemy import update

        stmt = update(Claim).where(Claim.id.in_(claim_ids)).values(
            assigned_to=assigned_to,
            assigned_at=datetime.utcnow()
        )
        result = await self.session.execute(stmt)
        await self.session.flush()

        logger.info(f"Bulk assigned {result.rowcount} claims to user {assigned_to} by user {assigned_by}")
        return result.rowcount

    async def add_note(
        self,
        claim_id: UUID,
        author_id: UUID,
        note_text: str,
        is_internal: bool = True
    ) -> ClaimNote:
        """
        Add a note to a claim.

        Args:
            claim_id: Claim ID
            author_id: User ID of note author
            note_text: Note content
            is_internal: Whether note is internal or customer-facing

        Returns:
            Created note with author loaded
        """
        note = ClaimNote(
            claim_id=claim_id,
            author_id=author_id,
            note_text=note_text,
            is_internal=is_internal
        )
        self.session.add(note)
        await self.session.flush()
        await self.session.refresh(note, ["author"])  # Refresh with author relationship loaded

        logger.info(f"Added {'internal' if is_internal else 'customer-facing'} note to claim {claim_id} by user {author_id}")
        return note

    async def get_notes(
        self,
        claim_id: UUID,
        include_internal: bool = True
    ) -> List[ClaimNote]:
        """
        Get notes for a claim.

        Args:
            claim_id: Claim ID
            include_internal: Whether to include internal notes

        Returns:
            List of notes
        """
        query = select(ClaimNote).where(ClaimNote.claim_id == claim_id).options(
            selectinload(ClaimNote.author)
        ).order_by(desc(ClaimNote.created_at))

        if not include_internal:
            query = query.where(ClaimNote.is_internal == False)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_status_history(
        self,
        claim_id: UUID
    ) -> List[ClaimStatusHistory]:
        """
        Get status change history for a claim.

        Args:
            claim_id: Claim ID

        Returns:
            List of status history entries
        """
        query = select(ClaimStatusHistory).where(
            ClaimStatusHistory.claim_id == claim_id
        ).options(
            selectinload(ClaimStatusHistory.changed_by_user)
        ).order_by(desc(ClaimStatusHistory.changed_at))

        result = await self.session.execute(query)
        return result.scalars().all()
