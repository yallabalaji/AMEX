"""
AmEx Default Prediction - Preprocessing Module.

This module provides a comprehensive suite of functions for preprocessing the 
American Express dataset. It handles:
- Missing value imputation (using medians, modes, and sentinels).
- Categorical encoding (consistency enforcement via category maps).
- Data type optimization (float16/float32 conversion).
- Feature selection (dropping low-correlation columns).

Usage:
    from src.preprocessing import preprocess_and_save_parquet, build_category_map
"""

import json
import os
import sys
from typing import List, Dict, Optional, Any

import humanize
import numpy as np
import pandas as pd


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# Sentinel values for missing data imputation
SENTINEL_NUMERIC = -999
SENTINEL_FLOAT = -999.0
SENTINEL_INT = -1
SENTINEL_STRING = "MISSING"

# Column Groups
BOOL_COLS: List[str] = ['B_31']

FLOAT16_COLS: List[str] = [
    'D_66', 'D_68', 'B_30', 'D_87', 'B_38', 'D_114', 'D_116',
    'D_117', 'D_120', 'D_126'
]

FLOAT32_COLS: List[str] = [
    'P_2', 'D_39', 'B_1', 'B_2', 'R_1', 'S_3', 'D_41', 'B_3', 'D_42',
    'D_43', 'D_44', 'B_4', 'D_45', 'B_5', 'R_2', 'D_46', 'D_47', 'D_48',
    'D_49', 'B_6', 'B_7', 'B_8', 'D_50', 'D_51', 'B_9', 'R_3', 'D_52',
    'P_3', 'B_10', 'D_53', 'S_5', 'B_11', 'S_6', 'D_54', 'R_4', 'S_7',
    'B_12', 'S_8', 'D_55', 'D_56', 'B_13', 'R_5', 'D_58', 'S_9', 'B_14',
    'D_59', 'D_60', 'D_61', 'B_15', 'S_11', 'D_62', 'D_65', 'B_16', 'B_17',
    'B_18', 'B_19', 'B_20', 'S_12', 'R_6', 'S_13', 'B_21', 'D_69', 'B_22',
    'D_70', 'D_71', 'D_72', 'S_15', 'B_23', 'D_73', 'P_4', 'D_74', 'D_75',
    'D_76', 'B_24', 'R_7', 'D_77', 'B_25', 'B_26', 'D_78', 'D_79', 'R_8',
    'R_9', 'S_16', 'D_80', 'R_10', 'R_11', 'B_27', 'D_81', 'D_82', 'S_17',
    'R_12', 'B_28', 'R_13', 'D_83', 'R_14', 'R_15', 'D_84', 'R_16', 'B_29',
    'S_18', 'D_86', 'R_17', 'R_18', 'D_88', 'S_19', 'R_19', 'B_32', 'S_20',
    'R_20', 'R_21', 'B_33', 'D_89', 'R_22', 'R_23', 'D_91', 'D_92', 'D_93',
    'D_94', 'R_24', 'R_25', 'D_96', 'S_22', 'S_23', 'S_24', 'S_25', 'S_26',
    'D_102', 'D_103', 'D_104', 'D_105', 'D_106', 'D_107', 'B_36', 'B_37',
    'R_26', 'R_27', 'D_108', 'D_109', 'D_110', 'D_111', 'B_39', 'D_112',
    'B_40', 'S_27', 'D_113', 'D_115', 'D_118', 'D_119', 'D_121', 'D_122',
    'D_123', 'D_124', 'D_125', 'D_127', 'D_128', 'D_129', 'B_41', 'B_42',
    'D_130', 'D_131', 'D_132', 'D_133', 'R_28', 'D_134', 'D_135', 'D_136',
    'D_137', 'D_138', 'D_139', 'D_140', 'D_141', 'D_142', 'D_143', 'D_144',
    'D_145'
]

HIGH_CORR_COLS: List[str] = [
    'D_111', 'D_110', 'B_39', 'D_134', 'D_135', 'D_136', 'D_137',
    'D_138', 'R_9', 'D_106', 'D_132', 'D_49', 'R_26', 'D_76',
    'D_66', 'D_42', 'D_142', 'D_53', 'D_82'
]

LOW_MISSING_CORR_COLS: List[str] = ['D_87', 'D_88', 'D_108', 'D_73', 'B_42', 'B_29']

# Cardinality mapping for categorical columns
CARDINALITY_MAP: Dict[str, int] = {
    "D_87": 1, "D_120": 2, "D_66": 2, "D_116": 2, "D_114": 2,
    "D_126": 3, "B_30": 3, "D_117": 7, "B_38": 7
}

CATEGORICAL_COLS: List[str] = list(CARDINALITY_MAP.keys())

# Extra categoricals used for linear models (string-based)
LINEAR_EXTRA_CATEGORICAL_COLS: List[str] = ["D_63", "D_64"]

# All categorical columns that should be one-hot encoded for linear models
LINEAR_CATEGORICAL_COLS: List[str] = CATEGORICAL_COLS + LINEAR_EXTRA_CATEGORICAL_COLS

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def print_variable_sizes(top_n: Optional[int] = None, scope: Optional[Dict[str, Any]] = None) -> None:
    """
    Prints all variables in the given scope, sorted by memory usage.
    
    Args:
        top_n: Number of top variables to display.
        scope: Dictionary to inspect (defaults to globals() if None).
    """
    if scope is None:
        scope = globals()

    var_list = []
    for k, v in scope.items():
        if k.startswith('_'):
            continue
        try:
            size = sys.getsizeof(v)
            var_list.append((k, type(v).__name__, size, humanize.naturalsize(size)))
        except Exception:
            continue

    var_list.sort(key=lambda x: x[2], reverse=True)

    print(f"{'Variable':<20} {'Type':<20} {'Size':<15}")
    print("-" * 55)
    for i, (name, vtype, size, size_str) in enumerate(var_list):
        if top_n is not None and i >= top_n:
            break
        print(f"{name:<20} {vtype:<20} {size_str:<15}")


# =============================================================================
# PREPROCESSING LOGIC
# =============================================================================

def handle_high_corr_missingness(df: pd.DataFrame, high_corr_cols: List[str]) -> pd.DataFrame:
    """
    Handles missing values for highly correlated columns by creating missingness flags
    and filling NaNs with sentinel values.

    Args:
        df: Input DataFrame.
        high_corr_cols: List of column names to process.

    Returns:
        DataFrame with added flags and imputed values.
    """
    # 1. Create missingness flags
    missing_flag_cols = {
        f"{col}_was_missing": df[col].isna().astype(np.uint8)
        for col in high_corr_cols if col in df.columns
    }
    if missing_flag_cols:
        df = pd.concat([df, pd.DataFrame(missing_flag_cols, index=df.index)], axis=1)

    # 2. Fill NaNs with sentinel values based on dtype
    for col in high_corr_cols:
        if col in df.columns:
            col_dtype = df[col].dtype

            if isinstance(col_dtype, pd.CategoricalDtype):
                base_type = df[col].cat.categories.dtype

                if pd.api.types.is_numeric_dtype(base_type):
                    sentinel = SENTINEL_NUMERIC
                    if sentinel not in df[col].cat.categories:
                        df[col] = df[col].cat.add_categories([sentinel])
                    df[col] = df[col].fillna(sentinel)
                else:
                    sentinel = SENTINEL_STRING
                    if sentinel not in df[col].cat.categories:
                        df[col] = df[col].cat.add_categories([sentinel])
                    df[col] = df[col].fillna(sentinel)

            elif pd.api.types.is_float_dtype(col_dtype):
                df[col] = df[col].fillna(SENTINEL_FLOAT)

            elif pd.api.types.is_integer_dtype(col_dtype):
                df[col] = df[col].fillna(SENTINEL_INT)

            else:
                df[col] = df[col].fillna(SENTINEL_STRING)

    return df


def preprocess_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocesses a single chunk of data.

    Operations:
    - Boolean conversion.
    - Float16/Float32 conversion and median imputation.
    - String and Datetime conversion.
    - Categorical imputation (mode/sentinel).
    - Feature selection (dropping low-correlation columns).
    - High-correlation missingness handling.

    NOTE:
    - This function does NOT perform one-hot encoding.
    - Linear models should always go through `load_and_prepare_for_linear`
      with a precomputed category map.
    """
    # Boolean conversions
    for col in BOOL_COLS:
        if col in chunk.columns:
            chunk[col] = chunk[col].astype(bool)

    # Float16 conversions and median imputation
    for col in FLOAT16_COLS:
        if col in chunk.columns:
            median_val = chunk[col].median()
            chunk[col] = chunk[col].fillna(median_val).astype('float16')

    # Float32 conversions and median imputation
    for col in FLOAT32_COLS:
        if col in chunk.columns:
            median_val = chunk[col].median()
            chunk[col] = chunk[col].fillna(median_val).astype('float32')

    # String conversion
    if 'customer_ID' in chunk.columns:
        chunk['customer_ID'] = chunk['customer_ID'].astype('string')

    # Datetime conversion
    if 'S_2' in chunk.columns:
        chunk['S_2'] = pd.to_datetime(chunk['S_2'])

    # Fixed known categorical columns and imputation
    for col in ['D_63', 'D_64']:
        if col in chunk.columns:
            chunk[col] = chunk[col].astype('category')
            if col == 'D_64':
                if SENTINEL_STRING not in chunk[col].cat.categories:
                    chunk[col] = chunk[col].cat.add_categories(SENTINEL_STRING)
                chunk[col] = chunk[col].fillna(SENTINEL_STRING)
            else:
                mode_val = chunk[col].mode()
                if not mode_val.empty:
                    chunk[col] = chunk[col].fillna(mode_val[0])

    # Other categorical columns and mode imputation
    for col in CATEGORICAL_COLS:
        if col in chunk.columns:
            if pd.api.types.is_float_dtype(chunk[col].dtype) and chunk[col].dtype == 'float16':
                chunk[col] = chunk[col].astype('float32')
            chunk[col] = chunk[col].astype('category')
            mode_val = chunk[col].mode()
            if not mode_val.empty:
                chunk[col] = chunk[col].fillna(mode_val[0])

    # Drop low missing correlation columns
    cols_to_drop = [col for col in LOW_MISSING_CORR_COLS if col in chunk.columns]
    if cols_to_drop:
        chunk = chunk.drop(columns=cols_to_drop)

    # Handle high correlation missingness
    chunk = handle_high_corr_missingness(chunk, HIGH_CORR_COLS)

    return chunk


def preprocess_and_save_parquet(input_csv: str, output_prefix: str, chunksize: int = 100_000) -> List[str]:
    """
    Reads a CSV in chunks, processes them, and saves as Parquet files.

    Args:
        input_csv: Path to input CSV.
        output_prefix: Prefix for output files (e.g., 'data/processed').
        chunksize: Number of rows per chunk.

    Returns:
        List of paths to the generated Parquet files.
    """
    refined_dir = os.path.join(os.path.dirname(output_prefix), "refined_data")
    os.makedirs(refined_dir, exist_ok=True)

    chunks = pd.read_csv(input_csv, chunksize=chunksize)
    parquet_parts = []

    for i, chunk in enumerate(chunks):
        processed = preprocess_chunk(chunk)  # Always save raw categories
        filename = f"{os.path.basename(output_prefix)}_part{i}.parquet"
        part_path = os.path.join(refined_dir, filename)
        processed.to_parquet(part_path, index=False)
        parquet_parts.append(part_path)

    return parquet_parts


def build_category_map(parquet_paths: List[str], output_path: str = "category_map.json") -> Dict[str, List[Any]]:
    """
    Scans Parquet files to identify all unique categories for categorical columns.
    Defensive: tolerates parquet parts missing some columns, and converts numpy/pandas
    scalars to native Python types so JSON serialization won't fail.
    """
    def _to_python_scalar(x):
        # Convert numpy / pandas scalars to native Python types; handle timestamps.
        try:
            if pd.isna(x):
                return None
        except Exception:
            pass

        # pandas Timestamp -> ISO string
        if isinstance(x, pd.Timestamp):
            return x.isoformat()

        # numpy / pandas scalar -> Python native
        if isinstance(x, (np.generic, )):
            try:
                return x.item()
            except Exception:
                return float(x)

        # plain python (int, float, str, bool)
        if isinstance(x, (int, float, str, bool)):
            return x

        # Fallback: convert to string
        return str(x)

    full_categories = {col: set() for col in LINEAR_CATEGORICAL_COLS}

    for path in parquet_paths:
        try:
            # Fast path: read only expected categorical columns
            df = pd.read_parquet(path, columns=[c for c in LINEAR_CATEGORICAL_COLS])
        except Exception:
            # Fallback: read whole file
            df = pd.read_parquet(path)

        present_cat_cols = [c for c in LINEAR_CATEGORICAL_COLS if c in df.columns]
        for col in present_cat_cols:
            # dropna() then iterate unique values
            uniques = df[col].dropna().unique()
            for u in uniques:
                py = _to_python_scalar(u)
                if py is not None:
                    full_categories[col].add(py)

    # Convert sets to sorted lists (deterministic). Use string sort key to avoid mixed-type compare issues.
    json_ready_map = {col: sorted(list(vals), key=lambda v: str(v)) for col, vals in full_categories.items()}

    # Optionally remove columns with empty category lists (if you want)
    # json_ready_map = {k: v for k, v in json_ready_map.items() if v}

    with open(output_path, 'w') as f:
        json.dump(json_ready_map, f)

    print(f"Category map saved to {output_path}")
    return json_ready_map


def load_and_prepare_for_linear(parquet_paths: List[str], category_map_path: str = "category_map.json") -> pd.DataFrame:
    with open(category_map_path, 'r') as f:
        category_map = json.load(f)

    dfs = []
    for path in parquet_paths:
        df = pd.read_parquet(path)

        # Enforce categories for all categorical columns that will be one-hot encoded
        for col, categories in category_map.items():
            if col in df.columns:
                cat_type = pd.CategoricalDtype(categories=categories, ordered=False)
                df[col] = df[col].astype(cat_type)

        # One-Hot Encoding for all linear categoricals (numeric + string)
        cat_cols = [col for col in LINEAR_CATEGORICAL_COLS if col in df.columns]
        if cat_cols:
            df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def load_and_prepare_for_tree(parquet_paths: List[str]) -> pd.DataFrame:
    """
    Loads data for tree-based models (preserves categorical dtypes).

    Args:
        parquet_paths: List of Parquet files to load.

    Returns:
        Concatenated DataFrame.
    """
    dfs = [pd.read_parquet(path) for path in parquet_paths]
    return pd.concat(dfs, ignore_index=True)