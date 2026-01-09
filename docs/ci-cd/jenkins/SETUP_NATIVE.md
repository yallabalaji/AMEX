# Jenkins Setup - Native Installation (Recommended)

## Why Native Installation?

✅ **Lower memory footprint** - No Docker overhead  
✅ **Direct file access** - No volume mounting needed  
✅ **Better performance** - Native Python execution  
✅ **Simpler debugging** - Direct access to logs  

## Installation Steps

### 1. Install Jenkins (macOS)

```bash
# Install via Homebrew
brew install jenkins-lts

# Start Jenkins service
brew services start jenkins-lts

# Check status
brew services list | grep jenkins
```

### 2. Initial Setup

```bash
# Get initial admin password
cat ~/.jenkins/secrets/initialAdminPassword

# Access Jenkins UI
open http://localhost:8080
```

### 3. Install Required Plugins

In Jenkins UI:
1. **Manage Jenkins** → **Manage Plugins**
2. Install these plugins:
   - **Pipeline** (for Jenkinsfile support)
   - **Git** (for SCM integration)
   - **Credentials Binding** (for Kaggle API)
   - **Email Extension** (optional, for notifications)

### 4. Configure Credentials

1. **Manage Jenkins** → **Manage Credentials**
2. Click **(global)** → **Add Credentials**
3. Add **Secret text**:
   - **ID**: `kaggle-api-credentials`
   - **Secret**: `your_username:your_api_key`
   - **Description**: Kaggle API credentials

### 5. Create Pipeline Job

1. **New Item** → Enter name: `AMEX-ML-Pipeline`
2. Select **Pipeline** → Click **OK**
3. Configure:
   - **Pipeline Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `/Users/balaji/Projects/AMEX/AMEX` (local path)
   - **Script Path**: `Jenkinsfile`
4. Click **Save**

## Memory Configuration

Since you're running large ML jobs, configure Jenkins memory:

```bash
# Edit Jenkins config
nano /opt/homebrew/opt/jenkins-lts/homebrew.mxcl.jenkins-lts.plist

# Add to <dict> section:
<key>EnvironmentVariables</key>
<dict>
    <key>JENKINS_JAVA_OPTIONS</key>
    <string>-Xmx2g -Xms1g</string>
</dict>

# Restart Jenkins
brew services restart jenkins-lts
```

## Running Your First Build

### Option 1: Manual Trigger

1. Go to **AMEX-ML-Pipeline** job
2. Click **Build with Parameters**
3. Select:
   - **PIPELINE_STAGE**: `full`
   - **CHUNK_SIZE**: `100000`
   - **MODEL_TYPE**: `lightgbm`
   - **SUBMIT_TO_KAGGLE**: `false` (for testing)
4. Click **Build**

### Option 2: Command Line

```bash
# Trigger build via CLI
java -jar /opt/homebrew/opt/jenkins-lts/libexec/jenkins-cli.jar \
  -s http://localhost:8080/ \
  build AMEX-ML-Pipeline \
  -p PIPELINE_STAGE=full \
  -p MODEL_TYPE=lightgbm
```

## Resource Management Tips

### 1. Limit Concurrent Builds

In Jenkins job configuration:
- **Throttle Concurrent Builds**: Check this
- **Maximum Concurrent Builds**: `1`

This prevents multiple memory-intensive jobs from running simultaneously.

### 2. Monitor System Resources

```bash
# Monitor memory during build
watch -n 2 'ps aux | grep python | head -5'

# Check disk usage
df -h

# Monitor Jenkins process
top -pid $(pgrep -f jenkins)
```

### 3. Cleanup Strategy

Add to your Jenkinsfile `post` section:

```groovy
post {
    cleanup {
        sh """
            # Remove intermediate files
            rm -rf data/stage/refined_data/*.parquet
            rm -rf data/stage/aggregated/agg_tmp
            
            # Keep only last 3 models
            cd models
            ls -t lightgbm_model_*.txt | tail -n +4 | xargs rm -f
        """
    }
}
```

## Estimated Resource Usage

| Stage | RAM Usage | Duration |
|-------|-----------|----------|
| Preprocess Train | 4-6 GB | 15-20 min |
| Preprocess Test | 6-8 GB | 20-25 min |
| Aggregate Train | 3-4 GB | 10-15 min |
| Aggregate Test | 4-5 GB | 12-18 min |
| Train LightGBM | 6-8 GB | 8-12 min |
| Predict (chunked) | 2-3 GB | 5-8 min |
| **Total** | **Peak: 8 GB** | **~90 min** |

## Troubleshooting

### Issue: Jenkins won't start

```bash
# Check logs
tail -f /opt/homebrew/var/log/jenkins-lts/jenkins.log

# Restart service
brew services restart jenkins-lts
```

### Issue: Build fails with OOM

**Solution**: Reduce chunk size in build parameters:
- Change `CHUNK_SIZE` from `100000` to `50000`

### Issue: Python venv not found

**Solution**: Ensure Jenkins user has access:

```bash
# Check Jenkins user
ps aux | grep jenkins

# Give permissions
chmod -R 755 /Users/balaji/Projects/AMEX/AMEX/venv
```

## Alternative: Lightweight Automation (No Jenkins)

If Jenkins feels too heavy, use a simple cron job:

```bash
# Edit crontab
crontab -e

# Add daily training job (runs at 2 AM)
0 2 * * * cd /Users/balaji/Projects/AMEX/AMEX && ./venv/bin/python scripts/train_lightgbm.py >> logs/cron.log 2>&1
```

Or use a simple shell script:

```bash
#!/bin/bash
# run_pipeline.sh

set -e  # Exit on error

echo "Starting AMEX ML Pipeline..."

# Activate venv
source venv/bin/activate

# Run pipeline stages
echo "[1/6] Preprocessing train data..."
python scripts/preprocess_train.py

echo "[2/6] Preprocessing test data..."
python scripts/preprocess_test.py

echo "[3/6] Aggregating train features..."
python scripts/aggregate_customer.py train

echo "[4/6] Aggregating test features..."
python scripts/aggregate_customer.py test

echo "[5/6] Training model..."
python scripts/train_lightgbm.py

echo "[6/6] Validating submission..."
python scripts/validate_submission.py

echo "✅ Pipeline complete!"
```

## Recommendation

For your use case, I recommend:

1. **Start with native Jenkins** (no Docker)
2. **Monitor resource usage** during first few runs
3. **Adjust chunk sizes** if needed
4. **Consider cron jobs** if Jenkins is overkill

This approach will give you automation without the Docker overhead!
