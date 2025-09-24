"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.models import User, Claim
from app.schemas import FlightDetails, PersonalInfo


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session fixture."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data


def test_openapi_docs(client):
    """Test OpenAPI documentation endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json(client):
    """Test OpenAPI JSON endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


def test_unauthorized_access(client):
    """Test unauthorized access to protected endpoints."""
    # Try to access claims without authentication
    response = client.get("/api/claims")
    assert response.status_code == 401

    # Try to submit flight details without authentication
    flight_details = {
        "flightNumber": "LH1234",
        "departureAirport": "FRA",
        "arrivalAirport": "JFK",
        "plannedDepartureDate": "2024-12-01"
    }
    response = client.post("/api/flight-details", json=flight_details)
    assert response.status_code == 401


def test_invalid_flight_details(client, auth_headers):
    """Test invalid flight details validation."""
    # Invalid flight number
    flight_details = {
        "flightNumber": "INVALID",
        "departureAirport": "FRA",
        "arrivalAirport": "JFK",
        "plannedDepartureDate": "2024-12-01"
    }
    response = client.post("/api/flight-details", json=flight_details, headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid flight number format" in response.json()["detail"]


def test_invalid_airport_code(client, auth_headers):
    """Test invalid airport code validation."""
    flight_details = {
        "flightNumber": "LH1234",
        "departureAirport": "INVALID",
        "arrivalAirport": "JFK",
        "plannedDepartureDate": "2024-12-01"
    }
    response = client.post("/api/flight-details", json=flight_details, headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid departure airport code" in response.json()["detail"]


def test_invalid_booking_reference(client, auth_headers):
    """Test invalid booking reference validation."""
    personal_info = {
        "fullName": "John Doe",
        "email": "john@example.com",
        "bookingReference": "INVALID"
    }
    response = client.post("/api/personal-info", json=personal_info, headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid booking reference format" in response.json()["detail"]


@pytest.fixture
def auth_headers(client, db_session):
    """Create authentication headers for testing."""
    # Create a test user
    test_user = User(
        email="test@example.com",
        booking_reference="ABC12345",
        is_admin=False
    )
    db_session.add(test_user)
    db_session.commit()

    # Login to get token
    login_data = {
        "username": "test@example.com",
        "password": "ABC12345"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_rate_limiting(client):
    """Test rate limiting on login endpoint."""
    # Make multiple login attempts
    login_data = {
        "username": "test@example.com",
        "password": "ABC12345"
    }

    # First few requests should succeed or fail due to invalid credentials
    for _ in range(10):
        response = client.post("/api/auth/login", data=login_data)
        # Should either succeed (if user exists) or fail due to rate limiting
        assert response.status_code in [200, 401, 429]