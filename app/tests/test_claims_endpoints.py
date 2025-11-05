"""Tests for claims endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Customer, Claim
from app.repositories import ClaimRepository


@pytest.mark.asyncio
class TestClaimsEndpoints:
    """Test claims endpoints."""

    async def test_create_claim(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_customer: Customer
    ):
        """Test creating a new claim."""
        claim_data = {
            "flightInfo": {
                "flightNumber": "LH1234",
                "airline": "Lufthansa",
                "departureDate": "2025-06-15",
                "departureAirport": "FRA",
                "arrivalAirport": "JFK"
            },
            "incidentType": "delay",
            "notes": "Flight delayed by 3 hours"
        }

        response = await client.post("/claims/", json=claim_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["customerId"] == str(test_customer.id)
        assert data["flightNumber"] == claim_data["flightInfo"]["flightNumber"]
        assert data["incidentType"] == claim_data["incidentType"]

    async def test_create_claim_unauthorized(self, client: AsyncClient):
        """Test creating claim without authentication."""
        claim_data = {
            "flightInfo": {
                "flightNumber": "LH1234",
                "airline": "Lufthansa",
                "departureDate": "2025-06-15",
                "departureAirport": "FRA",
                "arrivalAirport": "JFK"
            },
            "incidentType": "delay"
        }

        response = await client.post("/claims/", json=claim_data)

        assert response.status_code == 401

    async def test_submit_claim_with_customer(self, client: AsyncClient):
        """Test submitting a claim with customer info (creates customer if needed)."""
        claim_request = {
            "customerInfo": {
                "email": "newclaim@example.com",
                "firstName": "New",
                "lastName": "Claimant",
                "phone": "+1234567890"
            },
            "flightInfo": {
                "flightNumber": "BA5678",
                "airline": "British Airways",
                "departureDate": "2025-07-20",
                "departureAirport": "LHR",
                "arrivalAirport": "CDG"
            },
            "incidentType": "cancellation",
            "notes": "Flight cancelled"
        }

        response = await client.post("/claims/submit", json=claim_request)

        assert response.status_code == 201
        data = response.json()
        assert data["flightNumber"] == claim_request["flightInfo"]["flightNumber"]
        assert data["incidentType"] == claim_request["incidentType"]

    async def test_get_claim(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test getting a claim by ID."""
        # Create a claim first
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

        response = await client.get(f"/claims/{claim.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(claim.id)
        assert data["customerId"] == str(test_customer.id)

    async def test_get_claim_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting a non-existent claim."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/claims/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    async def test_get_claim_unauthorized_access(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_customer: Customer,
        test_admin: Customer
    ):
        """Test accessing another user's claim (should be denied for customers)."""
        # Create claim for admin
        claim_repo = ClaimRepository(db_session)
        admin_claim = await claim_repo.create_claim(
            customer_id=test_admin.id,
            flight_number="BA9999",
            airline="British Airways",
            departure_date="2025-08-01",
            departure_airport="LHR",
            arrival_airport="JFK",
            incident_type="delay"
        )
        await db_session.commit()

        # Try to access with customer token
        from app.services.auth_service import AuthService
        customer_token = AuthService.create_access_token(
            user_id=test_customer.id,
            email=test_customer.email,
            role=test_customer.role
        )
        headers = {"Authorization": f"Bearer {customer_token}"}

        response = await client.get(f"/claims/{admin_claim.id}", headers=headers)

        assert response.status_code == 403

    async def test_list_claims(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test listing claims."""
        # Create a few claims
        claim_repo = ClaimRepository(db_session)
        for i in range(3):
            await claim_repo.create_claim(
                customer_id=test_customer.id,
                flight_number=f"LH{1234 + i}",
                airline="Lufthansa",
                departure_date="2025-06-15",
                departure_airport="FRA",
                arrival_airport="JFK",
                incident_type="delay"
            )
        await db_session.commit()

        response = await client.get("/claims/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    async def test_list_claims_with_filters(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing claims with status filter."""
        response = await client.get(
            "/claims/?status=submitted&limit=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_update_claim_put(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test updating a claim with PUT (complete update)."""
        # Create a claim
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

        # Update it
        update_data = {
            "customerId": str(test_customer.id),
            "flightInfo": {
                "flightNumber": "LH5678",
                "airline": "Lufthansa",
                "departureDate": "2025-07-01",
                "departureAirport": "MUC",
                "arrivalAirport": "LAX"
            },
            "incidentType": "cancellation",
            "notes": "Updated notes"
        }

        response = await client.put(
            f"/claims/{claim.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["flightNumber"] == "LH5678"
        assert data["incidentType"] == "cancellation"

    async def test_update_claim_patch(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test updating a claim with PATCH (partial update)."""
        # Create a claim
        claim_repo = ClaimRepository(db_session)
        claim = await claim_repo.create_claim(
            customer_id=test_customer.id,
            flight_number="LH1234",
            airline="Lufthansa",
            departure_date="2025-06-15",
            departure_airport="FRA",
            arrival_airport="JFK",
            incident_type="delay",
            notes="Original notes"
        )
        await db_session.commit()

        # Partially update it
        patch_data = {
            "notes": "Updated notes only"
        }

        response = await client.patch(
            f"/claims/{claim.id}",
            json=patch_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes only"
        assert data["flightNumber"] == "LH1234"  # Should remain unchanged

    async def test_get_claims_by_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test getting claims by status."""
        # Create a claim
        claim_repo = ClaimRepository(db_session)
        await claim_repo.create_claim(
            customer_id=test_customer.id,
            flight_number="LH1234",
            airline="Lufthansa",
            departure_date="2025-06-15",
            departure_airport="FRA",
            arrival_airport="JFK",
            incident_type="delay"
        )
        await db_session.commit()

        response = await client.get("/claims/status/submitted", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_customer_claims(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_customer: Customer
    ):
        """Test getting all claims for a customer."""
        # Create claims
        claim_repo = ClaimRepository(db_session)
        for i in range(2):
            await claim_repo.create_claim(
                customer_id=test_customer.id,
                flight_number=f"LH{1234 + i}",
                airline="Lufthansa",
                departure_date="2025-06-15",
                departure_airport="FRA",
                arrival_airport="JFK",
                incident_type="delay"
            )
        await db_session.commit()

        response = await client.get(
            f"/claims/customer/{test_customer.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
