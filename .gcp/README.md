# GCP Setup for AMEX ML Pipeline

## Architecture: Hybrid Local + Cloud

```
┌─────────────────┐         ┌──────────────────────┐
│  Local (Mac)    │         │   GCP Cloud          │
│                 │         │                      │
│  • Development  │  sync   │  • Training          │
│  • Testing      │ ──────> │  • Hyperparameter    │
│  • Small runs   │         │    tuning            │
│                 │         │  • Large-scale runs  │
└─────────────────┘         └──────────────────────┘
```

## Benefits of Hybrid Approach

| Aspect | Local | GCP |
|--------|-------|-----|
| **Cost** | Free | Pay per use |
| **Speed** | Fast iteration | Parallel training |
| **Resources** | Limited (8-16GB) | Scalable (100GB+) |
| **Use Case** | Development | Production training |

## GCP Services to Use

### 1. **Compute Engine** (Virtual Machines)
- **Purpose**: Run training jobs
- **Machine Type**: `n1-highmem-8` (8 vCPUs, 52GB RAM)
- **Cost**: ~$0.47/hour (~$11/day if running 24/7)

### 2. **Cloud Storage** (GCS)
- **Purpose**: Store data and models
- **Cost**: ~$0.02/GB/month
- **Your data**: ~10GB = $0.20/month

### 3. **Vertex AI** (Optional)
- **Purpose**: Managed ML training
- **Cost**: Similar to Compute Engine but managed

### 4. **Cloud Build** (CI/CD)
- **Purpose**: Automated pipeline
- **Cost**: 120 build-minutes/day free

## Setup Guide

### Step 1: GCP Project Setup

```bash
# Install gcloud CLI
brew install google-cloud-sdk

# Initialize and login
gcloud init

# Create new project
gcloud projects create amex-ml-pipeline --name="AMEX ML Pipeline"

# Set as active project
gcloud config set project amex-ml-pipeline

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Create Cloud Storage Bucket

```bash
# Create bucket for data
gsutil mb -l us-central1 gs://amex-ml-data

# Create bucket for models
gsutil mb -l us-central1 gs://amex-ml-models

# Upload training data
gsutil -m cp -r data/raw/* gs://amex-ml-data/raw/
gsutil -m cp -r data/stage/* gs://amex-ml-data/stage/
```

### Step 3: Create VM Instance

```bash
# Create high-memory VM for training
gcloud compute instances create amex-training-vm \
  --zone=us-central1-a \
  --machine-type=n1-highmem-8 \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-standard \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --scopes=https://www.googleapis.com/auth/cloud-platform

# SSH into VM
gcloud compute ssh amex-training-vm --zone=us-central1-a
```

### Step 4: Setup VM Environment

Once SSH'd into the VM:

```bash
# Update system
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv git

# Clone your repo (or sync from local)
git clone https://github.com/yourusername/AMEX.git
cd AMEX

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install LightGBM with OpenMP support
pip install lightgbm --install-option=--mpi

# Download data from GCS
gsutil -m cp -r gs://amex-ml-data/raw/* data/raw/
```

### Step 5: Run Training on GCP

```bash
# SSH into VM
gcloud compute ssh amex-training-vm --zone=us-central1-a

# Activate environment
cd AMEX
source venv/bin/activate

# Run full pipeline
nohup python scripts/train_lightgbm.py > logs/gcp_train.log 2>&1 &

# Monitor progress
tail -f logs/gcp_train.log

# Upload results back to GCS
gsutil cp models/lightgbm_model.txt gs://amex-ml-models/
gsutil cp data/submissions/submission.csv gs://amex-ml-models/submissions/
```

### Step 6: Sync Results to Local

```bash
# On your local Mac
gsutil cp gs://amex-ml-models/lightgbm_model.txt models/
gsutil cp gs://amex-ml-models/submissions/submission.csv data/submissions/
```

## Automated Sync Script

Create `scripts/sync_to_gcp.sh`:

```bash
#!/bin/bash
# Sync local changes to GCP

set -e

PROJECT_ID="amex-ml-pipeline"
VM_NAME="amex-training-vm"
ZONE="us-central1-a"

echo "Syncing code to GCP VM..."

# Sync code (exclude data and models)
gcloud compute scp --recurse \
  --exclude="data/*" \
  --exclude="models/*" \
  --exclude="venv/*" \
  --zone=$ZONE \
  ./* $VM_NAME:~/AMEX/

echo "✓ Code synced to GCP"

# Optional: Trigger training
read -p "Start training on GCP? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="
        cd AMEX
        source venv/bin/activate
        nohup python scripts/train_lightgbm.py > logs/gcp_train.log 2>&1 &
        echo 'Training started. Check logs with: tail -f logs/gcp_train.log'
    "
fi
```

Create `scripts/sync_from_gcp.sh`:

```bash
#!/bin/bash
# Download results from GCP

set -e

BUCKET="gs://amex-ml-models"

echo "Downloading models from GCS..."
gsutil -m cp -r $BUCKET/lightgbm_model.txt models/

echo "Downloading submissions from GCS..."
gsutil -m cp -r $BUCKET/submissions/*.csv data/submissions/

echo "✓ Results downloaded from GCP"
```

## Cost Optimization

### 1. Use Preemptible VMs (70% cheaper)

```bash
gcloud compute instances create amex-training-vm-preemptible \
  --zone=us-central1-a \
  --machine-type=n1-highmem-8 \
  --preemptible \
  --boot-disk-size=100GB
```

**Caveat**: VM can be terminated anytime (save checkpoints!)

### 2. Auto-Shutdown After Training

Add to your training script:

```python
# At end of train_lightgbm.py
import subprocess
import os

if os.getenv('GCP_AUTO_SHUTDOWN') == 'true':
    print("Training complete. Shutting down VM in 5 minutes...")
    subprocess.run(['sudo', 'shutdown', '-h', '+5'])
```

### 3. Use Cloud Build for CI/CD (Free tier)

Create `cloudbuild.yaml`:

```yaml
steps:
  # Install dependencies
  - name: 'python:3.11'
    entrypoint: 'pip'
    args: ['install', '-r', 'requirements.txt']
  
  # Run preprocessing
  - name: 'python:3.11'
    entrypoint: 'python'
    args: ['scripts/preprocess_train.py']
  
  # Run aggregation
  - name: 'python:3.11'
    entrypoint: 'python'
    args: ['scripts/aggregate_customer.py', 'train']
  
  # Train model
  - name: 'python:3.11'
    entrypoint: 'python'
    args: ['scripts/train_lightgbm.py']

# Save artifacts
artifacts:
  objects:
    location: 'gs://amex-ml-models/builds/$BUILD_ID'
    paths: ['models/*', 'data/submissions/*']

timeout: '3600s'  # 1 hour
```

Trigger build:

```bash
gcloud builds submit --config cloudbuild.yaml
```

## Recommended Workflow

### Development (Local)
1. Write code on Mac
2. Test with small data samples
3. Commit to git

### Training (GCP)
1. Push code to git
2. Sync to GCP VM: `./scripts/sync_to_gcp.sh`
3. SSH to VM and run training
4. Download results: `./scripts/sync_from_gcp.sh`

### Production (GCP + Automation)
1. Use Cloud Build for automated training
2. Schedule with Cloud Scheduler (cron-like)
3. Monitor with Cloud Logging

## Cost Estimate

| Resource | Usage | Cost/Month |
|----------|-------|------------|
| VM (n1-highmem-8) | 2 hours/day | ~$28 |
| Storage (10GB) | Always on | $0.20 |
| Network egress | 1GB/day | $3 |
| **Total** | | **~$31/month** |

**Optimization**: Use preemptible VMs → **~$9/month**

## Monitoring & Alerts

### Setup Email Alerts

```bash
# Create notification channel
gcloud alpha monitoring channels create \
  --display-name="Email Alerts" \
  --type=email \
  --channel-labels=email_address=your-email@example.com

# Create alert for high costs
gcloud alpha monitoring policies create \
  --notification-channels=<channel-id> \
  --display-name="High GCP Costs" \
  --condition-threshold-value=50 \
  --condition-threshold-duration=3600s
```

## Troubleshooting

### Issue: VM out of memory

**Solution**: Upgrade to `n1-highmem-16` (104GB RAM):

```bash
gcloud compute instances set-machine-type amex-training-vm \
  --machine-type=n1-highmem-16 \
  --zone=us-central1-a
```

### Issue: Slow data transfer

**Solution**: Use `gsutil -m` for parallel uploads:

```bash
gsutil -m cp -r data/* gs://amex-ml-data/
```

### Issue: Training interrupted

**Solution**: Add checkpointing to your training script:

```python
# Save checkpoint every 100 iterations
if iteration % 100 == 0:
    model.save_model(f'models/checkpoint_{iteration}.txt')
```

## Next Steps

1. **Start Jenkins locally** for development
2. **Setup GCP project** for production training
3. **Test sync scripts** with small data
4. **Run first GCP training** and compare costs
5. **Automate with Cloud Build** once stable

This hybrid approach gives you the best of both worlds! 🚀
