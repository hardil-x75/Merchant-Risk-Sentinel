"""Feature engineering pipeline for Merchant Risk Sentinel.

Strictly enforces chronological feature computation where features for a transaction at time t
use ONLY historical data from transactions occurring at or before t (j < i, t_j <= t_i).
"""

from typing import List
import numpy as np
import pandas as pd
from app.ml.interface import BaseFeatureEngineer
from app.schemas.transaction import RiskAssessmentRequest
from app.utils.logger import logger


class TransactionFeatureEngineer(BaseFeatureEngineer):
    """Computes time-series sliding window features and behavioral anomaly indicators."""

    DISPOSABLE_DOMAINS = {"tempmail.com", "disposable.org", "mailinator.com", "guerrillamail.com"}

    FEATURE_COLUMNS: List[str] = [
        "amount",
        "log_amount",
        "txn_velocity_1h",
        "txn_velocity_24h",
        "failed_attempts_30m",
        "amount_ratio_merchant_avg",
        "amount_ratio_customer_avg",
        "time_since_prev_cust_txn_sec",
        "time_since_prev_merch_txn_sec",
        "disposable_email_flag",
        "non_domestic_billing_flag",
        "merchant_failure_rate_24h",
    ]

    def extract_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract historical sliding window features strictly respecting temporal sequence.

        Args:
            df: DataFrame sorted chronologically by timestamp

        Returns:
            pd.DataFrame containing feature matrix with target label 'is_fraud' if present.
        """
        if df.empty:
            return pd.DataFrame(columns=self.FEATURE_COLUMNS)

        logger.info(f"Extracting temporal sliding window features for {len(df)} transactions...")

        df_sorted = df.copy()
        if "timestamp_dt" not in df_sorted.columns:
            df_sorted["timestamp_dt"] = pd.to_datetime(df_sorted["timestamp"])
        df_sorted = df_sorted.sort_values("timestamp_dt").reset_index(drop=True)

        n = len(df_sorted)
        timestamps = df_sorted["timestamp_dt"].values
        amounts = df_sorted["amount"].values.astype(float)
        cust_ids = df_sorted["customer_id"].values
        merch_ids = df_sorted["merchant_id"].values
        statuses = df_sorted["transaction_status"].values
        email_domains = df_sorted.get("email_domain", pd.Series([""] * n)).values
        billing_countries = df_sorted.get("billing_country", pd.Series(["IN"] * n)).values

        # Preallocate feature arrays
        feat_amount = amounts
        feat_log_amount = np.log1p(amounts)
        feat_vel_1h = np.zeros(n, dtype=int)
        feat_vel_24h = np.zeros(n, dtype=int)
        feat_fails_30m = np.zeros(n, dtype=int)
        feat_amount_ratio_merch = np.ones(n, dtype=float)
        feat_amount_ratio_cust = np.ones(n, dtype=float)
        feat_time_prev_cust = np.full(n, 86400.0, dtype=float)
        feat_time_prev_merch = np.full(n, 86400.0, dtype=float)
        feat_disposable_email = np.zeros(n, dtype=int)
        feat_non_domestic = np.zeros(n, dtype=int)
        feat_merch_fail_rate_24h = np.zeros(n, dtype=float)

        # Stateful history maps for sequential historical lookups (t_j < t_i)
        cust_history: dict = {}   # cust_id -> list of (timestamp_dt, amount, status)
        merch_history: dict = {}  # merch_id -> list of (timestamp_dt, amount, status)

        for i in range(n):
            t_curr = timestamps[i]
            t_curr_sec = t_curr.astype("datetime64[s]").astype(int)
            amt_curr = amounts[i]
            c_id = cust_ids[i]
            m_id = merch_ids[i]
            e_dom = str(email_domains[i])
            b_cntry = str(billing_countries[i])

            # Static row signals
            feat_disposable_email[i] = 1 if e_dom in self.DISPOSABLE_DOMAINS else 0
            feat_non_domestic[i] = 1 if b_cntry != "IN" else 0

            # 1. Customer History Lookups (STRICTLY PRECEDING: j < i)
            if c_id in cust_history and len(cust_history[c_id]) > 0:
                c_events = cust_history[c_id]
                t_last_cust = c_events[-1][0].astype("datetime64[s]").astype(int)
                feat_time_prev_cust[i] = max(0.0, float(t_curr_sec - t_last_cust))

                # Window counts
                t_1h_cutoff = t_curr - np.timedelta64(1, "h")
                t_24h_cutoff = t_curr - np.timedelta64(24, "h")
                t_30m_cutoff = t_curr - np.timedelta64(30, "m")

                v1h = 0
                v24h = 0
                f30m = 0
                cust_sum_amt = 0.0

                for t_prev, a_prev, s_prev in c_events:
                    cust_sum_amt += a_prev
                    if t_prev >= t_24h_cutoff:
                        v24h += 1
                        if t_prev >= t_1h_cutoff:
                            v1h += 1
                        if t_prev >= t_30m_cutoff and s_prev == "failed":
                            f30m += 1

                feat_vel_1h[i] = v1h
                feat_vel_24h[i] = v24h
                feat_fails_30m[i] = f30m

                cust_avg = cust_sum_amt / len(c_events)
                feat_amount_ratio_cust[i] = amt_curr / (cust_avg + 1e-5)
            else:
                cust_history[c_id] = []

            # 2. Merchant History Lookups (STRICTLY PRECEDING: j < i)
            if m_id in merch_history and len(merch_history[m_id]) > 0:
                m_events = merch_history[m_id]
                t_last_merch = m_events[-1][0].astype("datetime64[s]").astype(int)
                feat_time_prev_merch[i] = max(0.0, float(t_curr_sec - t_last_merch))

                t_24h_cutoff = t_curr - np.timedelta64(24, "h")
                m24_total = 0
                m24_fails = 0
                merch_sum_amt = 0.0

                for t_prev, a_prev, s_prev in m_events:
                    merch_sum_amt += a_prev
                    if t_prev >= t_24h_cutoff:
                        m24_total += 1
                        if s_prev == "failed":
                            m24_fails += 1

                merch_avg = merch_sum_amt / len(m_events)
                feat_amount_ratio_merch[i] = amt_curr / (merch_avg + 1e-5)
                feat_merch_fail_rate_24h[i] = (m24_fails / m24_total) if m24_total > 0 else 0.0
            else:
                merch_history[m_id] = []

            # Append CURRENT transaction AFTER reading history (Guarantees no future leakage)
            cust_history[c_id].append((t_curr, amt_curr, statuses[i]))
            merch_history[m_id].append((t_curr, amt_curr, statuses[i]))

        # Construct final Feature DataFrame
        feats_dict = {
            "amount": feat_amount,
            "log_amount": feat_log_amount,
            "txn_velocity_1h": feat_vel_1h,
            "txn_velocity_24h": feat_vel_24h,
            "failed_attempts_30m": feat_fails_30m,
            "amount_ratio_merchant_avg": feat_amount_ratio_merch,
            "amount_ratio_customer_avg": feat_amount_ratio_cust,
            "time_since_prev_cust_txn_sec": feat_time_prev_cust,
            "time_since_prev_merch_txn_sec": feat_time_prev_merch,
            "disposable_email_flag": feat_disposable_email,
            "non_domestic_billing_flag": feat_non_domestic,
            "merchant_failure_rate_24h": feat_merch_fail_rate_24h,
        }

        res_df = pd.DataFrame(feats_dict, columns=self.FEATURE_COLUMNS)
        if "is_fraud" in df_sorted.columns:
            res_df["is_fraud"] = df_sorted["is_fraud"].values

        return res_df

class HistoricalStateStore:
    """In-memory state store for real-time temporal feature computation.

    Maintains historical lists of prior transactions per customer_id and merchant_id.
    Guarantees that feature calculation for a transaction at time t uses ONLY
    transactions occurring strictly before t (j < i).
    The current transaction is NOT appended to history until AFTER its features are computed.
    The ground-truth 'is_fraud' label is NEVER used.
    """

    DISPOSABLE_DOMAINS = {"tempmail.com", "disposable.org", "mailinator.com", "guerrillamail.com"}

    def __init__(self):
        self.cust_history: dict = {}   # cust_id -> list of (timestamp_dt, amount, status)
        self.merch_history: dict = {}  # merch_id -> list of (timestamp_dt, amount, status)

    def reset(self):
        """Reset historical state maps."""
        self.cust_history.clear()
        self.merch_history.clear()

    def prime_from_dataframe(self, df: pd.DataFrame):
        """Seed historical state store from transaction dataset.

        Args:
            df: DataFrame of transactions sorted chronologically
        """
        self.reset()
        if df.empty:
            return

        df_sorted = df.copy()
        if "timestamp_dt" not in df_sorted.columns:
            df_sorted["timestamp_dt"] = pd.to_datetime(df_sorted["timestamp"])
        df_sorted = df_sorted.sort_values("timestamp_dt")

        for _, row in df_sorted.iterrows():
            t_curr = row["timestamp_dt"]
            amt = float(row["amount"])
            c_id = str(row["customer_id"])
            m_id = str(row["merchant_id"])
            status = str(row.get("transaction_status", "captured"))

            if c_id not in self.cust_history:
                self.cust_history[c_id] = []
            self.cust_history[c_id].append((t_curr, amt, status))

            if m_id not in self.merch_history:
                self.merch_history[m_id] = []
            self.merch_history[m_id].append((t_curr, amt, status))

    def compute_live_features(
        self,
        txn_dict: dict,
        update_state: bool = True,
    ) -> pd.DataFrame:
        """Compute feature vector for a single transaction using prior state history.

        Args:
            txn_dict: Dictionary containing transaction fields:
                      customer_id, merchant_id, amount, timestamp, email_domain, billing_country, transaction_status
            update_state: If True, appends current transaction to history AFTER computing features.

        Returns:
            pd.DataFrame: Single-row DataFrame matching FEATURE_COLUMNS
        """
        c_id = str(txn_dict.get("customer_id", "cust_unknown"))
        m_id = str(txn_dict.get("merchant_id", "merch_unknown"))
        amt_curr = float(txn_dict.get("amount", 0.0))
        status = str(txn_dict.get("transaction_status", "captured"))
        email_dom = str(txn_dict.get("email_domain", "")).lower()
        billing_cntry = str(txn_dict.get("billing_country", "IN")).upper()

        raw_ts = txn_dict.get("timestamp")
        if isinstance(raw_ts, pd.Timestamp):
            t_curr = raw_ts
        elif isinstance(raw_ts, str) and raw_ts:
            try:
                t_curr = pd.to_datetime(raw_ts)
            except Exception:
                t_curr = pd.Timestamp.now(tz="UTC")
        else:
            t_curr = pd.Timestamp.now(tz="UTC")

        # Convert to seconds timestamp for delta math
        t_curr_sec = int(t_curr.timestamp()) if hasattr(t_curr, "timestamp") else 0

        # Static row signals
        disp_flag = 1 if email_dom in self.DISPOSABLE_DOMAINS else 0
        non_dom_flag = 1 if billing_cntry != "IN" else 0

        # Customer lookups (STRICTLY PRECEDING: j < i)
        c_events = self.cust_history.get(c_id, [])
        if c_events:
            t_last_cust = int(c_events[-1][0].timestamp()) if hasattr(c_events[-1][0], "timestamp") else 0
            time_prev_cust = max(0.0, float(t_curr_sec - t_last_cust))

            t_1h_cutoff = t_curr - pd.Timedelta(hours=1)
            t_24h_cutoff = t_curr - pd.Timedelta(hours=24)
            t_30m_cutoff = t_curr - pd.Timedelta(minutes=30)

            v1h = 0
            v24h = 0
            f30m = 0
            cust_sum_amt = 0.0

            for t_prev, a_prev, s_prev in c_events:
                cust_sum_amt += a_prev
                if t_prev >= t_24h_cutoff:
                    v24h += 1
                    if t_prev >= t_1h_cutoff:
                        v1h += 1
                    if t_prev >= t_30m_cutoff and s_prev == "failed":
                        f30m += 1

            cust_avg = cust_sum_amt / len(c_events)
            amt_ratio_cust = amt_curr / (cust_avg + 1e-5)
        else:
            time_prev_cust = 86400.0
            v1h = 0
            v24h = 0
            f30m = 0
            amt_ratio_cust = 1.0

        # Merchant lookups (STRICTLY PRECEDING: j < i)
        m_events = self.merch_history.get(m_id, [])
        if m_events:
            t_last_merch = int(m_events[-1][0].timestamp()) if hasattr(m_events[-1][0], "timestamp") else 0
            time_prev_merch = max(0.0, float(t_curr_sec - t_last_merch))

            t_24h_cutoff = t_curr - pd.Timedelta(hours=24)
            m24_total = 0
            m24_fails = 0
            merch_sum_amt = 0.0

            for t_prev, a_prev, s_prev in m_events:
                merch_sum_amt += a_prev
                if t_prev >= t_24h_cutoff:
                    m24_total += 1
                    if s_prev == "failed":
                        m24_fails += 1

            merch_avg = merch_sum_amt / len(m_events)
            amt_ratio_merch = amt_curr / (merch_avg + 1e-5)
            merch_fail_rate = (m24_fails / m24_total) if m24_total > 0 else 0.0
        else:
            time_prev_merch = 86400.0
            amt_ratio_merch = 1.0
            merch_fail_rate = 0.0

        # Update state AFTER computing features (Guarantees current transaction not in its own history)
        if update_state:
            if c_id not in self.cust_history:
                self.cust_history[c_id] = []
            self.cust_history[c_id].append((t_curr, amt_curr, status))

            if m_id not in self.merch_history:
                self.merch_history[m_id] = []
            self.merch_history[m_id].append((t_curr, amt_curr, status))

        row = {
            "amount": amt_curr,
            "log_amount": float(np.log1p(amt_curr)),
            "txn_velocity_1h": v1h,
            "txn_velocity_24h": v24h,
            "failed_attempts_30m": f30m,
            "amount_ratio_merchant_avg": amt_ratio_merch,
            "amount_ratio_customer_avg": amt_ratio_cust,
            "time_since_prev_cust_txn_sec": time_prev_cust,
            "time_since_prev_merch_txn_sec": time_prev_merch,
            "disposable_email_flag": disp_flag,
            "non_domestic_billing_flag": non_dom_flag,
            "merchant_failure_rate_24h": merch_fail_rate,
        }

        return pd.DataFrame([row], columns=TransactionFeatureEngineer.FEATURE_COLUMNS)


# Shared in-memory state store singleton instance
global_state_store = HistoricalStateStore()


class TransactionFeatureEngineer(BaseFeatureEngineer):
    """Computes time-series sliding window features and behavioral anomaly indicators."""

    DISPOSABLE_DOMAINS = {"tempmail.com", "disposable.org", "mailinator.com", "guerrillamail.com"}

    FEATURE_COLUMNS: List[str] = [
        "amount",
        "log_amount",
        "txn_velocity_1h",
        "txn_velocity_24h",
        "failed_attempts_30m",
        "amount_ratio_merchant_avg",
        "amount_ratio_customer_avg",
        "time_since_prev_cust_txn_sec",
        "time_since_prev_merch_txn_sec",
        "disposable_email_flag",
        "non_domestic_billing_flag",
        "merchant_failure_rate_24h",
    ]

    def extract_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract historical sliding window features strictly respecting temporal sequence.

        Args:
            df: DataFrame sorted chronologically by timestamp

        Returns:
            pd.DataFrame containing feature matrix with target label 'is_fraud' if present.
        """
        if df.empty:
            return pd.DataFrame(columns=self.FEATURE_COLUMNS)

        logger.info(f"Extracting temporal sliding window features for {len(df)} transactions...")

        df_sorted = df.copy()
        if "timestamp_dt" not in df_sorted.columns:
            df_sorted["timestamp_dt"] = pd.to_datetime(df_sorted["timestamp"])
        df_sorted = df_sorted.sort_values("timestamp_dt").reset_index(drop=True)

        n = len(df_sorted)
        timestamps = df_sorted["timestamp_dt"].values
        amounts = df_sorted["amount"].values.astype(float)
        cust_ids = df_sorted["customer_id"].values
        merch_ids = df_sorted["merchant_id"].values
        statuses = df_sorted["transaction_status"].values
        email_domains = df_sorted.get("email_domain", pd.Series([""] * n)).values
        billing_countries = df_sorted.get("billing_country", pd.Series(["IN"] * n)).values

        # Preallocate feature arrays
        feat_amount = amounts
        feat_log_amount = np.log1p(amounts)
        feat_vel_1h = np.zeros(n, dtype=int)
        feat_vel_24h = np.zeros(n, dtype=int)
        feat_fails_30m = np.zeros(n, dtype=int)
        feat_amount_ratio_merch = np.ones(n, dtype=float)
        feat_amount_ratio_cust = np.ones(n, dtype=float)
        feat_time_prev_cust = np.full(n, 86400.0, dtype=float)
        feat_time_prev_merch = np.full(n, 86400.0, dtype=float)
        feat_disposable_email = np.zeros(n, dtype=int)
        feat_non_domestic = np.zeros(n, dtype=int)
        feat_merch_fail_rate_24h = np.zeros(n, dtype=float)

        # Stateful history maps for sequential historical lookups (t_j < t_i)
        cust_history: dict = {}   # cust_id -> list of (timestamp_dt, amount, status)
        merch_history: dict = {}  # merch_id -> list of (timestamp_dt, amount, status)

        for i in range(n):
            t_curr = timestamps[i]
            t_curr_sec = t_curr.astype("datetime64[s]").astype(int)
            amt_curr = amounts[i]
            c_id = cust_ids[i]
            m_id = merch_ids[i]
            e_dom = str(email_domains[i])
            b_cntry = str(billing_countries[i])

            # Static row signals
            feat_disposable_email[i] = 1 if e_dom in self.DISPOSABLE_DOMAINS else 0
            feat_non_domestic[i] = 1 if b_cntry != "IN" else 0

            # 1. Customer History Lookups (STRICTLY PRECEDING: j < i)
            if c_id in cust_history and len(cust_history[c_id]) > 0:
                c_events = cust_history[c_id]
                t_last_cust = c_events[-1][0].astype("datetime64[s]").astype(int)
                feat_time_prev_cust[i] = max(0.0, float(t_curr_sec - t_last_cust))

                # Window counts
                t_1h_cutoff = t_curr - np.timedelta64(1, "h")
                t_24h_cutoff = t_curr - np.timedelta64(24, "h")
                t_30m_cutoff = t_curr - np.timedelta64(30, "m")

                v1h = 0
                v24h = 0
                f30m = 0
                cust_sum_amt = 0.0

                for t_prev, a_prev, s_prev in c_events:
                    cust_sum_amt += a_prev
                    if t_prev >= t_24h_cutoff:
                        v24h += 1
                        if t_prev >= t_1h_cutoff:
                            v1h += 1
                        if t_prev >= t_30m_cutoff and s_prev == "failed":
                            f30m += 1

                feat_vel_1h[i] = v1h
                feat_vel_24h[i] = v24h
                feat_fails_30m[i] = f30m

                cust_avg = cust_sum_amt / len(c_events)
                feat_amount_ratio_cust[i] = amt_curr / (cust_avg + 1e-5)
            else:
                cust_history[c_id] = []

            # 2. Merchant History Lookups (STRICTLY PRECEDING: j < i)
            if m_id in merch_history and len(merch_history[m_id]) > 0:
                m_events = merch_history[m_id]
                t_last_merch = m_events[-1][0].astype("datetime64[s]").astype(int)
                feat_time_prev_merch[i] = max(0.0, float(t_curr_sec - t_last_merch))

                t_24h_cutoff = t_curr - np.timedelta64(24, "h")
                m24_total = 0
                m24_fails = 0
                merch_sum_amt = 0.0

                for t_prev, a_prev, s_prev in m_events:
                    merch_sum_amt += a_prev
                    if t_prev >= t_24h_cutoff:
                        m24_total += 1
                        if s_prev == "failed":
                            m24_fails += 1

                merch_avg = merch_sum_amt / len(m_events)
                feat_amount_ratio_merch[i] = amt_curr / (merch_avg + 1e-5)
                feat_merch_fail_rate_24h[i] = (m24_fails / m24_total) if m24_total > 0 else 0.0
            else:
                merch_history[m_id] = []

            # Append CURRENT transaction AFTER reading history (Guarantees no future leakage)
            cust_history[c_id].append((t_curr, amt_curr, statuses[i]))
            merch_history[m_id].append((t_curr, amt_curr, statuses[i]))

        # Construct final Feature DataFrame
        feats_dict = {
            "amount": feat_amount,
            "log_amount": feat_log_amount,
            "txn_velocity_1h": feat_vel_1h,
            "txn_velocity_24h": feat_vel_24h,
            "failed_attempts_30m": feat_fails_30m,
            "amount_ratio_merchant_avg": feat_amount_ratio_merch,
            "amount_ratio_customer_avg": feat_amount_ratio_cust,
            "time_since_prev_cust_txn_sec": feat_time_prev_cust,
            "time_since_prev_merch_txn_sec": feat_time_prev_merch,
            "disposable_email_flag": feat_disposable_email,
            "non_domestic_billing_flag": feat_non_domestic,
            "merchant_failure_rate_24h": feat_merch_fail_rate_24h,
        }

        res_df = pd.DataFrame(feats_dict, columns=self.FEATURE_COLUMNS)
        if "is_fraud" in df_sorted.columns:
            res_df["is_fraud"] = df_sorted["is_fraud"].values

        return res_df

    def prepare_feature_matrix(
        self, request: RiskAssessmentRequest, state_store: HistoricalStateStore = None
    ) -> pd.DataFrame:
        """Convert single transaction API request payload into model feature vector using live historical state."""
        raw = request.raw_data
        derived = request.derived_features

        # If derived features are explicitly passed in request payload, use them directly
        if derived and (derived.txn_velocity_1h > 0 or derived.failed_attempts_30m > 0 or derived.amount_ratio_merchant_avg != 1.0):
            amt = float(raw.amount)
            row = {
                "amount": amt,
                "log_amount": float(np.log1p(amt)),
                "txn_velocity_1h": derived.txn_velocity_1h,
                "txn_velocity_24h": derived.txn_velocity_24h,
                "failed_attempts_30m": derived.failed_attempts_30m,
                "amount_ratio_merchant_avg": derived.amount_ratio_merchant_avg,
                "amount_ratio_customer_avg": 1.0,
                "time_since_prev_cust_txn_sec": 86400.0,
                "time_since_prev_merch_txn_sec": 300.0,
                "disposable_email_flag": 1 if (raw.email_domain and raw.email_domain.lower() in self.DISPOSABLE_DOMAINS) else 0,
                "non_domestic_billing_flag": 1 if (raw.billing_country and raw.billing_country.upper() != "IN") else 0,
                "merchant_failure_rate_24h": 0.05,
            }
            return pd.DataFrame([row], columns=self.FEATURE_COLUMNS)

        # Otherwise compute dynamically using HistoricalStateStore
        store = state_store if state_store is not None else global_state_store
        txn_dict = {
            "customer_id": raw.customer_id,
            "merchant_id": raw.merchant_id,
            "amount": raw.amount,
            "timestamp": raw.timestamp.isoformat() if hasattr(raw.timestamp, "isoformat") else str(raw.timestamp),
            "email_domain": raw.email_domain or "",
            "billing_country": raw.billing_country or "IN",
            "transaction_status": getattr(raw, "transaction_status", "captured"),
        }
        return store.compute_live_features(txn_dict, update_state=True)
