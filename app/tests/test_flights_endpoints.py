"""Tests for flights endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestFlightsEndpoints:
    """Test flight lookup endpoints."""

    async def test_get_flight_status(self, client: AsyncClient):
        """Test getting flight status (mock data)."""
        response = await client.get("/flights/status/BA123?date=2024-01-15")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert data["data"]["flightNumber"] == "BA123"
        assert "delay" in data["data"]

    async def test_get_flight_status_different_airline(self, client: AsyncClient):
        """Test getting flight status for different airline."""
        response = await client.get("/flights/status/LH456?date=2024-02-20")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["flightNumber"] == "LH456"

    async def test_get_flight_status_invalid_format(self, client: AsyncClient):
        """Test getting flight status with invalid flight number format."""
        response = await client.get("/flights/status/INVALID?date=2024-01-15")

        assert response.status_code == 404

    async def test_get_flight_status_missing_date(self, client: AsyncClient):
        """Test getting flight status without date parameter."""
        response = await client.get("/flights/status/BA123")

        assert response.status_code == 422  # Validation error

    async def test_get_flight_status_with_refresh(self, client: AsyncClient):
        """Test getting flight status with refresh parameter."""
        response = await client.get("/flights/status/AA789?date=2024-03-10&refresh=true")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
