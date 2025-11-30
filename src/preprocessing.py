#!/usr/bin/env python
# coding: utf-8

# In[1]:


# get_ipython().run_line_magic('reset', '-f')


# In[2]:


# get_ipython().run_line_magic('pip', 'install -q -r ../requirements.txt')


# In[19]:


import numpy as np
import pandas as pd
import json
from pathlib import Path
import os


# In[5]:


DATA_DIR = Path("./data")
train_data_path = DATA_DIR / "train_data.csv"
train_labels_path = DATA_DIR / 'train_labels.csv'


# In[6]:


# chunk_size = 100_000  # Tune based on available RAM
# chunks = pd.read_csv(train_data_path, chunksize=chunk_size)


# This below function will give object level memory utilization

# In[7]:


import sys
import humanize

def print_variable_sizes(top_n=None, scope=None):
    """
    Prints all variables in memory (default: globals()), sorted by size (largest first).

    Args:
        top_n (int): Optional. Show only top N variables.
        scope (dict): Optional. Dictionary to inspect (e.g., locals() or globals()).
    """
    if scope is None:
        scope = globals()

    var_list = []
    for k, v in scope.items():
        if k.startswith('_'):
            continue  # skip internal vars
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


# In[8]:


float16_columns = ['D_66', 'D_68', 'B_30', 'D_87', 'B_38', 'D_114', 'D_116', 'D_117', 'D_120', 'D_126']
float32_columns = ['P_2', 'D_39', 'B_1', 'B_2', 'R_1', 'S_3', 'D_41', 'B_3', 'D_42', 'D_43', 'D_44', 'B_4', 'D_45', 'B_5', 'R_2', 'D_46', 'D_47', 'D_48', 'D_49', 'B_6', 'B_7', 'B_8', 'D_50', 'D_51', 'B_9', 'R_3', 'D_52', 'P_3', 'B_10', 'D_53', 'S_5', 'B_11', 'S_6', 'D_54', 'R_4', 'S_7', 'B_12', 'S_8', 'D_55', 'D_56', 'B_13', 'R_5', 'D_58', 'S_9', 'B_14', 'D_59', 'D_60', 'D_61', 'B_15', 'S_11', 'D_62', 'D_65', 'B_16', 'B_17', 'B_18', 'B_19', 'B_20', 'S_12', 'R_6', 'S_13', 'B_21', 'D_69', 'B_22', 'D_70', 'D_71', 'D_72', 'S_15', 'B_23', 'D_73', 'P_4', 'D_74', 'D_75', 'D_76', 'B_24', 'R_7', 'D_77', 'B_25', 'B_26', 'D_78', 'D_79', 'R_8', 'R_9', 'S_16', 'D_80', 'R_10', 'R_11', 'B_27', 'D_81', 'D_82', 'S_17', 'R_12', 'B_28', 'R_13', 'D_83', 'R_14', 'R_15', 'D_84', 'R_16', 'B_29', 'S_18', 'D_86', 'R_17', 'R_18', 'D_88', 'S_19', 'R_19', 'B_32', 'S_20', 'R_20', 'R_21', 'B_33', 'D_89', 'R_22', 'R_23', 'D_91', 'D_92', 'D_93', 'D_94', 'R_24', 'R_25', 'D_96', 'S_22', 'S_23', 'S_24', 'S_25', 'S_26', 'D_102', 'D_103', 'D_104', 'D_105', 'D_106', 'D_107', 'B_36', 'B_37', 'R_26', 'R_27', 'D_108', 'D_109', 'D_110', 'D_111', 'B_39', 'D_112', 'B_40', 'S_27', 'D_113', 'D_115', 'D_118', 'D_119', 'D_121', 'D_122', 'D_123', 'D_124', 'D_125', 'D_127', 'D_128', 'D_129', 'B_41', 'B_42', 'D_130', 'D_131', 'D_132', 'D_133', 'R_28', 'D_134', 'D_135', 'D_136', 'D_137', 'D_138', 'D_139', 'D_140', 'D_141', 'D_142', 'D_143', 'D_144', 'D_145']
bool_cols = ['B_31']


# In[9]:


high_corr_cols = ['D_111', 'D_110', 'B_39', 'D_134', 'D_135', 'D_136', 'D_137',
                         'D_138', 'R_9', 'D_106', 'D_132', 'D_49', 'R_26', 'D_76',
                         'D_66', 'D_42', 'D_142', 'D_53', 'D_82']

low_missing_corr_cols = ['D_87', 'D_88', 'D_108', 'D_73', 'B_42', 'B_29']


# In[10]:


cardinality_json = '{"D_87":1,"D_120":2,"D_66":2,"D_116":2,"D_114":2,"D_126":3,"B_30":3,"D_117":7,"B_38":7}'
cardinality_dict = json.loads(cardinality_json)


# In[11]:


categorical_cols = list(cardinality_dict.keys())


# In[12]:


def handle_high_corr_missingness(df: pd.DataFrame, high_corr_cols: list) -> pd.DataFrame:
    # 1. Create missingness flags
    missing_flag_cols = {
        f"{col}_was_missing": df[col].isna().astype(np.uint8)
        for col in high_corr_cols if col in df.columns
    }
    df = pd.concat([df, pd.DataFrame(missing_flag_cols, index=df.index)], axis=1)

    # 2. Fill NaNs with sentinel values based on dtype
    for col in high_corr_cols:
        if col in df.columns:
            col_dtype = df[col].dtype

            if isinstance(col_dtype, pd.CategoricalDtype):
                base_type = df[col].cat.categories.dtype

                if pd.api.types.is_numeric_dtype(base_type):
                    sentinel = -999
                    # Add only if sentinel not already in categories
                    if sentinel not in df[col].cat.categories:
                        df[col] = df[col].cat.add_categories([sentinel])
                    df[col] = df[col].fillna(sentinel)

                else:  # assume string-based
                    sentinel = "MISSING"
                    if sentinel not in df[col].cat.categories:
                        df[col] = df[col].cat.add_categories([sentinel])
                    df[col] = df[col].fillna(sentinel)

            elif pd.api.types.is_float_dtype(col_dtype):
                sentinel = -999.0
                df[col] = df[col].fillna(sentinel)

            elif pd.api.types.is_integer_dtype(col_dtype):
                sentinel = -1
                df[col] = df[col].fillna(sentinel)

            else:
                # Fallback for any unexpected dtype
                df[col] = df[col].fillna("MISSING")

    return df


# In[13]:


def preprocess_chunk(chunk: pd.DataFrame, model_type: str = "tree") -> pd.DataFrame:
    # Boolean conversions
    for col in bool_cols:
        if col in chunk.columns:
            chunk[col] = chunk[col].astype(bool)

    # Float16 conversions and median imputation
    for col in float16_columns:
        if col in chunk.columns:
            median_val = chunk[col].median()
            chunk[col] = chunk[col].fillna(median_val).astype('float16')

    # Float32 conversions and median imputation
    for col in float32_columns:
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
                if 'MISSING' not in chunk[col].cat.categories:
                    chunk[col] = chunk[col].cat.add_categories('MISSING')
                chunk[col] = chunk[col].fillna('MISSING')
            else:
                mode_val = chunk[col].mode()
                if not mode_val.empty:
                    chunk[col] = chunk[col].fillna(mode_val[0])

    # Other categorical columns and mode imputation
    for col in categorical_cols:
        if col in chunk.columns:
            # If float16, convert first to float32 before category
            if pd.api.types.is_float_dtype(chunk[col].dtype) and chunk[col].dtype == 'float16':
                chunk[col] = chunk[col].astype('float32')
            chunk[col] = chunk[col].astype('category')
            mode_val = chunk[col].mode()
            if not mode_val.empty:
                chunk[col] = chunk[col].fillna(mode_val[0])

    # Drop low missing correlation columns
    chunk = chunk.drop(columns=[col for col in low_missing_corr_cols if col in chunk.columns])

    # Handle high correlation missingness
    chunk = handle_high_corr_missingness(chunk, high_corr_cols)

    # Model-specific processing
    if model_type == "linear":
        cat_cols = [col for col in categorical_cols if col in chunk.columns]
        if cat_cols:
            chunk = pd.get_dummies(chunk, columns=cat_cols, drop_first=True)

    return chunk


# In[20]:


def preprocess_and_save_parquet(input_csv: str, output_prefix: str, chunksize: int = 100_000):
    refined_dir = os.path.join(os.path.dirname(output_prefix), "refined_data")
    os.makedirs(refined_dir, exist_ok=True)
    chunks = pd.read_csv(input_csv, chunksize=chunksize)
    parquet_parts = []

    for i, chunk in enumerate(chunks):
        processed = preprocess_chunk(chunk, model_type="tree")  # always save raw categories
        filename = f"{os.path.basename(output_prefix)}_part{i}.parquet"
        part_path = os.path.join(refined_dir, filename)
        processed.to_parquet(part_path, index=False)
        parquet_parts.append(part_path)

    return parquet_parts


def build_category_map(parquet_paths: list, output_path: str = "category_map.json"):
    """
    Scans all parquet files to find the union of all categories for each categorical column.
    Saves the result to a JSON file.
    """
    full_categories = {col: set() for col in categorical_cols}
    
    for path in parquet_paths:
        df = pd.read_parquet(path, columns=[c for c in categorical_cols]) # Read only cat cols for speed
        for col in categorical_cols:
            if col in df.columns:
                # Drop NAs before getting unique values to avoid 'nan' as a category if not intended
                uniques = df[col].dropna().unique()
                full_categories[col].update(uniques)
    
    # Convert sets to sorted lists for JSON serialization and deterministic order
    json_ready_map = {col: sorted(list(vals)) for col, vals in full_categories.items()}
    
    with open(output_path, 'w') as f:
        json.dump(json_ready_map, f)
    
    print(f"Category map saved to {output_path}")
    return json_ready_map



# In[15]:


def load_and_prepare_for_linear(parquet_paths: list, category_map_path: str = "category_map.json"):
    # Load category map
    with open(category_map_path, 'r') as f:
        category_map = json.load(f)

    dfs = []
    for path in parquet_paths:
        df = pd.read_parquet(path)
        
        # Enforce categories for all categorical columns
        for col, categories in category_map.items():
            if col in df.columns:
                # Create CategoricalDtype with known categories
                cat_type = pd.CategoricalDtype(categories=categories, ordered=False)
                df[col] = df[col].astype(cat_type)
        
        # Now get_dummies will produce consistent columns
        cat_cols = [col for col in categorical_cols if col in df.columns]
        if cat_cols:
            df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
            
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


# In[16]:


def load_and_prepare_for_tree(parquet_paths: list):
    dfs = [pd.read_parquet(path) for path in parquet_paths]
    return pd.concat(dfs, ignore_index=True)


# In[21]:


if __name__ == "__main__":
    # Step 1: preprocess large CSV and save Parquet parts
    parquet_files = preprocess_and_save_parquet(train_data_path, "processed_data")

    # Step 1.5: Build and save category map from the training data
    build_category_map(parquet_files, "category_map.json")

    # Step 2a: load for linear model (one-hot encoding done here using the map)
    linear_df = load_and_prepare_for_linear(parquet_files, "category_map.json")

    # Step 2b: load for tree model (categorical dtypes preserved)
    tree_df = load_and_prepare_for_tree(parquet_files)


    # In[18]:


    print_variable_sizes()


    # In[22]:


    print(f"tree_df rows: {len(tree_df):,}")
    print(f"linear_df rows: {len(linear_df):,}")


    # In[31]:


    DATA_DIR = Path("./")
    os.makedirs(DATA_DIR/"stage1", exist_ok=True)
    STAGE1_DIR = DATA_DIR/"stage1"
    tree_df.to_parquet(STAGE1_DIR/"tree_df.parquet",compression="snappy", index=False)
    linear_df.to_parquet(STAGE1_DIR/"linear_df.parquet", compression="snappy", index=False)

