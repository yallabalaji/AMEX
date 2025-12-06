import warnings
warnings.filterwarnings("ignore", message="X does not have valid feature names")

#!/usr/bin/env python3
"""
Chunked submission generator for AMEX competition.

Usage:
    python scripts/generate_submission.py \
        --model-path models/best_model.pkl \
        --feature-path data/stage/feature_columns.json \
        --test-parquet data/stage/linear_test.parquet \
        --out submission/submission.csv \
        --batch-size 100000

Notes:
 - Requires: pyarrow, pandas, joblib, tqdm, numpy
 - Designed to be memory-friendly for very large test sets.
"""

import argparse
import json
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from tqdm import tqdm
import pyarrow.dataset as ds
from datetime import datetime

# -----------------------------
# Helpers
# -----------------------------
def load_model(model_path: Path):
    obj = joblib.load(model_path)
    if isinstance(obj, dict):
        model = obj.get("model") or obj.get("estimator") or obj.get("clf")
        scaler = obj.get("scaler")
        return model, scaler
    else:
        return obj, None

def predict_proba_array(model, X):
    """
    Unified predict_proba/predict wrapper.
    Returns float array of probabilities [0..1].
    """
    # Some boosters (lgb, xgb, catboost) implement predict returning probs directly.
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)
        # predict_proba may return shape (n,2)
        if probs.ndim == 2:
            return probs[:, 1]
        else:
            # fallback: if single-column proba
            return probs.ravel()
    else:
        # fallback to predict (some boosters return probabilities)
        ypred = model.predict(X)
        ypred = np.asarray(ypred)
        # If predictions are 0/1, convert to floats (not ideal but fallback)
        if ypred.dtype == np.int64 or ypred.dtype == np.int32 or np.array_equal(ypred, ypred.astype(bool)):
            return ypred.astype(float)
        return ypred.astype(float)

def ensure_feature_list(feature_path: Path):
    if not feature_path.exists():
        raise FileNotFoundError(f"Feature file not found: {feature_path}")
    with open(feature_path, "r") as f:
        features = json.load(f)
    if not isinstance(features, list):
        raise ValueError("Feature file must contain a JSON list of column names")
    return features

# -----------------------------
# Main
# -----------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-path", type=str, default="models/best_model.pkl")
    p.add_argument("--feature-path", type=str, default="data/stage/feature_columns.json")
    p.add_argument("--test-parquet", type=str, default="data/stage/linear_test.parquet")
    p.add_argument("--out", type=str, default="submission/submission.csv")
    p.add_argument("--temp-pred", type=str, default="submission/_row_predictions.csv")
    p.add_argument("--batch-size", type=int, default=100_000)
    p.add_argument("--customer-col", type=str, default="customer_ID")
    p.add_argument("--time-col", type=str, default="S_2")
    p.add_argument("--id-col-in-sample", type=str, default="customer_ID")
    args = p.parse_args()

    model_path = Path(args.model_path)
    feature_path = Path(args.feature_path)
    test_parquet = Path(args.test_parquet)
    out_path = Path(args.out)
    temp_pred = Path(args.temp_pred)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Loading model from: {model_path}")
    model, scaler = load_model(model_path)
    print(f"[INFO] Model loaded. Scaler present: {scaler is not None}")

    print(f"[INFO] Loading feature list from: {feature_path}")
    feature_cols = ensure_feature_list(feature_path)
    print(f"[INFO] Feature count: {len(feature_cols)}")

    print(f"[INFO] Preparing to stream test parquet: {test_parquet}")
    dataset = ds.dataset(str(test_parquet), format="parquet")

    # Remove existing temp preds if present
    if temp_pred.exists():
        print(f"[INFO] Removing existing temporary prediction file: {temp_pred}")
        temp_pred.unlink()

    # We'll append CSV rows: customer_ID, S_2 (ISO), proba
    header_written = False

    # Iterate over record batches
    print(f"[INFO] Streaming and predicting in batches (batch_size={args.batch_size})...")
    for batch in dataset.to_batches(batch_size=args.batch_size):
        df = batch.to_pandas()  # convert to pandas dataframe for operations

        # Keep only needed columns (customer, time, features). If time missing, keep NaT.
        keep_cols = [args.customer_col, args.time_col] + [c for c in feature_cols if c in df.columns]
        df_sub = df[keep_cols].copy()

        # Reindex to full feature columns (adds missing columns with NaN)
        # We need the feature columns in the exact order used for training
        X = df_sub.reindex(columns=[args.customer_col, args.time_col] + feature_cols, fill_value=np.nan)

        # Extract time and customer columns separately
        customer_series = X[args.customer_col]
        time_series = X[args.time_col]
        X_features = X[feature_cols].fillna(0.0)  # fill missing dummy columns with 0

        # If scaler present, apply it (scaler expects 2D numpy)
        if scaler is not None:
            X_input = scaler.transform(X_features)
        else:
            X_input = X_features.values

        # Predict probabilities
        try:
            probs = predict_proba_array(model, X_input)
        except Exception as e:
            # Try converting X_input to numpy explicitly and retry
            probs = predict_proba_array(model, np.asarray(X_input))

        # Build dataframe of results for this batch
        # Convert time to ISO string for reliable max comparisons later
        time_iso = pd.to_datetime(time_series).dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
        batch_out = pd.DataFrame({
            args.customer_col: customer_series.values,
            args.time_col: time_iso.values,
            "proba": probs.astype(float)
        })

        # Append to temp CSV
        mode = "a"
        header = not header_written
        batch_out.to_csv(temp_pred, mode=mode, header=header, index=False)
        header_written = True

    print(f"[INFO] Completed per-row predictions and saved to temp file: {temp_pred}")

    # -----------------------------
    # Aggregate to customer-level by last S_2
    # -----------------------------
    print("[INFO] Aggregating to customer-level (last S_2 per customer)...")
    # We'll stream-read the temp_pred CSV in chunks and keep an in-memory mapping for latest S_2 per customer
    cust_map = {}  # customer_id -> (latest_time_iso_str, proba)

    for chunk in pd.read_csv(temp_pred, chunksize=200_000):
        # Ensure proper dtypes
        # chunk[args.time_col] is ISO string; compare lexicographically is safe for isoformat
        for idx, row in chunk.iterrows():
            cust = row[args.customer_col]
            t = row[args.time_col]
            p = float(row["proba"])
            if pd.isna(cust):
                continue
            if cust not in cust_map:
                cust_map[cust] = (t, p)
            else:
                # Compare times (ISO strings)
                if t and (cust_map[cust][0] is None or t > cust_map[cust][0]):
                    cust_map[cust] = (t, p)

    print(f"[INFO] Aggregated predictions for {len(cust_map):,} customers")

    # -----------------------------
    # Build final submission DataFrame
    # -----------------------------
    print("[INFO] Building submission DataFrame...")
    # Some Kaggle formats expect customer_ID column name exact. We'll read sample_submission to get exact header.
    sample_sub_path = Path("data/raw/sample_submission.csv")
    if sample_sub_path.exists():
        sample = pd.read_csv(sample_sub_path, nrows=0)
        submission_cols = sample.columns.tolist()
        # Expecting ['customer_ID', 'prediction'] or similar
        if len(submission_cols) >= 2:
            id_col = submission_cols[0]
            pred_col = submission_cols[1]
        else:
            id_col = args.id_col_in_sample
            pred_col = "prediction"
    else:
        id_col = args.id_col_in_sample
        pred_col = "prediction"

    # Prepare final DF
    out_rows = []
    for cust, (t, p) in cust_map.items():
        out_rows.append({id_col: cust, pred_col: p})

    submission_df = pd.DataFrame(out_rows)
    # Ensure column order
    submission_df = submission_df[[id_col, pred_col]]

    # If sample submission exists, ensure we preserve order and missing customers (fill with 0.5)
    if sample_sub_path.exists():
        sample_full = pd.read_csv(sample_sub_path)
        # Merge to preserve order
        merged = sample_full[[id_col]].merge(submission_df, on=id_col, how="left")
        # Fill missing with mean or 0.5
        if pred_col in merged.columns:
            merged[pred_col] = merged[pred_col].fillna(merged[pred_col].mean() if merged[pred_col].notna().any() else 0.5)
        else:
            merged[pred_col] = 0.5
        submission_df = merged

    # Save submission
    print(f"[INFO] Saving submission to: {out_path}")
    submission_df.to_csv(out_path, index=False)
    print("[INFO] Submission saved.")

    # Optionally remove temp file
    # temp_pred.unlink(missing_ok=True)
    print("[INFO] Done.")

if __name__ == "__main__":
    main()
