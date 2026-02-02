import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_config

client = TestClient(app)
config = get_config()

def test_trusted_hosts_allowed():
    """Test that allowed hosts can access the API."""
    # We use /info because /health might try to connect to the database and fail with 503
    for host in config.ALLOWED_HOSTS:
        # Test with the host header
        response = client.get("/info", headers={"Host": host})
        assert response.status_code == 200

def test_trusted_hosts_forbidden():
    """Test that unauthorized hosts are rejected."""
    unauthorized_host = "malicious-domain.com"
    # Ensure it's not in the allowed list
    if unauthorized_host in config.ALLOWED_HOSTS:
        pytest.skip(f"{unauthorized_host} is in ALLOWED_HOSTS, cannot test rejection")
    
    response = client.get("/info", headers={"Host": unauthorized_host})
    # TrustedHostMiddleware returns 400 Bad Request for invalid hosts
    assert response.status_code == 400

def test_security_headers():
    """Test that security headers are present in the response."""
    # testserver is the default host for TestClient, we need to make sure it's allowed or use an allowed host
    response = client.get("/info", headers={"Host": "localhost"})
    assert response.status_code == 200
    
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers
    assert "Permissions-Policy" in response.headers
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"

def test_cors_headers():
    """Test CORS configuration."""
    origin = config.CORS_ORIGINS[0] if config.CORS_ORIGINS else "http://localhost:3000"
    
    # Preflight request
    response = client.options(
        "/info",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
            "Host": "localhost"
        }
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"

def test_invalid_cors_origin():
    """Test that invalid CORS origins are not allowed."""
    invalid_origin = "http://malicious-site.com"
    if invalid_origin in config.CORS_ORIGINS:
        pytest.skip(f"{invalid_origin} is in CORS_ORIGINS, cannot test rejection")
        
    response = client.get(
        "/health",
        headers={"Origin": invalid_origin}
    )
    # CORSMiddleware doesn't return 403 for invalid origin, it just doesn't include the CORS headers
    assert "access-control-allow-origin" not in response.headers
