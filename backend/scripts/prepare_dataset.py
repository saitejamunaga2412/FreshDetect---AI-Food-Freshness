import os
import shutil
import hashlib
import csv
import json
from collections import defaultdict
from sklearn.model_selection import train_test_split
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
DATASET_DIR = os.path.join("dataset", "Freshness44")
SPLIT_DIR = os.path.join("dataset", "Freshness44_Split")

def get_hash(filepath):
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    except:
        return None

def clean_and_merge():
    print("Starting Phase 3 & 4: Cleaning and Merging...")
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    # 1. Merge Grapes -> Grape
    merge_map = {
        "Grapes_Fresh": "Grape_Fresh",
        "Grapes_Rotten": "Grape_Rotten"
    }
    
    for src, dst in merge_map.items():
        src_dir = os.path.join(DATASET_DIR, src)
        dst_dir = os.path.join(DATASET_DIR, dst)
        if os.path.exists(src_dir):
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            for file in os.listdir(src_dir):
                src_file = os.path.join(src_dir, file)
                dst_file = os.path.join(dst_dir, file)
                # prevent overwrite collision if name exists
                if os.path.exists(dst_file):
                    dst_file = os.path.join(dst_dir, f"merged_{file}")
                shutil.move(src_file, dst_file)
            os.rmdir(src_dir)
            print(f"Merged {src} -> {dst}")
            
    # 2. Clean corrupted, invalid, and duplicate files
    hashes = set()
    removed = 0
    all_images = []
    labels = []
    
    class_counts = defaultdict(int)
    
    for cls in os.listdir(DATASET_DIR):
        cls_dir = os.path.join(DATASET_DIR, cls)
        if not os.path.isdir(cls_dir):
            continue
            
        files = os.listdir(cls_dir)
        for f in files:
            filepath = os.path.join(cls_dir, f)
            ext = os.path.splitext(f)[1].lower()
            
            if ext not in valid_exts:
                os.remove(filepath)
                removed += 1
                continue
                
            try:
                with Image.open(filepath) as img:
                    img.verify()
            except:
                os.remove(filepath)
                removed += 1
                continue
                
            h = get_hash(filepath)
            if h in hashes:
                os.remove(filepath)
                removed += 1
                continue
            
            hashes.add(h)
            all_images.append(filepath)
            labels.append(cls)
            class_counts[cls] += 1

    print(f"Removed {removed} invalid/corrupted/duplicate images.")
    
    # Generate Imbalance Report
    with open('class_imbalance_report.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Class', 'Count'])
        for cls, count in sorted(class_counts.items(), key=lambda x: x[1]):
            writer.writerow([cls, count])
            
    return all_images, labels

def split_dataset(all_images, labels):
    print("Starting Stratified Split (80/10/10)...")
    
    # Stratified Split (80 Train, 20 Temp)
    X_train, X_temp, y_train, y_temp = train_test_split(
        all_images, labels, test_size=0.20, stratify=labels, random_state=42
    )
    
    # Split Temp (50 Val, 50 Test of the 20% -> 10% Val, 10% Test)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
    )
    
    if os.path.exists(SPLIT_DIR):
        shutil.rmtree(SPLIT_DIR)
        
    for split_name in ['train', 'val', 'test']:
        for cls in set(labels):
            os.makedirs(os.path.join(SPLIT_DIR, split_name, cls), exist_ok=True)
            
    def copy_files(X, split_name):
        counts = defaultdict(int)
        for src in X:
            cls = os.path.basename(os.path.dirname(src))
            filename = os.path.basename(src)
            dst = os.path.join(SPLIT_DIR, split_name, cls, filename)
            shutil.copy2(src, dst)
            counts[cls] += 1
        return counts

    train_counts = copy_files(X_train, 'train')
    val_counts = copy_files(X_val, 'val')
    test_counts = copy_files(X_test, 'test')
    
    with open('dataset_split_report.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Class', 'Train', 'Validation', 'Test', 'Total'])
        for cls in sorted(set(labels)):
            tr = train_counts[cls]
            v = val_counts[cls]
            te = test_counts[cls]
            writer.writerow([cls, tr, v, te, tr+v+te])
            
    print("Dataset splitting complete.")

if __name__ == "__main__":
    imgs, lbls = clean_and_merge()
    split_dataset(imgs, lbls)
