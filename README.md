# AMEX Default Prediction - ML Pipeline

## 🎯 **Project Overview**

Complete end-to-end machine learning pipeline for credit default prediction using the AMEX dataset from Kaggle.

**Current Status:**
- ✅ Data preprocessing pipeline (handles 11M rows)
- ✅ Feature aggregation (50+ features)
- ✅ 4 trained models (LightGBM, XGBoost, CatBoost, HistGB)
- ✅ Jenkins CI/CD automation
- ✅ Kaggle submission automation
- ✅ Current best score: **0.764** (LightGBM)

---

## 🚀 **Quick Start (5 minutes)**

### **Prerequisites**
- Python 3.11+
- 16 GB RAM minimum
- 20 GB free disk space
- Kaggle account

### **Setup**

```bash
# 1. Clone repository
git clone https://github.com/yallabalaji/AMEX.git
cd AMEX

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download data from Kaggle
# Place in data/raw/:
#   - train_data.csv
#   - train_labels.csv
#   - test_data.csv
```

### **Run Training**

```bash
# Train LightGBM model (fastest)
python scripts/train_lightgbm.py

# Output:
# - models/lightgbm_model.txt
# - data/submissions/submission.csv
```

---

## 📂 **Project Structure**

```
AMEX/
├── data/
│   ├── raw/                    # Original CSV files (gitignored)
│   │   ├── train_data.csv      # 11M rows, 5 GB
│   │   ├── train_labels.csv    # Target labels
│   │   └── test_data.csv       # Test set
│   ├── stage/
│   │   ├── linear_*.parquet    # Preprocessed data
│   │   └── aggregated/         # Customer-level features
│   └── submissions/            # Generated submissions
│
├── models/                     # Trained models
│   ├── lightgbm_model.txt
│   ├── xgboost_model.json
│   ├── catboost_model.cbm
│   └── histgb_model.pkl
│
├── scripts/                    # Python scripts
│   ├── preprocess_train.py     # Preprocess training data
│   ├── preprocess_test.py      # Preprocess test data
│   ├── aggregate_customer.py   # Feature aggregation
│   ├── train_lightgbm.py       # Train LightGBM
│   ├── train_xgboost.py        # Train XGBoost
│   ├── train_catboost.py       # Train CatBoost
│   ├── train_histgb.py         # Train HistGB
│   ├── validate_features.py    # Validate features
│   ├── validate_submission.py  # Validate submission
│   └── submit_kaggle.py        # Submit to Kaggle
│
├── .jenkins/                   # Jenkins configuration
│   ├── SETUP_NATIVE.md         # Jenkins setup guide
│   ├── LOCAL_VS_GCP.md         # Local vs GCP comparison
│   └── RELOAD_CONFIG_GUIDE.md  # Config reload guide
│
├── Jenkinsfile                 # CI/CD pipeline
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🔄 **Complete Pipeline Workflow**

### **Step 1: Preprocessing (60 minutes)**

```bash
# Preprocess training data
python scripts/preprocess_train.py --chunksize 100000

# Preprocess test data
python scripts/preprocess_test.py --chunksize 100000

# Output: data/stage/linear_train.parquet, linear_test.parquet
```

### **Step 2: Feature Aggregation (20 minutes)**

```bash
# Aggregate training features
python scripts/aggregate_customer.py train

# Aggregate test features
python scripts/aggregate_customer.py test

# Output: data/stage/aggregated/customer_level_*.parquet
```

### **Step 3: Model Training (10 minutes)**

```bash
# Train your chosen model
python scripts/train_lightgbm.py   # Fastest (8 min)
python scripts/train_xgboost.py    # Best accuracy (12 min)
python scripts/train_catboost.py   # Most robust (15 min)
python scripts/train_histgb.py     # Scikit-learn (5 min)

# Output: models/<model_name>, data/submissions/submission.csv
```

### **Step 4: Validation & Submission (2 minutes)**

```bash
# Validate submission format
python scripts/validate_submission.py --submission data/submissions/submission.csv

# Submit to Kaggle
python scripts/submit_kaggle.py \
    --file data/submissions/submission.csv \
    --msg "LightGBM baseline"
```

---

## 🤖 **Jenkins Automation**

### **Setup Jenkins (30 minutes)**

See detailed guide: [.jenkins/SETUP_NATIVE.md](.jenkins/SETUP_NATIVE.md)

```bash
# Install Jenkins
brew install jenkins-lts

# Start Jenkins
brew services start jenkins-lts

# Open http://localhost:8080
```

### **Run Automated Pipeline**

1. Go to Jenkins → **AMEX-ML-Pipeline**
2. Click **"Build with Parameters"**
3. Select options:
   - `USE_CUSTOM_WORKSPACE`: ✅ (avoids data duplication)
   - `PIPELINE_STAGE`: `train` (skip preprocessing if data exists)
   - `MODEL_TYPE`: `lightgbm` (or xgboost/catboost/histgb)
   - `SUBMIT_TO_KAGGLE`: ✅ (auto-submit after training)
4. Click **"Build"**

**Pipeline automatically:**
- ✅ Checks for existing processed data (skips if exists)
- ✅ Trains selected model
- ✅ Generates predictions
- ✅ Validates submission
- ✅ Submits to Kaggle
- ✅ Archives models and submissions

**Time**: 15 minutes (with existing data) vs 90 minutes (full pipeline)

---

## 📊 **Model Comparison**

| Model | Score | Training Time | Memory | Best For |
|-------|-------|---------------|--------|----------|
| **LightGBM** | 0.764 | 8 min | 6 GB | Fast iterations |
| **XGBoost** | 0.768* | 12 min | 8 GB | Best accuracy |
| **CatBoost** | 0.766* | 15 min | 8 GB | Robustness |
| **HistGB** | 0.767* | 5 min | 6 GB | Scikit-learn |

*Expected scores (not yet tested)

---

## 🎯 **Next Steps for Improvement**

### **Quick Wins (2-10 hours)**

1. **Test All Models** (1 hour)
   - Run XGBoost, CatBoost, HistGB
   - Compare Kaggle scores
   - Expected: +0.5% improvement

2. **Simple Ensemble** (2 hours)
   - Average predictions from top 3 models
   - Expected: +1.2% improvement → **0.773**

3. **Hyperparameter Tuning** (6 hours)
   - Use Optuna for automated tuning
   - Expected: +0.8% improvement → **0.778**

### **Major Improvements (20-40 hours)**

4. **Advanced Features** (12 hours)
   - Difference features (last - first)
   - Lag features (previous month values)
   - Rolling aggregations (3-month, 6-month)
   - Expected: +2% improvement → **0.785**

5. **Custom AMEX Metric** (6 hours)
   - Implement competition-specific metric
   - Optimize for top 4% capture rate
   - Expected: +0.5% improvement → **0.790**

6. **Stacking Ensemble** (8 hours)
   - Meta-learner on top of base models
   - Expected: +1% improvement → **0.800+**

See detailed roadmap: [roadmap.md](roadmap.md)

---

## 🐛 **Troubleshooting**

### **Out of Memory Error**

```python
# Reduce chunk size in preprocessing
python scripts/preprocess_train.py --chunksize 50000  # Instead of 100000
```

### **Jenkins Not Finding Data**

```bash
# Ensure USE_CUSTOM_WORKSPACE is checked
# Or create symlink manually:
ln -s /Users/balaji/Projects/AMEX/AMEX/data /Users/balaji/.jenkins/workspace/AMEX-ML-Pipeline/data
```

### **Kaggle Submission Fails**

```bash
# Check Kaggle credentials
cat ~/.kaggle/kaggle.json

# Re-authenticate if needed
kaggle competitions list
```

### **Model Training Fails**

```bash
# Check if data exists
ls -lh data/stage/aggregated/

# If missing, run aggregation first
python scripts/aggregate_customer.py train
python scripts/aggregate_customer.py test
```

---

## 📚 **Documentation**

- **Implementation Plan**: [implementation_plan.md](implementation_plan.md) - GCP deployment & enhancements
- **Roadmap**: [roadmap.md](roadmap.md) - 3-month improvement plan
- **Walkthrough**: [walkthrough.md](walkthrough.md) - Complete feature overview
- **Jenkins Setup**: [.jenkins/SETUP_NATIVE.md](.jenkins/SETUP_NATIVE.md) - Local Jenkins installation
- **GCP Guide**: [.gcp/README.md](.gcp/README.md) - Cloud deployment (planned)

---

## 🤝 **Contributing**

This project is set up for easy continuation:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-features`
3. **Make changes and test**
4. **Commit**: `git commit -m "Add new features"`
5. **Push**: `git push origin feature/new-features`
6. **Create Pull Request**

---

## 📝 **License**

This project is for educational purposes.

---

## 🎓 **Learning Resources**

- **Kaggle Competition**: [AMEX Default Prediction](https://www.kaggle.com/competitions/amex-default-prediction)
- **LightGBM Docs**: https://lightgbm.readthedocs.io/
- **Jenkins Docs**: https://www.jenkins.io/doc/
- **Winning Solutions**: Check Kaggle discussion for top solutions

---

## 📞 **Support**

For questions or issues:
1. Check documentation in `.jenkins/` and artifact files
2. Review Kaggle competition discussions
3. Check GitHub issues

---

## ✅ **Project Checklist**

- [x] Data preprocessing pipeline
- [x] Feature aggregation
- [x] Model training (4 models)
- [x] Jenkins automation
- [x] Kaggle submission
- [ ] Hyperparameter tuning
- [ ] Advanced features
- [ ] Model ensemble
- [ ] GCP deployment
- [ ] Docker containerization
- [ ] API serving

**Current Score**: 0.764
**Target Score**: 0.800+

---

**Happy Learning! 🚀**
