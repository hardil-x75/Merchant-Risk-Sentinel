"""DataLoader implementation for ingestion and chronological train/val/test splits."""

import os
from typing import Tuple
import pandas as pd
from app.ml.interface import BaseDataLoader
from app.utils.logger import logger


class TransactionDataLoader(BaseDataLoader):
    """Handles raw transaction loading and chronologically isolated train/val/test partitioning."""

    def load_raw_data(self, source_path: str) -> pd.DataFrame:
        """Load raw CSV/Parquet dataset."""
        if not os.path.exists(source_path):
            logger.warning(f"Data source file not found at {source_path}. Returning empty DataFrame.")
            return pd.DataFrame()

        if source_path.endswith(".parquet"):
            return pd.read_parquet(source_path)
        return pd.read_csv(source_path)

    def split_chronological(
        self, df: pd.DataFrame, train_ratio: float = 0.6, val_ratio: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split data chronologically by timestamp without random shuffle or future leakage.

        Args:
            df: Raw transaction DataFrame
            train_ratio: Proportion for Training set (default 0.60)
            val_ratio: Proportion for Validation set (default 0.20)

        Returns:
            Tuple of (train_df, val_df, test_heldout_df)
        """
        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Parse timestamp to datetime and sort strictly chronologically
        if "timestamp" in df.columns:
            df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp_dt").reset_index(drop=True)
            df = df.drop(columns=["timestamp_dt"])

        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_df = df.iloc[:train_end].copy().reset_index(drop=True)
        val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_heldout_df = df.iloc[val_end:].copy().reset_index(drop=True)

        logger.info(
            f"Chronological split complete: Train={len(train_df)} ({len(train_df)/n:.1%}), "
            f"Val={len(val_df)} ({len(val_df)/n:.1%}), "
            f"HeldOutTest={len(test_heldout_df)} ({len(test_heldout_df)/n:.1%})"
        )
        return train_df, val_df, test_heldout_df
