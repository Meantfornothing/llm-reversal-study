import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np

# 1. LOAD AND CLEAN
file_path = 'quantitative/data/Speech Production Experience Survey (Responses) - Form responses 1(1).csv'
df = pd.read_csv(file_path)

# Identify column names
group_col = "Is your birth month between January-June or July-December?"
# Merge the branched columns (same as before)
df['Q1'] = df.iloc[:, 2].fillna(df.iloc[:, 5])
df['Q2'] = df.iloc[:, 3].fillna(df.iloc[:, 6])
df['Q3'] = df.iloc[:, 4].fillna(df.iloc[:, 7])

# Keep only the two intended groups and drop any empty rows
target_groups = ['January-June', 'July-December']
df_clean = df[df[group_col].isin(target_groups)].copy()
df_clean = df_clean[[group_col, 'Q1', 'Q2', 'Q3']]
df_clean.columns = ['Group', 'Q1_Alignment', 'Q2_PrePlanning', 'Q3_Correction']

questions = ['Q1_Alignment', 'Q2_PrePlanning', 'Q3_Correction']
groups = sorted(df_clean['Group'].unique()) # Ensuring only 2 groups exist

# 2. BOXPLOTS
plt.figure(figsize=(15, 5))
for i, q in enumerate(questions):
    plt.subplot(1, 3, i+1)
    # Using 'hue' instead of 'palette' directly to avoid warnings in newer Seaborn
    sns.boxplot(x='Group', y=q, data=df_clean, hue='Group', palette='Set2', legend=False)
    sns.stripplot(x='Group', y=q, data=df_clean, color='black', alpha=0.4)
    plt.title(f'Distribution: {q}')
plt.tight_layout()
plt.savefig('distribution_boxplots.png')
print("Saved: distribution_boxplots.png")

# 3. QQ-PLOTS (Robust Indexing)
fig, axes = plt.subplots(len(questions), len(groups), figsize=(10, 12))
for i, q in enumerate(questions):
    for j, g in enumerate(groups):
        data = df_clean[df_clean['Group'] == g][q].dropna()
        # Handle 1D or 2D axes array safely
        ax = axes[i, j] if len(groups) > 1 else axes[i]
        stats.probplot(data, dist="norm", plot=ax)
        ax.set_title(f'{q}\n({g})')
plt.tight_layout()
plt.savefig('normality_qq_plots.png')
print("Saved: normality_qq_plots.png")

# 4. STATISTICAL TESTS (T-Test + Non-Parametric Fallback)
print("\n--- STATISTICAL ANALYSIS ---")
for q in questions:
    data_a = df_clean[df_clean['Group'] == groups[0]][q].dropna()
    data_b = df_clean[df_clean['Group'] == groups[1]][q].dropna()
    
    # Assumption Checks
    levene_p = stats.levene(data_a, data_b)[1]
    shapiro_a = stats.shapiro(data_a)[1]
    shapiro_b = stats.shapiro(data_b)[1]
    
    # Welch's T-Test (Doesn't assume equal variance)
    t_stat, t_p = stats.ttest_ind(data_a, data_b, equal_var=False)
    
    # Mann-Whitney U (Non-parametric fallback)
    u_stat, u_p = stats.mannwhitneyu(data_a, data_b)
    
    print(f"\n[{q}]")
    print(f"  Normality (Shapiro): Group A p={shapiro_a:.3f}, Group B p={shapiro_b:.3f}")
    print(f"  Variance (Levene): p={levene_p:.3f}")
    
    # Decision Logic
    if shapiro_a < 0.05 or shapiro_b < 0.05:
        print(f"  RECOMMENDATION: Use Mann-Whitney U (p={u_p:.4f}) because data is non-normal.")
    else:
        print(f"  RECOMMENDATION: Use T-Test (p={t_p:.4f}).")