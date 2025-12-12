#!/bin/bash
# Download trained models and results from GCP

set -e

# Configuration
BUCKET="gs://amex-ml-models"

echo "📥 Downloading results from GCP..."

# Download models
echo "  • Models..."
gsutil -m cp -r $BUCKET/lightgbm_model*.txt models/ 2>/dev/null || echo "    No models found"

# Download submissions
echo "  • Submissions..."
gsutil -m cp -r $BUCKET/submissions/*.csv data/submissions/ 2>/dev/null || echo "    No submissions found"

# Download metrics
echo "  • Metrics..."
gsutil -m cp -r $BUCKET/metrics.json models/ 2>/dev/null || echo "    No metrics found"

# Download logs
echo "  • Logs..."
mkdir -p logs/gcp
gsutil -m cp -r $BUCKET/logs/*.log logs/gcp/ 2>/dev/null || echo "    No logs found"

echo "✅ Download complete!"
echo ""
echo "📊 Summary:"
ls -lh models/*.txt 2>/dev/null || echo "  No models"
ls -lh data/submissions/*.csv 2>/dev/null || echo "  No submissions"
