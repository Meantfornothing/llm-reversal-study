import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# 1. LOAD AND CLEAN
df = pd.read_csv('quantitative/data/Speech Production Experience Survey (Responses) - Form responses 1(1).csv')
group_col = "Is your birth month between January-June or July-December?"

# Data Cleaning: Strip spaces and filter groups
df[group_col] = df[group_col].str.strip()
target_groups = ['January-June', 'July-December']
df = df[df[group_col].isin(target_groups)].copy()

# Consolidation
# Note: Using iloc index 2 and 5 as per your original script
df['Q1'] = df.iloc[:, 2].fillna(df.iloc[:, 5])
df_clean = df[[group_col, 'Q1']].copy()
df_clean.columns = ['Group', 'Q1_Alignment']

# Separate groups
a = df_clean[df_clean['Group'] == 'January-June']['Q1_Alignment'].dropna().values
b = df_clean[df_clean['Group'] == 'July-December']['Q1_Alignment'].dropna().values

# --- NEW: MEAN RANK CALCULATION ---
# Combine all data to rank them together
combined = np.concatenate([a, b])
ranks = stats.rankdata(combined)

# Split ranks back into groups
ranks_a = ranks[:len(a)]
ranks_b = ranks[len(a):]

mean_rank_a = np.mean(ranks_a)
mean_rank_b = np.mean(ranks_b)

# 2. BOOTSTRAPPING FUNCTION (CI + P-VALUE)
def get_bootstrap_results(a, b, iterations=10000):
    obs_diff = np.mean(a) - np.mean(b)
    
    diffs = [np.mean(np.random.choice(a, len(a), True)) - 
             np.mean(np.random.choice(b, len(b), True)) for _ in range(iterations)]
    ci = np.percentile(diffs, [2.5, 97.5])
    
    mean_all = np.mean(np.concatenate([a, b]))
    a_shifted = a - np.mean(a) + mean_all
    b_shifted = b - np.mean(b) + mean_all
    
    null_diffs = [np.mean(np.random.choice(a_shifted, len(a), True)) - 
                  np.mean(np.random.choice(b_shifted, len(b), True)) for _ in range(iterations)]
    
    boot_p = np.mean(np.abs(null_diffs) >= np.abs(obs_diff))
    
    return obs_diff, ci, boot_p

obs_diff, ci, boot_p = get_bootstrap_results(a, b)

# 3. MANN-WHITNEY U (Traditional comparison)
u_stat, u_p = stats.mannwhitneyu(a, b, alternative='two-sided')

# Calculate Effect Size (Rank-Biserial Correlation r)
# Formula: r = 1 – (2U / (n1 * n2))
n1, n2 = len(a), len(b)
r_effect = 1 - (2 * u_stat / (n1 * n2))

# 4. PLOTTING
means = df_clean.groupby('Group')['Q1_Alignment'].mean()
stds = df_clean.groupby('Group')['Q1_Alignment'].std()

plt.figure(figsize=(8, 6))
means.plot(kind='bar', yerr=stds, capsize=5, color=['#3498db', '#e74c3c'], alpha=0.8)
plt.title('Question 1: Alignment with AI Description (AR vs Diffusion)')
plt.ylabel('Mean Score (1 - 6)')
plt.xticks(ticks=[0, 1], labels=['Autoregressiv\n Jan-June', 'Diffusion\n July-Dec'], rotation=0)
plt.ylim(1, 6)
plt.tight_layout()
plt.savefig('q1_alignment_plot.png')

# 5. OUTPUT RESULTS
print(f"--- Q1 Statistical Results ---")
print(f"Mean Rank (Autoregressive): {mean_rank_a:.2f}")
print(f"Mean Rank (Diffusion): {mean_rank_b:.2f}")
print(f"Mann-Whitney U: {u_stat:.4f}")
print(f"Mann-Whitney U p-value: {u_p:.4f}")
print(f"Rank-Biserial Correlation (r): {r_effect:.3f}")
print(f"--- Bootstrapping Results ---")
print(f"Bootstrapped p-value: {boot_p:.4f}")
print(f"Observed Mean Diff (AR - Diff): {obs_diff:.3f}")
print(f"95% CI for Difference: [{ci[0]:.3f}, {ci[1]:.3f}]")
print(f"Means:[{means}]")
print(f"SDs:[{stds}]")

