"""Inference Engine using trained Random Forest model and deterministic reason codes."""

import os
from datetime import datetime, timezone
from typing import List
import pandas as pd
from app.core.config import settings
from app.core.security import sanitize_defensive_recommendation
from app.ml.feature_engineering import TransactionFeatureEngineer
from app.ml.interface import BaseInferenceEngine
from app.ml.trainer import SentinelModelTrainer
from app.schemas.transaction import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    RiskTier,
    RiskExplanation,
)
from app.utils.logger import logger


class SentinelInferenceEngine(BaseInferenceEngine):
    """Executes trained model inference, risk tiering, deterministic reason code generation, and defensive recommendation."""

    def __init__(self, artifact_dir: str = None):
        self.feature_engineer = TransactionFeatureEngineer()
        self.trainer = SentinelModelTrainer()
        self.calibrated_threshold = 0.50

        if artifact_dir is None:
            artifact_dir = os.path.join(os.path.dirname(__file__), "saved_models")

        self.artifact_dir = artifact_dir
        self._try_load_model()

    def _try_load_model(self) -> bool:
        """Attempt to load saved model artifact if present."""
        try:
            model_file = os.path.join(self.artifact_dir, "sentinel_model.joblib")
            config_file = os.path.join(self.artifact_dir, "threshold_config.json")
            if os.path.exists(model_file):
                self.trainer.load_model(self.artifact_dir)
                if os.path.exists(config_file):
                    import json
                    with open(config_file, "r") as f:
                        cfg = json.load(f)
                        self.calibrated_threshold = cfg.get("calibrated_threshold", 0.50)
                logger.info(f"Inference engine initialized with model! Threshold={self.calibrated_threshold:.2f}")
                return True
        except Exception as e:
            logger.warning(f"Could not load trained model artifact: {e}. Falling back to baseline heuristics.")
        return False

    def predict_risk(
        self, request: RiskAssessmentRequest
    ) -> RiskAssessmentResponse:
        """Predict risk score, tier, deterministic reason codes, and defensive recommendation."""
        raw = request.raw_data
        derived = request.derived_features

        X_df = self.feature_engineer.prepare_feature_matrix(request)

        # 1. Model Inference or Fallback Probability
        if self.trainer.is_trained:
            proba = float(self.trainer.predict_proba(X_df)[0])
        else:
            # Baseline heuristic fallback if model not loaded
            proba = 0.05
            if derived:
                if derived.txn_velocity_1h >= 5:
                    proba += 0.35
                if derived.failed_attempts_30m >= 3:
                    proba += 0.30
                if derived.amount_ratio_merchant_avg >= 4.0:
                    proba += 0.20

        score = min(max(proba, 0.0), 1.0)

        # 2. Deterministic Reason Code Extraction from Feature Matrix Values
        explanations: List[RiskExplanation] = []
        row = X_df.iloc[0]

        v1h = int(row["txn_velocity_1h"])
        v24h = int(row["txn_velocity_24h"])
        f30m = int(row["failed_attempts_30m"])
        amt_ratio_m = float(row["amount_ratio_merchant_avg"])
        disp_flag = int(row["disposable_email_flag"])
        non_dom_flag = int(row["non_domestic_billing_flag"])
        m_fail_rate = float(row["merchant_failure_rate_24h"])

        if v1h >= 4:
            explanations.append(
                RiskExplanation(
                    feature_name="txn_velocity_1h",
                    contribution_score=0.35,
                    description=f"Elevated 1-hour transaction velocity ({v1h} transactions in 60m)",
                )
            )

        if f30m >= 3:
            explanations.append(
                RiskExplanation(
                    feature_name="failed_attempts_30m",
                    contribution_score=0.30,
                    description=f"Burst of failed payment attempts ({f30m} declines in last 30m)",
                )
            )

        if amt_ratio_m >= 3.5:
            explanations.append(
                RiskExplanation(
                    feature_name="amount_ratio_merchant_avg",
                    contribution_score=0.25,
                    description=f"Transaction amount is {amt_ratio_m:.1f}x higher than merchant historical average",
                )
            )

        if disp_flag == 1:
            explanations.append(
                RiskExplanation(
                    feature_name="disposable_email_flag",
                    contribution_score=0.20,
                    description="Temporary / disposable email domain detected",
                )
            )

        if non_dom_flag == 1:
            explanations.append(
                RiskExplanation(
                    feature_name="non_domestic_billing_flag",
                    contribution_score=0.15,
                    description=f"Non-domestic billing country ({raw.billing_country})",
                )
            )

        if m_fail_rate >= 0.25:
            explanations.append(
                RiskExplanation(
                    feature_name="merchant_failure_rate_24h",
                    contribution_score=0.15,
                    description=f"Merchant experiencing elevated 24h payment failure rate ({m_fail_rate:.1%})",
                )
            )

        if not explanations:
            explanations.append(
                RiskExplanation(
                    feature_name="baseline_behavior",
                    contribution_score=score,
                    description="Transaction metrics within standard operating parameters.",
                )
            )

        # 3. Risk Tiering & Calibrated Threshold Classification
        # Calibrated threshold divides LOW/MEDIUM from HIGH/CRITICAL
        high_cutoff = self.calibrated_threshold
        critical_cutoff = min(0.95, high_cutoff + 0.15)

        if score >= critical_cutoff:
            risk_tier = RiskTier.CRITICAL
            recommendation_code = "ENABLE_3DS"
        elif score >= high_cutoff:
            risk_tier = RiskTier.HIGH
            recommendation_code = "HOLD_FOR_REVIEW"
        elif score >= (high_cutoff * 0.6):
            risk_tier = RiskTier.MEDIUM
            recommendation_code = "VERIFY_CUSTOMER_CONTACT"
        else:
            risk_tier = RiskTier.LOW
            recommendation_code = "MONITOR_MERCHANT_VELOCITY"

        is_suspicious = score >= high_cutoff
        defensive_recommendation = sanitize_defensive_recommendation(recommendation_code)

        logger.info(
            f"Evaluated txn '{raw.transaction_id}': score={score:.4f}, threshold={high_cutoff:.2f}, tier={risk_tier.value}"
        )

        return RiskAssessmentResponse(
            transaction_id=raw.transaction_id,
            merchant_id=raw.merchant_id,
            risk_score=round(score, 4),
            risk_tier=risk_tier,
            is_suspicious=is_suspicious,
            signal_explanations=explanations,
            defensive_recommendation=defensive_recommendation,
            evaluated_at=datetime.now(timezone.utc),
        )
