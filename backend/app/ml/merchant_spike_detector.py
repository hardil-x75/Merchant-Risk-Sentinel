"""Merchant-Level Fraud Spike Aggregator and Alert Detector.

Aggregates window metrics across merchant accounts to detect sudden surges in velocity,
failure rates, or high-risk transaction clusters relative to merchant baselines.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd
from app.utils.logger import logger


class MerchantSpikeDetector:
    """Aggregates merchant transaction metrics and detects fraud spikes."""

    def __init__(self, risk_threshold: float = 0.50):
        self.risk_threshold = risk_threshold

    def analyze_merchant_spikes(
        self, df_txns: pd.DataFrame, risk_scores: np.ndarray = None
    ) -> List[Dict[str, Any]]:
        """Analyze transaction stream for merchant-level fraud spikes.

        Args:
            df_txns: DataFrame containing merchant transactions
            risk_scores: Optional array of model risk scores

        Returns:
            List of merchant risk spike summaries
        """
        if df_txns.empty or "merchant_id" not in df_txns.columns:
            return []

        df = df_txns.copy()
        if risk_scores is not None and len(risk_scores) == len(df):
            df["model_risk_score"] = risk_scores
        else:
            df["model_risk_score"] = 0.05

        spike_reports = []

        grouped = df.groupby("merchant_id")
        for m_id, group in grouped:
            total_txns = len(group)
            total_amt = float(group["amount"].sum())
            avg_amt = float(group["amount"].mean())
            failed_count = int((group["transaction_status"] == "failed").sum())
            failed_rate = failed_count / total_txns if total_txns > 0 else 0.0

            scores = group["model_risk_score"].values
            avg_risk = float(np.mean(scores)) if len(scores) > 0 else 0.0
            high_risk_count = int(np.sum(scores >= self.risk_threshold))
            high_risk_ratio = high_risk_count / total_txns if total_txns > 0 else 0.0

            # Detect Spike Condition
            is_spike_alert = False
            spike_reasons = []

            if high_risk_ratio >= 0.15:
                is_spike_alert = True
                spike_reasons.append(f"Elevated high-risk transaction proportion ({high_risk_ratio:.1%})")

            if failed_rate >= 0.25:
                is_spike_alert = True
                spike_reasons.append(f"Abnormal payment failure rate ({failed_rate:.1%})")

            if avg_risk >= 0.35:
                is_spike_alert = True
                spike_reasons.append(f"Average merchant risk score surge ({avg_risk:.4f})")

            spike_reports.append(
                {
                    "merchant_id": m_id,
                    "window_txn_count": total_txns,
                    "window_total_amount": round(total_amt, 2),
                    "window_avg_amount": round(avg_amt, 2),
                    "failed_txn_count": failed_count,
                    "failed_rate": round(failed_rate, 4),
                    "high_risk_txn_count": high_risk_count,
                    "high_risk_ratio": round(high_risk_ratio, 4),
                    "avg_risk_score": round(avg_risk, 4),
                    "is_spike_alert": is_spike_alert,
                    "spike_reasons": spike_reasons if is_spike_alert else ["Normal merchant baseline traffic"],
                }
            )

        logger.info(f"Analyzed {len(spike_reports)} merchants for fraud spikes.")
        return sorted(spike_reports, key=lambda x: x["avg_risk_score"], reverse=True)
