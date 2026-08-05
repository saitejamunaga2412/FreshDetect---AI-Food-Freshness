import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def validate_mendeley():
    """
    Validates the cleaned Mendeley dataset and performs Exploratory Data Analysis (EDA)
    by generating summary statistics, correlation heatmaps, distributions, and boxplots.
    """
    # Define file paths
    input_path = 'dataset/processed/mendeley_clean.csv'
    plots_dir = 'dataset/processed/plots'
    report_path = 'dataset/processed/validation_report.txt'
    
    try:
        # Step 1: Load the dataset
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Cleaned dataset not found at {input_path}")
            
        print(f"Loading dataset from: {input_path}")
        df = pd.read_csv(input_path)
        
        # Ensure output directories exist
        os.makedirs(plots_dir, exist_ok=True)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        # Step 2: Extract dataset information for validation
        shape = df.shape
        columns = df.columns.tolist()
        data_types = df.dtypes
        missing_values = df.isnull().sum()
        duplicates = df.duplicated().sum()
        
        # Identify categorical columns and get unique values
        categorical_cols = df.select_dtypes(include=['object']).columns
        unique_categorical = {col: df[col].unique() for col in categorical_cols}
        
        # Step 3 (Part A): Generate summary statistics
        summary_stats = df.describe(include='all')
        
        # Step 5: Save validation report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*40 + "\n")
            f.write("=== Mendeley Validation Report ===\n")
            f.write("="*40 + "\n\n")
            
            f.write(f"Dataset Shape: {shape}\n\n")
            f.write(f"Column Names: {columns}\n\n")
            f.write(f"Data Types:\n{data_types.to_string()}\n\n")
            f.write(f"Missing Values:\n{missing_values.to_string()}\n\n")
            f.write(f"Duplicate Rows: {duplicates}\n\n")
            
            f.write("Unique Values for Categorical Columns:\n")
            for col, unq in unique_categorical.items():
                f.write(f" - {col}:\n   {unq}\n")
                
            f.write("\nSummary Statistics:\n")
            f.write(summary_stats.to_string())

        # Print quick summary to terminal
        print("\n" + "="*40)
        print("Validation Info Summary")
        print("="*40)
        print(f"Shape: {shape}")
        print(f"Missing Values (Total): {missing_values.sum()}")
        print(f"Duplicates: {duplicates}")
        print("="*40 + "\n")

        # Set up seaborn style for plots
        sns.set_theme(style="whitegrid")
        
        # Step 3 (Part B): Generate and save plots
        print("Generating EDA plots...")
        
        # Attempt to find relevant categorical columns by checking substring matches
        fruit_col = next((c for c in categorical_cols if 'fruit' in c.lower() or 'item' in c.lower()), None)
        class_col = next((c for c in categorical_cols if 'class' in c.lower() or 'label' in c.lower()), None)
        
        # Fruit distribution
        if fruit_col:
            plt.figure(figsize=(10, 6))
            sns.countplot(data=df, x=fruit_col, hue=fruit_col, palette="viridis", legend=False)
            plt.title('Fruit Distribution')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, 'fruit_distribution.png'))
            plt.close()
            
        # Class distribution
        if class_col:
            plt.figure(figsize=(8, 6))
            sns.countplot(data=df, x=class_col, hue=class_col, palette="Set2", legend=False)
            plt.title('Class Distribution')
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, 'class_distribution.png'))
            plt.close()
            
        # Identify numerical columns for histograms
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        # Helper function to plot histograms dynamically
        def plot_hist(col_substring, filename, title):
            col = next((c for c in numeric_cols if col_substring.lower() in c.lower()), None)
            if col:
                plt.figure(figsize=(8, 6))
                sns.histplot(df[col], kde=True, bins=20, color='skyblue')
                plt.title(title)
                plt.tight_layout()
                plt.savefig(os.path.join(plots_dir, filename))
                plt.close()
                
        # Histograms for specific environmental metrics
        plot_hist('temp', 'temperature_histogram.png', 'Temperature Histogram')
        plot_hist('humid', 'humidity_histogram.png', 'Humidity Histogram')
        plot_hist('co2', 'co2_histogram.png', 'CO2 Histogram')
        plot_hist('light', 'light_histogram.png', 'Light Histogram')

        # Correlation heatmap
        if len(numeric_cols) > 1:
            plt.figure(figsize=(10, 8))
            corr = df[numeric_cols].corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
            plt.title('Correlation Heatmap')
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, 'correlation_heatmap.png'))
            plt.close()

        # Boxplots for numerical columns
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                plt.figure(figsize=(6, 4))
                sns.boxplot(y=df[col], color='lightgreen')
                plt.title(f'Boxplot for {col}')
                plt.tight_layout()
                plt.savefig(os.path.join(plots_dir, f'boxplot_{col}.png'))
                plt.close()
                
        print("\nEDA generation complete!")
        print(f"Validation report saved to: {os.path.abspath(report_path)}")
        print(f"Plots saved to: {os.path.abspath(plots_dir)}")

    # Step 6: Proper exception handling
    except FileNotFoundError as e:
        print(f"\n[ERROR - File Not Found] {e}")
        print("Please ensure you have successfully run the Mendeley preprocessing script first.")
    except ImportError as e:
        print(f"\n[ERROR - Missing Package] {e}")
        print("Please ensure you have installed seaborn and matplotlib. (Run: pip install seaborn matplotlib)")
    except Exception as e:
        print(f"\n[ERROR - Unexpected] An error occurred: {e}")

if __name__ == "__main__":
    validate_mendeley()
