import os
import sys

sys.path.append(os.path.abspath("backend"))

from app.services.yolo_detector import YoloDetector

def diagnose():
    yd = YoloDetector()
    print("Model Path:", yd.model_path)
    print("Model Classes:", yd.model.names)
    print("Backend Fruit Classes:", yd.fruit_classes)
    print("Backend Vegetable Classes:", yd.vegetable_classes)

if __name__ == "__main__":
    diagnose()
