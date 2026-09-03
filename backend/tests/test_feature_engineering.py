"""Tests for Chronological Splitter and Feature Engineering No-Future-Data-Leakage Guarantee."""

import os
import sys
import pandas as pd
import numpy as np

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

from app.ml.loader import TransactionDataLoader
from app.ml.feature_engineering import TransactionFeatureEngineer


def test_chronological_split_ordering():
    """Verify chronological split strictly isolates time boundaries: train_max <= val_min <= test_min."""
    loader = TransactionDataLoader()

    raw_data = []
    base_time = pd.Timestamp("2026-08-01 00:00:00")
    for i in range(100):
        raw_data.append({
            "transaction_id": f"txn_{i:03d}",
            "merchant_id": "merch_01",
            "customer_id": f"cust_{i % 5:02d}",
            "amount": 1000.0 + i,
            "timestamp": (base_time + pd.Timedelta(hours=i)).isoformat(),
            "transaction_status": "captured",
            "is_fraud": 1 if i in [20, 50, 80] else 0,
        })

    df = pd.DataFrame(raw_data)
    train_df, val_df, test_df = loader.split_chronological(df, train_ratio=0.60, val_ratio=0.20)

    assert len(train_df) == 60
    assert len(val_df) == 20
    assert len(test_df) == 20

    t_train_max = pd.to_datetime(train_df["timestamp"]).max()
    t_val_min = pd.to_datetime(val_df["timestamp"]).min()
    t_val_max = pd.to_datetime(val_df["timestamp"]).max()
    t_test_min = pd.to_datetime(test_df["timestamp"]).min()

    assert t_train_max <= t_val_min, "Train timestamps must be <= Validation timestamps"
    assert t_val_max <= t_test_min, "Validation timestamps must be <= Held-Out Test timestamps"


def test_feature_engineering_no_future_leakage():
    """Verify that inserting future transactions does NOT modify feature values for past transactions."""
    fe = TransactionFeatureEngineer()

    base_time = pd.Timestamp("2026-08-01 10:00:00")
    initial_txns = [
        {
            "transaction_id": "txn_001",
            "merchant_id": "m1",
            "customer_id": "c1",
            "amount": 1000.0,
            "timestamp": (base_time).isoformat(),
            "transaction_status": "captured",
            "is_fraud": 0,
        },
        {
            "transaction_id": "txn_002",
            "merchant_id": "m1",
            "customer_id": "c1",
            "amount": 2000.0,
            "timestamp": (base_time + pd.Timedelta(minutes=15)).isoformat(),
            "transaction_status": "captured",
            "is_fraud": 0,
        },
    ]

    df_initial = pd.DataFrame(initial_txns)
    feats_initial = fe.extract_derived_features(df_initial)

    # Now append future transactions (1 hour later) for customer c1
    future_txns = initial_txns + [
        {
            "transaction_id": "txn_003",
            "merchant_id": "m1",
            "customer_id": "c1",
            "amount": 50000.0,
            "timestamp": (base_time + pd.Timedelta(minutes=30)).isoformat(),
            "transaction_status": "failed",
            "is_fraud": 1,
        },
        {
            "transaction_id": "txn_004",
            "merchant_id": "m1",
            "customer_id": "c1",
            "amount": 90000.0,
            "timestamp": (base_time + pd.Timedelta(minutes=45)).isoformat(),
            "transaction_status": "failed",
            "is_fraud": 1,
        },
    ]

    df_future = pd.DataFrame(future_txns)
    feats_future = fe.extract_derived_features(df_future)

    # Features for txn_001 and txn_002 MUST be IDENTICAL in both runs (no future leakage)
    pd.testing.assert_frame_equal(
        feats_initial.iloc[:2].reset_index(drop=True),
        feats_future.iloc[:2].reset_index(drop=True),
        check_dtype=False,
    )
