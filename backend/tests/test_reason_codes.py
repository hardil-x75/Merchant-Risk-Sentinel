"""Tests verifying deterministic risk reason codes match feature matrix values."""

import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

from app.ml.inference import SentinelInferenceEngine
from app.schemas.transaction import (
    RiskAssessmentRequest,
    RawTransactionSignals,
    DerivedTransactionFeatures,
)


def test_deterministic_reason_codes_matching_features():
    """Verify reason codes directly correspond to elevated velocity, failure count, and email flags."""
    engine = SentinelInferenceEngine()

    request = RiskAssessmentRequest(
        raw_data=RawTransactionSignals(
            transaction_id="txn_reason_01",
            merchant_id="merch_10",
            customer_id="cust_99",
            amount=15000.0,
            currency="INR",
            payment_method="card",
            email_domain="tempmail.com",
            billing_country="US",
        ),
        derived_features=DerivedTransactionFeatures(
            txn_velocity_1h=8,
            txn_velocity_24h=15,
            amount_ratio_merchant_avg=4.5,
            failed_attempts_30m=4,
        ),
    )

    response = engine.predict_risk(request)

    assert response.transaction_id == "txn_reason_01"
    assert response.is_suspicious is True

    reason_texts = [sig.description for sig in response.signal_explanations]

    assert any("1-hour transaction velocity" in r for r in reason_texts), "Must explain high 1-hour velocity"
    assert any("failed payment attempts" in r for r in reason_texts), "Must explain high failed attempt burst"
    assert any("higher than merchant historical average" in r for r in reason_texts), "Must explain high amount ratio"
    assert any("disposable email domain" in r.lower() for r in reason_texts), "Must explain disposable email"
    assert any("non-domestic billing country" in r.lower() for r in reason_texts), "Must explain non-domestic country"
