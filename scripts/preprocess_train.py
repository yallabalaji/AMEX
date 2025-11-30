#!/usr/bin/env python

"""
Stage 1: Preprocess training data for AmEx Default Prediction.

Steps:
1. Read raw train_data.csv in chunks.
2. Apply preprocessing (types, imputations, missingness flags).
3. Save chunked parquet parts under data/stage/refined_data.
4. Build category_map.json from the parquet parts (for stable linear encoding).
5. Build a linear-ready DataFrame with one-hot encoding.
6. Merge with train_labels.csv.
7. Save:
   - data/stage/linear_train.parquet
   - data/stage/category_map.json
   - data/stage/feature_columns.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from src
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))


import pandas as pd

from src.preprocessing import (
    preprocess_and_save_parquet,
    build_category_map,
    load_and_prepare_for_linear,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chunksize",
        type=int,
        default=100_000,
        help="Number of rows per chunk when reading train_data.csv",
    )
    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # Paths
    # -------------------------------------------------------------------------
    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"
    stage_dir = project_root / "data" / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)

    train_data_path = raw_dir / "train_data.csv"
    train_labels_path = raw_dir / "train_labels.csv"

    if not train_data_path.exists():
        raise FileNotFoundError(f"train_data.csv not found at {train_data_path}")
    if not train_labels_path.exists():
        raise FileNotFoundError(f"train_labels.csv not found at {train_labels_path}")

    print(f"[INFO] Using train data:   {train_data_path}")
    print(f"[INFO] Using train labels: {train_labels_path}")
    print(f"[INFO] Stage directory:    {stage_dir}")

    # -------------------------------------------------------------------------
    # 1. Preprocess train_data.csv into parquet parts
    # -------------------------------------------------------------------------
    output_prefix = stage_dir / "train_processed"
    print("[INFO] Preprocessing train_data.csv into parquet parts...")
    parquet_paths = preprocess_and_save_parquet(
        input_csv=str(train_data_path),
        output_prefix=str(output_prefix),
        chunksize=args.chunksize,
    )
    print(f"[INFO] Created {len(parquet_paths)} parquet parts.")

    # -------------------------------------------------------------------------
    # 2. Build category map from training parquet parts
    # -------------------------------------------------------------------------
    category_map_path = stage_dir / "category_map.json"
    print(f"[INFO] Building category map at {category_map_path} ...")
    build_category_map(parquet_paths, output_path=str(category_map_path))

    # -------------------------------------------------------------------------
    # 3. Build linear-ready DataFrame (consistent one-hot encoding)
    # -------------------------------------------------------------------------
    print("[INFO] Loading parquet parts and preparing linear features...")
    linear_df = load_and_prepare_for_linear(
        parquet_paths=parquet_paths,
        category_map_path=str(category_map_path),
    )
    print(f"[INFO] linear_df shape (before merging labels): {linear_df.shape}")

    # -------------------------------------------------------------------------
    # 4. Merge with labels
    # -------------------------------------------------------------------------
    print("[INFO] Merging with train_labels.csv ...")
    labels_df = pd.read_csv(train_labels_path)

    # Ensure customer_ID type matches (string on both sides)
    if "customer_ID" in labels_df.columns:
        labels_df["customer_ID"] = labels_df["customer_ID"].astype("string")

    train_df = linear_df.merge(labels_df, on="customer_ID", how="left")

    if "target" not in train_df.columns:
        raise ValueError("Column 'target' not found after merging labels. Check join keys.")

    print(f"[INFO] train_df shape (after merging labels): {train_df.shape}")

    # -------------------------------------------------------------------------
    # 5. Save linear_train.parquet
    # -------------------------------------------------------------------------
    linear_train_path = stage_dir / "linear_train.parquet"
    print(f"[INFO] Saving full training table to {linear_train_path} ...")
    train_df.to_parquet(linear_train_path, index=False)

    # -------------------------------------------------------------------------
    # 6. Define and save feature_columns.json
    # -------------------------------------------------------------------------
    drop_cols = ["customer_ID", "target", "S_2"]  # we won't feed these to linear models
    feature_cols = [c for c in train_df.columns if c not in drop_cols]

    feature_cols_path = stage_dir / "feature_columns.json"
    with feature_cols_path.open("w") as f:
        json.dump(feature_cols, f)

    print(f"[INFO] Saved {len(feature_cols)} feature columns to {feature_cols_path}")
    print("[INFO] Preprocess train step completed successfully.")


if __name__ == "__main__":
    main()
