"""
Download AMEX Kaggle dataset safely using macOS Keychain via keyring.
Files are stored in: data/raw/
Already existing files are skipped.
"""

import os
import requests
import zipfile
from pathlib import Path
from tqdm import tqdm
import keyring

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Load credentials from macOS Keychain
# -----------------------------------------------------------------------------
KAGGLE_USERNAME = keyring.get_password("KAGGLE_USERNAME", "kaggle_username")
KAGGLE_KEY = keyring.get_password("KAGGLE_KEY", "kaggle_key")

if not KAGGLE_USERNAME or not KAGGLE_KEY:
    raise RuntimeError(
        "❌ Missing Kaggle credentials in macOS Keychain.\n"
        "Add them using:\n"
        "  keyring.set_password('KAGGLE_USERNAME', 'kaggle_username', '<your_username>')\n"
        "  keyring.set_password('KAGGLE_KEY', 'kaggle_key', '<your_key>')"
    )

# -----------------------------------------------------------------------------
# Helper for downloading Kaggle files
# -----------------------------------------------------------------------------
def download_kaggle_file(file_name: str):
    csv_path = RAW_DIR / file_name

    # Skip if already downloaded
    if csv_path.exists():
        print(f"✅ {file_name} already exists. Skipping download.")
        return

    print(f"\n⬇️  Downloading {file_name}...")

    # Kaggle API URL
    url = (
        "https://www.kaggle.com/api/v1/competitions/data/download/"
        f"amex-default-prediction/{file_name}"
    )
    zip_path = RAW_DIR / f"{file_name}.zip"

    with requests.get(
        url,
        stream=True,
        auth=(KAGGLE_USERNAME, KAGGLE_KEY),
        headers={"User-Agent": "Mozilla/5.0"}
    ) as r:
        r.raise_for_status()

        total_size = int(r.headers.get("content-length", 0))
        chunk_size = 1024 * 1024  # 1MB chunk

        with open(zip_path, "wb") as f:
            for chunk in tqdm(
                r.iter_content(chunk_size=chunk_size),
                total=total_size // chunk_size if total_size > 0 else None,
                unit="MB"
            ):
                if chunk:
                    f.write(chunk)

    # Extract zip
    print(f"📦 Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(RAW_DIR)

    print("🧹 Cleaning up zip...")
    zip_path.unlink(missing_ok=True)

    print(f"✅ Done: {file_name}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    files = [
        "train_data.csv",
        "train_labels.csv",
        "sample_submission.csv",
        "test_data.csv",   # ⚠️ Very large (~34 GB)
    ]

    print("📂 Downloading into:", RAW_DIR)

    for f in files:
        download_kaggle_file(f)

    print("\n🎉 Completed all downloads.")


if __name__ == "__main__":
    main()
