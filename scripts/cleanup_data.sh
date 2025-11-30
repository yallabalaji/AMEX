#!/usr/bin/env bash
set -euo pipefail

# Resolve project root as the parent of the scripts/ directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[INFO] Project root: $PROJECT_ROOT"

# -------------------------------------------------------------------
# 1. Clean data/stage (generated artifacts)
# -------------------------------------------------------------------
STAGE_DIR="$PROJECT_ROOT/data/stage"

if [ -d "$STAGE_DIR" ]; then
  echo "[INFO] Cleaning data/stage/ contents (parquet, maps, etc.) ..."
  rm -rf "$STAGE_DIR"/*
else
  echo "[WARN] data/stage does not exist, creating it..."
  mkdir -p "$STAGE_DIR"
fi

# Recreate subfolder for refined parquet parts
mkdir -p "$STAGE_DIR/refined_data"

# -------------------------------------------------------------------
# 2. Clean submission outputs (if any)
# -------------------------------------------------------------------
SUBMISSION_DIR="$PROJECT_ROOT/submission"

if [ -d "$SUBMISSION_DIR" ]; then
  echo "[INFO] Cleaning submission/ directory ..."
  rm -rf "$SUBMISSION_DIR"/*
else
  echo "[WARN] submission directory does not exist, creating it..."
  mkdir -p "$SUBMISSION_DIR"
fi

# -------------------------------------------------------------------
# 3. Clean logs (optional, only generated files)
# -------------------------------------------------------------------
LOGS_DIR="$PROJECT_ROOT/logs"

if [ -d "$LOGS_DIR" ]; then
  echo "[INFO] Cleaning logs/ directory ..."
  rm -rf "$LOGS_DIR"/*
fi

# -------------------------------------------------------------------
# 4. Remove old notebook-generated data folders (if present)
#    We keep .ipynb files, just delete old artifacts.
# -------------------------------------------------------------------
NB_DIR="$PROJECT_ROOT/notebooks"

if [ -d "$NB_DIR" ]; then
  for d in refined_data stage1 encoders models; do
    if [ -d "$NB_DIR/$d" ]; then
      echo "[INFO] Removing notebooks/$d (old artifacts) ..."
      rm -rf "$NB_DIR/$d"
    fi
  done
fi

echo "[INFO] Cleanup complete. Raw data, notebooks, and code are untouched."
echo "[INFO] You can now run: python scripts/preprocess_train.py"
