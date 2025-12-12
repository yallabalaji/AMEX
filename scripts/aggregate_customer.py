#!/usr/bin/env python3
"""
Simplified customer-level aggregation script.

Usage:
    python scripts/aggregate_customer.py train
    python scripts/aggregate_customer.py test

Behavior:
 - Uses fixed parts dir: data/stage/refined_data/
 - Writes outputs to: data/stage/aggregated/
 - Auto-cleans tmp folder before run (safe).
 - Produces:
     data/stage/aggregated/customer_level_{train|test}.parquet
     data/stage/aggregated/feature_columns_customer_{train|test}.json
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List
import sys
import gc


import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# -----------------------
# CONFIG (fixed per your choice)
# -----------------------
PARTS_DIR = Path("data/stage/refined_data")
OUT_DIR = Path("data/stage/aggregated")
TMP_DIR_NAME = "agg_tmp"

# These lists attempt to match your src.preprocessing; if you modify src you can keep this file unchanged.
# If you have src.preprocessing available, the script will import and use those lists instead.
try:
    from src.preprocessing import FLOAT16_COLS, FLOAT32_COLS, BOOL_COLS, CATEGORICAL_COLS
    logging.info("Imported column lists from src.preprocessing")
except Exception:
    logging.info("Falling back to embedded defaults for column lists")
    BOOL_COLS = ["B_31"]
    FLOAT16_COLS = [
        "D_66", "D_68", "B_30", "D_87", "B_38", "D_114", "D_116",
        "D_117", "D_120", "D_126",
    ]
    # abbreviated: real script will operate only on numeric cols present in parquet parts
    FLOAT32_COLS = ["P_2", "D_39", "B_1", "B_2", "R_1", "S_3", "D_41", "B_3"]
    CATEGORICAL_COLS = ["D_87", "D_120", "D_66", "D_116", "D_114", "D_126", "B_30", "D_117", "B_38"]

# Ensure D_63/D_64 are included as they are present in preprocessor and need mode-handling
ADDITIONAL_CAT = ["D_63", "D_64"]
LINEAR_CAT_COLS = sorted(set(CATEGORICAL_COLS + ADDITIONAL_CAT))

# numeric base - will be intersected with actual columns present in each part
NUMERIC_BASE = list(set(FLOAT16_COLS + FLOAT32_COLS))

LAST_ROW_KEEP = ["customer_ID", "S_2"] + ADDITIONAL_CAT

# -----------------------
# Utility helpers
# -----------------------
def find_parquet_parts(parts_dir: Path):
    parts = sorted([p for p in parts_dir.glob("*.parquet") if p.is_file()])
    return parts


def _clean_tmp(tmp_dir: Path):
    if tmp_dir.exists():
        logging.info("Auto-clean enabled: removing tmp dir %s", tmp_dir)
        for f in tmp_dir.glob("*"):
            try:
                f.unlink()
            except Exception:
                pass
    tmp_dir.mkdir(parents=True, exist_ok=True)


# -----------------------
# Per-part processing
# -----------------------
def per_part_aggregates(part_path: str, tmp_dir: str, numeric_cols: List[str], cat_cols: List[str],
                        customer_col: str = "customer_ID", time_col: str = "S_2") -> None:
    """
    Process a single parquet part and write three partial parquet outputs:
      - numeric partial (count, sum, sumsq, mean, std, min, max)
      - categorical partial (mode, nunique)
      - last-row partial (last row columns for each customer by time_col)

    Args:
        part_path: path to the parquet part file.
        tmp_dir: directory where partial parquet files will be written.
        numeric_cols: list of numeric columns to aggregate.
        cat_cols: list of categorical columns to summarise.
        customer_col: name of the customer id column (default 'customer_ID').
        time_col: name of the timestamp column used to pick the last row (default 'S_2').

    Notes:
        - If a column in numeric_cols/cat_cols is not present in the part, it is skipped.
        - Outputs are written as:
            <tmp_dir>/<part_stem>_numeric.parquet
            <tmp_dir>/<part_stem>_cat.parquet
            <tmp_dir>/<part_stem>_last.parquet
    """
    import pandas as pd
    import numpy as np
    from pathlib import Path

    p = Path(part_path)
    part_stem = p.stem

    print(f"[INFO] Processing part: {p.name}")

    df = pd.read_parquet(part_path)

    if customer_col not in df.columns:
        raise KeyError(f"{customer_col} not found in part {part_path}")

    # ensure time_col exists (if present, coerce to datetime)
    if time_col in df.columns:
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

    # -------------------------
    # Numeric aggregations
    # -------------------------
    present_numeric = [c for c in numeric_cols if c in df.columns]
    numeric_agg_frames = []

    if present_numeric:
        grp = df.groupby(customer_col)[present_numeric]

        # We'll compute count, sum, sumsq, mean, std, min, max in vectorized way
        # count & sum
        cnt = grp.count().rename(columns={c: f"{c}_count" for c in present_numeric})
        summ = grp.sum().rename(columns={c: f"{c}_sum" for c in present_numeric})
        # sum of squares (for potential variance calc)
        # compute via (x * x).sum() per group
        sumsqs = grp.apply(lambda g: (g**2).sum()).rename(columns={c: f"{c}_sumsq" for c in present_numeric})

        # min/max/mean/std
        minn = grp.min().rename(columns={c: f"{c}_min" for c in present_numeric})
        maxx = grp.max().rename(columns={c: f"{c}_max" for c in present_numeric})
        mean = grp.mean().rename(columns={c: f"{c}_mean" for c in present_numeric})
        std = grp.std(ddof=0).rename(columns={c: f"{c}_std" for c in present_numeric})  # population std (ddof=0)

        # Combine numeric pieces into a single DataFrame with a single concat to avoid fragmentation
        numeric_parts = [cnt, summ, sumsqs, mean, std, minn, maxx]
        numeric_df = pd.concat(numeric_parts, axis=1)

        # Defensive: ensure unique column names (remove duplicates, keep first)
        if numeric_df.columns.duplicated().any():
            numeric_df = numeric_df.loc[:, ~numeric_df.columns.duplicated()]

        # Reset index to have customer_ID as column (but be careful about collisions)
        numeric_out = numeric_df.reset_index()
    else:
        # create an empty numeric_out with only customer col
        numeric_out = pd.DataFrame(columns=[customer_col])

    # -------------------------
    # Categorical aggregations
    # -------------------------
    present_cat = [c for c in cat_cols if c in df.columns]
    if present_cat:
        # We'll compute mode and nunique per customer for each categorical col.
        # Building a dict of Series to concat once (avoid repeated inserts).
        cat_result_series = {}
        gcat = df.groupby(customer_col)

        # mode calculation helper: robust to empties
        def safe_mode(s):
            m = s.mode()
            if m.empty:
                return pd.NA
            return m.iloc[0]

        for c in present_cat:
            # mode
            mode_ser = gcat[c].agg(safe_mode).rename(f"{c}_mode")
            # nunique
            nunq = gcat[c].nunique(dropna=True).rename(f"{c}_nunique")
            cat_result_series[f"{c}_mode"] = mode_ser
            cat_result_series[f"{c}_nunique"] = nunq

        if cat_result_series:
            cat_df = pd.concat(cat_result_series.values(), axis=1)
            # ensure index name preserved
            cat_df.index.name = customer_col
            # drop duplicated columns if any
            if cat_df.columns.duplicated().any():
                cat_df = cat_df.loc[:, ~cat_df.columns.duplicated()]
            cat_out = cat_df.reset_index()
        else:
            cat_out = pd.DataFrame(columns=[customer_col])
    else:
        cat_out = pd.DataFrame(columns=[customer_col])

    # -------------------------
    # Last-row per customer (by timestamp)
    # -------------------------
    # We'll keep all columns listed in LAST_ROW_KEEP if present; otherwise fallback to S_2 and customer_ID
    LAST_ROW_KEEP = ["customer_ID", time_col]  # adjust externally if you want more columns kept
    keep_cols = [c for c in LAST_ROW_KEEP if c in df.columns]

    if time_col in df.columns:
        # idx of last row per customer
        idx = df.groupby(customer_col)[time_col].idxmax()
        # idx may contain NaN for groups where time is all NaT; drop those
        idx = idx.dropna().astype(int)
        if len(idx) > 0:
            last_rows = df.loc[idx, keep_cols + []].copy()  # keep a copy
            # make sure customer_ID is a column, not index
            if customer_col not in last_rows.columns and last_rows.index.name == customer_col:
                last_rows = last_rows.reset_index()
            # If customer_ID is index and also present as a column, remove duplicate column
            if customer_col in last_rows.columns and last_rows.index.name == customer_col:
                last_rows = last_rows.reset_index()
            last_out = last_rows.drop_duplicates(subset=[customer_col]).reset_index(drop=True)
        else:
            last_out = pd.DataFrame(columns=[customer_col] + [time_col])
    else:
        # No time column: fallback to taking the last appearance per customer by occurrence order
        idx = df.groupby(customer_col).apply(lambda g: g.index[-1] if len(g) else None)
        idx = idx.dropna().astype(int)
        if len(idx) > 0:
            last_rows = df.loc[idx, keep_cols + []].copy()
            last_out = last_rows.drop_duplicates(subset=[customer_col]).reset_index(drop=True)
        else:
            last_out = pd.DataFrame(columns=[customer_col])

    # Defensive: ensure no duplicate columns across outputs before writing
    def _dedup_columns_out(df_out: pd.DataFrame) -> pd.DataFrame:
        if df_out.columns.duplicated().any():
            df_out = df_out.loc[:, ~df_out.columns.duplicated()]
        return df_out

    numeric_out = _dedup_columns_out(numeric_out)
    cat_out = _dedup_columns_out(cat_out)
    last_out = _dedup_columns_out(last_out)

    # -------------------------
    # Write partial parquet files
    # -------------------------
    tmp_dir_p = Path(tmp_dir)
    tmp_dir_p.mkdir(parents=True, exist_ok=True)

    numeric_path = tmp_dir_p / f"{part_stem}_numeric.parquet"
    cat_path = tmp_dir_p / f"{part_stem}_cat.parquet"
    last_path = tmp_dir_p / f"{part_stem}_last.parquet"

    # Use to_parquet once per file
    numeric_out.to_parquet(numeric_path, index=False)
    cat_out.to_parquet(cat_path, index=False)
    last_out.to_parquet(last_path, index=False)

    print(f"[INFO] Wrote partials for part: {part_stem}")

# -----------------------
# Combine partials
# -----------------------
def combine_numeric_partials(tmp_dir: Path, out_path: Path):
    files = sorted(tmp_dir.glob("*_numeric.parquet"))
    if not files:
        logging.info("No numeric partials found")
        return pd.DataFrame()

    dfs = []
    for p in files:
        df = pd.read_parquet(p)
        if df.empty or "customer_ID" not in df.columns:
            continue
        df = df.set_index("customer_ID")
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    all_parts = pd.concat(dfs, axis=0, sort=False).fillna(0)
    grouped = all_parts.groupby(all_parts.index).sum()

    final = pd.DataFrame(index=grouped.index)
    # derive bases automatically
    cols = grouped.columns.tolist()
    bases = set()
    for c in cols:
        if c.endswith("_sum"):
            bases.add(c[:-4])
        elif c.endswith("_sumsq"):
            bases.add(c[:-7])
        elif c.endswith("_cnt"):
            bases.add(c[:-4])
    for base in sorted(bases):
        cnt = grouped.get(f"{base}_cnt", pd.Series(0, index=grouped.index)).astype(float)
        s = grouped.get(f"{base}_sum", pd.Series(0.0, index=grouped.index)).astype(float)
        ssq = grouped.get(f"{base}_sumsq", pd.Series(0.0, index=grouped.index)).astype(float)

        mean = s / cnt.replace({0: np.nan})
        var = (ssq / cnt.replace({0: np.nan})) - (mean ** 2)
        var = var.fillna(0.0).clip(lower=0.0)
        std = np.sqrt(var)

        # compute min/max by scanning partial files
        min_vals = []
        max_vals = []
        for p in files:
            part_df = pd.read_parquet(p).set_index("customer_ID")
            if f"{base}_min" in part_df.columns:
                min_vals.append(part_df[f"{base}_min"])
            if f"{base}_max" in part_df.columns:
                max_vals.append(part_df[f"{base}_max"])
        min_series = pd.concat(min_vals, axis=1).min(axis=1).reindex(index=grouped.index).fillna(np.nan) if min_vals else pd.Series(np.nan, index=grouped.index)
        max_series = pd.concat(max_vals, axis=1).max(axis=1).reindex(index=grouped.index).fillna(np.nan) if max_vals else pd.Series(np.nan, index=grouped.index)

        final[f"{base}_count"] = cnt.astype(int)
        final[f"{base}_mean"] = mean
        final[f"{base}_std"] = std
        final[f"{base}_min"] = min_series
        final[f"{base}_max"] = max_series

    out_path.parent.mkdir(parents=True, exist_ok=True)
    final_reset = final.reset_index()
    final_reset.to_parquet(out_path, index=False)
    return final_reset


def combine_cat_partials(tmp_dir: Path, out_path: Path, cat_cols):
    files = sorted(tmp_dir.glob("*_cat.parquet"))
    if not files:
        logging.info("No categorical partials found")
        return pd.DataFrame()

    dfs = []
    for p in files:
        df = pd.read_parquet(p)
        if df.empty or "customer_ID" not in df.columns:
            continue
        df = df.set_index("customer_ID")
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    all_parts = pd.concat(dfs, axis=0, sort=False)
    final = {}
    for c in [col for col in cat_cols if col in all_parts.columns]:
        mode_ser = all_parts.groupby(all_parts.index)[c].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA)
        final[c] = mode_ser

    if not final:
        # No categorical columns found - return empty DataFrame
        logging.info("No categorical columns found in partials")
        return pd.DataFrame()

    final_df = pd.concat(final, axis=1).reset_index()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(out_path, index=False)
    return final_df


def combine_last_partials(tmp_dir: Path, out_path: Path):
    files = sorted(tmp_dir.glob("*_last.parquet"))
    if not files:
        logging.info("No last-row partials found")
        return pd.DataFrame()

    dfs = []
    for p in files:
        df = pd.read_parquet(p)
        if df.empty or "customer_ID" not in df.columns:
            continue
        df = df.set_index("customer_ID")
        dfs.append(df)

    all_parts = pd.concat(dfs, axis=0, sort=False)
    if "S_2" in all_parts.columns:
        all_parts["S_2"] = pd.to_datetime(all_parts["S_2"])

    idx = all_parts.groupby(all_parts.index)["S_2"].idxmax()
    final = all_parts.loc[idx].reset_index()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final.to_parquet(out_path, index=False)
    return final


def merge_final(numeric_out: str, cat_out: str, last_out: str, final_out: str, customer_col: str = "customer_ID"):
    """
    Robust merging of partials into final customer-level table.

    Params:
        numeric_out, cat_out, last_out: file paths (parquet) — may not exist.
        final_out: output parquet filepath for merged table.
        customer_col: name of the customer id column (default 'customer_ID').

    Returns:
        merged DataFrame (also written to final_out).
    """
    import os
    import pandas as pd

    def _load_if_exists(path):
        if path and os.path.exists(path):
            df = pd.read_parquet(path)
            if df.shape[0] == 0:
                return None
            return df
        return None

    parts = []
    for path in (numeric_out, cat_out, last_out):
        df = _load_if_exists(path)
        if df is None:
            continue

        # Ensure customer_col is a column; if it's index, reset to column
        if df.index.name == customer_col:
            df = df.reset_index()
        # If customer_col is present as a column, set it as index
        if customer_col in df.columns:
            df = df.set_index(customer_col)

        # If index has duplicates, collapse them (keep first row per customer)
        if not df.index.is_unique:
            # use first non-null entry per column for duplicate customer rows
            df = df.groupby(df.index).first()

        parts.append(df)

    if not parts:
        # Nothing to merge: create an empty file (or raise)
        raise ValueError("No partials found to merge. Check agg_tmp for *_numeric/_cat/_last.parquet files.")

    # Now concat horizontally on index (customer_ID)
    merged = pd.concat(parts, axis=1, join="outer")

    # After concat, remove any duplicated columns (keep first occurrence)
    if merged.columns.duplicated().any():
        merged = merged.loc[:, ~merged.columns.duplicated()]

    # Reset index to have customer_ID as column
    merged = merged.reset_index()

    # Write final parquet (overwrite)
    out_dir = os.path.dirname(final_out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    merged.to_parquet(final_out, index=False)

    print(f"[INFO] Merged final customer-level table written to: {final_out} (rows={len(merged)})")
    return merged


def build_feature_list(customer_level_df: pd.DataFrame, out_json: Path, 
                       id_col="customer_ID", target_col="target"):
    # Columns to exclude from model input
    exclude = {id_col, target_col, "S_2"}

    cols = [c for c in customer_level_df.columns if c not in exclude]

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(cols, f, indent=2)

    logging.info("Feature list saved to: %s (cols=%d)", out_json, len(cols))
    return cols

def list_parts_for_mode(parts_dir: Path, mode: str) -> List[Path]:
    """
    Return list of parquet parts for the requested mode.

    Rules:
      - If mode == 'train', prefer files starting with 'train_'.
      - If mode == 'test', prefer files starting with 'test_'.
      - If no files match the strict prefix, attempt a looser match
        (containing 'train'/'test' anywhere).
      - Finally fallback to all parquet parts to avoid hard failure.

    This avoids mixing train/test parts accidentally.
    """
    parts_dir = Path(parts_dir)
    all_parts = sorted(parts_dir.glob("*.parquet"))

    if mode == "train":
        pref = "train_"
    elif mode == "test":
        pref = "test_"
    else:
        return all_parts

    strict = [p for p in all_parts if p.name.startswith(pref)]
    if strict:
        return strict

    # looser fallback
    loose = [p for p in all_parts if pref.rstrip("_") in p.name]
    if loose:
        return loose

    # final fallback to all files (keeps backward compatibility)
    return all_parts

# -----------------------
# Main
# -----------------------
def main():
    p = argparse.ArgumentParser(description="Aggregate customer-level features")
    p.add_argument("mode", choices=["train", "test"], help="mode: train or test")
    # optional overrides so you can run different folders without editing the script
    p.add_argument("--parts-dir", type=str, default=str(PARTS_DIR),
                   help="Directory containing parquet parts (default from constant PARTS_DIR)")
    p.add_argument("--out-dir", type=str, default=str(OUT_DIR),
                   help="Output directory for aggregated files (default from constant OUT_DIR)")
    p.add_argument("--verbose", action="store_true", help="Enable verbose debug output")
    args = p.parse_args()

    mode = args.mode
    parts_dir = Path(args.parts_dir)
    out_dir = Path(args.out_dir)
    tmp_dir = out_dir / TMP_DIR_NAME

    logging.info("Mode: %s", mode)
    logging.info("Parts dir: %s", parts_dir)
    logging.info("Out dir: %s", out_dir)

    if not parts_dir.exists():
        logging.error("Parts dir does not exist: %s", parts_dir)
        sys.exit(1)

    # Auto-clean tmp (existing behavior)
    _clean_tmp(tmp_dir)

    # --- use helper that filters parts by mode (train_/test_ preference) ---
    parts = list_parts_for_mode(parts_dir, mode)
    if not parts:
        logging.error("No parquet parts found in %s for mode=%s", parts_dir, mode)
        sys.exit(1)

    logging.info("Found %d parquet parts (mode=%s)", len(parts), mode)
    if args.verbose:
        example = ", ".join(p.name for p in parts[:5])
        logging.debug("Example parts: %s", example)

    numeric_cols = NUMERIC_BASE.copy()
    cat_cols = LINEAR_CAT_COLS.copy()

    for pth in parts:
        marker = tmp_dir / f"{pth.stem}_numeric.parquet"
        if marker.exists() and marker.stat().st_size > 0:
            logging.info("Skipping already-processed part: %s", pth.name)
            continue
        per_part_aggregates(pth, tmp_dir, numeric_cols, cat_cols)

    numeric_out = out_dir / f"customer_numeric_{mode}.parquet"
    cat_out = out_dir / f"customer_cat_{mode}.parquet"
    last_out = out_dir / f"customer_last_{mode}.parquet"
    final_out = out_dir / f"customer_level_{mode}.parquet"
    feature_json = out_dir / f"feature_columns_customer_{mode}.json"

    logging.info("Combining numeric partials...")
    df_num = combine_numeric_partials(tmp_dir, numeric_out)

    logging.info("Combining categorical partials...")
    df_cat = combine_cat_partials(tmp_dir, cat_out, cat_cols)

    logging.info("Combining last-row partials...")
    df_last = combine_last_partials(tmp_dir, last_out)

    logging.info("Merging final customer-level table...")
    final_df = merge_final(numeric_out, cat_out, last_out, final_out)

    logging.info("Building feature list...")
    build_feature_list(final_df, feature_json)

    logging.info("Completed aggregation. Final file: %s", final_out)
    logging.info("Temp files are stored in: %s (auto-cleaned before run)", tmp_dir)


if __name__ == "__main__":
    main()
