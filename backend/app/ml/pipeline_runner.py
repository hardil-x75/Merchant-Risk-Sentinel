"""End-to-End Pipeline Execution Script for Step 2.

Executes:
Synthetic Data Loading -> Chronological Splitting -> Feature Engineering ->
Random Forest Model Training -> Validation Threshold Calibration ->
Single-Pass Held-Out Test Set Evaluation -> Artifact Persistence
"""

import json
import os
import sys
import pandas as pd

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.ml.loader import TransactionDataLoader
from app.ml.feature_engineering import TransactionFeatureEngineer
from app.ml.trainer import SentinelModelTrainer
from app.ml.evaluation import SentinelRiskEvaluator
from app.utils.logger import logger


def run_pipeline(
    raw_data_path: str = None,
    artifact_dir: str = None,
    cost_per_fp: float = 250.0,
    base_chargeback_fee: float = 1000.0,
):
    """Run full ML model training, validation calibration, and held-out test evaluation."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    if raw_data_path is None:
        raw_data_path = os.path.join(root_dir, "data", "raw", "transactions_raw.csv")

    if artifact_dir is None:
        artifact_dir = os.path.join(os.path.dirname(__file__), "saved_models")

    processed_dir = os.path.join(root_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(artifact_dir, exist_ok=True)

    # 1. Load Raw Dataset
    logger.info("=== STEP 2 ML PIPELINE START ===")
    loader = TransactionDataLoader()
    if not os.path.exists(raw_data_path):
        logger.info("Raw data missing. Executing generate_dataset.py...")
        from data.generate_dataset import generate_synthetic_transactions
        df_raw = generate_synthetic_transactions()
        df_raw.to_csv(raw_data_path, index=False)
    else:
        df_raw = loader.load_raw_data(raw_data_path)

    logger.info(f"Loaded raw dataset with {len(df_raw)} transactions.")

    # 2. Chronological Data Partitioning (60% Train, 20% Val, 20% Held-Out Test)
    train_raw, val_raw, test_raw = loader.split_chronological(
        df_raw, train_ratio=0.60, val_ratio=0.20
    )

    # 3. Feature Extraction (No Future Data Leakage)
    feature_engineer = TransactionFeatureEngineer()
    logger.info("Extracting features for Training split...")
    train_feats = feature_engineer.extract_derived_features(train_raw)

    logger.info("Extracting features for Validation split...")
    val_feats = feature_engineer.extract_derived_features(val_raw)

    logger.info("Extracting features for Held-Out Test split...")
    test_feats = feature_engineer.extract_derived_features(test_raw)

    # Save processed split data
    train_feats.to_csv(os.path.join(processed_dir, "train.csv"), index=False)
    val_feats.to_csv(os.path.join(processed_dir, "val.csv"), index=False)
    test_feats.to_csv(os.path.join(processed_dir, "test_heldout.csv"), index=False)

    # 4. Model Training on Training Split
    trainer = SentinelModelTrainer(random_seed=42)
    train_summary = trainer.train(train_feats, target_col="is_fraud")

    # 5. Threshold Calibration on Validation Split
    X_val = val_feats.drop(columns=["is_fraud"])
    y_val = val_feats["is_fraud"].values
    val_amounts = val_raw["amount"].values if "amount" in val_raw.columns else None
    val_proba = trainer.predict_proba(X_val)

    evaluator = SentinelRiskEvaluator(
        cost_per_fp=cost_per_fp, base_chargeback_fee=base_chargeback_fee
    )
    calibration_summary = evaluator.calibrate_threshold_on_validation(
        y_val_true=y_val, y_val_proba=val_proba, val_amounts=val_amounts
    )
    selected_threshold = calibration_summary["selected_threshold"]

    # 6. Single-Pass Held-Out Test Set Evaluation
    X_test = test_feats.drop(columns=["is_fraud"])
    test_proba_rf = trainer.predict_proba(X_test)
    test_proba_lr = trainer.predict_proba_baseline(X_test)

    heldout_metrics = evaluator.evaluate_heldout_test_set(
        test_df=test_feats,
        y_test_proba=test_proba_rf,
        target_col="is_fraud",
        threshold=selected_threshold,
    )

    model_comparison = evaluator.evaluate_model_comparison(
        test_df=test_feats,
        y_rf_proba=test_proba_rf,
        y_lr_proba=test_proba_lr,
        threshold=selected_threshold,
    )

    # 7. Persist Model Artifacts & Evaluation Reports
    trainer.save_model(artifact_dir)

    threshold_config = {
        "calibrated_threshold": selected_threshold,
        "cost_per_fp_inr": cost_per_fp,
        "base_chargeback_fee_inr": base_chargeback_fee,
        "feature_columns": trainer.feature_columns,
    }
    with open(os.path.join(artifact_dir, "threshold_config.json"), "w") as f:
        json.dump(threshold_config, f, indent=2)

    with open(os.path.join(artifact_dir, "heldout_test_metrics.json"), "w") as f:
        json.dump(heldout_metrics, f, indent=2)

    with open(os.path.join(artifact_dir, "model_comparison.json"), "w") as f:
        json.dump(model_comparison, f, indent=2)

    logger.info("=== STEP 2 ML PIPELINE SUCCESSFUL ===")
    return {
        "train_summary": train_summary,
        "calibration_summary": calibration_summary,
        "heldout_metrics": heldout_metrics,
        "model_comparison": model_comparison,
    }


if __name__ == "__main__":
    results = run_pipeline()
    print("\n" + "=" * 60)
    print("STEP 2 ML PIPELINE RESULTS REPORT")
    print("=" * 60)
    print(f"Scope: {results['heldout_metrics']['evaluation_scope']}")
    print(f"Selected Threshold: {results['heldout_metrics']['threshold_used']:.2f}")
    print(f"Accuracy:  {results['heldout_metrics']['metrics']['accuracy']:.4f}")
    print(f"Precision: {results['heldout_metrics']['metrics']['precision']:.4f}")
    print(f"Recall:    {results['heldout_metrics']['metrics']['recall']:.4f}")
    print(f"F1-Score:  {results['heldout_metrics']['metrics']['f1_score']:.4f}")
    print("Confusion Matrix:", results['heldout_metrics']['confusion_matrix'])
    print(
        f"Net Merchant Savings: INR {results['heldout_metrics']['financial_cost_analysis']['net_merchant_savings_inr']:,.2f}"
    )
    print("=" * 60)
