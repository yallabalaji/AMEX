#!/usr/bin/env python3
"""
Validate train/test customer-level features and optionally reindex the test table
to exactly match the train feature list (same columns + ordering).

Usage:
    # Dry run: compare features and show summary
    python scripts/validate_features.py

    # Compare and save a reindexed test parquet (fill missing with 0.0)
    python scripts/validate_features.py --save --out data/stage/aggregated/customer_level_test_reindexed.parquet

    # Custom paths:
    python scripts/validate_features.py \
        --train-feats data/stage/aggregated/feature_columns_customer_train.json \
        --test-parquet data/stage/aggregated/customer_level_test.parquet \
        --out data/stage/aggregated/customer_level_test_reindexed.parquet \
        --fill-value 0.0
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_TRAIN_FEATS = Path("data/stage/aggregated/feature_columns_customer_train.json")
DEFAULT_TEST_PARQUET = Path("data/stage/aggregated/customer_level_test.parquet")


def load_feature_list(p: Path):
    if not p.exists():
        raise FileNotFoundError(f"Train feature list not found: {p}")
    with open(p, "r") as f:
        feats = json.load(f)
    if not isinstance(feats, list):
        raise ValueError("Feature file must be a JSON list")
    return feats


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--train-feats", type=str, default=str(DEFAULT_TRAIN_FEATS))
    p.add_argument("--test-parquet", type=str, default=str(DEFAULT_TEST_PARQUET))
    p.add_argument("--save", action="store_true", help="Save reindexed test parquet to --out")
    p.add_argument("--out", type=str, default="data/stage/aggregated/customer_level_test_reindexed.parquet")
    p.add_argument("--fill-value", type=float, default=0.0, help="Fill value for missing features")
    p.add_argument("--sample", type=int, default=5, help="Show up to N sample missing/extra columns")
    args = p.parse_args()

    train_feats = load_feature_list(Path(args.train_feats))
    test_p = Path(args.test_parquet)
    if not test_p.exists():
        raise FileNotFoundError(f"Test parquet not found: {test_p}")

    print(f"[INFO] Loaded train feature list ({len(train_feats)} features) from: {args.train_feats}")
    print(f"[INFO] Loading test parquet (customer-level) from: {test_p} (this may take a moment)...")
    df_test = pd.read_parquet(test_p)
    print(f"[INFO] test table shape: {df_test.shape}")

    # ensure customer id exists
    if "customer_ID" not in df_test.columns:
        raise KeyError("customer_ID not found in test parquet. Aggregation step may have failed.")

    # compute sets
    train_set = set(train_feats)
    test_set = set([c for c in df_test.columns if c != "customer_ID"])
    missing = sorted(list(train_set - test_set))
    extra = sorted(list(test_set - train_set))

    print(f"[RESULT] Train features: {len(train_feats)}")
    print(f"[RESULT] Test features (excl customer_ID): {len(test_set)}")
    print(f"[RESULT] Missing features in test (train - test): {len(missing)}")
    print(f"[RESULT] Extra features in test (test - train): {len(extra)}")
    if missing:
        print("  Missing sample:", missing[: args.sample])
    if extra:
        print("  Extra sample:", extra[: args.sample])

    # Column dtype sanity: check numeric columns that are present are numeric-ish
    numeric_cols = []
    non_numeric = []
    for col in train_feats:
        if col in df_test.columns:
            if pd.api.types.is_numeric_dtype(df_test[col].dtype):
                numeric_cols.append(col)
            else:
                non_numeric.append((col, str(df_test[col].dtype)))
    print(f"[INFO] Train features present in test and numeric: {len(numeric_cols)}")
    if non_numeric:
        print(f"[WARN] {len(non_numeric)} train features present in test but non-numeric (sample): {non_numeric[:5]}")

    # Show a small sample of rows for sanity (first customer)
    print("\n[INFO] Sample row (first 3 columns):")
    print(df_test.head(1).iloc[:, : min(8, df_test.shape[1])].T.head(10))

    if args.save:
        out_p = Path(args.out)
        print(f"[INFO] Reindexing test to train features and filling missing with {args.fill_value} ...")
        # create ordered columns: customer_ID then train features
        cols = ["customer_ID"] + train_feats
        # reindex will add missing columns with NaN
        df_reindexed = df_test.reindex(columns=cols)
        # fill missing with fill-value (only on features, not customer_ID)
        feat_cols = [c for c in cols if c != "customer_ID"]
        df_reindexed[feat_cols] = df_reindexed[feat_cols].fillna(args.fill_value).astype(np.float32)
        # keep customer_ID as string
        df_reindexed["customer_ID"] = df_reindexed["customer_ID"].astype("string")
        print(f"[INFO] Saving reindexed parquet to: {out_p}")
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_reindexed.to_parquet(out_p, index=False)
        print(f"[INFO] Saved {out_p} (shape={df_reindexed.shape})")

    print("[INFO] Done.")


if __name__ == "__main__":
    main()
