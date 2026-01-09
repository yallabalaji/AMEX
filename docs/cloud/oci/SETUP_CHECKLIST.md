# Oracle Cloud Free Tier - Quick Setup Checklist

**Goal**: Deploy AMEX ML Pipeline to OCI in 90 minutes

---

## ✅ **Pre-Setup (5 minutes)**

Before you start, have these ready:

- [ ] Credit card (for verification, no charges)
- [ ] Phone number (for verification)
- [ ] Email address
- [ ] SSH public key (`~/.ssh/id_rsa.pub`)
  - If you don't have one: `ssh-keygen -t rsa -b 4096`
- [ ] Kaggle API credentials (`~/.kaggle/kaggle.json`)
  - Get from: https://www.kaggle.com/settings → API → Create New Token

---

## 📋 **Step-by-Step Setup**

### **Phase 1: OCI Account (15 minutes)**

- [ ] **1.1** Go to https://www.oracle.com/cloud/free/
- [ ] **1.2** Click "Start for free"
- [ ] **1.3** Fill registration form
- [ ] **1.4** Verify email (check inbox)
- [ ] **1.5** Verify phone (SMS code)
- [ ] **1.6** Add credit card (verification only)
- [ ] **1.7** Login to OCI Console: https://cloud.oracle.com/
- [ ] **1.8** Note your **Home Region** (e.g., us-ashburn-1)

**✅ Account Created**

---

### **Phase 2: OCI CLI (10 minutes)**

- [ ] **2.1** Install OCI CLI:
  ```bash
  brew install oci-cli
  ```

- [ ] **2.2** Configure OCI CLI:
  ```bash
  oci setup config
  ```

- [ ] **2.3** When prompted, get these from OCI Console:
  - **User OCID**: Profile (top right) → User Settings → Copy OCID
  - **Tenancy OCID**: Profile → Tenancy → Copy OCID
  - **Region**: Use your home region (e.g., us-ashburn-1)

- [ ] **2.4** Generate API keys (follow prompts, accept defaults)

- [ ] **2.5** Upload public key to OCI:
  - Console → Profile → User Settings → API Keys → Add API Key
  - Paste the public key shown in terminal

- [ ] **2.6** Test connection:
  ```bash
  oci iam region list
  ```

**✅ OCI CLI Configured**

---

### **Phase 3: Create Compute Instance (10 minutes)**

- [ ] **3.1** In OCI Console, go to: **☰ → Compute → Instances**

- [ ] **3.2** Click **"Create Instance"**

- [ ] **3.3** Configure:
  - **Name**: `amex-ml-free-tier`
  - **Compartment**: (root) - leave default

- [ ] **3.4** Click **"Edit"** next to Image and Shape

- [ ] **3.5** Change Image:
  - Click **"Change Image"**
  - Select **"Canonical Ubuntu"**
  - Version: **22.04** (ARM)
  - Click **"Select Image"**

- [ ] **3.6** Change Shape:
  - Click **"Change Shape"**
  - Select **"Ampere"** (ARM)
  - Choose **"VM.Standard.A1.Flex"**
  - Set **OCPUs: 4**
  - Set **Memory: 24 GB**
  - Click **"Select Shape"**

- [ ] **3.7** Networking (leave defaults):
  - VCN: (auto-created)
  - Subnet: (auto-created)
  - ✅ Assign public IPv4 address

- [ ] **3.8** Add SSH Keys:
  - Select **"Paste public keys"**
  - Paste contents of `~/.ssh/id_rsa.pub`

- [ ] **3.9** Boot Volume:
  - Size: **200 GB** (max free tier)

- [ ] **3.10** Click **"Create"**

- [ ] **3.11** Wait for status: **RUNNING** (2-3 minutes)

- [ ] **3.12** **Copy Public IP Address** (you'll need this!)

**✅ Instance Created**  
**Public IP**: _________________ (write it down!)

---

### **Phase 4: Setup Instance (15 minutes)**

- [ ] **4.1** Run setup script:
  ```bash
  cd /Users/balaji/Projects/AMEX/AMEX
  bash .oci/setup_oci.sh
  ```

- [ ] **4.2** When prompted, enter your **instance Public IP**

- [ ] **4.3** Wait for setup to complete (~15 min)
  - Creates Object Storage buckets
  - Installs system packages
  - Installs Python dependencies
  - Saves instance IP

**✅ Instance Configured**

---

### **Phase 5: Deploy Scripts (2 minutes)**

- [ ] **5.1** Deploy code to OCI:
  ```bash
  bash .oci/deploy_to_oci.sh
  ```

**✅ Scripts Deployed**

---

### **Phase 6: Download Data & Run Pipeline (3 hours)**

- [ ] **6.1** SSH to instance:
  ```bash
  ssh ubuntu@<your-instance-ip>
  ```

- [ ] **6.2** Navigate to project:
  ```bash
  cd AMEX
  source venv/bin/activate
  ```

- [ ] **6.3** Setup Kaggle credentials (one-time):
  ```bash
  mkdir -p ~/.kaggle
  nano ~/.kaggle/kaggle.json
  ```
  - Paste your Kaggle API credentials
  - Press `Ctrl+X`, then `Y`, then `Enter` to save

- [ ] **6.4** Set permissions:
  ```bash
  chmod 600 ~/.kaggle/kaggle.json
  ```

- [ ] **6.5** Download data from Kaggle:
  ```bash
  kaggle competitions download -c amex-default-prediction
  unzip amex-default-prediction.zip -d data/raw/
  rm amex-default-prediction.zip
  ```
  ⏱️ **Wait: 20-25 minutes**

- [ ] **6.6** Run complete pipeline in background:
  ```bash
  nohup bash scripts/run_complete_pipeline.sh lightgbm true > logs/pipeline.log 2>&1 &
  ```

- [ ] **6.7** Check it's running:
  ```bash
  tail -f logs/pipeline.log
  ```
  - Press `Ctrl+C` to stop viewing (pipeline continues)

- [ ] **6.8** Exit SSH:
  ```bash
  exit
  ```

**✅ Pipeline Running**  
⏱️ **Wait: ~2.5 hours** (go get coffee, lunch, etc.)

---

### **Phase 7: Download Results (1 minute)**

- [ ] **7.1** Check if pipeline is done:
  ```bash
  ssh ubuntu@<ip> "tail -20 ~/AMEX/logs/pipeline.log"
  ```
  - Look for "✅ Pipeline Complete!"

- [ ] **7.2** Download results:
  ```bash
  bash .oci/sync_from_oci.sh
  ```

- [ ] **7.3** Verify results:
  ```bash
  ls -lh models/
  ls -lh data/submissions/
  ```

**✅ Results Downloaded**

---

## 🎉 **Setup Complete!**

You now have:
- ✅ Oracle Cloud account (free tier)
- ✅ Compute instance running (4 cores, 24GB RAM)
- ✅ Complete ML pipeline deployed
- ✅ Model trained and submitted to Kaggle
- ✅ Cost: $0/month forever!

---

## 🚀 **Future Runs (15 minutes)**

For subsequent training runs:

```bash
# 1. Deploy code changes (2 min)
bash .oci/deploy_to_oci.sh

# 2. SSH and train (12 min)
ssh ubuntu@<ip>
cd AMEX && source venv/bin/activate
python scripts/train_lightgbm.py
exit

# 3. Download results (1 min)
bash .oci/sync_from_oci.sh
```

**Total: 15 minutes per run!**

---

## 📞 **Need Help?**

- **OCI Console**: https://cloud.oracle.com/
- **Documentation**: `.oci/README.md`
- **Troubleshooting**: `PROJECT_CLOSURE.md`

---

**Time Estimate:**
- Active work: ~1 hour
- Waiting time: ~3 hours
- **Total: ~4 hours** (first time only)

**Good luck! 🚀**
