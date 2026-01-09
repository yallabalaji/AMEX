#!/bin/bash
# Complete End-to-End ML Pipeline
# Runs everything from raw data to Kaggle submission

set -e

echo "🚀 AMEX ML Pipeline - Complete Automation"
echo "=========================================="
echo ""

# Configuration
MODEL_TYPE=${1:-lightgbm}
SUBMIT_TO_KAGGLE=${2:-false}

echo "Configuration:"
echo "  Model: $MODEL_TYPE"
echo "  Submit to Kaggle: $SUBMIT_TO_KAGGLE"
echo ""

# Step 1: Check if raw data exists
echo "📊 Step 1/6: Checking data..."
if [ ! -f "data/raw/train_data.csv" ]; then
    echo "❌ Raw data not found!"
    echo "Please download data from Kaggle first:"
    echo "  kaggle competitions download -c amex-default-prediction"
    echo "  unzip amex-default-prediction.zip -d data/raw/"
    exit 1
fi
echo "✓ Raw data found"
echo ""

# Step 2: Preprocess training data
echo "🔧 Step 2/6: Preprocessing training data..."
if [ ! -f "data/stage/linear_train.parquet" ]; then
    python scripts/preprocess_train.py --chunksize 100000
    echo "✓ Training data preprocessed"
else
    echo "✓ Training data already preprocessed (skipping)"
fi
echo ""

# Step 3: Preprocess test data
echo "🔧 Step 3/6: Preprocessing test data..."
if [ ! -f "data/stage/linear_test.parquet" ]; then
    python scripts/preprocess_test.py --chunksize 100000
    echo "✓ Test data preprocessed"
else
    echo "✓ Test data already preprocessed (skipping)"
fi
echo ""

# Step 4: Aggregate features
echo "📈 Step 4/6: Aggregating features..."
if [ ! -f "data/stage/aggregated/customer_level_train.parquet" ]; then
    python scripts/aggregate_customer.py train
    echo "✓ Training features aggregated"
else
    echo "✓ Training features already aggregated (skipping)"
fi

if [ ! -f "data/stage/aggregated/customer_level_test.parquet" ]; then
    python scripts/aggregate_customer.py test
    echo "✓ Test features aggregated"
else
    echo "✓ Test features already aggregated (skipping)"
fi
echo ""

# Step 5: Train model
echo "🤖 Step 5/6: Training $MODEL_TYPE model..."
case $MODEL_TYPE in
    lightgbm)
        python scripts/train_lightgbm.py
        ;;
    xgboost)
        python scripts/train_xgboost.py
        ;;
    catboost)
        python scripts/train_catboost.py
        ;;
    histgb)
        python scripts/train_histgb.py
        ;;
    *)
        echo "❌ Unknown model type: $MODEL_TYPE"
        echo "Available: lightgbm, xgboost, catboost, histgb"
        exit 1
        ;;
esac
echo "✓ Model trained successfully"
echo ""

# Step 6: Submit to Kaggle (optional)
if [ "$SUBMIT_TO_KAGGLE" = "true" ]; then
    echo "📤 Step 6/6: Submitting to Kaggle..."
    python scripts/submit_kaggle.py \
        --file data/submissions/submission.csv \
        --msg "Automated submission - $MODEL_TYPE"
    echo "✓ Submitted to Kaggle"
else
    echo "⏭️  Step 6/6: Skipping Kaggle submission"
    echo "   (Run with 'true' as second argument to submit)"
fi
echo ""

# Summary
echo "✅ Pipeline Complete!"
echo ""
echo "📊 Results:"
echo "  Model: models/${MODEL_TYPE}_model.*"
echo "  Submission: data/submissions/submission.csv"
echo ""
echo "🎯 Next steps:"
echo "  1. Check model performance in logs"
echo "  2. Review submission file"
if [ "$SUBMIT_TO_KAGGLE" != "true" ]; then
    echo "  3. Submit manually: python scripts/submit_kaggle.py --file data/submissions/submission.csv"
fi
echo ""
