import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

file_path = 'quantitative/data/Speech Production Experience Survey (Responses) - Form responses 1(1).csv'

if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found.")
else:
    df = pd.read_csv(file_path)
    
    # --- DYNAMIC COLUMN SELECTION ---
    q2_col = df.columns[3]
    q3_col = df.columns[4]
    
    # Selecting the two similar Yes/No columns
    yn_col_a = df.columns[8]  # "Did you know..."
    yn_col_b = df.columns[9]  # "Do you know..."

    # --- COLLAPSING THE YES/NO COLUMNS ---
    # This takes the value from B if A is missing (NaN)
    df['Knowledge_Combined'] = df[yn_col_a].combine_first(df[yn_col_b])
    
    # Standardizing: Google Forms sometimes adds trailing spaces
    df['Knowledge_Combined'] = df['Knowledge_Combined'].str.strip()

    print("--- Data Summary ---")
    print(f"Total Participants: {len(df)}")
    print(f"Combined Y/N Responses: {df['Knowledge_Combined'].count()} / {len(df)}")

    # --- QUANTITATIVE ANALYSIS (Q2 & Q3) ---
    print("\n--- Descriptive Statistics for Q2 & Q3 ---")
    for i, col in [(2, q2_col), (3, q3_col)]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        avg = df[col].mean()
        
        print(f"Stats for Question {i}:")
        print(f"  Average (Mean): {avg:.2f}")
        print(f"  Median: {df[col].median()}")

        plt.figure(figsize=(8, 5))
        sns.histplot(df[col].dropna(), kde=True, color='skyblue', bins=6)
        plt.axvline(avg, color='red', linestyle='--', label=f'Mean: {avg:.2f}')
        plt.title(f'Distribution: Question {i}')
        plt.xlabel('Response Scale')
        plt.ylabel('Frequency')
        plt.legend()
        plt.savefig(f'plot_Q{i}.png')
        plt.close()

    # --- CATEGORICAL ANALYSIS (Combined Yes/No) ---
    print("\n--- Descriptive Statistics for Combined Yes/No ---")
    counts = df['Knowledge_Combined'].value_counts()
    pcts = df['Knowledge_Combined'].value_counts(normalize=True) * 100
    
    print(pd.DataFrame({'Counts': counts, 'Percentage (%)': pcts.round(2)}))

    plt.figure(figsize=(6, 5))
    sns.countplot(x='Knowledge_Combined', data=df, palette='viridis')
    plt.title('Knowledge of Diffusion LLMs (Combined)')
    plt.xlabel('Response')
    plt.ylabel('Count')
    plt.savefig('plot_knowledge_combined.png')
    
    print("\nAnalysis Complete. Plots saved as plot_Q2.png, plot_Q3.png, and plot_knowledge_combined.png")