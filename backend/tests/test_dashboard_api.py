"""Automated Integration Tests for Step 3 Dashboard Backend Endpoints."""


def test_get_transactions_endpoint(client):
    """Verify /api/v1/risk/transactions returns paginated transactions and valid schema."""
    response = client.get("/api/v1/risk/transactions?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert "total_count" in data
    assert len(data["transactions"]) <= 10
    if len(data["transactions"]) > 0:
        txn = data["transactions"][0]
        assert "transaction_id" in txn
        assert "risk_score" in txn
        assert "risk_tier" in txn
        assert "decision" in txn


def test_get_timeline_endpoint(client):
    """Verify /api/v1/risk/timeline returns time-series points."""
    response = client.get("/api/v1/risk/timeline")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        pt = data[0]
        assert "date" in pt
        assert "avg_risk_score" in pt
        assert "transaction_count" in pt


def test_get_feature_importance_endpoint(client):
    """Verify /api/v1/risk/feature-importance returns ranked feature list."""
    response = client.get("/api/v1/risk/feature-importance")
    assert response.status_code == 200
    data = response.json()
    assert "feature_importances" in data
    assert len(data["feature_importances"]) > 0
    first = data["feature_importances"][0]
    assert "feature_name" in first
    assert "importance" in first


def test_get_audit_log_endpoint(client):
    """Verify /api/v1/risk/audit-log returns event items."""
    response = client.get("/api/v1/risk/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    event = data[0]
    assert "event_type" in event
    assert "system_decision" in event
