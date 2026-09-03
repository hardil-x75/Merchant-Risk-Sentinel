"""Defensive security boundary utilities and sanitizers."""

from typing import List

# Pre-approved defensive action catalog (strictly defensive)
ALLOWED_DEFENSIVE_ACTIONS = {
    "ENABLE_3DS": "Enable 3D-Secure (OTP / Step-Up Verification) for this payment.",
    "HOLD_FOR_REVIEW": "Place order on 24-hour merchant review hold before shipping.",
    "FLAG_IP_BURST": "Rate-limit high-frequency checkout calls from this IP range.",
    "VERIFY_CUSTOMER_CONTACT": "Prompt customer support verification prior to fulfillment.",
    "MONITOR_MERCHANT_VELOCITY": "Add merchant ID to 1-hour risk spike monitor watchlist."
}


def sanitize_defensive_recommendation(action_code: str) -> str:
    """Ensure generated action recommendations stay strictly within defensive bounds."""
    if action_code in ALLOWED_DEFENSIVE_ACTIONS:
        return ALLOWED_DEFENSIVE_ACTIONS[action_code]
    return "Standard Defensive Monitor: Log transaction details for merchant audit review."


def get_all_defensive_action_catalog() -> dict:
    """Return catalog of approved defensive recommendations."""
    return ALLOWED_DEFENSIVE_ACTIONS.copy()
