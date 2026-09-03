# Defensive-Only Scope & Security Boundary

## Policy Overview
**Merchant Risk Sentinel** is built strictly as a **defense-only AI risk manager** for online merchants. 

The hackathon guidelines explicitly state:
> *"Strictly defense-only: anything offense-capable is disqualified."*

This document defines the strict operational boundaries of the Merchant Risk Sentinel application.

---

## 1. Permitted Defensive Capabilities

The system is explicitly designed and restricted to perform the following defensive functions:

1. **Risk Scoring & Anomaly Detection:**
   - Analyzing incoming merchant transaction metrics for anomalous patterns (e.g., velocity bursts, geo-distance mismatches, card network failure bursts).
   - Assigning calibrated risk scores ($[0.0, 1.0]$) and risk classification levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

2. **Merchant Risk Alerting:**
   - Real-time alerting for merchants when risk thresholds are breached.
   - Summarizing transaction spike characteristics across a merchant's payment volume.

3. **Risk Signal Explanation:**
   - Providing transparent, human-interpretable explanations of why a transaction or burst was flagged (e.g., *"Flagged due to 5 failed payment attempts within 10 minutes from a non-domestic IP"*).

4. **Defensive Action Recommendations:**
   - Recommending standard, safe merchant risk mitigations:
     - Request 3D-Secure (3DS / OTP) step-up authentication.
     - Place high-value physical goods delivery on 24-hour review hold.
     - Rate-limit API checkout calls from suspicious IP ranges.
     - Prompt merchant support to verify high-risk customer details before fulfillment.

---

## 2. Strictly Prohibited Offense-Capable Functions

The system will **NEVER** contain, generate, or execute any offense-capable logic. Specifically:

* **NO Fraud Strategy Generation:** The system does NOT generate, simulate, or output strategies for committing payment fraud or chargeback abuse.
* **NO Security Evasion Instructions:** The system does NOT provide advice on how to bypass 3DS, evade fraud detectors, or trick payment gateway risk algorithms.
* **NO Exploitative Code:** The system does NOT include bot scripts, carding automation tools, payload generators, or synthetic identity creation tools.
* **NO Adversarial Attack Simulation:** The system will NOT optimize adversarial payloads against payment gateways.

---

## 3. Governance & Auditability

* **Input Validation:** All incoming transaction data is validated against standard Pydantic schemas.
* **Defensive Output Sanitization:** System recommendations are hardcoded and validated against an approved dictionary of safe defensive actions.
* **Audit Logging:** System logs maintain clear records of all risk scoring activities without logging sensitive payment credentials (e.g. primary account numbers or CVVs).
