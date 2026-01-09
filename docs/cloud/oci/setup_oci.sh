#!/bin/bash
# OCI Free Tier Setup Script
# This script automates the creation of OCI resources for the AMEX ML Pipeline

set -e

echo "🚀 AMEX ML Pipeline - OCI Free Tier Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if OCI CLI is installed
if ! command -v oci &> /dev/null; then
    echo -e "${RED}❌ OCI CLI not found${NC}"
    echo "Install with: brew install oci-cli"
    echo "Then run: oci setup config"
    exit 1
fi

echo -e "${GREEN}✓ OCI CLI found${NC}"

# Check if OCI CLI is configured
if [ ! -f ~/.oci/config ]; then
    echo -e "${YELLOW}⚠️  OCI CLI not configured${NC}"
    echo "Run: oci setup config"
    exit 1
fi

echo -e "${GREEN}✓ OCI CLI configured${NC}"
echo ""

# Get compartment ID (use root compartment by default)
echo "📋 Getting tenancy information..."
TENANCY_ID=$(oci iam compartment list --all --query "data[?name=='root'] | [0].id" --raw-output 2>/dev/null || echo "")

if [ -z "$TENANCY_ID" ]; then
    echo -e "${RED}❌ Could not get tenancy ID${NC}"
    echo "Please check your OCI CLI configuration"
    exit 1
fi

COMPARTMENT_ID=$TENANCY_ID
echo -e "${GREEN}✓ Using compartment: $COMPARTMENT_ID${NC}"
echo ""

# Create Object Storage buckets
echo "📦 Creating Object Storage buckets..."

# Check if bucket exists
BUCKET_EXISTS=$(oci os bucket list --compartment-id $COMPARTMENT_ID --query "data[?name=='amex-ml-data'] | [0].name" --raw-output 2>/dev/null || echo "")

if [ -z "$BUCKET_EXISTS" ]; then
    oci os bucket create \
        --compartment-id $COMPARTMENT_ID \
        --name amex-ml-data \
        --public-access-type NoPublicAccess
    echo -e "${GREEN}✓ Created bucket: amex-ml-data${NC}"
else
    echo -e "${YELLOW}⚠️  Bucket amex-ml-data already exists${NC}"
fi

# Create models bucket
MODELS_BUCKET_EXISTS=$(oci os bucket list --compartment-id $COMPARTMENT_ID --query "data[?name=='amex-ml-models'] | [0].name" --raw-output 2>/dev/null || echo "")

if [ -z "$MODELS_BUCKET_EXISTS" ]; then
    oci os bucket create \
        --compartment-id $COMPARTMENT_ID \
        --name amex-ml-models \
        --public-access-type NoPublicAccess
    echo -e "${GREEN}✓ Created bucket: amex-ml-models${NC}"
else
    echo -e "${YELLOW}⚠️  Bucket amex-ml-models already exists${NC}"
fi

echo ""

# Get availability domain
echo "🌍 Getting availability domain..."
AVAILABILITY_DOMAIN=$(oci iam availability-domain list --compartment-id $COMPARTMENT_ID --query "data[0].name" --raw-output)
echo -e "${GREEN}✓ Using availability domain: $AVAILABILITY_DOMAIN${NC}"
echo ""

# Instructions for creating compute instance
echo "💻 Compute Instance Setup"
echo "========================="
echo ""
echo "To create a FREE TIER ARM compute instance:"
echo ""
echo "1. Go to OCI Console: https://cloud.oracle.com/"
echo "2. Navigate to: Compute → Instances → Create Instance"
echo "3. Configure:"
echo "   - Name: amex-ml-free-tier"
echo "   - Image: Ubuntu 22.04 (ARM)"
echo "   - Shape: VM.Standard.A1.Flex"
echo "   - OCPUs: 4 (use all 4 free cores)"
echo "   - Memory: 24 GB (use all free RAM)"
echo "   - Boot Volume: 200 GB (max free tier)"
echo "   - VCN: Use default or create new"
echo "   - SSH Keys: Upload your public key (~/.ssh/id_rsa.pub)"
echo ""
echo "4. Click 'Create' and wait for instance to be 'Running'"
echo ""
echo "5. Note the PUBLIC IP address"
echo ""
echo -e "${YELLOW}📝 Save your instance PUBLIC IP for next steps${NC}"
echo ""

# Ask if instance is created
read -p "Have you created the compute instance? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please create the instance first, then run this script again."
    exit 0
fi

echo ""
read -p "Enter the PUBLIC IP of your OCI instance: " INSTANCE_IP

if [ -z "$INSTANCE_IP" ]; then
    echo -e "${RED}❌ No IP provided${NC}"
    exit 1
fi

echo ""
echo "🔑 Testing SSH connection..."
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to instance${NC}"
    echo "Please check:"
    echo "  1. Instance is running"
    echo "  2. Security List allows SSH (port 22)"
    echo "  3. Your SSH key is added to the instance"
    exit 1
fi

echo ""
echo "📤 Uploading setup script to instance..."

# Create setup script for the instance
cat > /tmp/oci_instance_setup.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 Setting up AMEX ML Pipeline on OCI instance..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip git build-essential cmake libgomp1

# Clone repository
if [ ! -d "AMEX" ]; then
    echo "📥 Cloning AMEX repository..."
    git clone https://github.com/yallabalaji/AMEX.git
else
    echo "✓ AMEX repository already exists"
fi

cd AMEX

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate and install dependencies
echo "📚 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Create necessary directories
mkdir -p data/raw data/stage data/stage/aggregated data/submissions models logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Upload your data to OCI Object Storage"
echo "  2. Download data to this instance"
echo "  3. Run training: python scripts/train_lightgbm.py"
EOF

# Upload and run setup script
scp -o StrictHostKeyChecking=no /tmp/oci_instance_setup.sh ubuntu@$INSTANCE_IP:~/
ssh ubuntu@$INSTANCE_IP "bash ~/oci_instance_setup.sh"

echo ""
echo "✅ OCI Setup Complete!"
echo ""
echo "📋 Summary:"
echo "  - Object Storage buckets created: amex-ml-data, amex-ml-models"
echo "  - Compute instance configured: $INSTANCE_IP"
echo "  - Python environment ready"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Upload data to Object Storage:"
echo "   cd /Users/balaji/Projects/AMEX/AMEX"
echo "   bash .oci/upload_data.sh"
echo ""
echo "2. Deploy and run training:"
echo "   bash .oci/deploy_to_oci.sh $INSTANCE_IP"
echo ""
echo "3. Download results:"
echo "   bash .oci/sync_from_oci.sh $INSTANCE_IP"
echo ""
echo "📝 Save this IP address: $INSTANCE_IP"
echo ""

# Save instance IP for future use
echo $INSTANCE_IP > .oci/instance_ip.txt
echo -e "${GREEN}✓ Instance IP saved to .oci/instance_ip.txt${NC}"
