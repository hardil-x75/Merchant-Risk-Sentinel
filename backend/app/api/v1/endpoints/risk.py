"""Risk assessment, merchant spike detection, transaction exploration, timeline, feature importance, and evaluation API endpoints."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from app.schemas.transaction import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
)
from app.services.risk_service import risk_service

router = APIRouter()


@router.post(
    "/assess",
    response_model=RiskAssessmentResponse,
    summary="Assess Transaction Risk",
    description="Analyzes transaction signals with trained Random Forest model, returns risk score, tier, deterministic reason codes, and defensive recommendation.",
)
def assess_transaction_risk(request: RiskAssessmentRequest):
    """Evaluate a single transaction request for risk anomalies."""
    return risk_service.assess_transaction_risk(request)


@router.get(
    "/transactions",
    summary="Get Transaction List",
    description="Returns searchable and filterable list of transactions with evaluated risk scores and decisions.",
)
def get_transactions(
    merchant_id: Optional[str] = Query(None, description="Filter by merchant ID"),
    risk_tier: Optional[str] = Query(None, description="Filter by risk tier (LOW, MEDIUM, HIGH, CRITICAL)"),
    search: Optional[str] = Query(None, description="Search query string"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Fetch transactions with evaluation scores."""
    return risk_service.get_transactions(
        merchant_id=merchant_id,
        risk_tier=risk_tier,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/timeline",
    summary="Get Time-Series Risk Timeline",
    description="Returns chronological time-series aggregation of transaction volumes, risk scores, and fraud spike markers.",
)
def get_risk_timeline(
    merchant_id: Optional[str] = Query(None, description="Filter by merchant ID")
):
    """Fetch time-series risk metrics for timeline charts."""
    return risk_service.get_risk_timeline(merchant_id=merchant_id)


@router.get(
    "/feature-importance",
    summary="Get Model Feature Importance",
    description="Returns ranked list of feature importance values from the trained Random Forest classifier.",
)
def get_feature_importance():
    """Fetch model feature importance ranking."""
    return risk_service.get_feature_importances()


@router.get(
    "/merchant-spikes",
    summary="Detect Merchant Fraud Spikes",
    description="Aggregates transaction streams per merchant, detecting velocity, failure rate, and risk score surges.",
)
def get_merchant_spikes() -> List[Dict[str, Any]]:
    """Return merchant-level fraud spike detection alerts."""
    return risk_service.get_merchant_spikes()


@router.get(
    "/simulation-stream",
    summary="Get Live Transaction Simulation Stream",
    description="Returns sequential transactions from synthetic dataset for live monitor playback.",
)
def get_simulation_stream(
    mode: str = Query("NORMAL", description="NORMAL, SPIKE, or HIGH_RISK"),
    limit: int = Query(20, ge=1, le=100),
):
    """Fetch transactions for live simulation stream."""
    return risk_service.get_simulation_stream(mode=mode, limit=limit)


@router.get(
    "/threshold-analysis",
    summary="Get Validation Set Threshold Analysis Grid",
    description="Returns Precision, Recall, F1, and False-Positive Financial Loss across candidate probability thresholds computed on Validation Set.",
)
def get_threshold_analysis():
    """Fetch threshold calibration grid results."""
    return risk_service.get_threshold_analysis()


@router.get(
    "/model-comparison",
    summary="Get Model Comparison (Random Forest vs Logistic Regression)",
    description="Returns side-by-side held-out test evaluation metrics comparing primary Random Forest against Logistic Regression baseline.",
)
def get_model_comparison():
    """Fetch model comparison metrics."""
    return risk_service.get_model_comparison()


@router.get(
    "/audit-log",
    summary="Get System Audit Events",
    description="Returns chronological audit timeline of risk assessments, merchant spike alerts, and defensive actions.",
)
def get_audit_log(limit: int = Query(50, ge=1, le=500)):
    """Fetch system audit log timeline."""
    return risk_service.get_audit_log(limit=limit)


@router.get(
    "/evaluation-status",
    summary="Get Evaluation & Held-Out Test Status",
    description="Returns reported metrics from single-pass evaluation on the untouched Held-Out Test Set.",
)
def get_evaluation_status():
    """Return evaluation plan metrics and cost model parameters."""
    return risk_service.get_evaluation_status()
