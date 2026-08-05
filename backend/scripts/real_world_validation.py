import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import matplotlib.pyplot as plt
import cv2
import random

SPLIT_DIR = os.path.join("dataset", "Freshness44_Split", "test")
IMG_SIZE = (224, 224)

def simulate_real_world(img):
    """Apply random real-world degradations to simulate bad conditions."""
    img = np.array(img, dtype=np.float32)
    
    # Random slight blur
    if random.random() > 0.5:
        k = random.choice([3, 5])
        img = cv2.GaussianBlur(img, (k, k), 0)
        
    # Random lighting condition (brightness/contrast)
    alpha = random.uniform(0.7, 1.3) # Contrast control (1.0-3.0)
    beta = random.uniform(-30, 30) # Brightness control (0-100)
    img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    
    return img

def main():
    print("Starting Real-World Validation Test...")
    
    model = tf.keras.models.load_model('best_model.keras')
    with open('class_names.json', 'r') as f:
        class_names = json.load(f)
        
    # Select 100 random images from the test set
    all_test_files = []
    for cls in os.listdir(SPLIT_DIR):
        cls_dir = os.path.join(SPLIT_DIR, cls)
        if os.path.isdir(cls_dir):
            for f in os.listdir(cls_dir):
                all_test_files.append((os.path.join(cls_dir, f), cls))
                
    random.shuffle(all_test_files)
    sample_files = all_test_files[:100]
    
    correct = 0
    false_positives = 0 # Predicted fresh but was rotten
    false_negatives = 0 # Predicted rotten but was fresh
    
    confidences = []
    failure_cases = []
    
    os.makedirs('failure_cases', exist_ok=True)
    
    for i, (filepath, true_cls) in enumerate(sample_files):
        # Load and simulate real world conditions
        original_img = cv2.imread(filepath)
        original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        original_img = cv2.resize(original_img, IMG_SIZE)
        
        rw_img = simulate_real_world(original_img)
        
        # Predict
        input_tensor = np.expand_dims(rw_img, axis=0)
        pred_probs = model.predict(input_tensor, verbose=0)[0]
        pred_idx = np.argmax(pred_probs)
        pred_cls = class_names[pred_idx]
        conf = pred_probs[pred_idx]
        confidences.append(conf)
        
        is_true_fresh = 'Fresh' in true_cls
        is_pred_fresh = 'Fresh' in pred_cls
        
        if true_cls == pred_cls:
            correct += 1
        else:
            if not is_true_fresh and is_pred_fresh:
                false_positives += 1
            elif is_true_fresh and not is_pred_fresh:
                false_negatives += 1
                
            # Save failure case
            fail_filename = f"failure_cases/fail_{i}_{true_cls}_as_{pred_cls}.png"
            plt.figure()
            plt.imshow(rw_img.astype('uint8'))
            plt.title(f"True: {true_cls} | Pred: {pred_cls} ({conf:.2f})")
            plt.axis('off')
            plt.savefig(fail_filename)
            plt.close()
            
            failure_cases.append({
                "file": fail_filename,
                "true_label": true_cls,
                "pred_label": pred_cls,
                "confidence": float(conf),
                "reason": "Likely confused due to simulated blur/lighting or ambiguous visual features."
            })
            
    success_rate = correct / len(sample_files)
    
    # Confidence Histogram
    plt.figure()
    plt.hist(confidences, bins=10, range=(0, 1), color='skyblue', edgecolor='black')
    plt.title('Confidence Score Distribution (Real-World Sim)')
    plt.xlabel('Confidence Score')
    plt.ylabel('Frequency')
    plt.savefig('confidence_histogram.png')
    plt.close()
    
    # Recommend
    if success_rate >= 0.85:
        recommendation = "Ready for Production"
    elif success_rate >= 0.70:
        recommendation = "Ready for Beta Testing"
    else:
        recommendation = "Needs More Data"
        
    report = f"""# Deployment Validation Report (Real-World Simulation)

## 1. Summary Metrics
- **Total Evaluated Images**: {len(sample_files)}
- **Success Rate (Accuracy)**: {success_rate*100:.2f}%
- **False Positives (Predicted Fresh, Actually Rotten)**: {false_positives}
- **False Negatives (Predicted Rotten, Actually Fresh)**: {false_negatives}
- **Average Confidence**: {np.mean(confidences):.4f}

## 2. Failure Cases
Generated {len(failure_cases)} failure case images in the `failure_cases/` directory.
"""
    for fail in failure_cases:
        report += f"- **{fail['true_label']}** classified as **{fail['pred_label']}** (Confidence: {fail['confidence']:.2f}). Reason: {fail['reason']}\n"
        
    report += f"""
## 3. Recommendations
Based on simulated real-world conditions (blur, poor lighting):
- **Final Recommendation**: **{recommendation}**
- **Confidence Distribution**: Saved as `confidence_histogram.png`.
"""
    
    with open('deployment_validation_report.md', 'w') as f:
        f.write(report)
        
    print("Real-world validation complete. Report written to deployment_validation_report.md")

if __name__ == "__main__":
    main()
