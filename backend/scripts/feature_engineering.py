import os
import json
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder

def feature_engineering():
    """
    Performs feature engineering on the Mendeley dataset.
    This script extracts specific features (X) and target (y), encodes ONLY the target 
    variable using LabelEncoder, keeps the fruit column unchanged, saves the fitted encoders 
    and configuration for inference, and logs the process.
    """
    # 1. Define all necessary file paths
    input_path = 'dataset/processed/mendeley_final.csv'
    output_csv_path = 'dataset/processed/feature_engineered.csv'
    report_path = 'dataset/processed/feature_engineering_report.txt'
    
    encoders_dir = 'models/encoders/'
    feature_cols_path = 'models/feature_columns.json'
    target_col_path = 'models/target_column.txt'
    config_path = 'models/preprocessing_config.json'
    
    try:
        # Step 1: Load the cleaned dataset
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found at {input_path}. Please run cleaning first.")
            
        print(f"Loading dataset from: {input_path}")
        df = pd.read_csv(input_path)
        
        # Step 3 (Requirement): Explain every feature with comments
        # ---------------------------------------------------------
        # Feature Explanations:
        # 1. 'fruit': Categorical feature representing the type of fruit being monitored (e.g., Apple, Banana, Orange). Unchanged and not an ML feature.
        # 2. 'temp': Numerical feature for the ambient temperature around the fruit in degrees Celsius.
        # 3. 'humid_(%)': Numerical feature for the relative humidity percentage in the storage environment.
        # 4. 'light_(fux)': Numerical feature measuring ambient light intensity (lux/fux).
        # 5. 'co2_(pmm)': Numerical feature measuring carbon dioxide concentration in parts per million (ppm).
        # 6. 'class': Categorical Target variable representing the freshness state of the fruit (e.g., Good, Bad).
        # ---------------------------------------------------------
        
        # Identify data types and columns
        initial_shape = df.shape
        data_types = df.dtypes
        
        # Define specific columns as requested
        target_col = 'class' 
        fruit_col = 'fruit'
        feature_cols = ['temp', 'humid_(%)', 'light_(fux)', 'co2_(pmm)']
        
        # Validate required columns exist
        for col in [target_col, fruit_col] + feature_cols:
            if col not in df.columns:
                raise KeyError(f"Required column '{col}' not found in the dataset.")
            
        # Step 2: Print dataset metadata
        print("\n" + "="*40)
        print("Feature Engineering Setup")
        print("="*40)
        print(f"Dataset Shape: {initial_shape}")
        print("\nData Types:\n", data_types)
        print(f"\nFeature Columns (X): {feature_cols}")
        print(f"Target Column (y): {target_col}")
        print(f"Unchanged/Excluded Column: {fruit_col}")
        print("="*40 + "\n")
        
        # Initialize Report lines
        report = []
        report.append("="*50)
        report.append("=== Feature Engineering Report ===")
        report.append("="*50 + "\n")
        report.append(f"Input Shape: {initial_shape}\n")
        report.append(f"Target Column (y): {target_col}")
        report.append(f"Feature Columns (X): {feature_cols}")
        report.append(f"Excluded/Unchanged Column: {fruit_col}\n")
        
        # Ensure output directories exist before writing files
        os.makedirs(encoders_dir, exist_ok=True)
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        os.makedirs(os.path.dirname(feature_cols_path), exist_ok=True)
        
        # Step 5: Encode ONLY the Target Column using LabelEncoder
        report.append("--- Encoding Variables ---")
        print(f"Encoding target column: {target_col}")
        
        le = LabelEncoder()
        df[target_col] = le.fit_transform(df[target_col].astype(str))
        
        # Step 6: Save the fitted encoder for production inference
        encoder_path = os.path.join(encoders_dir, f"{target_col}_encoder.pkl")
        joblib.dump(le, encoder_path)
        
        # Record the exact label mapping for the report
        mapping = dict(zip(le.classes_, [int(x) for x in le.transform(le.classes_)]))
        report.append(f"Column '{target_col}' encoded successfully.")
        report.append(f"Mapping: {mapping}")
        report.append(f"Encoder saved to: {encoder_path}")
        report.append(f"NOTE: '{fruit_col}' column was kept intentionally unchanged and unencoded.\n")
            
        # Step 7: Save Feature names as JSON
        print("Saving metadata (Feature and Target columns)...")
        with open(feature_cols_path, 'w', encoding='utf-8') as f:
            json.dump(feature_cols, f, indent=4)
        report.append(f"Feature columns saved to: {feature_cols_path}")
            
        # Step 8: Save Target column name as text
        with open(target_col_path, 'w', encoding='utf-8') as f:
            f.write(target_col)
        report.append(f"Target column saved to: {target_col_path}\n")

        # Save Preprocessing Configuration as JSON
        config_data = {
            "feature_columns": feature_cols,
            "target_column": target_col,
            "fruit_column": fruit_col,
            "encoding_information": {
                target_col: mapping
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        report.append(f"Preprocessing configuration saved to: {config_path}\n")
        
        # Step 9: Save the processed dataset
        # (It still contains all rows and columns, including fruit, but only target is encoded)
        df.to_csv(output_csv_path, index=False)
        report.append("--- Final Output ---")
        report.append(f"Final Dataset Shape: {df.shape}")
        report.append(f"Processed dataset saved to: {output_csv_path}\n")
        
        # Document adherence to negative constraints
        report.append("--- Actions NOT Performed ---")
        report.append(" - [Rule 11] No dataset splitting (Train/Test) occurred.")
        report.append(" - [Rule 12] No model training occurred.")
        
        # Step 10: Generate the feature engineering report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
            
        print("\n" + "="*40)
        print("Feature Engineering Complete!")
        print(f"Dataset saved to: {os.path.abspath(output_csv_path)}")
        print(f"Config saved to: {os.path.abspath(config_path)}")
        print(f"Report saved to: {os.path.abspath(report_path)}")
        print("="*40 + "\n")
        
    # Step 13: Proper Exception Handling
    except FileNotFoundError as e:
        print(f"\n[ERROR - File Not Found] {e}")
    except KeyError as e:
        print(f"\n[ERROR - Column Missing] {e}")
    except ImportError as e:
        print(f"\n[ERROR - Missing Package] Please install scikit-learn and joblib. Error: {e}")
    except Exception as e:
        print(f"\n[ERROR - Unexpected] An error occurred: {e}")

if __name__ == "__main__":
    feature_engineering()
