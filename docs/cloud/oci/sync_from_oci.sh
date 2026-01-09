#!/bin/bash
# Sync results from OCI instance back to local machine

set -e

# Get instance IP
if [ -z "$1" ]; then
    if [ -f ".oci/instance_ip.txt" ]; then
        INSTANCE_IP=$(cat .oci/instance_ip.txt)
        echo "Using saved instance IP: $INSTANCE_IP"
    else
        echo "Usage: $0 <instance-ip>"
        exit 1
    fi
else
    INSTANCE_IP=$1
fi

echo "📥 Syncing results from OCI"
echo "==========================="
echo "Instance: $INSTANCE_IP"
echo ""

# Test connection
echo "🔑 Testing connection..."
if ! ssh -o ConnectTimeout=5 ubuntu@$INSTANCE_IP "echo 'Connected'" 2>/dev/null; then
    echo "❌ Cannot connect to instance"
    exit 1
fi
echo "✓ Connected"
echo ""

# Download models
echo "📦 Downloading models..."
rsync -avz --progress ubuntu@$INSTANCE_IP:~/AMEX/models/ ./models/
echo "✓ Models downloaded"
echo ""

# Download submissions
echo "📊 Downloading submissions..."
rsync -avz --progress ubuntu@$INSTANCE_IP:~/AMEX/data/submissions/ ./data/submissions/
echo "✓ Submissions downloaded"
echo ""

# Download logs
echo "📝 Downloading logs..."
rsync -avz --progress ubuntu@$INSTANCE_IP:~/AMEX/logs/ ./logs/
echo "✓ Logs downloaded"
echo ""

echo "✅ Sync complete!"
echo ""
echo "📁 Downloaded files:"
ls -lh models/ 2>/dev/null || echo "  No models found"
ls -lh data/submissions/ 2>/dev/null || echo "  No submissions found"
echo ""
