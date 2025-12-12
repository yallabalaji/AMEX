#!/usr/bin/env python3
"""
Train LightGBM model using:
 - customer_level_train.parquet
 - linear_train.parquet
 - train_labels.csv

Then merge test features, generate predictions, and create submission.csv.

Output files:
 - models/lightgbm_model.txt
 - data/submissions/submission.csv
"""

import pandas as pd
import lightgbm as lgb
from pathlib import Path
import json
import os
import numpy as np


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
BASE = Path("data")
STAGE = BASE / "stage"
RAW = BASE / "raw"
AGG = STAGE / "aggregated"

TRAIN_AGG = AGG / "customer_level_train.parquet"
TRAIN_LIN = STAGE / "linear_train.parquet"
TRAIN_LABELS = RAW / "train_labels.csv"

TEST_AGG = AGG / "customer_level_test.parquet"
TEST_LIN = STAGE / "linear_test.parquet"

FEATURE_JSON = AGG / "feature_columns_customer_train.json"

SUBMISSION_DIR = BASE / "submissions"
MODEL_DIR = Path("models")


# ---------------------------------------------------------
# Ensure dirs exist
# ---------------------------------------------------------
SUBMISSION_DIR.mkdir(exist_ok=True, parents=True)
MODEL_DIR.mkdir(exist_ok=True, parents=True)


# ---------------------------------------------------------
# Load training data
# ---------------------------------------------------------
print("\n[1] Loading train customer-level features...")
df_cust = pd.read_parquet(TRAIN_AGG)

print("[2] Loading train linear features (includes target)...")
df_lin = pd.read_parquet(TRAIN_LIN)

print(f"Train shapes → cust={df_cust.shape}, linear={df_lin.shape}")

# Verify target exists in linear data
if "target" not in df_lin.columns:
    print("[3] Loading labels...")
    df_lbl = pd.read_csv(TRAIN_LABELS)
    df_lin = df_lin.merge(df_lbl, on="customer_ID", how="left")
    print(f"Added target column. New shape: {df_lin.shape}")


# ---------------------------------------------------------
# Merge customer-level features with linear features
# ---------------------------------------------------------
print("\n[4] Merging training tables...")
df_train = df_lin.merge(df_cust, on="customer_ID", how="left")

print("Final merged train shape:", df_train.shape)
print("Has target:", "target" in df_train.columns)


# ---------------------------------------------------------
# Identify feature columns
# ---------------------------------------------------------
print("\n[5] Loading feature list...")
with open(FEATURE_JSON, "r") as f:
    customer_cols = json.load(f)

# Add linear feature columns (exclude customer_ID and target)
linear_cols = [c for c in df_lin.columns if c not in ["customer_ID", "target"]]

# Combine all potential features
all_features = sorted(set(customer_cols + linear_cols))

# Filter to only columns that actually exist in df_train (excluding ID and target)
exclude_cols = {"customer_ID", "target", "S_2"}
features = [c for c in all_features if c in df_train.columns and c not in exclude_cols]

print(f"Total features: {len(features)}")


# ---------------------------------------------------------
# Prepare LightGBM Dataset
# ---------------------------------------------------------
X_train = df_train[features]
y_train = df_train["target"]

print("[6] Training set:", X_train.shape, "labels:", y_train.shape)

train_set = lgb.Dataset(X_train, label=y_train)


# ---------------------------------------------------------
# Train LightGBM model
# ---------------------------------------------------------
print("\n[7] Training LightGBM model...")

params = {
    "objective": "binary",
    "metric": "binary_logloss",
    "learning_rate": 0.02,
    "num_leaves": 96,
    "max_depth": -1,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 3,
    "lambda_l2": 2.0,
    "verbosity": -1,
}

model = lgb.train(
    params,
    train_set,
    num_boost_round=1200,
)

model_file = MODEL_DIR / "lightgbm_model.txt"
model.save_model(str(model_file))
print(f"[✔] Model saved to {model_file}")


# ---------------------------------------------------------
# Load test features & predict in chunks (memory-efficient)
# ---------------------------------------------------------
print("\n[8] Loading test data...")
test_cust = pd.read_parquet(TEST_AGG)
test_lin = pd.read_parquet(TEST_LIN)

print("Test shapes → cust=", test_cust.shape, "linear=", test_lin.shape)

# Process test data in chunks to avoid OOM
CHUNK_SIZE = 500_000  # Process 500k rows at a time
print(f"\n[9] Processing test data in chunks of {CHUNK_SIZE:,} rows...")

predictions_list = []
total_rows = len(test_lin)
num_chunks = (total_rows + CHUNK_SIZE - 1) // CHUNK_SIZE

for chunk_idx in range(num_chunks):
    start_idx = chunk_idx * CHUNK_SIZE
    end_idx = min(start_idx + CHUNK_SIZE, total_rows)
    
    print(f"  Chunk {chunk_idx + 1}/{num_chunks}: rows {start_idx:,} to {end_idx:,}")
    
    # Get chunk of linear data
    chunk_lin = test_lin.iloc[start_idx:end_idx].copy()
    
    # Merge with customer-level features
    chunk_merged = chunk_lin.merge(test_cust, on="customer_ID", how="left")
    
    # Ensure same feature order and fill missing values
    chunk_features = chunk_merged[features].fillna(0)
    
    # Predict
    chunk_preds = model.predict(chunk_features)
    
    # Store customer_ID and predictions
    for cust_id, pred in zip(chunk_merged["customer_ID"], chunk_preds):
        predictions_list.append({"customer_ID": cust_id, "prediction": pred})
    
    # Free memory
    del chunk_lin, chunk_merged, chunk_features, chunk_preds
    
    # Force garbage collection every 5 chunks
    if (chunk_idx + 1) % 5 == 0:
        import gc
        gc.collect()

print(f"\n[10] Aggregating predictions to customer level...")
# Convert to DataFrame
df_predictions = pd.DataFrame(predictions_list)

# Aggregate to customer level (take last prediction per customer, matching test set structure)
df_submission = df_predictions.groupby("customer_ID", as_index=False).last()

print(f"Total unique customers in submission: {len(df_submission):,}")

# Create submission
submission_path = SUBMISSION_DIR / "submission.csv"
df_submission[["customer_ID", "prediction"]].to_csv(submission_path, index=False)

print(f"[✔] Submission saved to: {submission_path}")

print("\n[DONE] Training + Prediction pipeline completed successfully.")
