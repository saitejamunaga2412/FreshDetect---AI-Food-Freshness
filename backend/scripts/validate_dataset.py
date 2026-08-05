import pandas as pd
import os
import sys
import matplotlib.pyplot as plt

def validate_dataset():
    """
    Loads the cleaned FoodKeeper CSV, performs validation,
    generates a summary report, and creates basic visualizations.
    """
    csv_path = 'dataset/processed/foodkeeper_fruits_vegetables.csv'
    report_path = 'dataset/processed/validation_report.txt'
    plots_dir = 'dataset/processed/plots'

    try:
        # Step 1: Load the cleaned CSV file
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Cleaned CSV not found at {csv_path}. Please run preprocessing first.")
        
        df = pd.read_csv(csv_path)

        # Create output directories
        os.makedirs(plots_dir, exist_ok=True)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        # Step 2: Validate the dataset
        num_records = df.shape[0]
        num_features = df.shape[1]
        
        # Missing values
        missing_values = df.isnull().sum()
        total_missing = missing_values.sum()
        
        # Duplicates
        duplicates = df.duplicated()
        num_duplicates = duplicates.sum()
        
        # Data types
        data_types = df.dtypes
        
        # Unique fruits and vegetables
        fruits = df[df['Category_ID'] == 18]['Name'].dropna().unique()
        vegetables = df[df['Category_ID'] == 19]['Name'].dropna().unique()

        # Step 3: Save the validation report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*40 + "\n")
            f.write("=== Dataset Validation Report ===\n")
            f.write("="*40 + "\n\n")
            
            f.write(f"Total Records: {num_records}\n")
            f.write(f"Total Features: {num_features}\n")
            f.write(f"Total Missing Values: {total_missing}\n")
            f.write(f"Total Duplicate Rows: {num_duplicates}\n\n")
            
            f.write("--- Missing Values per Feature ---\n")
            f.write(missing_values.to_string() + "\n\n")
            
            if num_duplicates > 0:
                f.write("--- Sample Duplicate Rows ---\n")
                f.write(df[duplicates].head().to_string() + "\n\n")
                
            f.write("--- Data Types ---\n")
            f.write(data_types.to_string() + "\n\n")
            
            f.write("--- Unique Fruits (Category 18) ---\n")
            f.write(", ".join(sorted([str(x) for x in fruits])) + "\n\n")
            
            f.write("--- Unique Vegetables (Category 19) ---\n")
            f.write(", ".join(sorted([str(x) for x in vegetables])) + "\n\n")

        # Step 6: Generate basic visualizations
        
        # a. Fruits vs Vegetables count
        plt.figure(figsize=(8, 6))
        category_counts = df['Category_ID'].value_counts()
        category_counts.index = category_counts.index.map({18: 'Fruits', 19: 'Vegetables'})
        ax = category_counts.plot(kind='bar', color=['#ffa600', '#003f5c'])
        plt.title('Fruits vs Vegetables Count')
        plt.ylabel('Number of Items')
        plt.xticks(rotation=0)
        
        # Add labels on top of bars
        for p in ax.patches:
            ax.annotate(str(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.005))
            
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'fruits_vs_veg_count.png'))
        plt.close()

        # b. Storage duration distributions
        storage_types = ['Pantry', 'Refrigerate', 'Freeze']
        colors = ['#bc5090', '#58508d', '#ff6361']
        
        for i, storage_type in enumerate(storage_types):
            col_name = f'{storage_type}_Max'
            if col_name in df.columns:
                plt.figure(figsize=(8, 6))
                
                # Convert to numeric, ignoring non-numeric characters for plotting
                numeric_series = pd.to_numeric(df[col_name], errors='coerce').dropna()
                
                if not numeric_series.empty:
                    numeric_series.plot(kind='hist', bins=15, edgecolor='black', color=colors[i], alpha=0.7)
                    plt.title(f'{storage_type} Storage Duration (Max) Distribution')
                    plt.xlabel('Duration (Max Value)')
                    plt.ylabel('Frequency')
                    plt.grid(axis='y', alpha=0.75)
                    plt.tight_layout()
                    plt.savefig(os.path.join(plots_dir, f'{storage_type.lower()}_distribution.png'))
                plt.close()

        # Step 7: Console Output (Also for AI evaluation)
        print("\n" + "="*50)
        print("Dataset Validation Completed!")
        print("="*50)
        print(f"Number of records: {num_records}")
        print(f"Number of features: {num_features}")
        print(f"Total Missing values: {total_missing}")
        print(f"Total Duplicate rows: {num_duplicates}")
        print("\n--- Missing Details ---")
        print(missing_values)
        if num_duplicates > 0:
            print("\n--- Sample Duplicates ---")
            print(df[duplicates].head())
            
        print(f"\nOutputs saved successfully:")
        print(f" - Report: {os.path.abspath(report_path)}")
        print(f" - Plots : {os.path.abspath(plots_dir)}")
        print("="*50 + "\n")

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
    except ImportError as e:
        print(f"\n[ERROR] Missing package. Please ensure 'matplotlib' and 'pandas' are installed. Error: {e}")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    validate_dataset()
