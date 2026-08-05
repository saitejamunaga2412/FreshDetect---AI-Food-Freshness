import os
import hashlib
import json
import csv
from collections import defaultdict
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

def get_image_hash(filepath):
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except:
        return None

def verify_image(filepath):
    try:
        with Image.open(filepath) as img:
            img.verify()
        return True, None
    except Exception as e:
        return False, str(e)

def audit_dataset(dataset_dir):
    stats = {
        "Total classes": 0,
        "Total images": 0,
        "Duplicate count": 0,
        "Corrupted count": 0,
        "Missing count": 0,
        "Empty folders": 0,
        "Invalid images": 0
    }
    
    class_counts = defaultdict(int)
    class_names = []
    
    empty_folders = []
    corrupted_files = []
    invalid_files = []
    
    image_hashes = defaultdict(list)
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    for class_name in os.listdir(dataset_dir):
        class_path = os.path.join(dataset_dir, class_name)
        if not os.path.isdir(class_path):
            continue
            
        class_names.append(class_name)
        stats["Total classes"] += 1
        
        files = os.listdir(class_path)
        if len(files) == 0:
            empty_folders.append(class_name)
            stats["Empty folders"] += 1
            continue
            
        for file in files:
            filepath = os.path.join(class_path, file)
            if not os.path.isfile(filepath):
                continue
                
            ext = os.path.splitext(file)[1].lower()
            if ext not in valid_extensions:
                invalid_files.append(filepath)
                stats["Invalid images"] += 1
                continue
                
            stats["Total images"] += 1
            class_counts[class_name] += 1
            
            is_valid, err = verify_image(filepath)
            if not is_valid:
                corrupted_files.append(filepath)
                stats["Corrupted count"] += 1
                continue
                
            img_hash = get_image_hash(filepath)
            if img_hash:
                image_hashes[img_hash].append(filepath)

    duplicates = {h: paths for h, paths in image_hashes.items() if len(paths) > 1}
    for h, paths in duplicates.items():
        stats["Duplicate count"] += (len(paths) - 1)
        
    conflicts = []
    bases = defaultdict(list)
    for c in class_names:
        base = c.lower().replace('_fresh', '').replace('_rotten', '')
        bases[base].append(c)
    
    for base, names in bases.items():
        if base.endswith('s'):
            singular = base[:-1]
            if singular in bases:
                conflicts.append((base, singular, bases[base], bases[singular]))
                
    report = {
        "stats": stats,
        "class_counts": class_counts,
        "empty_folders": empty_folders,
        "conflicts": conflicts
    }
    
    with open('dataset_statistics.json', 'w') as f:
        json.dump(report, f, indent=4)
        
    with open('dataset_statistics.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        for k, v in stats.items():
            writer.writerow([k, v])
            
    print("Audit Complete. Wrote dataset_statistics.json and dataset_statistics.csv")

if __name__ == "__main__":
    audit_dataset(os.path.join("dataset", "Freshness44"))
