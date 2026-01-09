# Oracle Cloud Free Tier - Quick Start Guide

**Goal**: Deploy AMEX ML Pipeline to Oracle Cloud in 15 minutes using 100% FREE resources.

---

## ⚡ **15-Minute Quick Start**

### **Step 1: Create OCI Account** (5 min)
1. Visit: https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Complete registration (credit card required for verification, won't be charged)
4. Login to console: https://cloud.oracle.com/

### **Step 2: Install OCI CLI** (3 min)
```bash
# Install
brew install oci-cli

# Configure (follow prompts)
oci setup config
```

**You'll need from OCI Console:**
- User OCID: Profile → User Settings
- Tenancy OCID: Profile → Tenancy
- Region: e.g., `us-ashburn-1`

### **Step 3: Create Free Tier Instance** (5 min)

**Via Console:**
1. Compute → Instances → Create Instance
2. Settings:
   - Name: `amex-ml-free-tier`
   - Image: **Ubuntu 22.04 (ARM)**
   - Shape: **VM.Standard.A1.Flex**
   - OCPUs: **4** (max free)
   - Memory: **24 GB** (max free)
   - Boot Volume: **200 GB**
3. Upload SSH key (`~/.ssh/id_rsa.pub`)
4. Create → Wait for "Running" status
5. **Copy Public IP**

### **Step 4: Deploy** (2 min)
```bash
cd /Users/balaji/Projects/AMEX/AMEX

# Run setup (will configure instance)
bash .oci/setup_oci.sh
# Enter instance IP when prompted

# Deploy code
bash .oci/deploy_to_oci.sh
```

---

## 🚀 **Run Training**

### **Option 1: SSH and Run**
```bash
# SSH to instance
ssh ubuntu@<instance-ip>

# Navigate and activate
cd AMEX
source venv/bin/activate

# Run training
python scripts/train_lightgbm.py
```

### **Option 2: Background Job**
```bash
# Run in background
nohup python scripts/train_lightgbm.py > logs/oci_train.log 2>&1 &

# Monitor
tail -f logs/oci_train.log

# Exit SSH (training continues)
exit
```

---

## 📥 **Download Results**

```bash
# From local machine
cd /Users/balaji/Projects/AMEX/AMEX
bash .oci/sync_from_oci.sh
```

Results downloaded to:
- `models/lightgbm_model.txt`
- `data/submissions/submission.csv`

---

## 💾 **Data Management**

### **Upload Data to Cloud**
```bash
# Upload to Object Storage
bash .oci/upload_data.sh
```

### **Download on Instance**
```bash
# SSH to instance
ssh ubuntu@<instance-ip>
cd AMEX

# Download from Object Storage
oci os object bulk-download \
  --bucket-name amex-ml-data \
  --download-dir data/raw \
  --prefix raw/
```

---

## 🐛 **Quick Troubleshooting**

**Can't SSH?**
- Check Security List: Networking → VCN → Security Lists → Allow port 22

**Out of Memory?**
```bash
# Add swap space
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Slow Performance?**
- ARM is ~1.5x slower than x86
- Still free and usable!
- Expected training time: ~12 minutes (vs 8 minutes local)

---

## 💰 **Cost: $0/month**

Free tier includes:
- ✅ 4 ARM cores + 24GB RAM (forever free)
- ✅ 200GB storage (forever free)
- ✅ 10GB Object Storage (forever free)

**No hidden charges!**

---

## 📚 **Next Steps**

- **Full Guide**: See `.oci/README.md`
- **Troubleshooting**: See `PROJECT_CLOSURE.md`
- **Advanced**: See `.gcp/README.md` for paid alternatives

---

## 🎯 **Common Commands**

```bash
# Deploy code
bash .oci/deploy_to_oci.sh <ip>

# Download results
bash .oci/sync_from_oci.sh <ip>

# Upload data
bash .oci/upload_data.sh

# SSH to instance
ssh ubuntu@<ip>

# Stop instance (save resources)
oci compute instance action --instance-id <id> --action STOP

# Start instance
oci compute instance action --instance-id <id> --action START
```

---

**That's it! You're running on Oracle Cloud for FREE! 🎉**
