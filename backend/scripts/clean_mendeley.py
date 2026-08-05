import os
import pandas as pd
import numpy as np

def clean_mendeley():
    """
    Cleans the Mendeley dataset by handling duplicates, missing values, 
    standardizing categoricals, and removing outliers using the IQR method.
    Rules: No normalization, no encoding, no splitting.
    """
    # Define file paths
    input_path = 'dataset/processed/mendeley_clean.csv'
    output_path = 'dataset/processed/mendeley_final.csv'
    report_path = 'dataset/processed/cleaning_report.txt'

    try:
        # Step 1: Read the dataset
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input dataset not found at {input_path}")
            
        print(f"Loading dataset from: {input_path}")
        df = pd.read_csv(input_path)
        
        # Step 2: Print initial stats
        initial_shape = df.shape
        initial_missing = df.isnull().sum()
        initial_duplicates = df.duplicated().sum()
        
        print("\n" + "="*40)
        print("Initial Dataset State")
        print("="*40)
        print(f"Initial Shape: {initial_shape}")
        print(f"Missing Values (Total): {initial_missing.sum()}")
        print(f"Duplicate Rows: {initial_duplicates}")
        print("="*40 + "\n")

        # Initialize the cleaning report text array
        report_lines = []
        report_lines.append("="*50)
        report_lines.append("=== Mendeley Dataset Cleaning Report ===")
        report_lines.append("="*50 + "\n")
        report_lines.append(f"Initial Shape: {initial_shape}")
        report_lines.append(f"Total Missing Values: {initial_missing.sum()}")
        report_lines.append(f"Total Duplicate Rows: {initial_duplicates}\n")

        # Step 4: Explain and Handle Duplicate Rows
        report_lines.append("--- Duplicates Handling ---")
        report_lines.append("Explanation: In IoT sensor datasets, consecutive readings might occasionally "
                            "produce similar values. However, if EVERY column is exactly identical "
                            "(exact duplicate rows), it usually points to a logging error, a glitch in the "
                            "data collection script, or accidental appending. We DO NOT blindly remove "
                            "near-matches, but we DO remove EXACT duplicate rows across all columns to "
                            "prevent data leakage and artificially weighted samples during model training.")
        
        if initial_duplicates > 0:
            df = df.drop_duplicates(keep='first')
            report_lines.append(f"Action Taken: Removed {initial_duplicates} exact duplicate rows.\n")
        else:
            report_lines.append("Action Taken: No exact duplicates found. None removed.\n")

        # Step 3: Standardize categorical values
        categorical_cols = df.select_dtypes(include=['object', 'string']).columns
        report_lines.append("--- Categorical Standardization ---")
        if len(categorical_cols) > 0:
            for col in categorical_cols:
                # Strip leading/trailing spaces and convert to Title Case
                # This fixes variations like ' BAD ', 'Bad', 'bad', 'BAD' -> 'Bad'
                df[col] = df[col].astype(str).str.strip().str.title()
            report_lines.append(f"Action Taken: Standardized categorical columns {list(categorical_cols)} "
                                "to Title Case and stripped whitespace (e.g. ' BAD ' -> 'Bad').\n")
        else:
            report_lines.append("Action Taken: No categorical columns found to standardize.\n")

        # Step 5: Handle Missing Values
        report_lines.append("--- Missing Values Handling ---")
        missing_count = df.isnull().sum().sum()
        if missing_count > 0:
            # Impute numerical columns with median and categorical with mode
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                if df[col].isnull().any():
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    
            for col in categorical_cols:
                if df[col].isnull().any():
                    mode_val = df[col].mode()[0]
                    df[col] = df[col].fillna(mode_val)
            report_lines.append(f"Action Taken: Found {missing_count} missing values. "
                                "Imputed numericals with Median and categoricals with Mode to preserve data size.\n")
        else:
            report_lines.append("Action Taken: No missing values found.\n")

        # Step 6: Detect Outliers (IQR Method) - No Automatic Removal
        report_lines.append("--- Outlier Detection (IQR Method) ---")
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        outlier_report_path = 'dataset/processed/outliers_report.csv'
        outliers_dict = {}
        all_outlier_indices = set()
        
        print("\n--- IQR Bounds for Numerical Columns ---")
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            print(f"{col}: Lower Bound = {lower_bound:.2f}, Upper Bound = {upper_bound:.2f}")
            
            # Find indices of outliers
            col_outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index
            outliers_dict[col] = len(col_outliers)
            all_outlier_indices.update(col_outliers)
            
        print("----------------------------------------\n")
            
        # Report the number of outliers for every numerical feature
        report_lines.append("Outliers Detected per Feature:")
        for col, count in outliers_dict.items():
            report_lines.append(f" - {col}: {count} outliers")
            print(f"Outliers in {col}: {count}")
            
        # Save all detected outlier rows to CSV
        if len(all_outlier_indices) > 0:
            df_outliers = df.loc[list(all_outlier_indices)]
            os.makedirs(os.path.dirname(outlier_report_path), exist_ok=True)
            df_outliers.to_csv(outlier_report_path, index=False)
            report_lines.append(f"\nAction Taken: Detected {len(all_outlier_indices)} total rows with at least one outlier.")
            report_lines.append(f"Saved outlier rows to: {outlier_report_path}")
        else:
            report_lines.append("\nAction Taken: No outliers detected in any numerical column.")
            
        report_lines.append("\nNOTE: Outliers were NOT automatically removed. Outlier treatment will be decided after manual inspection.\n")

        # Steps 7, 8, 9: Explicit constraints
        report_lines.append("--- Transformations NOT Applied ---")
        report_lines.append(" - [Rule 7] No normalization or scaling performed.")
        report_lines.append(" - [Rule 8] No categorical encoding performed.")
        report_lines.append(" - [Rule 9] No dataset splitting (Train/Test) performed.\n")

        # Step 10: Save cleaned dataset
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        report_lines.append("="*50)
        report_lines.append("--- Final Output ---")
        report_lines.append(f"Final Dataset Shape: {df.shape}")
        report_lines.append(f"Cleaned dataset saved to: {output_path}")
        report_lines.append("="*50 + "\n")

        # Step 11: Generate cleaning report
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))

        # Console summary
        print("Cleaning Complete!")
        print(f"Final Shape: {df.shape}")
        print(f"Total Outlier Rows Detected (Kept): {len(all_outlier_indices)}")
        print(f"Dataset saved to: {os.path.abspath(output_path)}")
        print(f"Report saved to: {os.path.abspath(report_path)}")
        print("="*40 + "\n")

    # Step 12: Proper exception handling
    except FileNotFoundError as e:
        print(f"\n[ERROR - File Not Found] {e}")
        print("Ensure 'dataset/processed/mendeley_clean.csv' exists.")
    except Exception as e:
        print(f"\n[ERROR - Unexpected] An error occurred during data cleaning: {e}")

if __name__ == "__main__":
    clean_mendeley()
