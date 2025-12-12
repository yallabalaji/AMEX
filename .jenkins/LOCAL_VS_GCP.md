# Jenkins Pipeline: Local vs GCP - Complete Guide

## ✅ **Good News: One Jenkinsfile Works Everywhere!**

Your current `Jenkinsfile` is **already portable** because:
- ✅ Uses `${WORKSPACE}` (Jenkins variable, works anywhere)
- ✅ Python scripts use relative paths (`data/`, `models/`, etc.)
- ✅ No hardcoded absolute paths like `/Users/balaji`

## 📋 **Setup Comparison**

| Aspect | Local (Mac) | GCP VM |
|--------|-------------|---------|
| **Jenkinsfile** | Same file | Same file |
| **Setup Time** | 5 min | 30 min (first time) |
| **Ongoing Effort** | None | None (auto-sync) |
| **Cost** | Free | ~$9-31/month |

## 🚀 **30-Minute GCP Setup Guide**

### **Step 1: Install GCP CLI (5 min)**

```bash
# On your Mac
brew install google-cloud-sdk

# Initialize
gcloud init
# Follow prompts to login and select/create project
```

### **Step 2: Create GCP Resources (10 min)**

```bash
# Set project
export PROJECT_ID="amex-ml-pipeline"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com

# Create storage buckets
gsutil mb -l us-central1 gs://${PROJECT_ID}-data
gsutil mb -l us-central1 gs://${PROJECT_ID}-models

# Create VM with Jenkins pre-installed
gcloud compute instances create jenkins-vm \
  --zone=us-central1-a \
  --machine-type=n1-standard-2 \
  --boot-disk-size=50GB \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --tags=http-server,https-server \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata=startup-script='#!/bin/bash
    apt-get update
    apt-get install -y openjdk-21-jdk git python3.11 python3.11-venv
    wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | apt-key add -
    sh -c "echo deb https://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list"
    apt-get update
    apt-get install -y jenkins
    systemctl start jenkins
    systemctl enable jenkins
  '

# Create firewall rule for Jenkins
gcloud compute firewall-rules create allow-jenkins \
  --allow tcp:8080 \
  --target-tags http-server \
  --description="Allow Jenkins web interface"
```

### **Step 3: Setup Jenkins on GCP (10 min)**

```bash
# Get VM external IP
export VM_IP=$(gcloud compute instances describe jenkins-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "Jenkins URL: http://${VM_IP}:8080"

# SSH to VM and get initial password
gcloud compute ssh jenkins-vm --zone=us-central1-a --command="
  sudo cat /var/lib/jenkins/secrets/initialAdminPassword
"

# Open Jenkins in browser
open "http://${VM_IP}:8080"
```

Follow Jenkins setup wizard:
1. Enter initial password
2. Install suggested plugins
3. Create admin user
4. Configure Jenkins URL

### **Step 4: Clone Your Repo to GCP (5 min)**

```bash
# SSH to VM
gcloud compute ssh jenkins-vm --zone=us-central1-a

# On VM: Clone repo
cd /var/lib/jenkins
sudo -u jenkins git clone https://github.com/yourusername/AMEX.git workspace/AMEX

# Or sync from local
exit  # Back to Mac
./scripts/sync_to_gcp.sh
```

### **Step 5: Create Jenkins Job (5 min)**

In Jenkins UI (http://${VM_IP}:8080):

1. **New Item** → Name: `AMEX-ML-Pipeline` → **Pipeline**
2. **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `/var/lib/jenkins/workspace/AMEX` (local path on VM)
   - Script Path: `Jenkinsfile`
3. **Save**

## 🔄 **Workflow: Local Development + GCP Training**

### **Daily Development (Local)**

```bash
# 1. Develop on Mac
vim scripts/train_lightgbm.py

# 2. Test locally with small data
python scripts/train_lightgbm.py

# 3. Commit changes
git commit -am "Improved model"
git push
```

### **Production Training (GCP)**

```bash
# Option A: Sync and trigger manually
./scripts/sync_to_gcp.sh
# Then open Jenkins UI and click "Build with Parameters"

# Option B: Auto-trigger via webhook (setup once)
# Jenkins will auto-build on git push
```

## 📝 **Jenkinsfile Portability**

Your Jenkinsfile uses **environment variables** that work everywhere:

```groovy
environment {
    VENV_PATH = "${WORKSPACE}/venv"      // ✅ Works on Mac & GCP
    DATA_DIR = "${WORKSPACE}/data"        // ✅ Works on Mac & GCP
    MODELS_DIR = "${WORKSPACE}/models"    // ✅ Works on Mac & GCP
}
```

**No changes needed!** The same Jenkinsfile runs on:
- Local Mac Jenkins
- GCP VM Jenkins
- Any other Jenkins instance

## 🎯 **Path Verification**

Your Python scripts already use relative paths:

```python
# ✅ GOOD - Relative paths (already in your code)
BASE = Path("data")
STAGE = BASE / "stage"
RAW = BASE / "raw"

# ❌ BAD - Absolute paths (NOT in your code)
BASE = Path("/Users/balaji/Projects/AMEX/AMEX/data")
```

I verified: **No absolute paths found in your scripts!** ✅

## 💡 **Best Practice: Environment Detection**

Add this to your scripts for environment-aware behavior:

```python
# Add to scripts/train_lightgbm.py
import os

# Detect environment
IS_GCP = os.getenv('GCP_ENVIRONMENT', 'false') == 'true'
IS_JENKINS = os.getenv('JENKINS_HOME') is not None

if IS_GCP:
    # Use larger chunk size on GCP (more RAM)
    CHUNK_SIZE = 500_000
else:
    # Use smaller chunk size locally
    CHUNK_SIZE = 100_000

print(f"Running on: {'GCP' if IS_GCP else 'Local'}")
```

Then in Jenkinsfile, add to GCP VM:

```groovy
environment {
    GCP_ENVIRONMENT = 'true'  // Add this line
    VENV_PATH = "${WORKSPACE}/venv"
    // ... rest
}
```

## 📊 **Setup Time Breakdown**

| Task | Time | One-time? |
|------|------|-----------|
| Install gcloud CLI | 5 min | ✅ Yes |
| Create GCP project | 2 min | ✅ Yes |
| Create VM & buckets | 8 min | ✅ Yes |
| Install Jenkins on VM | 10 min | ✅ Yes |
| Configure Jenkins job | 5 min | ✅ Yes |
| **Total First Time** | **30 min** | |
| **Subsequent syncs** | **1 min** | ❌ No |

## 🔧 **Maintenance**

### **Daily** (0 min - automated)
- Code changes auto-sync via git webhook
- Jenkins auto-triggers builds

### **Weekly** (2 min)
- Check GCP costs: `gcloud billing accounts list`
- Review build logs

### **Monthly** (5 min)
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Clean old artifacts: `gsutil rm gs://bucket/old-models/*`

## 💰 **Cost Optimization**

### **Scenario 1: Minimal Usage** (~$3/month)
```bash
# Use preemptible VM, only when training
gcloud compute instances create jenkins-vm --preemptible
# Start VM only when needed
gcloud compute instances start jenkins-vm --zone=us-central1-a
# Stop after training
gcloud compute instances stop jenkins-vm --zone=us-central1-a
```

### **Scenario 2: Regular Usage** (~$28/month)
```bash
# Standard VM, running 24/7
# Good for frequent experiments
```

### **Scenario 3: On-Demand** (~$0.50/hour)
```bash
# Create VM when needed, delete after
gcloud compute instances create temp-training-vm
# ... run training ...
gcloud compute instances delete temp-training-vm
```

## 🎓 **Quick Start Checklist**

### **Local Setup** (Already Done ✅)
- [x] Jenkins installed
- [x] Jenkinsfile created
- [x] Code uses relative paths

### **GCP Setup** (30 min)
- [ ] Install gcloud CLI
- [ ] Create GCP project
- [ ] Create VM with Jenkins
- [ ] Create storage buckets
- [ ] Configure Jenkins job
- [ ] Test first build

### **Ongoing** (1 min/day)
- [ ] Sync code: `./scripts/sync_to_gcp.sh`
- [ ] Trigger build in Jenkins UI
- [ ] Download results: `./scripts/sync_from_gcp.sh`

## 🚨 **Common Issues**

### **Issue: "Jenkinsfile not found"**
**Solution**: Ensure repo is cloned to `/var/lib/jenkins/workspace/AMEX`

### **Issue: "Permission denied"**
**Solution**: 
```bash
sudo chown -R jenkins:jenkins /var/lib/jenkins/workspace/AMEX
```

### **Issue: "Out of memory on GCP"**
**Solution**: Upgrade VM:
```bash
gcloud compute instances set-machine-type jenkins-vm \
  --machine-type=n1-highmem-8 --zone=us-central1-a
```

## 📚 **Next Steps**

1. **Start local Jenkins** (already installed):
   ```bash
   brew services start jenkins-lts
   open http://localhost:8080
   ```

2. **Test locally first** (5 min):
   - Create Jenkins job
   - Run pipeline with `PIPELINE_STAGE=train`
   - Verify it works

3. **Then setup GCP** (30 min):
   - Follow steps above
   - Same Jenkinsfile works!

4. **Hybrid workflow**:
   - Develop locally
   - Train on GCP
   - Best of both worlds!

## ✅ **Summary**

| Question | Answer |
|----------|--------|
| Separate Jenkinsfiles? | ❌ No - one file works everywhere |
| Change paths? | ❌ No - already using relative paths |
| Setup time? | ✅ 30 min (one-time) |
| Maintenance? | ✅ 1 min/day (automated) |
| Worth it? | ✅ Yes - scalable + cost-effective |

You're ready to go! 🚀
