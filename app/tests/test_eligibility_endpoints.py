"""Tests for eligibility check endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestEligibilityEndpoints:
    """Test eligibility check endpoints."""

    async def test_check_eligibility_short_haul_delay(self, client: AsyncClient):
        """Test eligibility check for short haul delayed flight."""
        eligibility_data = {
            "departure_airport": "LHR",
            "arrival_airport": "CDG",
            "delay_hours": 4.0,
            "incident_type": "delay"
        }

        response = await client.post("/eligibility/check", json=eligibility_data)

        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data
        assert "amount" in data
        assert "distance_km" in data
        assert "reason" in data
        assert "requires_manual_review" in data

    async def test_check_eligibility_long_haul_cancellation(self, client: AsyncClient):
        """Test eligibility check for long haul cancelled flight."""
        eligibility_data = {
            "departure_airport": "MAD",
            "arrival_airport": "JFK",
            "delay_hours": None,
            "incident_type": "cancellation"
        }

        response = await client.post("/eligibility/check", json=eligibility_data)

        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data
        assert "amount" in data
        # Long haul should have higher compensation
        if data["eligible"]:
            assert float(data["amount"]) >= 400

    async def test_check_eligibility_invalid_airport_code(self, client: AsyncClient):
        """Test eligibility check with invalid airport codes."""
        eligibility_data = {
            "departure_airport": "XXX",
            "arrival_airport": "YYY",
            "delay_hours": 4.0,
            "incident_type": "delay"
        }

        response = await client.post("/eligibility/check", json=eligibility_data)

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    async def test_check_eligibility_denied_boarding(self, client: AsyncClient):
        """Test eligibility check for denied boarding."""
        eligibility_data = {
            "departure_airport": "BCN",
            "arrival_airport": "LHR",
            "delay_hours": None,
            "incident_type": "denied_boarding"
        }

        response = await client.post("/eligibility/check", json=eligibility_data)

        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data

    async def test_check_eligibility_baggage_delay(self, client: AsyncClient):
        """Test eligibility check for baggage delay."""
        eligibility_data = {
            "departure_airport": "FRA",
            "arrival_airport": "IST",
            "delay_hours": 3.0,
            "incident_type": "baggage_delay"
        }

        response = await client.post("/eligibility/check", json=eligibility_data)

        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data

    async def test_check_eligibility_missing_fields(self, client: AsyncClient):
        """Test eligibility check with missing required fields."""
        eligibility_data = {
            "departure_airport": "MAD"
            # Missing other required fields
        }

        response = await client.post("/eligibility/check", json=eligibility_data)

        assert response.status_code == 422
