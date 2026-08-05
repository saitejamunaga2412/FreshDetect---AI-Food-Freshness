import os
import json
import pandas as pd
from sklearn.model_selection import train_test_split

def split_dataset():
    """
    Splits the feature-engineered dataset into training (80%) and testing (20%) sets.
    Ensures strict class stratification and validates zero data leakage.
    """
    # Define file paths
    input_csv = 'dataset/processed/feature_engineered.csv'
    config_path = 'models/preprocessing_config.json'
    
    out_dir = 'dataset/SplitDataset'
    train_path = os.path.join(out_dir, 'train.csv')
    test_path = os.path.join(out_dir, 'test.csv')
    report_path = os.path.join(out_dir, 'split_report.txt')
    
    try:
        # Step 1: Load the feature-engineered dataset
        if not os.path.exists(input_csv):
            raise FileNotFoundError(f"Feature engineered dataset not found at {input_csv}.")
        print(f"Loading dataset from: {input_csv}")
        df = pd.read_csv(input_csv)
        
        # Step 2: Read the preprocessing configuration to dynamically get the target column
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Preprocessing config not found at {config_path}.")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        target_col = config.get('target_column')
        if not target_col or target_col not in df.columns:
            raise KeyError(f"Target column '{target_col}' is missing or not declared in config.")
            
        print(f"Target Column for Stratification: {target_col}")
            
        # Step 3 & 4: Split the dataset (80% Train, 20% Test)
        # Using random_state=42 for reproducibility and stratify=target to maintain class distributions
        print("Splitting dataset into 80% Training and 20% Testing sets...")
        df_train, df_test = train_test_split(
            df, 
            test_size=0.20, 
            random_state=42, 
            stratify=df[target_col]
        )
        
        # Step 8: Verify that no rows overlap between train and test
        # We check the intersection of the original DataFrame indices
        overlap = df_train.index.intersection(df_test.index)
        if len(overlap) > 0:
            # Raise an error immediately if leakage is detected
            raise ValueError(f"DATA LEAKAGE DETECTED! {len(overlap)} overlapping rows found between train and test sets.")
        
        # Step 11: Verify required columns exist in both splits
        required_cols = ['temp', 'humid_(%)', 'light_(fux)', 'co2_(pmm)', 'class', 'fruit']
        for col in required_cols:
            if col not in df_train.columns or col not in df_test.columns:
                raise ValueError(f"Required column '{col}' is missing from the split datasets. Execution stopped.")
        
        # Step 5: Save the split datasets
        os.makedirs(out_dir, exist_ok=True)
        df_train.to_csv(train_path, index=False)
        df_test.to_csv(test_path, index=False)
        
        # Step 12: Print shapes of train.csv and test.csv
        print(f"Saved {train_path} with shape: {df_train.shape}")
        print(f"Saved {test_path} with shape: {df_test.shape}")
        
        # Calculate Class Distributions for the Report
        # normalize=True gives the percentage (multiplied by 100)
        total_dist = df[target_col].value_counts(normalize=True) * 100
        train_dist = df_train[target_col].value_counts(normalize=True) * 100
        test_dist = df_test[target_col].value_counts(normalize=True) * 100
        
        total_counts = df[target_col].value_counts()
        train_counts = df_train[target_col].value_counts()
        test_counts = df_test[target_col].value_counts()
        
        def format_distribution(dist_percentages, counts):
            """Helper function to format distribution lines clearly."""
            return "\n".join([f"  Class {cls}: {counts[cls]} samples ({perc:.2f}%)" for cls, perc in dist_percentages.items()])
        
        # Step 6 & 7: Generate the split report
        report_lines = []
        report_lines.append("="*50)
        report_lines.append("=== Dataset Splitting Report ===")
        report_lines.append("="*50 + "\n")
        
        # Record sample sizes
        report_lines.append(f"Total Samples: {len(df)}")
        report_lines.append(f"Training Samples (80%): {len(df_train)}")
        report_lines.append(f"Testing Samples (20%): {len(df_test)}\n")
        
        # Record overlap verification
        report_lines.append("--- Verification ---")
        report_lines.append("Overlap Check: PASSED. Zero overlapping rows between Training and Testing sets.\n")
        
        # Record distributions
        report_lines.append("--- Class Distribution Before Split ---")
        report_lines.append(format_distribution(total_dist, total_counts) + "\n")
        
        report_lines.append("--- Class Distribution in Training Set ---")
        report_lines.append(format_distribution(train_dist, train_counts) + "\n")
        
        report_lines.append("--- Class Distribution in Testing Set ---")
        report_lines.append(format_distribution(test_dist, test_counts) + "\n")
        
        # Document constraints
        report_lines.append("--- Splitting Configuration ---")
        report_lines.append(f"Target Column: {target_col}")
        report_lines.append("Random State: 42")
        report_lines.append("Stratify: True (Balanced split enforced)")
        report_lines.append("Model Training: None performed.\n")
        
        # Document outputs
        report_lines.append("--- Output Locations ---")
        report_lines.append(f"Training Dataset: {train_path}")
        report_lines.append(f"Testing Dataset: {test_path}")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
            
        print("\n" + "="*40)
        print("Dataset Splitting Complete!")
        print(f"Total: {len(df)} | Train: {len(df_train)} | Test: {len(df_test)}")
        print("Overlap Verification: PASSED (No data leakage)")
        print(f"Train File: {os.path.abspath(train_path)}")
        print(f"Test File:  {os.path.abspath(test_path)}")
        print(f"Report:     {os.path.abspath(report_path)}")
        print("="*40 + "\n")
        
    # Step 9: Proper exception handling
    except FileNotFoundError as e:
        print(f"\n[ERROR - File Missing] {e}")
    except KeyError as e:
        print(f"\n[ERROR - Config/Column Error] {e}")
    except ValueError as e:
        print(f"\n[ERROR - Data Leakage / Splitting Issue] {e}")
    except ImportError as e:
        print(f"\n[ERROR - Missing Dependency] Please run 'pip install scikit-learn pandas'. Error: {e}")
    except Exception as e:
        print(f"\n[ERROR - Unexpected] An error occurred: {e}")

if __name__ == "__main__":
    split_dataset()