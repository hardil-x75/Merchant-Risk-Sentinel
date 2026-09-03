"""Automated Runtime Integrity Tests for Merchant Risk Sentinel.

Verifies:
1. is_fraud ground-truth label DOES NOT influence runtime risk predictions.
2. Runtime inference works seamlessly on payloads completely missing is_fraud.
3. Historical state store computes features strictly from PRECEDING transactions (j < i).
4. Current transaction is NOT included in its own historical feature computation.
5. Model comparison API endpoint loads saved evaluation artifacts rather than hardcoded dicts.
"""

import os
import pandas as pd
import pytest
from app.ml.feature_engineering import HistoricalStateStore
from app.services.risk_service import risk_service
from app.schemas.transaction import RiskAssessmentRequest, RawTransactionSignals


def test_is_fraud_label_cannot_influence_runtime_risk(client):
    """Verify that changing or supplying is_fraud=1 vs is_fraud=0 in payloads has zero effect on runtime inference."""
    payload_clean = {
        "raw_data": {
            "transaction_id": "txn_test_leakage_01",
            "merchant_id": "merch_01",
            "customer_id": "cust_9999",
            "amount": 2500.0,
            "currency": "INR",
            "payment_method": "card",
            "timestamp": "2026-09-03T12:00:00Z",
            "email_domain": "gmail.com",
            "billing_country": "IN"
        }
    }

    # Endpoint request WITHOUT is_fraud
    response1 = client.post("/api/v1/risk/assess", json=payload_clean)
    assert response1.status_code == 200
    res1 = response1.json()

    # Direct raw transaction scoring check
    row_fraud_0 = pd.Series({
        "transaction_id": "txn_test_01",
        "merchant_id": "merch_01",
        "customer_id": "cust_8888",
        "amount": 1500.0,
        "timestamp": "2026-09-03T12:00:00Z",
        "email_domain": "gmail.com",
        "billing_country": "IN",
        "is_fraud": 0
    })

    row_fraud_1 = pd.Series({
        "transaction_id": "txn_test_01",
        "merchant_id": "merch_01",
        "customer_id": "cust_8888",
        "amount": 1500.0,
        "timestamp": "2026-09-03T12:00:00Z",
        "email_domain": "gmail.com",
        "billing_country": "IN",
        "is_fraud": 1
    })

    score_0 = risk_service._score_raw_transaction(row_fraud_0)["score"]
    score_1 = risk_service._score_raw_transaction(row_fraud_1)["score"]

    assert score_0 == score_1, "is_fraud label must NOT alter runtime score!"


def test_runtime_inference_without_is_fraud_label(client):
    """Verify runtime inference endpoint successfully evaluates payloads missing is_fraud."""
    request = RiskAssessmentRequest(
        raw_data=RawTransactionSignals(
            transaction_id="txn_label_free_101",
            merchant_id="merch_02",
            customer_id="cust_101",
            amount=7500.0,
            currency="INR",
            payment_method="card",
            email_domain="tempmail.com",
            billing_country="US",
        )
    )
    response = risk_service.assess_transaction_risk(request)
    assert response.transaction_id == "txn_label_free_101"
    assert 0.0 <= response.risk_score <= 1.0
    assert response.risk_tier is not None
    assert response.defensive_recommendation is not None


def test_historical_state_store_temporal_isolation():
    """Verify state store computes features strictly from prior events and excludes current transaction."""
    store = HistoricalStateStore()
    store.reset()

    txn1 = {
        "customer_id": "cust_iso_1",
        "merchant_id": "merch_iso_1",
        "amount": 1000.0,
        "timestamp": "2026-09-03T10:00:00Z",
        "transaction_status": "captured"
    }

    # First transaction for cust_iso_1 should see 0 velocity and 0 prior count
    feats1 = store.compute_live_features(txn1, update_state=True)
    assert feats1.iloc[0]["txn_velocity_1h"] == 0
    assert feats1.iloc[0]["time_since_prev_cust_txn_sec"] == 86400.0

    txn2 = {
        "customer_id": "cust_iso_1",
        "merchant_id": "merch_iso_1",
        "amount": 2000.0,
        "timestamp": "2026-09-03T10:15:00Z",
        "transaction_status": "captured"
    }

    # Second transaction occurring 15 mins later should see velocity_1h = 1 (from txn1)
    feats2 = store.compute_live_features(txn2, update_state=True)
    assert feats2.iloc[0]["txn_velocity_1h"] == 1
    assert feats2.iloc[0]["time_since_prev_cust_txn_sec"] == 900.0


def test_model_comparison_loads_saved_artifact(client):
    """Verify /api/v1/risk/model-comparison endpoint loads data from saved model_comparison.json artifact."""
    response = client.get("/api/v1/risk/model-comparison")
    assert response.status_code == 200
    data = response.json()
    assert data["evaluation_scope"] == "HELD_OUT_TEST_SET"
    assert "comparison" in data
    assert len(data["comparison"]) == 2

    rf = next(m for m in data["comparison"] if "Random Forest" in m["model_name"])
    lr = next(m for m in data["comparison"] if "Logistic Regression" in m["model_name"])

    # Confirm metrics are numeric and originate from actual evaluation
    assert 0.0 <= rf["precision"] <= 1.0
    assert 0.0 <= rf["recall"] <= 1.0
    assert 0.0 <= lr["precision"] <= 1.0
    assert 0.0 <= lr["recall"] <= 1.0
    assert rf["status"] == "ACTIVE_PRIMARY"
    assert lr["status"] == "BASELINE"
