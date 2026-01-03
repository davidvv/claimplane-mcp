"""Deletion request repository for managing account deletion workflows."""
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date, timezone

from sqlalchemy import select, func, and_, or_, String, bindparam, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AccountDeletionRequest, Customer
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class DeletionRequestRepository(BaseRepository[AccountDeletionRequest]):
    """Repository for account deletion request operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(AccountDeletionRequest, session)

    async def get_deletion_requests_with_details(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "requested_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get deletion requests with filtering, sorting, and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status (pending, approved, rejected, completed)
            date_from: Filter by request date from
            date_to: Filter by request date to
            search: Search in customer email, name
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            Dictionary with requests and pagination info
        """
        # Build base query with eager loading
        query = select(AccountDeletionRequest).options(
            selectinload(AccountDeletionRequest.customer),
            selectinload(AccountDeletionRequest.reviewer)
        )

        # Apply filters
        filters = []

        if status:
            filters.append(AccountDeletionRequest.status == status)

        if date_from:
            filters.append(AccountDeletionRequest.requested_at >= date_from)

        if date_to:
            # Include the entire day
            filters.append(AccountDeletionRequest.requested_at < date_to.replace(hour=23, minute=59, second=59))

        # Search functionality
        if search:
            # Join with Customer for searching customer details
            query = query.join(Customer, AccountDeletionRequest.customer_id == Customer.id)
            # Using bindparam to prevent SQL injection
            search_filters = or_(
                Customer.first_name.ilike(bindparam('search_param')),
                Customer.last_name.ilike(bindparam('search_param')),
                Customer.email.ilike(bindparam('search_param')),
                AccountDeletionRequest.email.ilike(bindparam('search_param'))
            )
            filters.append(search_filters)

        # Apply filters to query
        if filters:
            query = query.where(and_(*filters))

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())

        # Prepare params for parameterized queries
        params = {}
        if search:
            params['search_param'] = f"%{search}%"

        total_result = await self.session.execute(count_query, params)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(AccountDeletionRequest, sort_by, AccountDeletionRequest.requested_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.session.execute(query, params)
        requests = result.scalars().all()

        return {
            "requests": requests,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + len(requests)) < total
        }

    async def get_request_with_customer_details(
        self,
        request_id: UUID
    ) -> Optional[AccountDeletionRequest]:
        """
        Get single deletion request with all customer details loaded.

        Args:
            request_id: UUID of the deletion request

        Returns:
            AccountDeletionRequest or None if not found
        """
        query = select(AccountDeletionRequest).options(
            selectinload(AccountDeletionRequest.customer),
            selectinload(AccountDeletionRequest.reviewer)
        ).where(AccountDeletionRequest.id == request_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def approve_request(
        self,
        request_id: UUID,
        admin_id: UUID,
        notes: Optional[str] = None
    ) -> AccountDeletionRequest:
        """
        Approve a deletion request.

        Args:
            request_id: UUID of the deletion request
            admin_id: UUID of the admin approving the request
            notes: Optional notes for the approval

        Returns:
            Updated AccountDeletionRequest

        Raises:
            ValueError: If request not found or not in pending status
        """
        request = await self.get_by_id(request_id)
        if not request:
            raise ValueError(f"Deletion request {request_id} not found")

        if request.status != AccountDeletionRequest.STATUS_PENDING:
            raise ValueError(
                f"Request is not pending (current status: {request.status}). "
                "Only pending requests can be approved."
            )

        request.status = AccountDeletionRequest.STATUS_APPROVED
        request.reviewed_by = admin_id
        request.reviewed_at = datetime.now(timezone.utc)
        if notes:
            request.notes = notes

        await self.session.commit()
        await self.session.refresh(request)

        logger.info(f"Deletion request {request_id} approved by admin {admin_id}")

        return request

    async def reject_request(
        self,
        request_id: UUID,
        admin_id: UUID,
        rejection_reason: str
    ) -> AccountDeletionRequest:
        """
        Reject a deletion request and unblacklist the customer account.

        Args:
            request_id: UUID of the deletion request
            admin_id: UUID of the admin rejecting the request
            rejection_reason: Reason for rejection (required)

        Returns:
            Updated AccountDeletionRequest

        Raises:
            ValueError: If request not found or not in pending status
        """
        request = await self.get_by_id(request_id)
        if not request:
            raise ValueError(f"Deletion request {request_id} not found")

        if request.status != AccountDeletionRequest.STATUS_PENDING:
            raise ValueError(
                f"Request is not pending (current status: {request.status}). "
                "Only pending requests can be rejected."
            )

        request.status = AccountDeletionRequest.STATUS_REJECTED
        request.reviewed_by = admin_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.notes = rejection_reason

        # Unblacklist the customer account so they can log in again
        customer = await self.session.get(Customer, request.customer_id)
        if customer:
            customer.is_blacklisted = False
            customer.blacklisted_at = None
            logger.info(f"Customer {customer.id} ({customer.email}) unblacklisted after rejection")

        await self.session.commit()
        await self.session.refresh(request)

        logger.info(f"Deletion request {request_id} rejected by admin {admin_id}")

        return request
