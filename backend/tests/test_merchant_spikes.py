"""Tests for Merchant-Level Fraud Spike Aggregator and Anomaly Detector."""

import os
import sys
import numpy as np
import pandas as pd

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

from app.ml.merchant_spike_detector import MerchantSpikeDetector


def test_merchant_spike_detection_alert():
    """Verify detector triggers spike alert when high-risk ratio and failure rates surge."""
    detector = MerchantSpikeDetector(risk_threshold=0.50)

    txns = [
        {"merchant_id": "m_normal", "amount": 1000.0, "transaction_status": "captured"},
        {"merchant_id": "m_normal", "amount": 1200.0, "transaction_status": "captured"},
        {"merchant_id": "m_normal", "amount": 1100.0, "transaction_status": "captured"},

        {"merchant_id": "m_spiking", "amount": 5000.0, "transaction_status": "failed"},
        {"merchant_id": "m_spiking", "amount": 8000.0, "transaction_status": "failed"},
        {"merchant_id": "m_spiking", "amount": 9000.0, "transaction_status": "failed"},
        {"merchant_id": "m_spiking", "amount": 12000.0, "transaction_status": "captured"},
    ]

    df = pd.DataFrame(txns)
    risk_scores = np.array([0.05, 0.05, 0.05, 0.85, 0.90, 0.75, 0.80])

    reports = detector.analyze_merchant_spikes(df, risk_scores=risk_scores)

    assert len(reports) == 2

    spiking_report = next(r for r in reports if r["merchant_id"] == "m_spiking")
    normal_report = next(r for r in reports if r["merchant_id"] == "m_normal")

    assert spiking_report["is_spike_alert"] is True
    assert len(spiking_report["spike_reasons"]) > 0
    assert normal_report["is_spike_alert"] is False
