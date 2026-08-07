import glob
import os
import json
from app.services.yolo_detector import YoloDetector
from app.services.freshness_classifier import VisualFreshnessClassifier
from PIL import Image

def test():
    print("Initializing Models...")
    detector = YoloDetector()
    classifier = VisualFreshnessClassifier()

    fruits_to_test = ["Apple_Fresh", "Banana_Fresh", "Orange_Fresh", "Tomato_Fresh"]
    base_dir = r"d:\FreshDetect---AI-Food-Freshness\backend\dataset\Freshness44"
    
    results = {}

    for folder in fruits_to_test:
        search_path = os.path.join(base_dir, folder, "*.jpg")
        images = glob.glob(search_path)
        if not images:
            print(f"No images found for {folder}")
            continue
            
        test_img = images[0]
        fruit_name = folder.split("_")[0]
        
        print(f"\n--- Testing {fruit_name} ---")
        print(f"Image: {test_img}")
        
        # YOLO Detection
        det = detector.detect(test_img)
        print("YOLO Detection:")
        print(json.dumps(det, indent=2))
        
        # CNN Freshness
        bbox = det.get("bbox")
        try:
            with Image.open(test_img) as img:
                if bbox and len(bbox) == 4:
                    cropped_img = img.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
                else:
                    cropped_img = img
                cnn_result = classifier.predict(cropped_img)
            
            print("CNN Prediction:")
            print(json.dumps(cnn_result, indent=2))
        except Exception as e:
            print(f"Error predicting freshness: {e}")

if __name__ == "__main__":
    test()
