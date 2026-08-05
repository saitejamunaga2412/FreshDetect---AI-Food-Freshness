import sys
import os
import csv

def verify():
    print("--- 1. Verification of Libraries ---")
    try:
        import tensorflow as tf
        print(f"TensorFlow Version: {tf.__version__}")
        
        # In newer tf versions, keras is often tf.keras, but we can try to import it directly
        try:
            import keras
            print(f"Keras Version: {keras.__version__}")
        except:
            print(f"Keras Version: (integrated within tf)")
            
        print(f"CUDA Available: {tf.test.is_built_with_cuda()}")
        print(f"GPU Available: {len(tf.config.list_physical_devices('GPU')) > 0}")
        if len(tf.config.list_physical_devices('GPU')) > 0:
            print(f"GPU Details: {tf.config.list_physical_devices('GPU')}")
    except ImportError as e:
        print(f"Failed to import TensorFlow: {e}")
        sys.exit(1)

    try:
        import numpy as np
        import pandas as pd
        import matplotlib
        import sklearn
        import cv2
        from PIL import Image
        import seaborn as sns
        import tqdm
        print("All required libraries (numpy, pandas, matplotlib, scikit-learn, opencv-python, pillow, seaborn, tqdm) are installed successfully.")
    except ImportError as e:
        print(f"Missing library: {e}")
        sys.exit(1)

    print(f"\nPython Version: {sys.version}")

    print("\n--- 3. Dataset Verification ---")
    dataset_dir = os.path.join("dataset", "Freshness44")
    split_dir = os.path.join("dataset", "Freshness44_Split")
    
    if os.path.exists(dataset_dir):
        print("Freshness44 cleaned dataset exists.")
        if not os.path.exists(os.path.join(dataset_dir, "Grapes_Fresh")):
            print("Grape/Grapes merge completed (Grapes_Fresh missing).")
        else:
            print("Warning: Grapes_Fresh still exists.")
    else:
        print("Error: Original dataset missing.")
        sys.exit(1)
        
    if os.path.exists(split_dir):
        print("80/10/10 stratified split completed (Split directory exists).")
    else:
        print("Error: Split directory missing.")
        sys.exit(1)
        
    if os.path.exists("dataset_statistics.csv"):
        print("Dataset statistics available.")
    else:
        print("Warning: dataset_statistics.csv missing.")

    print("\n--- 4. Split Counts Verification ---")
    
    for split in ['train', 'val', 'test']:
        split_path = os.path.join(split_dir, split)
        if not os.path.exists(split_path):
            print(f"Error: missing split directory {split_path}")
            sys.exit(1)
        classes = os.listdir(split_path)
        img_count = sum(len(os.listdir(os.path.join(split_path, c))) for c in classes)
        print(f"Number of {split} images: {img_count}")
        if split == 'train':
            print(f"Number of classes: {len(classes)}")

    print("\nVerification Successful! Ready to begin training.")

if __name__ == "__main__":
    verify()
