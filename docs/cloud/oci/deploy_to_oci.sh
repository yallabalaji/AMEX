#!/bin/bash
# Deploy AMEX ML Pipeline to OCI Instance

set -e

# Get instance IP
if [ -z "$1" ]; then
    if [ -f ".oci/instance_ip.txt" ]; then
        INSTANCE_IP=$(cat .oci/instance_ip.txt)
        echo "Using saved instance IP: $INSTANCE_IP"
    else
        echo "Usage: $0 <instance-ip>"
        echo "Or run setup_oci.sh first to save instance IP"
        exit 1
    fi
else
    INSTANCE_IP=$1
fi

echo "🚀 Deploying AMEX ML Pipeline to OCI"
echo "====================================="
echo "Instance: $INSTANCE_IP"
echo ""

# Test connection
echo "🔑 Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 ubuntu@$INSTANCE_IP "echo 'Connected'" 2>/dev/null; then
    echo "❌ Cannot connect to instance"
    exit 1
fi
echo "✓ Connected"
echo ""

# Sync code (exclude large files)
echo "📤 Syncing code to OCI instance..."
rsync -avz --progress \
    --exclude 'data/' \
    --exclude 'models/' \
    --exclude 'venv/' \
    --exclude '.git/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'logs/' \
    --exclude '.DS_Store' \
    ./ ubuntu@$INSTANCE_IP:~/AMEX/

echo "✓ Code synced"
echo ""

# Update dependencies
echo "📚 Updating dependencies on instance..."
ssh ubuntu@$INSTANCE_IP << 'EOF'
cd AMEX
source venv/bin/activate
pip install -r requirements.txt -q
echo "✓ Dependencies updated"
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🎯 Next steps:"
echo ""
echo "1. SSH to instance:"
echo "   ssh ubuntu@$INSTANCE_IP"
echo ""
echo "2. Run training:"
echo "   cd AMEX"
echo "   source venv/bin/activate"
echo "   python scripts/train_lightgbm.py"
echo ""
echo "3. Or run in background:"
echo "   nohup python scripts/train_lightgbm.py > logs/oci_train.log 2>&1 &"
echo "   tail -f logs/oci_train.log"
echo ""
