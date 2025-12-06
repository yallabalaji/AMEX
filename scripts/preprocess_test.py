#!/usr/bin/env python

"""
Stage 3: Preprocess Kaggle test data for AmEx Default Prediction.

Steps:
1. Read raw test_data.csv in chunks.
2. Apply the same preprocessing pipeline as training
   (types, imputations, missingness flags).
3. Save parquet parts under data/stage/refined_data (via preprocess_and_save_parquet).
4. Load those parts and apply load_and_prepare_for_linear
   using the existing category_map.json.
5. Save:
   - data/stage/linear_test.parquet
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from src
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.preprocessing import (
    preprocess_and_save_parquet,
    load_and_prepare_for_linear,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chunksize",
        type=int,
        default=100_000,
        help="Number of rows per chunk when reading test_data.csv",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"
    stage_dir = project_root / "data" / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)

    test_data_path = raw_dir / "test_data.csv"
    category_map_path = stage_dir / "category_map.json"

    if not test_data_path.exists():
        raise FileNotFoundError(f"test_data.csv not found at {test_data_path}")
    if not category_map_path.exists():
        raise FileNotFoundError(f"category_map.json not found at {category_map_path}")

    print(f"[INFO] Using test data: {test_data_path}")
    print(f"[INFO] Using category map: {category_map_path}")

    # -------------------------------------------------------------------------
    # 1. Preprocess test_data.csv into parquet parts
    # -------------------------------------------------------------------------
    output_prefix = stage_dir / "test_processed"
    print("[INFO] Preprocessing test_data.csv into parquet parts...")
    parquet_paths = preprocess_and_save_parquet(
        input_csv=str(test_data_path),
        output_prefix=str(output_prefix),
        chunksize=args.chunksize,
    )
    print(f"[INFO] Created {len(parquet_paths)} test parquet parts.")

    # -------------------------------------------------------------------------
    # 2. Build linear-ready DataFrame using existing category map
    # -------------------------------------------------------------------------
    print("[INFO] Loading test parquet parts and preparing linear features...")
    linear_test_df = load_and_prepare_for_linear(
        parquet_paths=parquet_paths,
        category_map_path=str(category_map_path),
    )
    print(f"[INFO] linear_test_df shape: {linear_test_df.shape}")

    # -------------------------------------------------------------------------
    # 3. Save linear_test.parquet
    # -------------------------------------------------------------------------
    linear_test_path = stage_dir / "linear_test.parquet"
    print(f"[INFO] Saving linear_test.parquet to {linear_test_path}")
    linear_test_df.to_parquet(linear_test_path, index=False)

    print("[INFO] Test preprocessing step completed successfully.")


if __name__ == "__main__":
    main()
