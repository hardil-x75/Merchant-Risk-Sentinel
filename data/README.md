# Data Directory Structure

This directory stores transaction datasets used for training, validating, and testing **Merchant Risk Sentinel**.

```
data/
├── raw/         # Raw transaction logs / synthetic payment events
├── processed/   # Cleaned, feature-engineered datasets & train/val/test splits
└── README.md
```

## Held-Out Test Set Isolation Notice
All files placed in `data/processed/` that end in `_test.csv` or `_test.parquet` represent the **Held-Out Test Set**. 

These files must NOT be accessed during feature scaling fitting, model training, or hyperparameter optimization.
