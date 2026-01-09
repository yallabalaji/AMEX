# Oracle Cloud Infrastructure (OCI) Free Tier Deployment Guide

## 🎯 **Overview**

Deploy the AMEX ML Pipeline to Oracle Cloud using **100% FREE** resources from OCI's Always Free tier.

### **What You Get (FREE Forever)**
- ✅ **4 ARM Ampere A1 cores** (up to 24 GB RAM)
- ✅ **200 GB Block Volume** storage
- ✅ **10 GB Object Storage**
- ✅ **Outbound data transfer** (10 TB/month)
- ✅ **No credit card charges** (stays free forever)

---

## 🚀 **Quick Start (30 Minutes)**

### **Step 1: Create OCI Account** (5 minutes)

1. Go to https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Fill in details (requires credit card for verification, but won't be charged)
4. Verify email and phone
5. Login to OCI Console: https://cloud.oracle.com/

### **Step 2: Install OCI CLI** (5 minutes)

```bash
# On macOS
brew install oci-cli

# Verify installation
oci --version

# Configure OCI CLI
oci setup config
```

**During setup, you'll need:**
- User OCID (from OCI Console → Profile → User Settings)
- Tenancy OCID (from OCI Console → Profile → Tenancy)
- Region (e.g., `us-ashburn-1`)
- Generate API key (follow prompts)

### **Step 3: Create Free Tier Compute Instance** (10 minutes)

```bash
# Run the automated setup script
cd /Users/balaji/Projects/AMEX/AMEX
bash .oci/setup_oci.sh
```

**Or manually:**

1. Go to **Compute → Instances → Create Instance**
2. Configure:
   - **Name**: `amex-ml-free-tier`
   - **Image**: Ubuntu 22.04 (ARM)
   - **Shape**: VM.Standard.A1.Flex
   - **OCPUs**: 4 (use all 4 free cores)
   - **Memory**: 24 GB (use all free RAM)
   - **Boot Volume**: 200 GB (max free tier)
3. **Networking**: Use default VCN (auto-created)
4. **SSH Keys**: Upload your public key (`~/.ssh/id_rsa.pub`)
5. Click **Create**

### **Step 4: Setup Object Storage** (5 minutes)

```bash
# Create bucket for data
oci os bucket create \
  --name amex-ml-data \
  --compartment-id <your-compartment-ocid>

# Create bucket for models
oci os bucket create \
  --name amex-ml-models \
  --compartment-id <your-compartment-ocid>
```

### **Step 5: Deploy Application** (5 minutes)

```bash
# Deploy to OCI
bash .oci/deploy_to_oci.sh

# This will:
# 1. Copy code to OCI instance
# 2. Install dependencies
# 3. Setup environment
# 4. Ready to run training
```

---

## 📦 **Deployment Options**

### **Option 1: Direct Python (Recommended for Free Tier)**

```bash
# SSH to instance
ssh ubuntu@<instance-public-ip>

# Navigate to project
cd AMEX

# Activate environment
source venv/bin/activate

# Run training
python scripts/train_lightgbm.py
```

**Pros**: Lower memory overhead, faster on ARM
**Cons**: Manual dependency management

### **Option 2: Docker (If you have enough RAM)**

```bash
# On OCI instance
cd AMEX

# Build Docker image
docker build -t amex-ml-pipeline .

# Run training
docker run -v $(pwd)/data:/app/data -v $(pwd)/models:/app/models amex-ml-pipeline
```

**Pros**: Consistent environment
**Cons**: Higher memory usage (~2GB overhead)

---

## 💾 **Data Management**

### **Upload Data to Object Storage**

```bash
# From local machine
oci os object bulk-upload \
  --bucket-name amex-ml-data \
  --src-dir data/raw \
  --prefix raw/

# Upload processed data
oci os object bulk-upload \
  --bucket-name amex-ml-data \
  --src-dir data/stage \
  --prefix stage/
```

### **Download Data on OCI Instance**

```bash
# On OCI instance
oci os object bulk-download \
  --bucket-name amex-ml-data \
  --download-dir data/raw \
  --prefix raw/

oci os object bulk-download \
  --bucket-name amex-ml-data \
  --download-dir data/stage \
  --prefix stage/
```

---

## 🔧 **Instance Setup Script**

The instance needs initial setup. SSH to your instance and run:

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3-pip git

# Install build tools (for ML libraries)
sudo apt-get install -y build-essential cmake libgomp1

# Clone repository
git clone https://github.com/yallabalaji/AMEX.git
cd AMEX

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure OCI CLI on instance
oci setup config
```

---

## 🎯 **Complete Workflow**

### **1. Local Development**
```bash
# Develop and test locally
python scripts/train_lightgbm.py

# Commit changes
git add .
git commit -m "Update model"
git push
```

### **2. Deploy to OCI**
```bash
# Sync code to OCI
bash .oci/deploy_to_oci.sh

# Or manually:
ssh ubuntu@<instance-ip> "cd AMEX && git pull"
```

### **3. Run Training on OCI**
```bash
# SSH to instance
ssh ubuntu@<instance-ip>

# Run training
cd AMEX
source venv/bin/activate
nohup python scripts/train_lightgbm.py > logs/oci_train.log 2>&1 &

# Monitor progress
tail -f logs/oci_train.log
```

### **4. Download Results**
```bash
# From local machine
bash .oci/sync_from_oci.sh

# Or manually:
scp ubuntu@<instance-ip>:~/AMEX/models/lightgbm_model.txt models/
scp ubuntu@<instance-ip>:~/AMEX/data/submissions/submission.csv data/submissions/
```

---

## 💰 **Cost Analysis**

### **Free Tier Resources**
| Resource | Free Tier | Your Usage | Cost |
|----------|-----------|------------|------|
| Compute (ARM) | 4 OCPUs, 24GB | 4 OCPUs, 24GB | **$0** |
| Block Storage | 200 GB | 100 GB | **$0** |
| Object Storage | 10 GB | ~5 GB | **$0** |
| Outbound Transfer | 10 TB/month | ~1 GB/month | **$0** |
| **Total** | | | **$0/month** |

### **If You Exceed Free Tier**
- Additional ARM compute: ~$0.01/OCPU/hour
- Additional storage: ~$0.0255/GB/month
- **Still very affordable!**

---

## 🔒 **Security Best Practices**

### **1. SSH Key Authentication**
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/oci_rsa

# Add to OCI instance during creation
# Or add later via Console → Compute → Instance → Edit
```

### **2. Firewall Rules**
```bash
# Only allow SSH from your IP
# In OCI Console → Networking → Security Lists
# Add Ingress Rule:
#   Source: <your-ip>/32
#   Port: 22
```

### **3. API Keys**
```bash
# Store Kaggle credentials securely
ssh ubuntu@<instance-ip>
mkdir -p ~/.kaggle
nano ~/.kaggle/kaggle.json
# Paste your Kaggle API credentials
chmod 600 ~/.kaggle/kaggle.json
```

---

## 🐛 **Troubleshooting**

### **Issue: Out of Memory on Free Tier**

**Solution 1**: Use swap space
```bash
# Create 8GB swap file
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Solution 2**: Reduce chunk size
```python
# In scripts/preprocess_train.py
python scripts/preprocess_train.py --chunksize 50000  # Instead of 100000
```

### **Issue: Slow ARM Performance**

**ARM is slower than x86 for some ML libraries**

**Solution**: Use optimized builds
```bash
# Install ARM-optimized LightGBM
pip uninstall lightgbm
pip install lightgbm --no-binary lightgbm
```

### **Issue: Can't SSH to Instance**

**Check Security List**
1. Go to **Networking → Virtual Cloud Networks**
2. Click your VCN → Security Lists → Default Security List
3. Ensure Ingress Rule exists:
   - Source: 0.0.0.0/0 (or your IP)
   - Protocol: TCP
   - Port: 22

### **Issue: OCI CLI Not Working**

```bash
# Reconfigure OCI CLI
oci setup config

# Test connection
oci iam region list
```

---

## 📊 **Performance Expectations**

### **Free Tier ARM (4 cores, 24GB RAM)**
- Preprocessing: ~90 minutes (vs 60 min on x86)
- Aggregation: ~30 minutes (vs 20 min on x86)
- LightGBM training: ~12 minutes (vs 8 min on x86)
- **Total pipeline**: ~2.5 hours (vs 1.5 hours on x86)

**Still very usable for development and training!**

---

## 🎓 **Learning Resources**

- **OCI Documentation**: https://docs.oracle.com/en-us/iaas/
- **OCI Free Tier**: https://www.oracle.com/cloud/free/
- **OCI CLI Reference**: https://docs.oracle.com/en-us/iaas/tools/oci-cli/
- **ARM Optimization**: https://developer.arm.com/documentation

---

## ✅ **Quick Reference Commands**

```bash
# SSH to instance
ssh ubuntu@<instance-ip>

# Upload file to Object Storage
oci os object put --bucket-name amex-ml-data --file data.csv --name data.csv

# Download file from Object Storage
oci os object get --bucket-name amex-ml-data --name data.csv --file data.csv

# List instances
oci compute instance list --compartment-id <compartment-ocid>

# Stop instance (to save resources)
oci compute instance action --instance-id <instance-ocid> --action STOP

# Start instance
oci compute instance action --instance-id <instance-ocid> --action START
```

---

## 🎉 **Benefits of OCI Free Tier**

✅ **Truly Free**: No time limits, free forever
✅ **Generous Resources**: 4 ARM cores + 24GB RAM
✅ **No Surprise Charges**: Free tier resources never expire
✅ **Production Ready**: Same infrastructure as paid tier
✅ **Great for Learning**: Perfect for ML projects and portfolio

---

**Ready to deploy? Run `bash .oci/setup_oci.sh` to get started!** 🚀
