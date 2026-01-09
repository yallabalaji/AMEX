# Project Setup Guide

This guide will help you set up the AMEX ML Pipeline project from scratch, whether you're restoring it after deletion or setting it up for the first time to contribute.

---

## 📋 **Prerequisites**

### **Required**
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **16GB RAM minimum** (32GB recommended)
- **20GB free disk space**

### **Optional (for specific features)**
- **Jenkins** - For CI/CD automation ([Install Guide](docs/ci-cd/jenkins/SETUP_NATIVE.md))
- **Kaggle Account** - For competition submissions ([Sign up](https://www.kaggle.com/))

---

## 🚀 **Quick Setup (10 minutes)**

### **Step 1: Clone Repository**

```bash
# Clone from GitHub
git clone https://github.com/yallabalaji/AMEX.git
cd AMEX
```

### **Step 2: Create Virtual Environment**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### **Step 3: Install Dependencies**

```bash
# Install all required Python packages
pip install -r requirements.txt
```

### **Step 4: Download Data**

You have two options:

#### **Option A: Download from Kaggle (Recommended)**

```bash
# 1. Install Kaggle CLI (if not already installed)
pip install kaggle

# 2. Setup Kaggle credentials
# - Go to https://www.kaggle.com/settings
# - Click "Create New API Token"
# - Save kaggle.json to ~/.kaggle/kaggle.json
mkdir -p ~/.kaggle
# Move downloaded kaggle.json to ~/.kaggle/

# 3. Download competition data
kaggle competitions download -c amex-default-prediction

# 4. Unzip to data/raw/
unzip amex-default-prediction.zip -d data/raw/
```

#### **Option B: Manual Download**

1. Go to [AMEX Competition](https://www.kaggle.com/competitions/amex-default-prediction/data)
2. Download these files:
   - `train_data.csv` (~5GB)
   - `train_labels.csv` (~1MB)
   - `test_data.csv` (~3GB)
3. Place them in `data/raw/` directory

### **Step 5: Verify Setup**

```bash
# Check if data exists
ls -lh data/raw/

# Expected output:
# train_data.csv
# train_labels.csv
# test_data.csv

# Test Python environment
python -c "import lightgbm, xgboost, catboost, pandas; print('✅ All dependencies installed!')"
```

---

## 🎯 **Running Your First Model**

### **Quick Test (5 minutes)**

```bash
# Train LightGBM model (fastest)
python scripts/train_lightgbm.py

# This will:
# 1. Preprocess data (if not already done)
# 2. Aggregate features
# 3. Train model
# 4. Generate predictions
# 5. Save to data/submissions/submission.csv
```

### **Submit to Kaggle (Optional)**

```bash
# Submit your predictions
python scripts/submit_kaggle.py \
    --file data/submissions/submission.csv \
    --msg "First submission"
```

---

## 📂 **Project Structure After Setup**

```
AMEX/
├── data/
│   ├── raw/                    # ✅ Downloaded CSV files
│   ├── stage/                  # ⏳ Created during preprocessing
│   └── submissions/            # ⏳ Created during training
├── models/                     # ⏳ Created during training
├── logs/                       # ⏳ Created automatically
├── venv/                       # ✅ Virtual environment
├── scripts/                    # ✅ Python scripts
├── src/                        # ✅ Source code
├── docs/                       # ✅ Documentation
└── requirements.txt            # ✅ Dependencies
```

**Legend:**
- ✅ = Should exist after setup
- ⏳ = Will be created when needed

---

## 🤖 **Jenkins Setup (Optional)**

For automated CI/CD pipeline:

### **Quick Setup**

```bash
# Install Jenkins (macOS)
brew install jenkins-lts

# Start Jenkins
brew services start jenkins-lts

# Open browser
open http://localhost:8080
```

### **Detailed Guide**
See [docs/ci-cd/jenkins/SETUP_NATIVE.md](docs/ci-cd/jenkins/SETUP_NATIVE.md) for complete setup instructions.

### **When to Use Jenkins**
- ✅ Automated training on schedule
- ✅ Testing multiple models automatically
- ✅ Automated Kaggle submissions
- ❌ One-time experiments (use scripts directly)

---

## ☁️ **Cloud Deployment (Optional)**

### **Oracle Cloud (FREE)**

**Resources**: 4 ARM cores, 24GB RAM, 200GB storage  
**Cost**: $0/month (forever free)

**Quick Start**: See [docs/cloud/oci/QUICKSTART.md](docs/cloud/oci/QUICKSTART.md)

### **Google Cloud Platform**

**Resources**: Configurable (8 vCPUs, 52GB RAM recommended)  
**Cost**: ~$30/month

**Guide**: See [docs/cloud/gcp/README.md](docs/cloud/gcp/README.md)

---

## 🔧 **Development Workflow**

### **1. Create Feature Branch**

```bash
git checkout -b feature/my-new-feature
```

### **2. Make Changes**

Edit files in `scripts/`, `src/`, or add new notebooks.

### **3. Test Your Changes**

```bash
# Run specific script
python scripts/your_script.py

# Or run complete pipeline
bash scripts/run_complete_pipeline.sh
```

### **4. Commit and Push**

```bash
git add .
git commit -m "Add: description of changes"
git push origin feature/my-new-feature
```

### **5. Create Pull Request**

Go to GitHub and create a pull request from your branch.

---

## 📊 **Data Pipeline Overview**

Understanding the data flow helps with setup:

```
1. Raw Data (data/raw/)
   ├── train_data.csv (5GB)
   ├── train_labels.csv (1MB)
   └── test_data.csv (3GB)
   
2. Preprocessing (scripts/preprocess_*.py)
   ↓
   
3. Staged Data (data/stage/)
   ├── linear_train.parquet
   └── linear_test.parquet
   
4. Aggregation (scripts/aggregate_customer.py)
   ↓
   
5. Aggregated Features (data/stage/aggregated/)
   ├── customer_level_train.parquet
   └── customer_level_test.parquet
   
6. Model Training (scripts/train_*.py)
   ↓
   
7. Predictions (data/submissions/)
   └── submission.csv
```

---

## 🐛 **Troubleshooting**

### **Problem: Out of Memory**

```bash
# Solution: Reduce chunk size
python scripts/preprocess_train.py --chunksize 50000
```

### **Problem: Missing Dependencies**

```bash
# Solution: Reinstall requirements
pip install --upgrade -r requirements.txt
```

### **Problem: Data Not Found**

```bash
# Solution: Check data directory
ls -lh data/raw/

# If empty, download data again (see Step 4 above)
```

### **Problem: Kaggle API Not Working**

```bash
# Solution: Verify credentials
cat ~/.kaggle/kaggle.json

# Should contain:
# {"username":"your_username","key":"your_api_key"}

# Set permissions
chmod 600 ~/.kaggle/kaggle.json
---

## 📝 **Essential Files Checklist**

Before starting work, ensure these files exist:

### **Must Have (Project Won't Work Without)**
- [ ] `requirements.txt` - Python dependencies
- [ ] `scripts/` directory - All Python scripts
- [ ] `src/` directory - Source code modules
- [ ] `data/raw/` directory - With downloaded CSV files

### **Should Have (For Full Functionality)**
- [ ] `docs/` directory - Documentation
- [ ] `notebooks/` directory - Jupyter notebooks
- [ ] `.gitignore` - Git ignore rules
- [ ] `README.md` - Project overview

### **Optional (For Specific Features)**
- [ ] `Jenkinsfile` - For CI/CD
- [ ] `docs/cloud/` - For cloud deployment

---

## 🎓 **Learning Path**

If you're new to the project, follow this order:

### **Week 1: Understanding**
1. Read [README.md](README.md)
2. Review project structure
3. Run first model training
4. Submit to Kaggle

### **Week 2: Experimentation**
1. Test different models
2. Modify hyperparameters
3. Try simple ensemble
4. Review [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md)

### **Week 3: Advanced**
1. Feature engineering
2. Model optimization
3. Cloud deployment (optional)
4. CI/CD setup (optional)

---

## 🔄 **Restoring After Deletion**

If you deleted the project locally and want to restore:

### **What You Need to Re-download**
1. **Code**: Clone from GitHub (all code is backed up)
2. **Data**: Download from Kaggle (5GB+)
3. **Models**: Retrain or download from cloud backup

### **What's Preserved on GitHub**
- ✅ All source code
- ✅ All documentation
- ✅ All scripts and configurations
- ❌ Data files (too large, must re-download)
- ❌ Trained models (must retrain)
- ❌ Virtual environment (must recreate)

### **Quick Restore (15 minutes)**

```bash
# 1. Clone repository
git clone https://github.com/yallabalaji/AMEX.git
cd AMEX

# 2. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Download data
kaggle competitions download -c amex-default-prediction
unzip amex-default-prediction.zip -d data/raw/

# 4. You're ready!
python scripts/train_lightgbm.py
```

---

## 💾 **What to Backup Before Deletion**

If you're deleting locally to save space:

### **Already Backed Up (on GitHub)**
- ✅ All code files
- ✅ All documentation
- ✅ All configuration files

### **Should Backup Manually**
- ⚠️ Trained models (if you want to keep them)
- ⚠️ Custom notebooks with experiments
- ⚠️ Any local configuration changes

### **Can Re-download**
- 🔄 Raw data from Kaggle
- 🔄 Python dependencies

### **Backup Commands**

```bash
# Backup trained models (if you want to keep them)
tar -czf models_backup.tar.gz models/

# Backup custom notebooks
tar -czf notebooks_backup.tar.gz notebooks/

# Upload to cloud storage (optional)
# For OCI: see docs/cloud/oci/upload_data.sh
# For GCP: see docs/cloud/gcp/README.md
```

---

## ✅ **Setup Verification**

Run this checklist to ensure everything is set up correctly:

```bash
# 1. Python version
python --version
# Expected: Python 3.11 or higher

# 2. Virtual environment active
which python
# Expected: /path/to/AMEX/venv/bin/python

# 3. Dependencies installed
pip list | grep -E "lightgbm|xgboost|catboost|pandas"
# Expected: All packages listed

# 4. Data exists
ls -lh data/raw/*.csv
# Expected: train_data.csv, train_labels.csv, test_data.csv

# 5. Scripts executable
python scripts/train_lightgbm.py --help
# Expected: Help message (or script runs)

# 6. Git configured
git remote -v
# Expected: origin pointing to GitHub repo
```

---

## 🤝 **Contributing**

Ready to contribute? Here's how:

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch
4. **Make** your changes
5. **Test** thoroughly
6. **Commit** with clear messages
7. **Push** to your fork
8. **Create** a pull request

See [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for ideas on what to work on!

---

## 📞 **Getting Help**

- **Documentation**: Check `docs/` folder
- **Issues**: Create a GitHub issue
- **Kaggle**: Review competition discussions
- **Community**: Join Kaggle forums

---

**Last Updated**: January 9, 2026  
**Estimated Setup Time**: 10-15 minutes (excluding data download)  
**Estimated Full Restore Time**: 15-20 minutes
