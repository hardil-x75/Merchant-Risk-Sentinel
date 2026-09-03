"""Model Trainer module for Merchant Risk Sentinel.

Trains Logistic Regression baseline and Random Forest classifiers on historical training data
with class imbalance weighting.
"""

import os
from typing import Dict, Any, Tuple
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from app.ml.interface import BaseModelTrainer
from app.utils.logger import logger


class SentinelModelTrainer(BaseModelTrainer):
    """Trains scikit-learn Random Forest and Logistic Regression risk classifiers."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            class_weight="balanced",
            random_state=random_seed,
            n_jobs=-1,
        )
        self.baseline_model = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=random_seed,
        )
        self.feature_columns = []
        self.is_trained = False

    def train(
        self, train_df: pd.DataFrame, target_col: str = "is_fraud"
    ) -> Dict[str, Any]:
        """Train Random Forest classifier on training feature matrix.

        Args:
            train_df: Chronologically isolated training DataFrame
            target_col: Target label column name

        Returns:
            Dict containing training summary and feature importances
        """
        if train_df.empty or target_col not in train_df.columns:
            raise ValueError("Invalid training dataset or missing target column.")

        X_train = train_df.drop(columns=[target_col])
        y_train = train_df[target_col].values

        self.feature_columns = list(X_train.columns)
        logger.info(
            f"Training Random Forest on {len(X_train)} samples with {len(self.feature_columns)} features..."
        )

        # Fit feature scaler
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Train Baseline Logistic Regression
        self.baseline_model.fit(X_train_scaled, y_train)

        # Train Primary Random Forest Classifier
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Extract Feature Importances
        importances = self.model.feature_importances_
        feature_importance_map = dict(
            sorted(
                zip(self.feature_columns, importances),
                key=lambda x: x[1],
                reverse=True,
            )
        )

        logger.info(f"Model training completed! Top features: {list(feature_importance_map.keys())[:3]}")

        return {
            "status": "trained",
            "train_samples": len(X_train),
            "fraud_samples": int(y_train.sum()),
            "feature_count": len(self.feature_columns),
            "feature_importances": feature_importance_map,
        }

    def predict_proba(self, X_df: pd.DataFrame) -> Any:
        """Predict fraud probability [0.0 - 1.0] using primary Random Forest model."""
        if not self.is_trained:
            raise RuntimeError("Model is not trained yet.")
        # Ensure column alignment
        X_aligned = X_df[self.feature_columns]
        return self.model.predict_proba(X_aligned)[:, 1]

    def predict_proba_baseline(self, X_df: pd.DataFrame) -> Any:
        """Predict fraud probability [0.0 - 1.0] using Logistic Regression baseline model."""
        if not self.is_trained:
            raise RuntimeError("Baseline model is not trained yet.")
        X_aligned = X_df[self.feature_columns]
        X_scaled = self.scaler.transform(X_aligned)
        return self.baseline_model.predict_proba(X_scaled)[:, 1]

    def save_model(self, artifact_dir: str) -> None:
        """Persist model, scaler, and feature metadata to disk."""
        if not self.is_trained:
            raise RuntimeError("Cannot save untrained model.")

        os.makedirs(artifact_dir, exist_ok=True)
        model_path = os.path.join(artifact_dir, "sentinel_model.joblib")
        meta_path = os.path.join(artifact_dir, "model_metadata.joblib")

        artifact_data = {
            "model": self.model,
            "baseline_model": self.baseline_model,
            "scaler": self.scaler,
            "feature_columns": self.feature_columns,
            "random_seed": self.random_seed,
        }

        joblib.dump(artifact_data, model_path)
        logger.info(f"Model artifacts saved successfully to: {artifact_dir}")

    def load_model(self, artifact_dir: str) -> None:
        """Load model, scaler, and feature metadata from disk."""
        model_path = os.path.join(artifact_dir, "sentinel_model.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model artifact not found at {model_path}")

        artifact_data = joblib.load(model_path)
        self.model = artifact_data["model"]
        self.baseline_model = artifact_data.get("baseline_model")
        self.scaler = artifact_data["scaler"]
        self.feature_columns = artifact_data["feature_columns"]
        self.is_trained = True
        logger.info(f"Loaded model artifact from {model_path}")
