"""Tests for Health Check and Root API endpoints."""


def test_root_endpoint(client):
    """Verify root info endpoint returns 200 OK and valid metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Merchant Risk Sentinel"
    assert data["status"] == "online"


def test_health_check_endpoint(client):
    """Verify /api/v1/health returns 200 OK and healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"
