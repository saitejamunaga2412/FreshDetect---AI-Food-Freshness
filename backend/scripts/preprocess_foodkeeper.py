import pandas as pd
import os

def preprocess_foodkeeper():
    """
    Reads the raw FoodKeeper dataset, filters it for Fruits and Vegetables, 
    selects required columns, and saves it as a CSV. Includes production-quality
    error handling and validation.
    """
    # 1. Define Paths
    raw_data_path = 'dataset/raw/FoodKeeper-Data.xls'
    processed_dir = 'dataset/processed'
    processed_data_path = os.path.join(processed_dir, 'foodkeeper_fruits_vegetables.csv')
    
    # Define required columns exactly as requested
    required_columns = [
        'Category_ID', 'Name', 'Name_subtitle', 
        'Pantry_Max', 'Pantry_Metric', 'Pantry_tips', 
        'Refrigerate_Max', 'Refrigerate_Metric', 'Refrigerate_tips', 
        'Freeze_Max', 'Freeze_Metric', 'Freeze_Tips'
    ]

    try:
        # Step 1: Verify the raw file exists before proceeding
        if not os.path.exists(raw_data_path):
            raise FileNotFoundError(f"The raw dataset file was not found at: {raw_data_path}")

        print(f"Loading Excel file: {raw_data_path}")
        
        # Use pd.ExcelFile to inspect sheets before reading data
        try:
            xls = pd.ExcelFile(raw_data_path, engine='xlrd')
        except ImportError as e:
            raise ImportError(f"Missing required dependency. Please install 'xlrd'. Error: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse the Excel file. It might be invalid or corrupted. Error: {e}")

        # Step 2: Print all worksheet names
        sheet_names = xls.sheet_names
        print(f"Found {len(sheet_names)} worksheet(s): {sheet_names}")

        # Automatically determine the correct worksheet
        target_sheet = None
        if len(sheet_names) == 1:
            target_sheet = sheet_names[0]
            print(f"Automatically using the only worksheet: '{target_sheet}'")
        else:
            # If multiple sheets, default to 'Product' if it exists (common for FoodKeeper)
            if 'Product' in sheet_names:
                target_sheet = 'Product'
            else:
                target_sheet = sheet_names[0] # Fallback to first sheet
            print(f"Multiple worksheets found. Selected worksheet: '{target_sheet}'")

        # Read the targeted sheet into a DataFrame
        try:
            df = pd.read_excel(xls, sheet_name=target_sheet)
        except Exception as e:
            raise Exception(f"Failed to read worksheet '{target_sheet}'. Error: {e}")

        # Strip extra whitespace from column names to prevent matching errors
        df.columns = df.columns.str.strip()

        # Step 3: Verify all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise KeyError(f"The following required columns are missing in the dataset: {missing_columns}")

        print(f"Successfully verified all {len(required_columns)} required columns.")

        # Step 4: Filter only Category_ID 18 (Fruits) and 19 (Vegetables)
        # We ensure it's numeric in case it was loaded as strings
        df['Category_ID'] = pd.to_numeric(df['Category_ID'], errors='coerce')
        df_filtered = df[df['Category_ID'].isin([18, 19])]

        # Keep only the required columns
        df_final = df_filtered[required_columns]

        # Step 6: Create the processed folder if it doesn't exist
        os.makedirs(processed_dir, exist_ok=True)

        # Step 5: Save the cleaned dataset as CSV
        df_final.to_csv(processed_data_path, index=False)

        # Step 7: Print success messages
        print("\n" + "="*50)
        print("Preprocessing Completed Successfully!")
        print("="*50)
        print(f"Output File: {os.path.abspath(processed_data_path)}")
        print(f"Total Rows: {df_final.shape[0]}")
        print(f"Total Columns: {df_final.shape[1]}")
        print("\nFirst 5 rows preview:")
        print(df_final.head())
        print("="*50 + "\n")

    # Step 8: Proper Exception Handling
    except FileNotFoundError as e:
        print(f"\n[ERROR - File Not Found] {e}")
        print("Please ensure you have placed 'FoodKeeper-Data.xls' in 'dataset/raw/'.")
    except ImportError as e:
        print(f"\n[ERROR - Missing Package] {e}")
        print("Run: pip install pandas xlrd")
    except ValueError as e:
        print(f"\n[ERROR - Invalid Excel] {e}")
        print("Please ensure the file is a valid Excel document.")
    except KeyError as e:
        print(f"\n[ERROR - Missing Columns] {e}")
        print("The dataset columns might have changed or you selected the wrong worksheet.")
    except Exception as e:
        print(f"\n[ERROR - Unexpected] An unexpected error occurred: {e}")

if __name__ == "__main__":
    preprocess_foodkeeper()
