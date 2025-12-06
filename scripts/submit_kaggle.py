#!/usr/bin/env python3
"""
Submit a Kaggle CSV to a competition — wrapper used by pipelines.

Usage (examples):
  python scripts/submit_kaggle.py --file submission/submission.linear.csv --msg "linear v1"
  python scripts/submit_kaggle.py --file submission/submission.linear.csv --msg "auto" --wait 30

Features:
 - Validates submission via scripts/validate_submission.py if available
 - Backs up the submission to backup/submissions/
 - Calls `kaggle competitions submit` under the hood (so requires kaggle CLI)
 - Parses submission id & status and prints it (return code = 0 on success)
"""

import argparse
import subprocess
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime
import os

def run_cmd(cmd, capture_output=True, check=False, env=None):
    return subprocess.run(cmd, shell=False, capture_output=capture_output, text=True, check=check, env=env)

def validate_submission(path_submission, sample=None, validator_script="scripts/validate_submission.py"):
    if not Path(validator_script).exists():
        print(f"[WARN] Validator script not found at {validator_script}. Skipping validation.")
        return True
    cmd = [sys.executable, validator_script, "--submission", str(path_submission)]
    if sample:
        cmd += ["--sample", str(sample)]
    print("[INFO] Running validator:", " ".join(cmd))
    res = run_cmd(cmd, check=False)
    print(res.stdout)
    if res.returncode != 0:
        print("[ERROR] Validation failed. Validator output:", res.stderr or res.stdout)
        return False
    return True

def backup_submission(path_submission, backup_dir="backup/submissions"):
    p = Path(backup_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dst = p / f"{path_submission.stem}.{ts}{path_submission.suffix}"
    shutil.copy2(path_submission, dst)
    print(f"[INFO] Backed up submission to {dst}")
    return dst

def ensure_kaggle_cli():
    # check presence
    try:
        res = run_cmd(["kaggle", "--version"], capture_output=True, check=True)
        print("[INFO] Kaggle CLI:", res.stdout.strip())
        return True
    except Exception as e:
        print("[ERROR] kaggle CLI not found or failed. Install with 'pip install kaggle' and configure ~/.kaggle/kaggle.json")
        return False

def submit_to_kaggle(path_submission: Path, competition: str, message: str, env=None):
    cmd = ["kaggle", "competitions", "submit", "-c", competition, "-f", str(path_submission), "-m", message]
    print("[INFO] Running:", " ".join(cmd))
    res = run_cmd(cmd, check=False, env=env)
    if res.returncode != 0:
        print("[ERROR] Kaggle submit failed:", res.stderr or res.stdout)
        raise RuntimeError("kaggle submit failed")
    out = (res.stdout or "") + (res.stderr or "")
    print("[INFO] Kaggle CLI output:\n", out)
    return out

def parse_submission_response(kaggle_output: str):
    # Typical output contains "Successfully submitted to ... Submission ID: 1234567"
    lines = kaggle_output.splitlines()
    data = {"raw": kaggle_output, "submission_id": None, "message": None}
    for line in lines:
        if "Submission ID" in line:
            # e.g. "Submission ID: 1234567"
            parts = line.split("Submission ID")
            if len(parts) >= 2:
                # try to extract numeric id
                import re
                m = re.search(r"(\d+)", line)
                if m:
                    data["submission_id"] = m.group(1)
        if "Successfully submitted" in line:
            data["message"] = line.strip()
    return data

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", "-f", required=True, help="Submission CSV to upload")
    p.add_argument("--msg", "-m", default="auto submit", help="Submission message")
    p.add_argument("--competition", "-c", default="amex-default-prediction", help="Kaggle competition code")
    p.add_argument("--backup", action="store_true", help="Backup submission to backup/submissions/")
    p.add_argument("--sample", default="data/raw/sample_submission.csv", help="Optional sample file for validator")
    p.add_argument("--wait", type=int, default=0, help="Optional: wait up to N seconds for Kaggle status (polling). 0 = don't wait")
    args = p.parse_args()

    submission_path = Path(args.file)
    if not submission_path.exists():
        print(f"[ERROR] Submission file not found: {submission_path}")
        sys.exit(2)

    # Step 0: validate
    ok = validate_submission(submission_path, sample=args.sample)
    if not ok:
        print("[ERROR] Submission validation failed. Aborting.")
        sys.exit(3)

    # Step 1: backup
    if args.backup:
        backup_submission(submission_path)

    # Step 2: ensure kaggle CLI
    if not ensure_kaggle_cli():
        sys.exit(4)

    # Step 3: set up env optionally (KAGGLE creds)
    # You can also provider KAGGLE_USERNAME/KAGGLE_KEY via env; here we pass current env through.
    env = os.environ.copy()

    # Step 4: submit
    try:
        out = submit_to_kaggle(submission_path, args.competition, args.msg, env=env)
    except Exception as e:
        print("[ERROR] Submission failed:", e)
        sys.exit(5)

    parsed = parse_submission_response(out)
    print("[INFO] Parsed response:", json.dumps(parsed, indent=2))

    # Optional: poll for status (basic naive implementation)
    if args.wait and parsed.get("submission_id"):
        import time
        sid = parsed["submission_id"]
        timeout = args.wait
        interval = 10
        start = time.time()
        print(f"[INFO] Polling Kaggle for submission {sid} status up to {timeout}s ...")
        while time.time() - start < timeout:
            # Use `kaggle competitions submissions -c COMPETITION` to list
            try:
                r = run_cmd(["kaggle", "competitions", "submissions", "-c", args.competition], check=True)
                print(r.stdout)
                # crude check for the submission id in the output; you can parse full table if needed
                if sid in (r.stdout or ""):
                    print("[INFO] Found submission in listing; you can inspect status on Kaggle site.")
                    break
            except Exception:
                pass
            time.sleep(interval)

    sys.exit(0)


if __name__ == "__main__":
    main()
