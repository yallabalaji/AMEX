# Jenkins Stage View Setup Guide

## 🎨 **Visual Pipeline Representation**

Jenkins Stage View shows your pipeline as a visual flow diagram with stage status, duration, and logs.

## 🚀 **Quick Setup (5 minutes)**

### **Method 1: Blue Ocean (Recommended)**

**Best for**: Modern, beautiful UI with detailed visualizations

1. **Install Blue Ocean Plugin**
   ```
   Manage Jenkins → Manage Plugins → Available
   Search: "Blue Ocean"
   Install without restart
   ```

2. **Access Blue Ocean**
   ```
   Jenkins Home → Open Blue Ocean (left sidebar)
   Click: AMEX-ML-Pipeline
   ```

3. **What You'll See**
   ```
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │   Setup      │─▶│   Validate   │─▶│    Train     │─▶│   Submit     │
   │  Workspace   │  │     Data     │  │    Model     │  │  to Kaggle   │
   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
        ✅ 2s             ✅ 5s            🔄 8m 30s          ⏸ Waiting
   ```

### **Method 2: Classic Stage View**

**Best for**: Simple, lightweight visualization

1. **Install Stage View Plugin**
   ```
   Manage Jenkins → Manage Plugins → Available
   Search: "Pipeline: Stage View"
   Install and restart
   ```

2. **Access Stage View**
   ```
   AMEX-ML-Pipeline → Build #X → Stage View tab
   ```

3. **What You'll See**
   ```
   Setup Workspace  |  Validate Data  |  Train Model  |  Submit
       [2s] ✅      |     [5s] ✅     |   [8m 30s] ✅ |  [10s] ✅
   ```

## 📊 **Stage View Features**

### **Status Indicators**

| Icon | Meaning | Description |
|------|---------|-------------|
| ✅ | Success | Stage completed successfully |
| ❌ | Failed | Stage failed, click for logs |
| 🔵 | Running | Stage currently executing |
| ⏸ | Waiting | Stage waiting to start |
| ⏭ | Skipped | Stage skipped (when condition) |

### **Interactive Features**

1. **Click on Stage** → See detailed logs for that stage only
2. **Hover over Stage** → See duration and status
3. **Parallel Stages** → Shown side-by-side
4. **Failed Stages** → Highlighted in red with error details

## 🎯 **Your Pipeline Stages**

Based on your Jenkinsfile, here's what you'll see:

### **Full Pipeline View**

```
┌─────────────────────────────────────────────────────────────────┐
│                    AMEX ML Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Setup Workspace ──▶ Setup Environment ──▶ Check Existing Files │
│       [1s]                 [30s]                  [2s]           │
│        ✅                   ✅                     ✅             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Preprocessing (if needed)                   │   │
│  │  Preprocess Train ──▶ Preprocess Test                   │   │
│  │     [30m] ⏭             [25m] ⏭                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Aggregation (if needed)                     │   │
│  │  Aggregate Train ──▶ Aggregate Test                     │   │
│  │     [10m] ⏭            [10m] ⏭                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Train Model ──▶ Evaluate Model ──▶ Generate Predictions        │
│    [8m 30s]          [5s]              [5m]                     │
│      ✅              ✅                 ✅                        │
│                                                                  │
│  Validate Submission ──▶ Submit to Kaggle ──▶ Display Results   │
│       [2s]                   [10s]                [1s]          │
│        ✅                     ✅                   ✅            │
│                                                                  │
│  Archive Artifacts ──▶ Cleanup                                  │
│       [5s]               [10s]                                  │
│        ✅                 ✅                                     │
└─────────────────────────────────────────────────────────────────┘

Total Duration: 15m 30s
Status: SUCCESS ✅
```

### **Train-Only Pipeline View**

When you select `PIPELINE_STAGE: train`:

```
Setup Workspace ──▶ Setup Environment ──▶ Check Files ──▶ Train Model
     [1s] ✅            [30s] ✅            [2s] ✅         [8m] ✅
                                                              │
                                                              ▼
Evaluate ──▶ Generate Predictions ──▶ Validate ──▶ Submit ──▶ Archive
 [5s] ✅         [5m] ✅                [2s] ✅      [10s] ✅    [5s] ✅

Total: 13m 55s
```

## 🎨 **Blue Ocean Specific Features**

### **1. Pipeline Visualization**

- **Horizontal Flow**: Stages flow left to right
- **Parallel Stages**: Shown vertically aligned
- **Nested Stages**: Expandable sections

### **2. Log Viewer**

- **Real-time Logs**: Updates as stage runs
- **ANSI Colors**: Colored output preserved
- **Search**: Find specific log entries
- **Download**: Save logs locally

### **3. Branch View**

- **Multiple Branches**: See all branches
- **Pull Requests**: Automatic PR builds
- **Comparison**: Compare builds across branches

### **4. Artifacts**

- **Visual List**: See all archived artifacts
- **Download**: One-click download
- **Preview**: View text files inline

## 📱 **Mobile-Friendly**

Blue Ocean is responsive and works on:
- 📱 iPhone/iPad
- 🤖 Android devices
- 💻 Tablets

## 🔧 **Customization**

### **Add Stage Descriptions**

```groovy
stage('Train Model') {
    options {
        description 'Train selected model (LightGBM/XGBoost/CatBoost/HistGB)'
    }
    steps {
        // ...
    }
}
```

### **Add Stage Timeout**

```groovy
stage('Train Model') {
    options {
        timeout(time: 30, unit: 'MINUTES')
    }
    steps {
        // ...
    }
}
```

### **Add Stage Retry**

```groovy
stage('Submit to Kaggle') {
    options {
        retry(3)
    }
    steps {
        // ...
    }
}
```

## 📊 **Performance Insights**

Stage View helps you identify:

1. **Bottlenecks**: Which stages take longest?
2. **Failures**: Which stages fail most often?
3. **Optimization**: Where to focus improvement efforts?

### **Example Analysis**

```
Stage                Duration    % of Total
─────────────────────────────────────────────
Setup Environment    30s         3%
Preprocess Train     30m         33%  ← Bottleneck!
Preprocess Test      25m         28%  ← Bottleneck!
Aggregate Train      10m         11%
Aggregate Test       10m         11%
Train Model          8m          9%
Generate Predictions 5m          5%
─────────────────────────────────────────────
Total               88m         100%

Optimization: Add file existence checks ✅
New Total: 13m (85% faster!)
```

## 🎯 **Quick Access**

### **Blue Ocean URLs**

```
Main View:
http://localhost:8080/blue/organizations/jenkins/pipelines

Your Pipeline:
http://localhost:8080/blue/organizations/jenkins/AMEX-ML-Pipeline/activity

Latest Build:
http://localhost:8080/blue/organizations/jenkins/AMEX-ML-Pipeline/detail/AMEX-ML-Pipeline/1/pipeline
```

### **Classic Stage View URLs**

```
Stage View:
http://localhost:8080/job/AMEX-ML-Pipeline/1/flowGraphTable/

Console Output:
http://localhost:8080/job/AMEX-ML-Pipeline/1/console
```

## 🐛 **Troubleshooting**

### **Issue: Blue Ocean not appearing**

**Solution**:
```bash
# Restart Jenkins
brew services restart jenkins-lts

# Clear browser cache
Cmd+Shift+R (Mac) / Ctrl+Shift+F5 (Windows)
```

### **Issue: Stages not showing**

**Solution**:
- Ensure Jenkinsfile has proper `stage` blocks
- Check pipeline syntax
- Rebuild the job

### **Issue: Logs not loading**

**Solution**:
- Check Jenkins disk space
- Increase Java heap: `-Xmx2g` in Jenkins config
- Clear old builds

## 📚 **Resources**

- [Blue Ocean Documentation](https://www.jenkins.io/doc/book/blueocean/)
- [Pipeline Stage View Plugin](https://plugins.jenkins.io/pipeline-stage-view/)
- [Pipeline Syntax Reference](https://www.jenkins.io/doc/book/pipeline/syntax/)

## ✅ **Summary**

**Install**: Blue Ocean plugin (5 min)
**Access**: Jenkins → Open Blue Ocean
**View**: Beautiful visual pipeline
**Benefit**: Better debugging and monitoring

Your pipeline will look amazing! 🎨
