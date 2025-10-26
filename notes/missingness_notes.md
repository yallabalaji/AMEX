# Missingness Correlation Analysis Notes

**Objective:**  
To understand whether missing values in features carry predictive information about the target variable.

---

## Methodology
We calculated the Pearson correlation between the binary indicator of missingness (1 = missing, 0 = not missing) for each feature and the target variable.

A high absolute correlation (|corr| > 0.1) suggests that the presence of missing values itself may carry predictive information.

---

## Observations
| Type | Columns |
|------|----------|
| **High missingness correlation** | D_111, D_110, B_39, D_134, D_135, D_136, D_137, D_138, R_9, D_106, D_132, D_49, R_26, D_76, D_42, D_142, D_53, D_82 |
| **Low missingness correlation** | D_87, D_88, D_108, D_73, B_42, B_29, D_66 |

---

## Decision (Iteration 1)
For the **first model iteration**, we drop columns with *low missingness correlation*  
to simplify the dataset and reduce noise.

```python
low_corr_cols = ['D_87', 'D_88', 'D_108', 'D_73', 'B_42', 'B_29', 'D_66']
df = df.drop(columns=low_corr_cols, errors='ignore')
