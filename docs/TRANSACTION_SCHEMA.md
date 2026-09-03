# Transaction Schema & Feature Definitions

This document details the transaction schema for **Merchant Risk Sentinel**.

To maintain technical clarity and honesty, signals are categorized into three distinct layers:
1. **Category A:** Realistic Payment Gateway / Gateway API Fields
2. **Category B:** Derived System Features (calculated dynamically by Sentinel engine)
3. **Category C:** Synthetic Benchmark Features (explicitly documented test attributes)

---

## Category A — Realistic Gateway / Payment Fields
*These fields represent data available in standard payment webhook/event payloads.*

| Field Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `transaction_id` | `string` | Unique transaction identifier | `"txn_1092837491"` |
| `merchant_id` | `string` | Unique merchant account identifier | `"merch_88231"` |
| `customer_id` | `string` | Anonymized unique customer identifier | `"cust_anon_9921"` |
| `amount` | `float` | Transaction value in currency sub-units or base units | `4500.00` |
| `currency` | `string` | 3-letter ISO currency code | `"INR"` |
| `payment_method` | `string` | Method used (`card`, `upi`, `netbanking`, `wallet`) | `"card"` |
| `timestamp` | `datetime / ISO8601` | Timestamp of payment request execution | `"2026-09-02T21:05:00Z"` |
| `transaction_status` | `string` | Gateway processing status (`captured`, `failed`, `pending`) | `"captured"` |
| `card_network` | `string` | Network name if card payment (`visa`, `mastercard`, `rupay`) | `"visa"` |
| `bank_name` | `string` | Issuing bank or UPI handle domain | `"HDFC"` |
| `email_domain` | `string` | Customer email domain for domain-trust scoring | `"gmail.com"` |
| `billing_country` | `string` | ISO 2-letter billing country code | `"IN"` |

---

## Category B — Derived System Features
*These features are computed by the Merchant Risk Sentinel backend over sliding time windows.*

| Feature Name | Type | Window / Scope | Description |
| :--- | :--- | :--- | :--- |
| `txn_velocity_1h` | `integer` | 1 Hour (Customer/Device) | Number of transactions attempted by customer in last 60 minutes |
| `txn_velocity_24h` | `integer` | 24 Hours (Customer/Device) | Number of transactions attempted by customer in last 24 hours |
| `amount_ratio_merchant_avg` | `float` | Merchant History | Ratio of current transaction amount to merchant's 30-day average amount |
| `failed_attempts_30m` | `integer` | 30 Minutes (Customer/Device) | Count of recent failed/declined attempts before current transaction |
| `customer_account_age_days` | `float` | Merchant History | Age of customer profile registered with merchant in days |
| `geo_ip_distance_km` | `float` | Real-time | Estimated distance between IP geolocation and card issuing/billing country |
| `device_fingerprint_changes_7d` | `integer` | 7 Days | Count of distinct device signatures associated with customer ID in 7 days |
| `payment_method_switches_24h` | `integer` | 24 Hours | Count of distinct payment methods tried by customer in last 24 hours |

---

## Category C — Synthetic Benchmark Features
*These features are generated for testing and benchmarking model performance where live gateway telemetry is absent.*

| Feature Name | Type | Purpose | Notes |
| :--- | :--- | :--- | :--- |
| `synthetic_risk_noise_factor` | `float` | Stress testing model robustness | Controlled Gaussian noise injected during simulation |
| `simulated_botnet_flag` | `boolean` | Micro-burst anomaly simulation | Identifies synthetic automated bot cluster events |

---

## JSON Payload Example (Backend Interface Schema)

```json
{
  "raw_data": {
    "transaction_id": "txn_89712391",
    "merchant_id": "merch_55102",
    "customer_id": "cust_99201",
    "amount": 12500.00,
    "currency": "INR",
    "payment_method": "card",
    "timestamp": "2026-09-02T21:05:00Z",
    "transaction_status": "captured",
    "card_network": "visa",
    "bank_name": "ICICI",
    "email_domain": "tempmail.com",
    "billing_country": "IN"
  },
  "derived_features": {
    "txn_velocity_1h": 8,
    "txn_velocity_24h": 14,
    "amount_ratio_merchant_avg": 4.5,
    "failed_attempts_30m": 4,
    "customer_account_age_days": 0.2,
    "geo_ip_distance_km": 850.5,
    "device_fingerprint_changes_7d": 3,
    "payment_method_switches_24h": 3
  }
}
```
