# Jenkins Pipeline Configuration Reload Job

## 📋 **Purpose**

This job reloads the AMEX-ML-Pipeline configuration to pick up new parameters, dropdowns, checkboxes, and pipeline stages after you modify the Jenkinsfile.

## 🎯 **When to Use**

Run this job after making changes to `Jenkinsfile` such as:
- ✅ Adding new parameters (dropdowns, checkboxes, text fields)
- ✅ Adding new pipeline stages
- ✅ Modifying stage conditions
- ✅ Updating parameter choices

## 🚀 **Setup Instructions**

### **Step 1: Create the Job**

1. Open Jenkins: http://localhost:8080
2. Click **"New Item"**
3. Enter name: `Reload-Pipeline-Config`
4. Select: **"Pipeline"**
5. Click **"OK"**

### **Step 2: Configure the Job**

1. **General Section**:
   - Description: `Reloads AMEX-ML-Pipeline configuration to pick up new parameters and stages`

2. **Pipeline Section**:
   - Definition: **"Pipeline script from SCM"**
   - SCM: **"Git"**
   - Repository URL: `https://github.com/yallabalaji/AMEX.git`
   - Branch: `*/main`
   - Script Path: `.jenkins/ReloadPipelineConfig.jenkinsfile`

3. Click **"Save"**

### **Step 3: Alternative - Direct Script**

If you prefer not to use SCM:

1. **Pipeline Section**:
   - Definition: **"Pipeline script"**
   - Copy the entire content from [ReloadPipelineConfig.jenkinsfile](file:///Users/balaji/Projects/AMEX/AMEX/.jenkins/ReloadPipelineConfig.jenkinsfile)
   - Paste into the **Script** box

2. Click **"Save"**

## 📖 **Usage**

### **Scenario: You Added a New Parameter**

```groovy
// You added this to Jenkinsfile:
booleanParam(
    name: 'ENABLE_TUNING',
    defaultValue: false,
    description: 'Enable hyperparameter tuning'
)
```

**Steps:**
1. Commit and push Jenkinsfile changes
2. Go to Jenkins → **Reload-Pipeline-Config**
3. Click **"Build Now"**
4. Wait 10 seconds
5. Refresh browser
6. Go to **AMEX-ML-Pipeline** → **Build with Parameters**
7. ✅ You should see the new `ENABLE_TUNING` checkbox!

### **Scenario: You Added a New Stage**

```groovy
// You added this to Jenkinsfile:
stage('Hyperparameter Tuning') {
    when {
        expression { params.ENABLE_TUNING == true }
    }
    steps {
        // tuning logic
    }
}
```

**Steps:**
1. Commit and push Jenkinsfile changes
2. Run **Reload-Pipeline-Config** job
3. The new stage will be available in the next build

## 🔧 **What It Does**

The reload job performs these actions:

1. **Reloads Configuration**
   - Forces Jenkins to re-read the Jenkinsfile
   - Discovers new parameters
   - Updates stage definitions

2. **Triggers Parameter Discovery**
   - Runs a dummy build (may fail, that's OK)
   - Forces Jenkins to parse parameter definitions

3. **Displays Instructions**
   - Shows what changed
   - Provides troubleshooting tips

## ⚡ **Quick Reference**

### **When Parameters Don't Appear**

**Option 1: Use Reload Job** (Easiest)
```
Jenkins → Reload-Pipeline-Config → Build Now
```

**Option 2: Manual Reload**
```
Manage Jenkins → Reload Configuration from Disk
```

**Option 3: Restart Jenkins** (Nuclear option)
```bash
brew services restart jenkins-lts
```

### **Common Issues**

#### **Issue: "Job not found: reload-configuration"**
**Solution**: Ignore this error - it's expected. The configuration still reloads.

#### **Issue: Parameters still not showing**
**Solution**: 
1. Clear browser cache (Cmd+Shift+R / Ctrl+Shift+F5)
2. Try incognito/private window
3. Restart Jenkins

#### **Issue: "Build failed"**
**Solution**: Check the console output. The reload might still succeed even if the build fails.

## 📊 **Comparison: Before vs After**

### **Before (Manual Process)**

1. Modify Jenkinsfile
2. Commit and push
3. Go to AMEX-ML-Pipeline
4. Click "Build Now" (fails because parameters not loaded)
5. Wait for build to fail
6. Refresh browser
7. Click "Build with Parameters"
8. **Still don't see new parameters** 😞
9. Restart Jenkins
10. Wait 30 seconds
11. Finally see new parameters

**Time: ~2-3 minutes + frustration**

### **After (With Reload Job)**

1. Modify Jenkinsfile
2. Commit and push
3. Run **Reload-Pipeline-Config** job
4. Wait 10 seconds
5. Refresh browser
6. See new parameters! ✅

**Time: ~20 seconds**

## 🎯 **Best Practices**

### **Development Workflow**

```bash
# 1. Modify Jenkinsfile locally
vim Jenkinsfile

# 2. Test syntax (optional)
# Use Jenkins Linter or online validator

# 3. Commit and push
git add Jenkinsfile
git commit -m "Add ENABLE_TUNING parameter"
git push

# 4. Reload configuration
# Go to Jenkins → Reload-Pipeline-Config → Build Now

# 5. Test new parameter
# Go to AMEX-ML-Pipeline → Build with Parameters
# Verify new parameter appears
```

### **Testing New Parameters**

Always test new parameters with a quick build:
```
PIPELINE_STAGE: train
MODEL_TYPE: lightgbm
<NEW_PARAMETER>: test_value
```

## 📝 **Example Changes**

### **Adding a Dropdown**

```groovy
choice(
    name: 'TUNING_METHOD',
    choices: ['optuna', 'grid_search', 'random_search'],
    description: 'Hyperparameter tuning method'
)
```

**After reload**: Dropdown appears in build parameters

### **Adding a Checkbox**

```groovy
booleanParam(
    name: 'ENABLE_EARLY_STOPPING',
    defaultValue: true,
    description: 'Enable early stopping during training'
)
```

**After reload**: Checkbox appears in build parameters

### **Adding a Text Field**

```groovy
string(
    name: 'MAX_ITERATIONS',
    defaultValue: '1200',
    description: 'Maximum training iterations'
)
```

**After reload**: Text field appears in build parameters

## 🎊 **Summary**

**What**: Utility job to reload pipeline configuration

**When**: After modifying Jenkinsfile parameters or stages

**How**: Click "Build Now" on Reload-Pipeline-Config job

**Time**: ~10 seconds vs 2-3 minutes manual process

**Result**: New parameters/stages immediately available

---

**Pro Tip**: Bookmark this job in Jenkins for quick access! 🔖
