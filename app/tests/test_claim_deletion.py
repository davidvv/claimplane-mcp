"""Tests for claim deletion endpoint."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import date

from app.models import Customer, Claim
from app.repositories import ClaimRepository


@pytest.mark.asyncio
class TestClaimDeletion:
    """Test claim deletion endpoints."""

    async def test_delete_draft_claim(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test deleting a draft claim as customer."""
        # Create a draft claim
        claim_repo = ClaimRepository(db_session)
        claim = await claim_repo.create_draft_claim(
            customer_id=test_customer.id,
            flight_number="LH1234",
            airline="Lufthansa",
            departure_date=date(2025, 6, 15),
            departure_airport="FRA",
            arrival_airport="JFK",
            incident_type="delay"
        )
        await db_session.commit()

        # Delete it
        response = await client.delete(f"/claims/{claim.id}", headers=auth_headers)

        assert response.status_code == 204
        
        # Verify it's gone
        deleted_claim = await claim_repo.get_by_id(claim.id)
        assert deleted_claim is None

    async def test_delete_submitted_claim_customer_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test customer cannot delete submitted claim."""
        # Create a submitted claim
        claim_repo = ClaimRepository(db_session)
        claim = await claim_repo.create_claim(
            customer_id=test_customer.id,
            flight_number="LH1234",
            airline="Lufthansa",
            departure_date=date(2025, 6, 15),
            departure_airport="FRA",
            arrival_airport="JFK",
            incident_type="delay"
        )
        # Manually ensure status is SUBMITTED
        claim.status = Claim.STATUS_SUBMITTED
        await db_session.commit()

        # Try to delete it
        response = await client.delete(f"/claims/{claim.id}", headers=auth_headers)

        assert response.status_code == 403
        
        # Verify it's still there
        existing_claim = await claim_repo.get_by_id(claim.id)
        assert existing_claim is not None

    async def test_delete_claim_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test deleting non-existent claim."""
        fake_id = uuid4()
        response = await client.delete(f"/claims/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
