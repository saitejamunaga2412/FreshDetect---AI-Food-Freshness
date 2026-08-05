import os
import pandas as pd

def preprocess_mendeley():
    """
    Preprocesses the Mendeley dataset by standardizing column names
    and performing an initial data inspection without altering the data contents.
    """
    # Define file paths
    raw_data_path = 'dataset/raw/Mendeley/dataset.csv'
    processed_dir = 'dataset/processed'
    processed_data_path = os.path.join(processed_dir, 'mendeley_clean.csv')

    try:
        # Step 1 & 2: Verify the file exists and load the dataset
        if not os.path.exists(raw_data_path):
            raise FileNotFoundError(f"The raw dataset file was not found at: {raw_data_path}")

        print(f"Loading Mendeley dataset from: {raw_data_path}")
        df = pd.read_csv(raw_data_path)

        # Step 3: Print requested dataset details
        print("\n" + "="*40)
        print("Dataset Initial Statistics")
        print("="*40)
        
        # - Dataset shape
        print(f"\nDataset Shape (Rows, Columns): {df.shape}")
        
        # - Column names
        print(f"\nOriginal Column Names:\n{df.columns.tolist()}")
        
        # - Data types
        
        print(f"\nData Types:\n{df.dtypes}")
        
        # - Missing values
        print(f"\nMissing Values:\n{df.isnull().sum()}")
        
        # - Duplicate rows
        print(f"\nTotal Duplicate Rows: {df.duplicated().sum()}")
        
        # - Unique values in the Class column
        # Attempt to find the 'Class' column robustly (case-insensitive before stripping)
        class_col = None
        for col in df.columns:
            if col.strip().lower() == 'class':
                class_col = col
                break
        
        if class_col:
            print(f"\nUnique values in the '{class_col}' column:\n{df[class_col].unique()}")
        else:
            print("\nWarning: Could not find a column named 'Class' to print unique values.")

        # Step 4: Strip extra spaces from column names
        df.columns = df.columns.str.strip()

        # Step 5: Standardize column names to lowercase with underscores
        df.columns = df.columns.str.lower().str.replace(' ', '_')

        print("\n" + "="*40)
        print(f"Standardized Column Names:\n{df.columns.tolist()}")
        print("="*40)

        # Rules 6, 7, 8: 
        # - Do NOT remove any data yet.
        # - Do NOT encode any categorical columns.
        # - Do NOT perform feature engineering.
        # (This is intentionally left exactly as is without any row filtering or data mutations)

        # Step 9: Save an exact cleaned copy to dataset/processed/mendeley_clean.csv
        os.makedirs(processed_dir, exist_ok=True)
        df.to_csv(processed_data_path, index=False)

        print(f"\nCleaned dataset saved successfully to: {processed_data_path}")
        print("="*40 + "\n")

    # Step 10: Add proper exception handling
    except FileNotFoundError as e:
        print(f"\n[ERROR - File Not Found] {e}")
        print("Please ensure the CSV is placed at 'dataset/raw/Mendeley/dataset.csv'.")
    except pd.errors.EmptyDataError as e:
        print(f"\n[ERROR - Empty File] The dataset file is empty: {e}")
    except Exception as e:
        print(f"\n[ERROR - Unexpected] An unexpected error occurred: {e}")

if __name__ == "__main__":
    preprocess_mendeley()
