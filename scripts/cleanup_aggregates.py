#!/usr/bin/env python3
import shutil
from pathlib import Path

AGG_DIR = Path("data/stage/aggregated")
TMP_DIR = AGG_DIR / "agg_tmp"

def safe_remove(path: Path):
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Removed dir: {path}")
        else:
            path.unlink()
            print(f"Removed file: {path}")
    else:
        print(f"Not found: {path}")

def main():
    if not AGG_DIR.exists():
        print("No aggregated folder found. Nothing to clean.")
        return

    # Remove tmp dir
    safe_remove(TMP_DIR)

    # Remove pattern-based partials
    for pat in ["*_numeric.parquet", "*_cat.parquet", "*_last.parquet", "final_*.parquet"]:
        for p in AGG_DIR.glob(pat):
            safe_remove(p)

    # Recreate tmp dir
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    print("Recreated tmp dir:", TMP_DIR)

if __name__ == "__main__":
    main()
