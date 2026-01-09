#!/bin/bash
# Upload data to OCI Object Storage

set -e

echo "📤 Uploading data to OCI Object Storage"
echo "======================================="
echo ""

# Check if data exists
if [ ! -d "data/raw" ] && [ ! -d "data/stage" ]; then
    echo "❌ No data found in data/raw or data/stage"
    echo "Please download data first"
    exit 1
fi

# Upload raw data if exists
if [ -d "data/raw" ] && [ "$(ls -A data/raw)" ]; then
    echo "📦 Uploading raw data..."
    oci os object bulk-upload \
        --bucket-name amex-ml-data \
        --src-dir data/raw \
        --prefix raw/ \
        --overwrite
    echo "✓ Raw data uploaded"
    echo ""
fi

# Upload processed data if exists
if [ -d "data/stage" ] && [ "$(ls -A data/stage)" ]; then
    echo "📦 Uploading processed data..."
    oci os object bulk-upload \
        --bucket-name amex-ml-data \
        --src-dir data/stage \
        --prefix stage/ \
        --overwrite
    echo "✓ Processed data uploaded"
    echo ""
fi

echo "✅ Upload complete!"
echo ""
echo "📋 To download on OCI instance, run:"
echo "   ssh ubuntu@<instance-ip>"
echo "   cd AMEX"
echo "   oci os object bulk-download --bucket-name amex-ml-data --download-dir data/raw --prefix raw/"
echo "   oci os object bulk-download --bucket-name amex-ml-data --download-dir data/stage --prefix stage/"
echo ""
