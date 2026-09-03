"""Abstract interfaces and base classes for the ML risk pipeline.

This defines the contracts for:
1. DataLoader: Loading raw transaction data and historical sets
2. FeatureEngineer: Transforming raw event streams into model features
3. ModelTrainer: Training, hyperparameter tuning, and saving model artifacts
4. InferenceEngine: Executing inference, risk scoring, and signal attribution
5. RiskEvaluator: Evaluating performance against held-out test sets with false-positive costs
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import pandas as pd
from app.schemas.transaction import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
)


class BaseDataLoader(ABC):
    """Abstract interface for dataset loading and partitioning."""

    @abstractmethod
    def load_raw_data(self, source_path: str) -> pd.DataFrame:
        """Load raw transaction logs into pandas DataFrame."""
        pass

    @abstractmethod
    def split_chronological(
        self, df: pd.DataFrame, train_ratio: float = 0.6, val_ratio: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split data into Train, Validation, and Held-Out Test sets without data leakage."""
        pass


class BaseFeatureEngineer(ABC):
    """Abstract interface for derived feature extraction and scaling."""

    @abstractmethod
    def extract_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute sliding window velocities, ratios, and risk indicators."""
        pass

    @abstractmethod
    def prepare_feature_matrix(
        self, request: RiskAssessmentRequest
    ) -> pd.DataFrame:
        """Convert a single API transaction request into a model feature vector."""
        pass


class BaseModelTrainer(ABC):
    """Abstract interface for model training and artifact persistence."""

    @abstractmethod
    def train(
        self, train_df: pd.DataFrame, target_col: str = "is_fraud"
    ) -> Dict[str, Any]:
        """Train classifier model on training set."""
        pass

    @abstractmethod
    def save_model(self, artifact_path: str) -> None:
        """Persist trained model artifact to disk."""
        pass

    @abstractmethod
    def load_model(self, artifact_path: str) -> None:
        """Load trained model artifact from disk."""
        pass


class BaseInferenceEngine(ABC):
    """Abstract interface for risk scoring, tier classification, and signal explanation."""

    @abstractmethod
    def predict_risk(
        self, request: RiskAssessmentRequest
    ) -> RiskAssessmentResponse:
        """Perform end-to-end inference, returning risk score, tier, and defensive recommendation."""
        pass


class BaseRiskEvaluator(ABC):
    """Abstract interface for evaluating model metrics on held-out test sets."""

    @abstractmethod
    def evaluate_heldout_test_set(
        self, test_df: pd.DataFrame, target_col: str = "is_fraud"
    ) -> Dict[str, Any]:
        """Compute Precision, Recall, F1, Confusion Matrix, and False-Positive Cost."""
        pass
