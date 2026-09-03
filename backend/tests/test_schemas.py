"""Tests for transaction schemas and risk scoring endpoint."""

def test_risk_assessment_endpoint_low_risk(client):
    """Test risk assessment endpoint with normal transaction metrics."""
    payload = {
        "raw_data": {
            "transaction_id": "txn_test_1001",
            "merchant_id": "merch_99",
            "customer_id": "cust_123",
            "amount": 500.0,
            "currency": "INR",
            "payment_method": "upi",
            "transaction_status": "captured"
        },
        "derived_features": {
            "txn_velocity_1h": 1,
            "txn_velocity_24h": 2,
            "amount_ratio_merchant_avg": 0.8,
            "failed_attempts_30m": 0,
            "customer_account_age_days": 45.0,
            "geo_ip_distance_km": 12.0
        }
    }

    response = client.post("/api/v1/risk/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "txn_test_1001"
    assert data["merchant_id"] == "merch_99"
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_tier"] == "LOW"
    assert data["is_suspicious"] is False
    assert len(data["signal_explanations"]) > 0


def test_risk_assessment_endpoint_high_velocity_burst(client):
    """Test risk assessment endpoint with high velocity burst triggering elevated risk."""
    payload = {
        "raw_data": {
            "transaction_id": "txn_burst_2002",
            "merchant_id": "merch_99",
            "customer_id": "cust_999",
            "amount": 25000.0,
            "currency": "INR",
            "payment_method": "card",
            "transaction_status": "captured"
        },
        "derived_features": {
            "txn_velocity_1h": 12,
            "txn_velocity_24h": 20,
            "amount_ratio_merchant_avg": 5.5,
            "failed_attempts_30m": 4,
            "customer_account_age_days": 0.1,
            "geo_ip_distance_km": 1200.0
        }
    }

    response = client.post("/api/v1/risk/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "txn_burst_2002"
    assert data["risk_tier"] in ["HIGH", "CRITICAL"]
    assert data["is_suspicious"] is True
    assert "defensive_recommendation" in data
    assert len(data["signal_explanations"]) >= 3


def test_evaluation_status_endpoint(client):
    """Test evaluation diagnostic status endpoint."""
    response = client.get("/api/v1/risk/evaluation-status")
    assert response.status_code == 200
    data = response.json()
    assert data["evaluation_scope"] == "HELD_OUT_TEST_SET"
    assert "metrics" in data
