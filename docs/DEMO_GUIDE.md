# Merchant Risk Sentinel — 5-Minute Buildathon Judge Demo Guide

This script provides an exact 5-minute presentation sequence for showcasing **Merchant Risk Sentinel** during live Buildathon judging.

---

## Pitch Overview
- **Track 02:** AI Risk Manager
- **Product:** Merchant Risk Sentinel
- **Core Value:** Defensive fraud detection, merchant spike alerting, transparent deterministic explanations, and measured held-out test performance.

---

## 5-Minute Presentation Sequence

### `0:00 – 0:30` | The Problem & Product Positioning
- **What to say:**  
  *"Online merchants lose millions to sub-threshold fraud spikes, velocity surges, and chargebacks. Over-blocking hurts legitimate buyers, while delayed detection leads to unrecoverable chargeback penalties. We built Merchant Risk Sentinel — a strictly defensive AI Risk Manager that scores transactions in real time, alerts merchants to anomalous risk spikes, explains WHY events were flagged using deterministic signals, and recommends safe merchant-side safeguards."*
- **What to click:**  
  Start on the **Live Risk Stream** tab (`/`).

---

### `0:30 – 1:30` | Live Risk Monitor & Sequential Playback
- **What to say:**  
  *"Here in the Live Risk Monitor, incoming transactions stream in real time from our benchmark payment dataset. Each transaction is evaluated against our trained Random Forest classifier and temporal sliding-window engine. Notice how benign transactions pass cleanly with low scores, but as suspicious activity streams in, Sentinel instantly tags risk tiers — LOW, MEDIUM, HIGH, or CRITICAL — and triggers high-risk alerts."*
- **What to click:**  
  1. Click **"Start Stream"** in the top control bar to show real-time transaction playback.
  2. Click **"Simulate Spike (merch_03)"** scenario button to demonstrate burst playback.

---

### `1:30 – 2:15` | Merchant-Level Fraud Spike Detection
- **What to say:**  
  *"This is our core product differentiator — Merchant Risk Spikes. Standard gateways evaluate individual transactions in isolation. Sentinel aggregates sliding-window metrics across merchant accounts, comparing CURRENT activity directly against historical baselines. Here on merchant `merch_03`, Sentinel detected a 42.5% payment failure rate surge and an elevated high-risk score cluster, triggering an immediate CRITICAL Fraud Spike alert."*
- **What to click:**  
  Click the **"Merchant Spikes"** tab in the sidebar. Point out the `CURRENT ACTIVITY` vs `NORMAL BASELINE` comparison column.

---

### `2:15 – 3:00` | Investigating Suspicious Transactions & Deterministic Explanations
- **What to say:**  
  *"When a risk officer inspects a high-risk transaction like `txn_004912` (scored at 94.5% CRITICAL RISK), Sentinel provides complete transparency. Rather than relying on uninterpretable 'black box' scores or LLM hallucinations, Sentinel extracts deterministic, feature-grounded reason codes. For example: 1-hour transaction velocity reached 8 txns (vs baseline 3.2), amount is 4.5x above merchant average, and a disposable email domain was detected. Sentinel then recommends standard defensive actions: STEP-UP 3DS VERIFICATION or 24-HOUR REVIEW HOLD."*
- **What to click:**  
  1. Click the **"Guided 3-Stage Pitch Demo"** button in the header (or click any row in the Transactions table).
  2. Highlight the **"Why was this flagged?"** deterministic reason code section and the **"Defensive Action Panel"**.

---

### `3:00 – 4:00` | Model Architecture & Validation Threshold Calibration
- **What to say:**  
  *"Buildathon rules mandate honest metrics. We split our 10,000 transaction chronological dataset into 60% Train, 20% Validation, and 20% Held-Out Test Set. Crucially, our decision threshold — p* = 0.25 — was calibrated strictly on the Validation set to minimize False-Positive Cost loss. Our threshold analysis grid proves that p* = 0.25 minimizes total merchant financial friction (₹250 review cost vs ₹1,000 chargeback penalty)."*
- **What to click:**  
  1. Click the **"Model Performance"** tab in the sidebar.
  2. Point out the **Validation Set Threshold Calibration Analysis** grid table.

---

### `4:00 – 4:45` | Untouched Held-Out Test Set Evaluation Results
- **What to say:**  
  *"The Held-Out Test Set was kept strictly untouched during threshold calibration and training. On 2,000 unseen test transactions, Sentinel achieved a 91.71% Recall — catching 177 out of 193 fraudulent transactions — with a 62.11% Precision and an F1-score of 0.7406. Our False Positive Rate is just 5.98%, preserving buyer conversion while delivering ₹1.93 Million in net merchant financial savings vs no detection system."*
- **What to click:**  
  Highlight the **KPI Cards**, **Confusion Matrix** ($TP=177, FP=108, FN=16, TN=1,699$), and **Model Comparison** table (Random Forest vs Logistic Regression).

---

### `4:45 – 5:00` | Impact, Limitations & Closing
- **What to say:**  
  *"Sentinel is strictly defense-only, production-minded, and verified by an 18-test automated suite. All financial metrics are transparently documented as benchmark assumptions. Sentinel gives merchants the explainable AI intelligence they need to stop fraud losses without alienating legitimate buyers. Thank you!"*
- **What to click:**  
  Click **"Reset Demo"** in the header to return the dashboard to its clean starting state.
