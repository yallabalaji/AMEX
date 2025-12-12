#!/bin/bash
# Sync local code to GCP VM

set -e

# Configuration
PROJECT_ID="amex-ml-pipeline"
VM_NAME="amex-training-vm"
ZONE="us-central1-a"

echo "🔄 Syncing code to GCP VM..."

# Check if VM exists
if ! gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
    echo "❌ VM '$VM_NAME' not found in zone '$ZONE'"
    echo "Create it first with: gcloud compute instances create $VM_NAME ..."
    exit 1
fi

# Sync code (exclude large directories)
echo "📦 Uploading code..."
gcloud compute scp --recurse \
  --exclude="data/raw/*" \
  --exclude="data/stage/*" \
  --exclude="models/*" \
  --exclude="venv/*" \
  --exclude=".git/*" \
  --exclude="__pycache__/*" \
  --zone=$ZONE \
  ./* $VM_NAME:~/AMEX/ 2>/dev/null || true

echo "✅ Code synced to GCP"

# Optional: Start training
read -p "🚀 Start training on GCP? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting training job..."
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="
        cd AMEX
        source venv/bin/activate
        export GCP_AUTO_SHUTDOWN=true
        nohup python scripts/train_lightgbm.py > logs/gcp_train_\$(date +%Y%m%d_%H%M%S).log 2>&1 &
        echo '✅ Training started!'
        echo 'Monitor with: gcloud compute ssh $VM_NAME --zone=$ZONE --command=\"tail -f AMEX/logs/gcp_train_*.log\"'
    "
fi
