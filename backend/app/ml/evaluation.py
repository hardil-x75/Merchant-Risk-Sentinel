"""Evaluator module for threshold calibration, held-out test evaluation, and model baseline comparison."""

import json
import os
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from app.ml.interface import BaseRiskEvaluator
from app.utils.logger import logger


class SentinelRiskEvaluator(BaseRiskEvaluator):
    """Calibrates risk thresholds on validation set, evaluates held-out test metrics, and compares models."""

    def __init__(self, cost_per_fp: float = 250.0, base_chargeback_fee: float = 1000.0):
        self.cost_per_fp = cost_per_fp
        self.base_chargeback_fee = base_chargeback_fee
        self.selected_threshold = 0.20

    def calibrate_threshold_on_validation(
        self,
        y_val_true: np.ndarray,
        y_val_proba: np.ndarray,
        val_amounts: np.ndarray = None,
        candidate_thresholds: List[float] = None,
    ) -> Dict[str, Any]:
        """Calibrate decision threshold on Validation Set to minimize False-Positive Financial Cost."""
        if candidate_thresholds is None:
            candidate_thresholds = [round(t, 2) for t in np.arange(0.10, 0.95, 0.05)]

        if val_amounts is None:
            val_amounts = np.ones(len(y_val_true)) * 2500.0

        best_threshold = 0.20
        min_financial_loss = float("inf")
        grid_results = []

        for t in candidate_thresholds:
            y_pred = (y_val_proba >= t).astype(int)

            tp = int(np.sum((y_pred == 1) & (y_val_true == 1)))
            fp = int(np.sum((y_pred == 1) & (y_val_true == 0)))
            fn = int(np.sum((y_pred == 0) & (y_val_true == 1)))
            tn = int(np.sum((y_pred == 0) & (y_val_true == 0)))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            # Compute Financial Loss Function
            fp_cost = fp * self.cost_per_fp
            fn_indices = np.where((y_pred == 0) & (y_val_true == 1))[0]
            fn_amount_loss = float(np.sum(val_amounts[fn_indices]))
            fn_penalty_cost = fn * self.base_chargeback_fee
            fn_total_cost = fn_amount_loss + fn_penalty_cost

            total_loss = fp_cost + fn_total_cost

            grid_results.append(
                {
                    "threshold": float(t),
                    "precision": float(round(precision, 4)),
                    "recall": float(round(recall, 4)),
                    "f1": float(round(f1, 4)),
                    "tp": int(tp),
                    "fp": int(fp),
                    "fn": int(fn),
                    "tn": int(tn),
                    "financial_loss_inr": float(round(total_loss, 2)),
                    "is_selected": bool(abs(t - 0.20) < 1e-5),
                }
            )

            if total_loss < min_financial_loss:
                min_financial_loss = total_loss
                best_threshold = t

        self.selected_threshold = best_threshold
        logger.info(
            f"Threshold calibration on Validation set complete! "
            f"Selected Threshold={best_threshold:.2f} (Min Financial Loss=INR {min_financial_loss:,.2f})"
        )

        return {
            "selected_threshold": best_threshold,
            "min_financial_loss_inr": round(min_financial_loss, 2),
            "grid_results": grid_results,
        }

    def evaluate_heldout_test_set(
        self,
        test_df: pd.DataFrame,
        y_test_proba: np.ndarray,
        target_col: str = "is_fraud",
        threshold: float = None,
    ) -> Dict[str, Any]:
        """Execute single-pass evaluation on untouched Held-Out Test Set."""
        if threshold is None:
            threshold = self.selected_threshold

        y_true = test_df[target_col].values.astype(int)
        amounts = test_df["amount"].values if "amount" in test_df.columns else np.ones(len(y_true)) * 2500.0

        y_pred = (y_test_proba >= threshold).astype(int)

        tp = int(np.sum((y_pred == 1) & (y_true == 1)))
        fp = int(np.sum((y_pred == 1) & (y_true == 0)))
        fn = int(np.sum((y_pred == 0) & (y_true == 1)))
        tn = int(np.sum((y_pred == 0) & (y_true == 0)))

        total = len(y_true)
        positives = int(np.sum(y_true == 1))
        negatives = int(np.sum(y_true == 0))

        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        fpr = fp / negatives if negatives > 0 else 0.0
        fnr = fn / positives if positives > 0 else 0.0

        fp_cost = fp * self.cost_per_fp
        fn_indices = np.where((y_pred == 0) & (y_true == 1))[0]
        fn_amount_loss = float(np.sum(amounts[fn_indices]))
        fn_penalty_cost = fn * self.base_chargeback_fee
        total_system_cost = fp_cost + fn_amount_loss + fn_penalty_cost

        all_fraud_indices = np.where(y_true == 1)[0]
        baseline_fraud_amount = float(np.sum(amounts[all_fraud_indices]))
        baseline_penalty = positives * self.base_chargeback_fee
        baseline_loss = baseline_fraud_amount + baseline_penalty

        net_merchant_savings = baseline_loss - total_system_cost

        results = {
            "evaluation_scope": "HELD_OUT_TEST_SET",
            "threshold_used": threshold,
            "total_test_samples": total,
            "fraud_prevalence": round(positives / total, 4) if total > 0 else 0.0,
            "metrics": {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "false_positive_rate": round(fpr, 4),
                "false_negative_rate": round(fnr, 4),
            },
            "confusion_matrix": {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
            },
            "financial_cost_analysis": {
                "cost_per_fp_inr": self.cost_per_fp,
                "chargeback_penalty_fee_inr": self.base_chargeback_fee,
                "fp_friction_cost_inr": round(fp_cost, 2),
                "fn_unrecovered_loss_inr": round(fn_amount_loss + fn_penalty_cost, 2),
                "total_system_cost_inr": round(total_system_cost, 2),
                "baseline_no_detection_loss_inr": round(baseline_loss, 2),
                "net_merchant_savings_inr": round(net_merchant_savings, 2),
            },
        }

        logger.info(
            f"Held-Out Test Set Evaluation Complete! Precision={precision:.2%}, Recall={recall:.2%}, "
            f"F1={f1:.4f}, Net Savings=INR {net_merchant_savings:,.2f}"
        )

        return results

    def evaluate_model_comparison(
        self,
        test_df: pd.DataFrame,
        y_rf_proba: np.ndarray,
        y_lr_proba: np.ndarray,
        threshold: float = 0.20,
    ) -> Dict[str, Any]:
        """Evaluate Random Forest and Logistic Regression side-by-side on untouched Held-Out Test Set."""
        rf_eval = self.evaluate_heldout_test_set(test_df, y_rf_proba, threshold=threshold)
        lr_eval = self.evaluate_heldout_test_set(test_df, y_lr_proba, threshold=threshold)

        return {
            "evaluation_scope": "HELD_OUT_TEST_SET",
            "threshold_used": threshold,
            "comparison": [
                {
                    "model_name": "Random Forest (Primary)",
                    "precision": rf_eval["metrics"]["precision"],
                    "recall": rf_eval["metrics"]["recall"],
                    "f1_score": rf_eval["metrics"]["f1_score"],
                    "accuracy": rf_eval["metrics"]["accuracy"],
                    "false_positives": rf_eval["confusion_matrix"]["fp"],
                    "false_negatives": rf_eval["confusion_matrix"]["fn"],
                    "net_savings_inr": rf_eval["financial_cost_analysis"]["net_merchant_savings_inr"],
                    "status": "ACTIVE_PRIMARY",
                },
                {
                    "model_name": "Logistic Regression (Baseline)",
                    "precision": lr_eval["metrics"]["precision"],
                    "recall": lr_eval["metrics"]["recall"],
                    "f1_score": lr_eval["metrics"]["f1_score"],
                    "accuracy": lr_eval["metrics"]["accuracy"],
                    "false_positives": lr_eval["confusion_matrix"]["fp"],
                    "false_negatives": lr_eval["confusion_matrix"]["fn"],
                    "net_savings_inr": lr_eval["financial_cost_analysis"]["net_merchant_savings_inr"],
                    "status": "BASELINE",
                },
            ],
        }

    def compute_false_positive_cost(
        self, fp_count: int, fn_count: int, fn_amounts: list = None
    ) -> Dict[str, float]:
        """Compute financial cost breakdown."""
        fp_total_cost = fp_count * self.cost_per_fp
        fn_penalty_cost = fn_count * self.base_chargeback_fee
        fn_amount_loss = sum(fn_amounts) if fn_amounts else 0.0

        fn_total_cost = fn_penalty_cost + fn_amount_loss
        total_system_cost = fp_total_cost + fn_total_cost

        return {
            "fp_count": fp_count,
            "fn_count": fn_count,
            "fp_total_cost": round(fp_total_cost, 2),
            "fn_total_cost": round(fn_total_cost, 2),
            "total_system_cost": round(total_system_cost, 2),
        }
