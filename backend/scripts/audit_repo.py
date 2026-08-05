import os
import glob
from pathlib import Path

def audit_datasets():
    print("--- Dataset Audit ---")
    dataset_dir = Path("dataset")
    if not dataset_dir.exists():
        print("Dataset directory not found.")
        return
    
    datasets = {
        "Freshness44": dataset_dir / "Freshness44",
        "Fruits-detection": dataset_dir / "Fruits-detection",
        "Mendeley": dataset_dir / "processed/mendeley_final.csv",
        "FoodKeeper": dataset_dir / "processed/foodkeeper_fruits_vegetables.csv"
    }
    
    for name, path in datasets.items():
        if path.exists():
            if path.is_dir():
                num_files = len(list(path.rglob("*.*")))
                num_dirs = len([d for d in path.iterdir() if d.is_dir()])
                print(f"[{name}] OK - Directory exists with {num_dirs} classes and {num_files} total files.")
            else:
                size = path.stat().st_size / 1024 / 1024
                print(f"[{name}] OK - File exists ({size:.2f} MB).")
        else:
            print(f"[{name}] MISSING - Path {path} not found.")

def audit_models():
    print("\n--- AI Model Audit ---")
    expected_models = {
        "YOLO Detection": "weights/best.pt",
        "Visual Freshness CNN": "backend/ai/models/freshness/freshness_classifier.pth",
        "XGBoost Environmental": "weights/freshness_model.pkl",
        "Scaler": "weights/scaler.pkl",
        "Fruit Encoder": "weights/fruit_encoder.pkl"
    }
    
    for name, path_str in expected_models.items():
        path = Path(path_str)
        if path.exists():
            size = path.stat().st_size / 1024 / 1024
            print(f"[{name}] OK - {path} ({size:.2f} MB)")
        else:
            print(f"[{name}] MISSING - {path}")
            
def main():
    print("Starting Repository Audit...\n")
    audit_datasets()
    audit_models()
    print("\nAudit Complete.")

if __name__ == "__main__":
    main()
