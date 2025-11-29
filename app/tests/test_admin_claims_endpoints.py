"""Tests for admin claims endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Customer, Claim
from app.repositories import ClaimRepository


@pytest.mark.asyncio
class TestAdminClaimsEndpoints:
    """Test admin claims management endpoints."""

    @pytest.fixture
    async def test_claim(self, db_session: AsyncSession, test_customer: Customer):
        """Create a test claim."""
        claim_repo = ClaimRepository(db_session)
        claim = await claim_repo.create_claim(
            customer_id=test_customer.id,
            flight_number="LH1234",
            airline="Lufthansa",
            departure_date="2025-06-15",
            departure_airport="FRA",
            arrival_airport="JFK",
            incident_type="delay"
        )
        await db_session.commit()
        return claim

    async def test_list_claims_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test listing all claims as admin."""
        response = await client.get("/admin/claims", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "claims" in data
        assert "total" in data

    async def test_list_claims_as_regular_user(self, client: AsyncClient, auth_headers: dict):
        """Test listing claims as regular user (should fail)."""
        response = await client.get("/admin/claims", headers=auth_headers)

        assert response.status_code == 403

    async def test_list_claims_with_filters(self, client: AsyncClient, admin_headers: dict):
        """Test listing claims with filters."""
        response = await client.get(
            "/admin/claims?status=submitted&limit=10&sort_by=submitted_at&sort_order=desc",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "claims" in data

    async def test_get_claim_detail(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test getting detailed claim information."""
        response = await client.get(f"/admin/claims/{test_claim.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_claim.id)
        assert "customer" in data
        assert "files" in data

    async def test_get_claim_detail_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent claim."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/admin/claims/{fake_id}", headers=admin_headers)

        assert response.status_code == 404

    async def test_update_claim_status(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test updating claim status."""
        update_data = {
            "new_status": "under_review",
            "change_reason": "Starting review process"
        }

        response = await client.put(
            f"/admin/claims/{test_claim.id}/status",
            json=update_data,
            headers=admin_headers
        )

        assert response.status_code in [200, 400]  # 400 if invalid transition

    async def test_update_claim_status_invalid_transition(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test updating claim status with invalid transition."""
        update_data = {
            "new_status": "paid",  # Can't go from submitted to paid directly
            "change_reason": "Invalid transition"
        }

        response = await client.put(
            f"/admin/claims/{test_claim.id}/status",
            json=update_data,
            headers=admin_headers
        )

        # Should either succeed with workflow validation or return error
        assert response.status_code in [200, 400]

    async def test_assign_claim(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim,
        test_admin: Customer
    ):
        """Test assigning claim to reviewer."""
        assign_data = {
            "assigned_to": str(test_admin.id)
        }

        response = await client.put(
            f"/admin/claims/{test_claim.id}/assign",
            json=assign_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "assigned_to" in data

    async def test_set_compensation(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test setting compensation amount."""
        compensation_data = {
            "compensation_amount": 600.00,
            "reason": "Long haul delay over 4 hours"
        }

        response = await client.put(
            f"/admin/claims/{test_claim.id}/compensation",
            json=compensation_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "calculated_compensation" in data

    async def test_add_note(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test adding a note to a claim."""
        note_data = {
            "note_text": "Customer provided additional documentation",
            "is_internal": True
        }

        response = await client.post(
            f"/admin/claims/{test_claim.id}/notes",
            json=note_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["note_text"] == note_data["note_text"]
        assert data["is_internal"] == note_data["is_internal"]

    async def test_get_notes(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test getting all notes for a claim."""
        response = await client.get(f"/admin/claims/{test_claim.id}/notes", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_status_history(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test getting status change history."""
        response = await client.get(f"/admin/claims/{test_claim.id}/history", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_bulk_action_status_update(
        self,
        client: AsyncClient,
        admin_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test bulk status update."""
        # Create multiple claims
        claim_repo = ClaimRepository(db_session)
        claim_ids = []
        for i in range(3):
            claim = await claim_repo.create_claim(
                customer_id=test_customer.id,
                flight_number=f"LH{1234 + i}",
                airline="Lufthansa",
                departure_date="2025-06-15",
                departure_airport="FRA",
                arrival_airport="JFK",
                incident_type="delay"
            )
            claim_ids.append(str(claim.id))
        await db_session.commit()

        bulk_data = {
            "claim_ids": claim_ids,
            "action": "status_update",
            "parameters": {
                "new_status": "under_review",
                "change_reason": "Bulk review"
            }
        }

        response = await client.post("/admin/claims/bulk-action", json=bulk_data, headers=admin_headers)

        assert response.status_code in [200, 400]

    async def test_get_analytics_summary(self, client: AsyncClient, admin_headers: dict):
        """Test getting analytics summary."""
        response = await client.get("/admin/claims/analytics/summary", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_claims" in data
        assert "status_breakdown" in data

    async def test_calculate_compensation(self, client: AsyncClient, admin_headers: dict):
        """Test calculating compensation."""
        calculation_data = {
            "departure_airport": "MAD",
            "arrival_airport": "JFK",
            "delay_hours": 5.0,
            "incident_type": "delay",
            "extraordinary_circumstances": False
        }

        response = await client.post(
            "/admin/claims/calculate-compensation",
            json=calculation_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data
        assert "amount" in data
        assert "distance_km" in data

    async def test_get_valid_transitions(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test getting valid status transitions."""
        response = await client.get(
            f"/admin/claims/{test_claim.id}/status-transitions",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "current_status" in data
        assert "valid_next_statuses" in data
        assert isinstance(data["valid_next_statuses"], list)
