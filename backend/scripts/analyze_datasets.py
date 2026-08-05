import os
from collections import defaultdict
import json

def analyze_yolo_dataset(base_path):
    # Check data.yaml
    classes = {}
    counts = defaultdict(int)
    
    if os.path.exists(os.path.join(base_path, 'data.yaml')):
        print(f"Dataset {base_path} has data.yaml")
    
    for split in ['train', 'valid', 'test']:
        lbl_dir = os.path.join(base_path, split, 'labels')
        if not os.path.exists(lbl_dir):
            continue
        for f in os.listdir(lbl_dir):
            if f.endswith('.txt'):
                with open(os.path.join(lbl_dir, f), 'r') as file:
                    for line in file:
                        cls_id = int(line.split()[0])
                        counts[cls_id] += 1
                        
    return dict(counts)

def analyze_classification_dataset(base_path):
    counts = {}
    for d in os.listdir(base_path):
        d_path = os.path.join(base_path, d)
        if os.path.isdir(d_path):
            files = [f for f in os.listdir(d_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            counts[d] = len(files)
    return counts

def main():
    print("--- Fruits-detection (YOLO) ---")
    yolo_counts = analyze_yolo_dataset('dataset/Fruits-detection')
    print(json.dumps(yolo_counts, indent=2))
    
    print("\n--- Fruit16K (New) ---")
    f16k_counts = analyze_classification_dataset('datasets_optional/Fruit16K')
    print(json.dumps(f16k_counts, indent=2))
    
    print("\n--- Freshness44 ---")
    f44_counts = analyze_classification_dataset('dataset/Freshness44')
    print(json.dumps(f44_counts, indent=2))

if __name__ == "__main__":
    main()
