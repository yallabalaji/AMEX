# AmEx Default Prediction Project

## Project Structure

This project follows a standard data science project structure to ensure maintainability and reproducibility.

### 1. `src/` (Source Code)
**"The Library"**
*   **Purpose**: Contains reusable code, functions, classes, and configuration.
*   **Why**: Code here is meant to be imported by other scripts or notebooks. It should not run anything when executed directly.
*   **Example**: `src/preprocessing.py` contains the logic for cleaning data, but doesn't actually run the cleaning process until called.

### 2. `scripts/` (Executable Scripts)
**"The Actions"**
*   **Purpose**: Contains command-line scripts that perform specific tasks (training, preprocessing, inference).
*   **Why**: These scripts orchestrate the functions from `src/` to do real work. They usually take arguments (like `--chunksize`).
*   **Example**: `scripts/preprocess_train.py` imports functions from `src/preprocessing.py` and runs them on the raw data.

### 3. `notebooks/` (Jupyter Notebooks)
**"The Lab"**
*   **Purpose**: For experimentation, data exploration (EDA), and prototyping.
*   **Why**: Notebooks are great for seeing results interactively but bad for production pipelines. Once an experiment works here, move the logic to `src/`.

### 4. `data/` (Data Storage)
*   **Purpose**: Stores all data files.
*   **Structure**:
    *   `raw/`: Original, immutable data (e.g., `train_data.csv`).
    *   `stage/`: Intermediate processed data (e.g., Parquet files).
    *   `final/`: Final datasets ready for modeling.

## Usage

### Preprocessing
To preprocess the training data:
```bash
python scripts/preprocess_train.py --chunksize 100000
```
