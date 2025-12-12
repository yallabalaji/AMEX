pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.14'
        VENV_PATH = "${WORKSPACE}/venv"
        DATA_DIR = "${WORKSPACE}/data"
        MODELS_DIR = "${WORKSPACE}/models"
        KAGGLE_CONFIG = credentials('kaggle-api-credentials')
    }
    
    parameters {
        booleanParam(
            name: 'USE_CUSTOM_WORKSPACE',
            defaultValue: true,
            description: 'Use custom workspace (local dev) to avoid data duplication. Uncheck for GCP/default workspace.'
        )
        choice(
            name: 'PIPELINE_STAGE',
            choices: ['full', 'preprocess', 'aggregate', 'train', 'predict'],
            description: 'Which stage of the pipeline to run'
        )
        string(
            name: 'CHUNK_SIZE',
            defaultValue: '100000',
            description: 'Chunk size for preprocessing'
        )
        string(
            name: 'MODEL_TYPE',
            defaultValue: 'lightgbm',
            description: 'Model type: lightgbm, xgboost, catboost'
        )
        booleanParam(
            name: 'SUBMIT_TO_KAGGLE',
            defaultValue: false,
            description: 'Submit predictions to Kaggle after training'
        )
    }
    
    stages {
        stage('Setup Workspace') {
            steps {
                script {
                    if (params.USE_CUSTOM_WORKSPACE) {
                        echo "Using custom workspace: /Users/balaji/Projects/AMEX/AMEX"
                        // Create symlink to avoid data duplication
                        sh """
                            if [ ! -L "${WORKSPACE}/data" ] && [ ! -d "${WORKSPACE}/data" ]; then
                                ln -s /Users/balaji/Projects/AMEX/AMEX/data ${WORKSPACE}/data
                                echo "✓ Created symlink to data directory"
                            else
                                echo "✓ Data directory already exists"
                            fi
                        """
                    } else {
                        echo "Using default Jenkins workspace: ${WORKSPACE}"
                        echo "Note: You'll need to upload data separately for GCP"
                    }
                }
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    echo "Setting up Python virtual environment..."
                    sh """
                        python3 -m venv ${VENV_PATH}
                        . ${VENV_PATH}/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    """
                }
            }
        }
        
        stage('Validate Data') {
            steps {
                script {
                    echo "Validating raw data files..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        python -c "
import pandas as pd
from pathlib import Path

raw_dir = Path('${DATA_DIR}/raw')
required_files = ['train_data.csv', 'train_labels.csv', 'test_data.csv']

for f in required_files:
    path = raw_dir / f
    if not path.exists():
        raise FileNotFoundError(f'Missing required file: {f}')
    print(f'✓ Found {f} ({path.stat().st_size / 1e9:.2f} GB)')
                        "
                    """
                }
            }
        }
        
        stage('Preprocess Training Data') {
            when {
                expression { params.PIPELINE_STAGE in ['full', 'preprocess'] }
            }
            steps {
                script {
                    echo "Preprocessing training data..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        python scripts/preprocess_train.py --chunksize ${params.CHUNK_SIZE}
                    """
                }
            }
        }
        
        stage('Preprocess Test Data') {
            when {
                expression { params.PIPELINE_STAGE in ['full', 'preprocess'] }
            }
            steps {
                script {
                    echo "Preprocessing test data..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        python scripts/preprocess_test.py --chunksize ${params.CHUNK_SIZE}
                    """
                }
            }
        }
        
        stage('Aggregate Features - Train') {
            when {
                expression { params.PIPELINE_STAGE in ['full', 'aggregate'] }
            }
            steps {
                script {
                    echo "Aggregating training features..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        python scripts/aggregate_customer.py train
                    """
                }
            }
        }
        
        stage('Aggregate Features - Test') {
            when {
                expression { params.PIPELINE_STAGE in ['full', 'aggregate'] }
            }
            steps {
                script {
                    echo "Aggregating test features..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        python scripts/aggregate_customer.py test
                    """
                }
            }
        }
        
        stage('Train Model') {
            when {
                expression { params.PIPELINE_STAGE in ['full', 'train'] }
            }
            steps {
                script {
                    echo "Training ${params.MODEL_TYPE} model..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        python scripts/train_${params.MODEL_TYPE}.py
                    """
                }
            }
        }
        
        stage('Evaluate Model') {
            when {
                expression { params.PIPELINE_STAGE in ['full', 'train'] }
            }
            steps {
                script {
                    echo "Evaluating model performance..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        python -c "
import json
from pathlib import Path

metrics_path = Path('${MODELS_DIR}/metrics.json')
if metrics_path.exists():
    with open(metrics_path) as f:
        metrics = json.load(f)
    print('Model Metrics:')
    for k, v in metrics.items():
        print(f'  {k}: {v}')
else:
    print('No metrics file found')
                        "
                    """
                }
            }
        }
        
        stage('Generate Predictions') {
            when {
                expression { params.PIPELINE_STAGE in ['full', 'predict'] }
            }
            steps {
                script {
                    echo "Generating predictions on test set..."
                    // Predictions are generated in train script
                    sh """
                        . ${VENV_PATH}/bin/activate
                        ls -lh ${DATA_DIR}/submissions/submission.csv
                    """
                }
            }
        }
        
        stage('Validate Submission') {
            when {
                expression { params.PIPELINE_STAGE in ['full', 'predict'] }
            }
            steps {
                script {
                    echo "Validating submission format..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        python scripts/validate_submission.py \
                            --submission ${DATA_DIR}/submissions/submission.csv
                    """
                }
            }
        }
        
        stage('Submit to Kaggle') {
            when {
                expression { params.SUBMIT_TO_KAGGLE == true }
            }
            steps {
                script {
                    echo "Submitting to Kaggle..."
                    sh """
                        . ${VENV_PATH}/bin/activate
                        export KAGGLE_USERNAME=\$(echo \$KAGGLE_CONFIG | cut -d: -f1)
                        export KAGGLE_KEY=\$(echo \$KAGGLE_CONFIG | cut -d: -f2)
                        
                        python scripts/submit_kaggle.py \
                            --file ${DATA_DIR}/submissions/submission.csv \
                            --msg "Jenkins build #${BUILD_NUMBER} - ${params.MODEL_TYPE}"
                    """
                }
            }
        }
        
        stage('Archive Artifacts') {
            steps {
                script {
                    echo "Archiving artifacts..."
                    archiveArtifacts artifacts: 'models/*.txt,models/*.pkl,models/*.json', allowEmptyArchive: true
                    archiveArtifacts artifacts: 'data/submissions/*.csv', allowEmptyArchive: true
                    archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true
                }
            }
        }
    }
    
    post {
        success {
            echo "Pipeline completed successfully!"
            // Optional: Send notification
        }
        failure {
            echo "Pipeline failed!"
            // Optional: Send notification
        }
        cleanup {
            echo "Cleaning up workspace..."
            // Optional: Clean up large intermediate files
            sh """
                rm -rf ${DATA_DIR}/stage/refined_data/*.parquet || true
                rm -rf ${DATA_DIR}/stage/aggregated/agg_tmp || true
            """
        }
    }
}
