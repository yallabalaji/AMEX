# Jenkins CI/CD Pipeline for AMEX ML Project

## Overview

This Jenkins pipeline automates the entire ML workflow from data preprocessing to Kaggle submission.

## Pipeline Stages

```
Setup → Validate → Preprocess → Aggregate → Train → Predict → Submit
```

### Stage Details

1. **Setup Environment** - Creates Python venv and installs dependencies
2. **Validate Data** - Checks that required CSV files exist
3. **Preprocess Training Data** - Runs `preprocess_train.py`
4. **Preprocess Test Data** - Runs `preprocess_test.py`
5. **Aggregate Features (Train)** - Runs `aggregate_customer.py train`
6. **Aggregate Features (Test)** - Runs `aggregate_customer.py test`
7. **Train Model** - Runs `train_lightgbm.py` (or other model)
8. **Evaluate Model** - Displays metrics from `models/metrics.json`
9. **Generate Predictions** - Creates submission file
10. **Validate Submission** - Checks submission format
11. **Submit to Kaggle** - Uploads to Kaggle (optional)
12. **Archive Artifacts** - Saves models and submissions

## Setup Instructions

### 1. Jenkins Server Setup

```bash
# Install Jenkins (macOS)
brew install jenkins-lts
brew services start jenkins-lts

# Access Jenkins at http://localhost:8080
```

### 2. Configure Jenkins Credentials

1. Go to **Manage Jenkins** → **Manage Credentials**
2. Add **Secret text** credential:
   - ID: `kaggle-api-credentials`
   - Secret: `<your_kaggle_username>:<your_kaggle_key>`

### 3. Create Jenkins Job

1. **New Item** → **Pipeline**
2. Name: `AMEX-ML-Pipeline`
3. **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `<your_repo_url>`
   - Script Path: `Jenkinsfile`

### 4. Configure Build Parameters

The pipeline supports these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `PIPELINE_STAGE` | Choice | `full` | Which stage to run |
| `CHUNK_SIZE` | String | `100000` | Preprocessing chunk size |
| `MODEL_TYPE` | String | `lightgbm` | Model type to train |
| `SUBMIT_TO_KAGGLE` | Boolean | `false` | Auto-submit to Kaggle |

## Usage

### Run Full Pipeline

```
Build with Parameters:
- PIPELINE_STAGE: full
- CHUNK_SIZE: 100000
- MODEL_TYPE: lightgbm
- SUBMIT_TO_KAGGLE: true
```

### Run Specific Stage

```
# Only preprocess data
PIPELINE_STAGE: preprocess

# Only train model
PIPELINE_STAGE: train

# Only generate predictions
PIPELINE_STAGE: predict
```

## Pipeline Triggers

### Manual Trigger
- Click **Build with Parameters** in Jenkins UI

### Scheduled Trigger (Cron)
Add to Jenkinsfile:
```groovy
triggers {
    cron('H 2 * * *')  // Run daily at 2 AM
}
```

### Git Webhook Trigger
Add to Jenkinsfile:
```groovy
triggers {
    githubPush()  // Trigger on git push
}
```

## Monitoring

### View Build Logs
- Jenkins UI → Build #X → Console Output

### Check Artifacts
- Jenkins UI → Build #X → Artifacts
  - `models/lightgbm_model.txt`
  - `models/metrics.json`
  - `data/submissions/submission.csv`

### Performance Tracking
Create a dashboard to track:
- Build duration
- Model performance (ROC-AUC)
- Kaggle scores over time

## Advanced Configuration

### Parallel Execution

Modify Jenkinsfile to run train/test preprocessing in parallel:

```groovy
stage('Preprocess Data') {
    parallel {
        stage('Train') {
            steps {
                sh "python scripts/preprocess_train.py"
            }
        }
        stage('Test') {
            steps {
                sh "python scripts/preprocess_test.py"
            }
        }
    }
}
```

### Multi-Model Training

Train multiple models in parallel:

```groovy
stage('Train Models') {
    parallel {
        stage('LightGBM') {
            steps {
                sh "python scripts/train_lightgbm.py"
            }
        }
        stage('XGBoost') {
            steps {
                sh "python scripts/train_xgboost.py"
            }
        }
        stage('CatBoost') {
            steps {
                sh "python scripts/train_catboost.py"
            }
        }
    }
}
```

### Email Notifications

Add to `post` section:

```groovy
post {
    success {
        emailext (
            subject: "✅ AMEX Pipeline Success - Build #${BUILD_NUMBER}",
            body: "Model trained successfully. Kaggle score: ${KAGGLE_SCORE}",
            to: "your-email@example.com"
        )
    }
    failure {
        emailext (
            subject: "❌ AMEX Pipeline Failed - Build #${BUILD_NUMBER}",
            body: "Check logs: ${BUILD_URL}console",
            to: "your-email@example.com"
        )
    }
}
```

## Troubleshooting

### Issue: Out of Memory

**Solution**: Reduce chunk size or increase Jenkins executor memory:

```bash
# In Jenkins startup script
JENKINS_JAVA_OPTIONS="-Xmx8g -Xms4g"
```

### Issue: Kaggle Submission Fails

**Solution**: Check credentials and network:

```bash
# Test Kaggle API
export KAGGLE_USERNAME="your_username"
export KAGGLE_KEY="your_key"
kaggle competitions list
```

### Issue: Build Takes Too Long

**Solution**: Use incremental builds:

```groovy
// Skip preprocessing if data already exists
when {
    expression { 
        !fileExists("${DATA_DIR}/stage/linear_train.parquet")
    }
}
```

## Best Practices

1. **Version Control**: Commit Jenkinsfile to git
2. **Artifact Management**: Archive only essential files
3. **Resource Cleanup**: Clean intermediate files in `post` section
4. **Error Handling**: Add try-catch blocks for critical stages
5. **Logging**: Use structured logging for easier debugging

## Next Steps

1. **Add Unit Tests**: Run `pytest` before training
2. **Model Registry**: Store models in MLflow or similar
3. **A/B Testing**: Compare multiple model versions
4. **Auto-Tuning**: Integrate hyperparameter optimization
5. **Monitoring**: Set up Grafana dashboards for metrics
