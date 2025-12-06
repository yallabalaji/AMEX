#!/usr/bin/env python3
"""
AMEX Submission Validator
-------------------------

Runs in two modes:

1) ZERO-ARG MODE (default):
       python scripts/validate_submission.py
   Uses:
       submission/submission.csv
       data/raw/sample_submission.csv

2) ARGUMENT MODE:
       python scripts/validate_submission.py \
           --submission mysub.csv \
           --sample sample.csv \
           --out report.json

Both modes validated automatically.
"""

import argparse
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np


# -------------------------------
# Default paths (zero-arg mode)
# -------------------------------
DEFAULT_SUB = Path("submission/submission.csv")
DEFAULT_SAMPLE = Path("data/raw/sample_submission.csv")
DEFAULT_REPORT = Path("submission/validation_report.json")


# -------------------------------
# Helper: write fail message
# -------------------------------
def fail(msg, report, out_path):
    report["status"] = "FAIL"
    report["errors"].append(msg)
    out_path.write_text(json.dumps(report, indent=2))
    print("[FAIL]", msg)
    sys.exit(1)


# -------------------------------
# Main
# -------------------------------
def main():
    parser = argparse.ArgumentParser(description="Validate AMEX submission format.")
    parser.add_argument("--submission", type=str, help="Path to submission CSV")
    parser.add_argument("--sample", type=str, help="Path to sample_submission.csv")
    parser.add_argument("--out", type=str, help="Path to validation_report.json")

    args = parser.parse_args()

    # -----------------------------
    # Resolve paths based on mode
    # -----------------------------
    submission_path = Path(args.submission) if args.submission else DEFAULT_SUB
    sample_path = Path(args.sample) if args.sample else DEFAULT_SAMPLE
    report_path = Path(args.out) if args.out else DEFAULT_REPORT

    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Starting report
    report = {"status": "UNKNOWN", "errors": [], "metrics": {}}

    print(f"[INFO] Validating submission at: {submission_path}")

    # -----------------------------
    # Load submission
    # -----------------------------
    if not submission_path.exists():
        fail(f"Submission file not found: {submission_path}", report, report_path)

    try:
        df = pd.read_csv(submission_path)
    except Exception as e:
        fail(f"Could not read submission CSV: {e}", report, report_path)

    # Column validation
    cols = df.columns.tolist()
    report["metrics"]["columns"] = cols
    report["metrics"]["rows"] = len(df)

    if len(cols) < 2:
        fail(f"Submission must have 2 columns. Found: {cols}", report, report_path)

    id_col, pred_col = cols[:2]

    # Prediction column checks
    preds = pd.to_numeric(df[pred_col], errors="coerce")
    n_nan = int(preds.isna().sum())
    report["metrics"]["nan_predictions"] = n_nan

    if n_nan > 0:
        fail(f"Prediction column contains {n_nan} NaN values", report, report_path)

    pmin, pmax, mean_val = float(preds.min()), float(preds.max()), float(preds.mean())
    report["metrics"]["pred_min"] = pmin
    report["metrics"]["pred_max"] = pmax
    report["metrics"]["pred_mean"] = mean_val

    if pmin < 0.0 or pmax > 1.0:
        fail(f"Predictions out of range [0,1]: min={pmin}, max={pmax}", report, report_path)

    # -----------------------------
    # Compare with sample_submission (optional)
    # -----------------------------
    if sample_path.exists():
        sample = pd.read_csv(sample_path)
        if len(sample) != len(df):
            fail(f"Row mismatch: sample={len(sample)}, submission={len(df)}",
                 report, report_path)
    else:
        print(f"[WARN] No sample file at {sample_path}. Skipping row count validation.")

    # -----------------------------
    # Success
    # -----------------------------
    report["status"] = "OK"
    report_path.write_text(json.dumps(report, indent=2))

    print("[OK] Submission validated successfully.")
    print(f"[INFO] Report saved to {report_path}")


if __name__ == "__main__":
    main()
