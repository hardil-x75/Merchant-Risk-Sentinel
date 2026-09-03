"""Tests for Synthetic Dataset Generator reproducibility and class distribution."""

import os
import sys
import pandas as pd

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, root_dir)

from data.generate_dataset import generate_synthetic_transactions


def test_dataset_generation_reproducibility():
    """Verify dataset generation produces identical output given the same random seed."""
    df1 = generate_synthetic_transactions(
        num_merchants=5, txns_per_merchant=50, random_seed=42
    )
    df2 = generate_synthetic_transactions(
        num_merchants=5, txns_per_merchant=50, random_seed=42
    )

    assert len(df1) == len(df2) == 250
    pd.testing.assert_frame_equal(df1, df2)


def test_dataset_class_distribution():
    """Verify generated dataset contains both positive (fraud) and negative (legitimate) classes."""
    df = generate_synthetic_transactions(
        num_merchants=10, txns_per_merchant=100, fraud_prevalence=0.10, random_seed=42
    )

    assert "is_fraud" in df.columns
    fraud_count = df["is_fraud"].sum()
    legit_count = (df["is_fraud"] == 0).sum()

    assert fraud_count > 0, "Dataset must contain fraudulent transactions"
    assert legit_count > 0, "Dataset must contain legitimate transactions"
    assert fraud_count + legit_count == len(df) == 1000
