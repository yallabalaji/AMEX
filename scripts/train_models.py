#!/usr/bin/env python

"""
Stage 2: Train baseline linear model for AmEx Default Prediction.

This script:
1. Loads preprocessed training data from:
   - data/stage/linear_train.parquet
   - data/stage/feature_columns.json
2. Performs a customer-wise 80/20 train/validation split.
3. Trains a Logistic Regression model (with StandardScaler).
4. Evaluates on validation set using ROC-AUC.
5. Saves:
   - models/best_model.pkl
   - models/metrics.json
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test_size",
        type=float,
        default=0.2,
        help="Proportion of customers to use for validation (default: 0.2).",
    )
    parser.add_argument(
        "--random_state",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # Paths
    # -------------------------------------------------------------------------
    project_root = Path(__file__).resolve().parents[1]
    stage_dir = project_root / "data" / "stage"
    models_dir = project_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    linear_train_path = stage_dir / "linear_train.parquet"
    feature_cols_path = stage_dir / "feature_columns.json"

    if not linear_train_path.exists():
        raise FileNotFoundError(f"linear_train.parquet not found at {linear_train_path}")
    if not feature_cols_path.exists():
        raise FileNotFoundError(f"feature_columns.json not found at {feature_cols_path}")

    print(f"[INFO] Loading training data from {linear_train_path}")
    df = pd.read_parquet(linear_train_path)
    print(f"[INFO] Training table shape: {df.shape}")

    # -------------------------------------------------------------------------
    # Load feature columns
    # -------------------------------------------------------------------------
    with feature_cols_path.open("r") as f:
        feature_cols = json.load(f)

    missing_features = [c for c in feature_cols if c not in df.columns]
    if missing_features:
        raise ValueError(f"The following feature columns are missing in data: {missing_features}")

    if "target" not in df.columns:
        raise ValueError("Column 'target' is missing in training data.")
    if "customer_ID" not in df.columns:
        raise ValueError("Column 'customer_ID' is missing in training data.")

    # -------------------------------------------------------------------------
    # Customer-wise train/validation split
    # -------------------------------------------------------------------------
    print("[INFO] Performing customer-wise train/validation split...")
    customer_ids = df["customer_ID"].astype("string").unique()

    # Simple random split of customers (no time-based logic for now)
    train_customers, val_customers = train_test_split(
        customer_ids,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    train_mask = df["customer_ID"].isin(train_customers)
    val_mask = df["customer_ID"].isin(val_customers)

    train_df = df.loc[train_mask].reset_index(drop=True)
    val_df = df.loc[val_mask].reset_index(drop=True)

    print(f"[INFO] Train customers: {len(train_customers)}, rows: {train_df.shape[0]}")
    print(f"[INFO] Val customers:   {len(val_customers)}, rows: {val_df.shape[0]}")

    # -------------------------------------------------------------------------
    # Build X, y
    # -------------------------------------------------------------------------
    X_train = train_df[feature_cols]
    y_train = train_df["target"].astype(int)

    X_val = val_df[feature_cols]
    y_val = val_df["target"].astype(int)

    print(f"[INFO] X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"[INFO] X_val shape:   {X_val.shape}, y_val shape:   {y_val.shape}")

    # -------------------------------------------------------------------------
    # Define model pipeline
    # -------------------------------------------------------------------------
    # StandardScaler + LogisticRegression
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler(with_mean=False)),  # with_mean=False for sparse-safety
            (
                "logreg",
                LogisticRegression(
                    solver="saga",
                    penalty="l2",
                    max_iter=100,
                    n_jobs=-1,
                    verbose=1,
                ),
            ),
        ]
    )

    # -------------------------------------------------------------------------
    # Train
    # -------------------------------------------------------------------------
    print("[INFO] Training Logistic Regression model...")
    model.fit(X_train, y_train)

    # -------------------------------------------------------------------------
    # Evaluate
    # -------------------------------------------------------------------------
    print("[INFO] Evaluating on validation set...")
    # For ROC-AUC we need predicted probabilities
    if hasattr(model.named_steps["logreg"], "predict_proba"):
        y_val_pred_proba = model.predict_proba(X_val)[:, 1]
    else:
        # fallback: use decision function scaled via logistic
        decision = model.decision_function(X_val)
        y_val_pred_proba = 1 / (1 + np.exp(-decision))

    roc_auc = roc_auc_score(y_val, y_val_pred_proba)
    print(f"[RESULT] Validation ROC-AUC: {roc_auc:.6f}")

    # -------------------------------------------------------------------------
    # Save model and metrics
    # -------------------------------------------------------------------------
    model_path = models_dir / "best_model.pkl"
    metrics_path = models_dir / "metrics.json"

    print(f"[INFO] Saving trained model to {model_path}")
    joblib.dump(model, model_path)

    metrics = {
        "roc_auc": float(roc_auc),
        "n_train_rows": int(X_train.shape[0]),
        "n_val_rows": int(X_val.shape[0]),
        "n_features": int(X_train.shape[1]),
        "test_size": args.test_size,
        "random_state": args.random_state,
        "model_type": "logistic_regression_saga",
    }

    with metrics_path.open("w") as f:
        json.dump(metrics, f, indent=2)

    print(f"[INFO] Saved metrics to {metrics_path}")
    print("[INFO] Training step completed successfully.")


if __name__ == "__main__":
    main()
