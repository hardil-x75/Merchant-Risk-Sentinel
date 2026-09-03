# Comprehensive Evaluation Evidence Summary

This document presents the complete evaluation evidence for **Merchant Risk Sentinel** (Track 02 — AI Risk Manager), generated directly from executed model training and test artifacts.

---

## 1. Dataset & Temporal Partitioning Specification

| Attribute | Specification / Value |
| :--- | :--- |
| **Total Transactions** | 10,000 Transactions |
| **Merchant Account Count** | 20 Merchants (`merch_01` .. `merch_20`) |
| **Time Span** | 30 Days Chronological Window (Aug 1, 2026 – Aug 31, 2026) |
| **Fraud Prevalence** | 800 Fraud Transactions (**8.00%**), 9,200 Legitimate (**92.00%**) |
| **Data Partitioning Protocol** | **60% Train** (6,000 txns) / **20% Validation** (2,000 txns) / **20% Held-Out Test** (2,000 txns) |
| **Temporal Isolation** | Strictly time-ordered. No random cross-validation. No future data leakage. |

---

## 2. Feature Matrix (12 Features)

1. `amount`: Transaction monetary value in INR
2. `log_amount`: `np.log1p(amount)`
3. `txn_velocity_1h`: Customer transaction count in preceding 1 hour $[t - 3600\text{s}, t)$
4. `txn_velocity_24h`: Customer transaction count in preceding 24 hours $[t - 86400\text{s}, t)$
5. `failed_attempts_30m`: Customer failed attempts in preceding 30 minutes $[t - 1800\text{s}, t)$
6. `amount_ratio_merchant_avg`: Ratio of transaction amount to merchant's historical mean amount
7. `amount_ratio_customer_avg`: Ratio of transaction amount to customer's historical mean amount
8. `time_since_prev_cust_txn_sec`: Elapsed seconds since customer's previous transaction
9. `time_since_prev_merch_txn_sec`: Elapsed seconds since merchant's previous transaction
10. `disposable_email_flag`: 1 if email domain is disposable/temporary, else 0
11. `non_domestic_billing_flag`: 1 if billing country is non-domestic (`!= IN`), else 0
12. `merchant_failure_rate_24h`: Proportion of failed transactions for merchant in preceding 24 hours

---

## 3. Threshold Calibration Methodology (Validation Set)

The decision threshold $p^*$ was calibrated strictly on the **Validation Set** ($2,000$ transactions) by minimizing total financial loss:

$$\text{Financial Loss}(p) = (C_{\text{FP}} \times FP) + \sum_{i \in FN} (\text{Amount}_i + C_{\text{chargeback}})$$

Where $C_{\text{FP}} = \text{₹250.00}$ (review friction) and $C_{\text{chargeback}} = \text{₹1,000.00}$ (penalty fee).

Optimal threshold selected on Validation Set: **$p^* = 0.25$**.

---

## 4. Official Held-Out Test Set Performance (Untouched 20% Split)

Single-pass evaluation executed on the **2,000 untouched test transactions** using calibrated threshold $p^* = 0.25$:

- **Total Test Samples:** 2,000 Transactions (193 Fraud, 1,807 Legitimate)

| Metric | Result |
| :--- | :--- |
| **Accuracy** | **93.80%** |
| **Precision** | **62.11%** |
| **Recall (Detection Rate)** | **91.71%** (177 / 193 Frauds Caught) |
| **F1-Score** | **0.7406** |
| **False Positive Rate (FPR)** | **5.98%** (108 False Alarms / 1,807 Legitimate) |
| **False Negative Rate (FNR)** | **8.29%** (16 Missed Frauds / 193 Frauds) |

### Confusion Matrix (Held-Out Test Set)
```
                  Predicted Legitimate    Predicted Fraudulent
Actual Legitimate     TN = 1,699              FP = 108
Actual Fraudulent     FN = 16                 TP = 177
```

---

## 5. Side-by-Side Model Architecture Comparison

| Model Architecture | Precision | Recall | F1-Score | Accuracy | False Positives | False Negatives | Net Merchant Savings (INR) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Forest (Primary)** | **62.11%** | **91.71%** | **0.7406** | **93.80%** | **108** | **16** | **INR 1,927,465.28** |
| **Logistic Regression (Baseline)** | 50.00% | 96.37% | 0.6584 | 90.35% | 186 | 7 | INR 1,935,605.37 |

---

## 6. Financial Accounting & Savings Model

- **False Positive Friction Cost ($108 \times \text{₹250}$):** **INR 27,000.00**
- **Unrecovered Chargeback Loss (16 Missed Frauds):** **INR 55,255.95**
- **Total System Cost:** **INR 82,255.95**
- **Baseline Loss (No Detection System):** **INR 2,009,721.23**
- **Net Merchant Financial Savings:** **INR 1,927,465.28**

---

## 7. Limitations & Honest Disclaimers
1. **Synthetic Data:** Benchmark data generated for reproducible local validation. Does NOT contain live production Razorpay telemetry.
2. **Configurable Cost Parameters:** Financial metrics depend on assumed parameters ($C_{\text{FP}}=\text{₹250}$, $C_{\text{penalty}}=\text{₹1,000}$).
3. **Defensive Actions:** System provides safe recommendations (`STEP-UP 3DS`, `HOLD FOR REVIEW`) for merchant action.
