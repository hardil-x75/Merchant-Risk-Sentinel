"""Pydantic schemas for payment transactions, derived features, and risk assessments."""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PaymentMethod(str, Enum):
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    OTHER = "other"


class TransactionStatus(str, Enum):
    CAPTURED = "captured"
    FAILED = "failed"
    PENDING = "pending"


class RawTransactionSignals(BaseModel):
    """Category A: Realistic payment gateway payload fields."""

    transaction_id: str = Field(..., description="Unique transaction ID")
    merchant_id: str = Field(..., description="Unique merchant ID")
    customer_id: str = Field(..., description="Anonymized customer identifier")
    amount: float = Field(..., gt=0, description="Transaction monetary amount")
    currency: str = Field(default="INR", description="3-letter ISO currency code")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Transaction timestamp")
    transaction_status: TransactionStatus = Field(default=TransactionStatus.CAPTURED)
    card_network: Optional[str] = Field(default=None, description="e.g. visa, mastercard, rupay")
    bank_name: Optional[str] = Field(default=None, description="Issuing bank or handle domain")
    email_domain: Optional[str] = Field(default=None, description="Customer email domain")
    billing_country: str = Field(default="IN", description="2-letter ISO country code")


class DerivedTransactionFeatures(BaseModel):
    """Category B: Features calculated dynamically by Sentinel over sliding windows."""

    txn_velocity_1h: int = Field(default=0, ge=0, description="Customer txn count in last 1 hour")
    txn_velocity_24h: int = Field(default=0, ge=0, description="Customer txn count in last 24 hours")
    amount_ratio_merchant_avg: float = Field(default=1.0, ge=0, description="Ratio of amount to merchant 30-day average")
    failed_attempts_30m: int = Field(default=0, ge=0, description="Failed attempts in last 30 minutes")
    customer_account_age_days: float = Field(default=0.0, ge=0, description="Customer account age in days")
    geo_ip_distance_km: float = Field(default=0.0, ge=0, description="IP geolocation to billing country distance")
    device_fingerprint_changes_7d: int = Field(default=0, ge=0, description="Device footprint switches in 7 days")
    payment_method_switches_24h: int = Field(default=0, ge=0, description="Payment method switches in 24 hours")


class SyntheticBenchmarkSignals(BaseModel):
    """Category C: Explicit synthetic test features (used during simulation)."""

    is_synthetic: bool = Field(default=False)
    synthetic_risk_noise_factor: Optional[float] = Field(default=0.0)


class RiskAssessmentRequest(BaseModel):
    """Combined request payload for risk evaluation."""

    raw_data: RawTransactionSignals
    derived_features: Optional[DerivedTransactionFeatures] = None
    synthetic_signals: Optional[SyntheticBenchmarkSignals] = None


class RiskExplanation(BaseModel):
    """Explanation of contributing risk factors."""

    feature_name: str
    contribution_score: float
    description: str


class RiskAssessmentResponse(BaseModel):
    """Structured response from the Sentinel Risk Engine."""

    transaction_id: str
    merchant_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated risk score between 0.0 and 1.0")
    risk_tier: RiskTier
    is_suspicious: bool
    signal_explanations: List[RiskExplanation]
    defensive_recommendation: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
