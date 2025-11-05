"""Tests for health check endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    async def test_database_health(self, client: AsyncClient):
        """Test detailed database health check."""
        response = await client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "version" in data["database"]
        assert "name" in data["database"]
        assert "user" in data["database"]

    async def test_detailed_health_check(self, client: AsyncClient):
        """Test detailed health check with system information."""
        response = await client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data
        assert "system" in data
        assert "database" in data
        assert "python_version" in data["system"]
        assert "platform" in data["system"]
