# AMEX Default Prediction - Production ML Pipeline

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Jenkins-D24939.svg)](https://www.jenkins.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 **Project Overview**

A complete, production-ready machine learning pipeline for credit default prediction, demonstrating end-to-end MLOps practices on real-world financial data from Kaggle's AMEX competition.

### **🏆 Key Achievements**
- 📊 **11M+ rows processed** with memory-efficient chunked processing
- 🤖 **4 production models** trained and ready (LightGBM, XGBoost, CatBoost, HistGB)
- 🎯 **0.764 Kaggle score** (Top 30%) with baseline model
- ⚡ **85% time savings** through intelligent caching
- 🚀 **Full CI/CD automation** with Jenkins
- ☁️ **Cloud-ready** with OCI and GCP deployment guides

### **💡 Technical Highlights**
- **Data Engineering**: Efficient processing of 5GB+ datasets with limited memory
- **MLOps**: Automated training, validation, and deployment pipeline
- **Cloud Architecture**: Multi-cloud deployment strategies (OCI free tier + GCP)
- **CI/CD**: Jenkins automation for continuous integration
- **Model Development**: Multiple algorithms with ensemble potential

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
├── docs/                       # Documentation
│   ├── cloud/                  # Cloud deployment guides
│   │   ├── oci/               # Oracle Cloud (free tier)
│   │   └── gcp/               # Google Cloud Platform
│   ├── ci-cd/                  # CI/CD documentation
│   │   └── jenkins/           # Jenkins setup guides
│   ├── learnings/              # Project learnings
│   └── notes/                  # Development notes
│
├── Jenkinsfile                 # CI/CD pipeline
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── SETUP.md                    # Setup guide for restoration
└── FUTURE_ENHANCEMENTS.md      # Roadmap and future work
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

See detailed guide: [docs/ci-cd/jenkins/SETUP_NATIVE.md](docs/ci-cd/jenkins/SETUP_NATIVE.md)

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

### **Cloud Deployment & MLOps**

7. **Deploy to Oracle Cloud** (2 hours)
   - Free tier deployment (4 ARM cores, 24GB RAM)
   - See: [docs/cloud/oci/QUICKSTART.md](docs/cloud/oci/QUICKSTART.md)

8. **Model Serving API** (15 hours)
   - FastAPI REST endpoints
   - Real-time predictions
   - Model versioning

9. **Experiment Tracking** (10 hours)
   - MLflow integration
   - Automated monitoring
   - Performance tracking

**See detailed roadmap**: [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md)

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

### **Getting Started**
- **[README.md](README.md)**: Project overview and quick start guide
- **[FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md)**: Roadmap and enhancement opportunities

### **Cloud Deployment**
- **Oracle Cloud (FREE)**: [docs/cloud/oci/README.md](docs/cloud/oci/README.md) - Free tier deployment guide
- **OCI Quick Start**: [docs/cloud/oci/QUICKSTART.md](docs/cloud/oci/QUICKSTART.md) - 15-minute deployment
- **GCP (Paid)**: [docs/cloud/gcp/README.md](docs/cloud/gcp/README.md) - Google Cloud deployment

### **Automation & CI/CD**
- **Jenkins Setup**: [docs/ci-cd/jenkins/SETUP_NATIVE.md](docs/ci-cd/jenkins/SETUP_NATIVE.md) - Local Jenkins installation
- **Local vs Cloud**: [docs/ci-cd/jenkins/LOCAL_VS_GCP.md](docs/ci-cd/jenkins/LOCAL_VS_GCP.md) - Deployment comparison

### **Project Learnings**
- **Postmortem**: [docs/learnings/postmortem.md](docs/learnings/postmortem.md) - Lessons learned
- **Development Notes**: [docs/notes/](docs/notes/) - Technical notes and insights

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

## 🎓 **Technologies & Skills Demonstrated**

### **Machine Learning**
- Gradient Boosting Models (LightGBM, XGBoost, CatBoost)
- Feature Engineering & Aggregation
- Model Training & Evaluation
- Hyperparameter Optimization

### **Data Engineering**
- Large-scale data processing (11M+ rows)
- Memory-efficient chunked processing
- Data validation and quality checks
- Parquet format optimization

### **MLOps & DevOps**
- CI/CD with Jenkins
- Multi-cloud deployment (OCI, GCP)
- Infrastructure as Code
- Automated testing and validation

### **Software Engineering**
- Python best practices
- Modular code architecture
- Version control with Git
- Documentation and code quality

---

## 📞 **Support & Resources**

### **Documentation**
- Check comprehensive guides in `docs/` folder
- Review troubleshooting section in this README
- Explore [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for improvement ideas

### **Community Resources**
- **Kaggle Competition**: [AMEX Default Prediction](https://www.kaggle.com/competitions/amex-default-prediction)
- **Discussion Forums**: Learn from competition discussions
- **Winning Solutions**: Study top performers' approaches

### **Technical Resources**
- **LightGBM**: https://lightgbm.readthedocs.io/
- **Jenkins**: https://www.jenkins.io/doc/
- **Oracle Cloud**: https://www.oracle.com/cloud/free/

---

## ✅ **Project Status**

### **Completed ✅**
- [x] Data preprocessing pipeline (11M rows)
- [x] Feature aggregation (50+ features)
- [x] Model training (4 models implemented)
- [x] Jenkins CI/CD automation
- [x] Kaggle submission automation
- [x] Cloud deployment guides (OCI + GCP)
- [x] Comprehensive documentation

### **Future Enhancements 🚀**
- [ ] Hyperparameter tuning with Optuna
- [ ] Advanced feature engineering
- [ ] Model ensemble and stacking
- [ ] Cloud deployment (OCI free tier)
- [ ] Model serving API (FastAPI)
- [ ] MLflow experiment tracking
- [ ] Monitoring and logging

**Current Score**: 0.764 (Top 30%)  
**Target Score**: 0.800+ (Top 10%)

See [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for detailed roadmap.

---

**Happy Learning! 🚀**
