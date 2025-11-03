"""Claim workflow service for managing status transitions and business rules."""
import logging
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models import Claim, ClaimStatusHistory

logger = logging.getLogger(__name__)


class ClaimWorkflowService:
    """Service for managing claim status transitions and workflow rules."""

    # Define valid status transitions
    # Format: current_status -> [list of valid next statuses]
    VALID_TRANSITIONS = {
        Claim.STATUS_DRAFT: [
            Claim.STATUS_SUBMITTED
        ],
        Claim.STATUS_SUBMITTED: [
            Claim.STATUS_UNDER_REVIEW,
            Claim.STATUS_REJECTED  # Can reject without review if clearly invalid
        ],
        Claim.STATUS_UNDER_REVIEW: [
            Claim.STATUS_APPROVED,
            Claim.STATUS_REJECTED,
            Claim.STATUS_SUBMITTED  # Can send back for more info
        ],
        Claim.STATUS_APPROVED: [
            Claim.STATUS_PAID,
            Claim.STATUS_REJECTED  # Can reverse approval if fraud detected
        ],
        Claim.STATUS_REJECTED: [
            Claim.STATUS_SUBMITTED,     # Customer can resubmit with corrections
            Claim.STATUS_UNDER_REVIEW,  # Can reconsider if new evidence provided
            Claim.STATUS_CLOSED         # Final rejection
        ],
        Claim.STATUS_PAID: [
            Claim.STATUS_CLOSED
        ],
        Claim.STATUS_CLOSED: [
            # Generally final, but can reopen in exceptional cases
            Claim.STATUS_UNDER_REVIEW
        ]
    }

    # Statuses that require rejection reason
    REQUIRE_REJECTION_REASON = [
        Claim.STATUS_REJECTED
    ]

    # Statuses that require manual review
    REQUIRE_MANUAL_REVIEW = [
        Claim.STATUS_APPROVED,
        Claim.STATUS_PAID
    ]

    @staticmethod
    def is_valid_transition(current_status: str, new_status: str) -> bool:
        """
        Check if a status transition is valid.

        Args:
            current_status: Current claim status
            new_status: Desired new status

        Returns:
            True if transition is valid, False otherwise
        """
        if current_status == new_status:
            return True  # No transition needed

        valid_next_statuses = ClaimWorkflowService.VALID_TRANSITIONS.get(current_status, [])
        return new_status in valid_next_statuses

    @staticmethod
    def get_valid_next_statuses(current_status: str) -> List[str]:
        """
        Get list of valid next statuses for a given current status.

        Args:
            current_status: Current claim status

        Returns:
            List of valid next statuses
        """
        return ClaimWorkflowService.VALID_TRANSITIONS.get(current_status, [])

    @staticmethod
    async def validate_status_transition(
        claim: Claim,
        new_status: str,
        changed_by: UUID,
        change_reason: Optional[str] = None
    ) -> Dict:
        """
        Validate a status transition and return validation result.

        Args:
            claim: Claim instance
            new_status: Desired new status
            changed_by: ID of user making the change
            change_reason: Reason for status change

        Returns:
            Dictionary with validation result:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        current_status = claim.status

        # Check if transition is valid
        if not ClaimWorkflowService.is_valid_transition(current_status, new_status):
            result["valid"] = False
            result["errors"].append(
                f"Invalid status transition from '{current_status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(ClaimWorkflowService.get_valid_next_statuses(current_status))}"
            )

        # Check if rejection reason is required
        if new_status in ClaimWorkflowService.REQUIRE_REJECTION_REASON and not change_reason:
            result["valid"] = False
            result["errors"].append(f"Rejection reason is required when changing status to '{new_status}'")

        # Check if compensation is set for approval
        if new_status == Claim.STATUS_APPROVED and claim.compensation_amount is None:
            result["warnings"].append("Compensation amount is not set. Consider calculating compensation before approval.")

        # Check if reviewer is assigned for under_review status
        if new_status == Claim.STATUS_UNDER_REVIEW and claim.assigned_to is None:
            result["warnings"].append("No reviewer assigned. Consider assigning a reviewer.")

        # Note: Removed document check to avoid lazy-loading 'files' relationship
        # which would trigger sync DB query in async context.
        # Document validation should be done separately via explicit query if needed.

        return result

    @staticmethod
    async def transition_status(
        session: AsyncSession,
        claim: Claim,
        new_status: str,
        changed_by: UUID,
        change_reason: Optional[str] = None,
        auto_timestamp: bool = True
    ) -> Claim:
        """
        Transition a claim to a new status with validation and audit trail.

        Args:
            session: Database session
            claim: Claim instance
            new_status: Desired new status
            changed_by: ID of user making the change
            change_reason: Reason for status change
            auto_timestamp: Whether to automatically set reviewed_at timestamp

        Returns:
            Updated claim instance

        Raises:
            HTTPException: If transition is invalid
        """
        # Validate transition
        validation = await ClaimWorkflowService.validate_status_transition(
            claim, new_status, changed_by, change_reason
        )

        if not validation["valid"]:
            error_msg = "; ".join(validation["errors"])
            logger.error(f"Invalid status transition for claim {claim.id}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid status transition", "errors": validation["errors"]}
            )

        # Log warnings if any
        if validation["warnings"]:
            for warning in validation["warnings"]:
                logger.warning(f"Claim {claim.id} status transition warning: {warning}")

        # Store previous status
        previous_status = claim.status

        # Update claim status
        claim.status = new_status

        # Update timestamps based on status
        if auto_timestamp:
            if new_status == Claim.STATUS_UNDER_REVIEW:
                claim.reviewed_at = datetime.utcnow()
                claim.reviewed_by = changed_by
            elif new_status == Claim.STATUS_REJECTED:
                claim.reviewed_at = datetime.utcnow()
                claim.reviewed_by = changed_by
                claim.rejection_reason = change_reason
            elif new_status == Claim.STATUS_APPROVED:
                claim.reviewed_at = datetime.utcnow()
                claim.reviewed_by = changed_by

        # Create status history entry
        status_history = ClaimStatusHistory(
            claim_id=claim.id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            change_reason=change_reason
        )
        session.add(status_history)

        # Commit changes
        await session.flush()
        await session.refresh(claim)

        logger.info(
            f"Claim {claim.id} status changed from '{previous_status}' to '{new_status}' "
            f"by user {changed_by}"
        )

        return claim

    @staticmethod
    async def assign_claim(
        session: AsyncSession,
        claim: Claim,
        assigned_to: UUID,
        assigned_by: UUID
    ) -> Claim:
        """
        Assign a claim to a reviewer.

        Args:
            session: Database session
            claim: Claim instance
            assigned_to: ID of user to assign to
            assigned_by: ID of user making the assignment

        Returns:
            Updated claim instance
        """
        previous_assignee = claim.assigned_to

        claim.assigned_to = assigned_to
        claim.assigned_at = datetime.utcnow()

        await session.flush()
        await session.refresh(claim)

        action = "reassigned" if previous_assignee else "assigned"
        logger.info(
            f"Claim {claim.id} {action} to user {assigned_to} by user {assigned_by}"
        )

        return claim

    @staticmethod
    async def set_compensation(
        session: AsyncSession,
        claim: Claim,
        compensation_amount: float,
        set_by: UUID,
        reason: Optional[str] = None
    ) -> Claim:
        """
        Set or update compensation amount for a claim.

        Args:
            session: Database session
            claim: Claim instance
            compensation_amount: Compensation amount in EUR
            set_by: ID of user setting the compensation
            reason: Reason for the compensation amount

        Returns:
            Updated claim instance
        """
        from decimal import Decimal

        previous_amount = claim.compensation_amount
        claim.compensation_amount = Decimal(str(compensation_amount))

        # If calculated compensation differs from set amount, add note
        if claim.calculated_compensation and claim.calculated_compensation != claim.compensation_amount:
            logger.warning(
                f"Manual compensation amount (€{compensation_amount}) differs from "
                f"calculated amount (€{claim.calculated_compensation}) for claim {claim.id}"
            )

        await session.flush()
        await session.refresh(claim)

        action = "updated" if previous_amount else "set"
        logger.info(
            f"Claim {claim.id} compensation {action} to €{compensation_amount} by user {set_by}"
        )

        return claim

    @staticmethod
    def get_status_display_info(status: str) -> Dict:
        """
        Get display information for a status.

        Args:
            status: Claim status

        Returns:
            Dictionary with display information:
            {
                "label": str,
                "color": str,
                "icon": str,
                "description": str
            }
        """
        status_info = {
            Claim.STATUS_DRAFT: {
                "label": "Draft",
                "color": "gray",
                "icon": "📝",
                "description": "Claim is being prepared"
            },
            Claim.STATUS_SUBMITTED: {
                "label": "Submitted",
                "color": "blue",
                "icon": "📨",
                "description": "Claim has been submitted and awaiting review"
            },
            Claim.STATUS_UNDER_REVIEW: {
                "label": "Under Review",
                "color": "yellow",
                "icon": "🔍",
                "description": "Claim is being reviewed by an administrator"
            },
            Claim.STATUS_APPROVED: {
                "label": "Approved",
                "color": "green",
                "icon": "✅",
                "description": "Claim has been approved for compensation"
            },
            Claim.STATUS_REJECTED: {
                "label": "Rejected",
                "color": "red",
                "icon": "❌",
                "description": "Claim has been rejected"
            },
            Claim.STATUS_PAID: {
                "label": "Paid",
                "color": "purple",
                "icon": "💰",
                "description": "Compensation has been paid"
            },
            Claim.STATUS_CLOSED: {
                "label": "Closed",
                "color": "dark-gray",
                "icon": "🔒",
                "description": "Claim has been closed"
            }
        }

        return status_info.get(status, {
            "label": status.replace("_", " ").title(),
            "color": "gray",
            "icon": "📋",
            "description": "Unknown status"
        })
