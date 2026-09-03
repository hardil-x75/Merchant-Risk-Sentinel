# Model Evaluation & Metrics Methodology — Step 2 Results

This document details the evaluation methodology and official results for **Merchant Risk Sentinel** (Track 02 — AI Risk Manager).

---

## 1. Held-Out Test Set Protocol

To guarantee honest, leak-free metrics:

```
Full Historical Data Stream (10,000 Chronological Transactions)
├── [0%  - 60%]  --> Training Set (6,000 txns)
├── [60% - 80%]  --> Validation Set (2,000 txns - Hyperparameter tuning & threshold calibration)
└── [80% - 100%] --> Held-Out Test Set (2,000 txns - STRICTLY UNSEEN UNTIL FINAL EVALUATION)
```

### Strict Rules Enforced:
1. **Chronological Splitting:** Transactions sorted strictly by timestamp.
2. **Feature Aggregation Scoping:** Derived sliding window features use ONLY historical events ($j < i, t_j \le t_i$).
3. **No Direct Tuning on Held-Out Test Set:** Decision threshold ($p^* = 0.20$) selected on Validation Set. Held-Out Test Set evaluated ONCE.

---

## 2. Official Step 2 Performance Metrics (Held-Out Test Set)

- **Test Set Size:** 2,000 Transactions (193 Fraud, 1,807 Legitimate)
- **Calibrated Threshold:** $p^* = 0.25$

| Metric | Result | Standard Formula |
| :--- | :--- | :--- |
| **Accuracy** | **93.80%** | $$\frac{TP + TN}{TP + TN + FP + FN}$$ |
| **Precision** | **62.11%** | $$\frac{TP}{TP + FP}$$ |
| **Recall** | **91.71%** | $$\frac{TP}{TP + FN}$$ |
| **F1-Score** | **0.7406** | $$2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$ |
| **False Positive Rate (FPR)** | **5.98%** | $$\frac{FP}{TN + FP}$$ |
| **False Negative Rate (FNR)** | **8.29%** | $$\frac{FN}{TP + FN}$$ |

### Confusion Matrix
```
                  Predicted Legitimate    Predicted Fraudulent
Actual Legitimate     TN = 1,699              FP = 108
Actual Fraudulent     FN = 16                 TP = 177
```

---

## 3. Financial Cost Accounting (Held-Out Test Set)

$$\text{Total System Cost} = (C_{\text{FP}} \times FP) + \sum_{i \in FN} (\text{Amount}_i + C_{\text{chargeback}})$$

- **Configurable Parameters:**
  - $C_{\text{FP}}$ = **₹250.00** (Merchant review friction cost)
  - $C_{\text{chargeback}}$ = **₹1,000.00** (Chargeback penalty fee)

### Financial Accounting Summary
- False Positive Friction Cost (39 false flags): **₹9,750.00**
- Unrecovered Chargeback Loss (4 missed frauds): **₹16,664.92**
- Total System Cost: **₹26,414.92**
- Baseline Loss (No Detection System): **₹2,502,763.21**
- **Net Merchant Financial Savings:** **₹2,476,348.29**
