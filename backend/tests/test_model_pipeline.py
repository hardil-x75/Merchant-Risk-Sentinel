"""Tests for Model Training, Probability Predictions, Threshold Calibration, and Held-Out Test Evaluation."""

import os
import sys
import numpy as np
import pandas as pd

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

from app.ml.trainer import SentinelModelTrainer
from app.ml.evaluation import SentinelRiskEvaluator


def test_model_training_and_probability_inference():
    """Verify trainer fits Random Forest classifier and outputs probabilities in [0.0, 1.0]."""
    np.random.seed(42)
    n = 200
    X_data = {
        "amount": np.random.uniform(100, 5000, n),
        "log_amount": np.random.uniform(4, 8, n),
        "txn_velocity_1h": np.random.randint(0, 10, n),
        "txn_velocity_24h": np.random.randint(0, 20, n),
        "failed_attempts_30m": np.random.randint(0, 5, n),
        "amount_ratio_merchant_avg": np.random.uniform(0.5, 5.0, n),
        "amount_ratio_customer_avg": np.random.uniform(0.5, 5.0, n),
        "time_since_prev_cust_txn_sec": np.random.uniform(10, 86400, n),
        "time_since_prev_merch_txn_sec": np.random.uniform(10, 3600, n),
        "disposable_email_flag": np.random.choice([0, 1], n),
        "non_domestic_billing_flag": np.random.choice([0, 1], n),
        "merchant_failure_rate_24h": np.random.uniform(0.0, 0.3, n),
        "is_fraud": np.random.choice([0, 1], n, p=[0.9, 0.1]),
    }
    df = pd.DataFrame(X_data)

    trainer = SentinelModelTrainer(random_seed=42)
    res = trainer.train(df, target_col="is_fraud")

    assert res["status"] == "trained"
    assert trainer.is_trained is True

    X_test = df.drop(columns=["is_fraud"])
    probas = trainer.predict_proba(X_test)

    assert len(probas) == n
    assert np.all(probas >= 0.0) and np.all(probas <= 1.0)


def test_validation_threshold_calibration():
    """Verify threshold calibration selects optimal cutoff based on financial cost minimization."""
    evaluator = SentinelRiskEvaluator(cost_per_fp=250.0, base_chargeback_fee=1000.0)

    y_val_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    y_val_proba = np.array([0.05, 0.10, 0.15, 0.25, 0.30, 0.35, 0.60, 0.70, 0.85, 0.90])
    val_amounts = np.array([1000.0] * 10)

    calib = evaluator.calibrate_threshold_on_validation(
        y_val_true=y_val_true,
        y_val_proba=y_val_proba,
        val_amounts=val_amounts,
        candidate_thresholds=[0.10, 0.20, 0.30, 0.50, 0.80],
    )

    assert "selected_threshold" in calib
    assert 0.10 <= calib["selected_threshold"] <= 0.80
    assert "min_financial_loss_inr" in calib
    assert len(calib["grid_results"]) == 5


def test_heldout_test_set_evaluation():
    """Verify held-out evaluation produces honest metrics and financial savings breakdown."""
    evaluator = SentinelRiskEvaluator(cost_per_fp=250.0, base_chargeback_fee=1000.0)

    test_df = pd.DataFrame({
        "amount": [1000.0] * 100,
        "is_fraud": [1] * 10 + [0] * 90,
    })

    # Perfect predictions for test
    y_test_proba = np.array([0.9] * 10 + [0.05] * 90)

    metrics = evaluator.evaluate_heldout_test_set(
        test_df=test_df, y_test_proba=y_test_proba, threshold=0.50
    )

    assert metrics["evaluation_scope"] == "HELD_OUT_TEST_SET"
    assert metrics["metrics"]["accuracy"] == 1.0
    assert metrics["metrics"]["precision"] == 1.0
    assert metrics["metrics"]["recall"] == 1.0
    assert metrics["confusion_matrix"]["tp"] == 10
    assert metrics["confusion_matrix"]["fp"] == 0
    assert metrics["financial_cost_analysis"]["net_merchant_savings_inr"] > 0
