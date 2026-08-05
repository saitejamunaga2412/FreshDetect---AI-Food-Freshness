import os
import sys

sys.path.append(os.path.abspath("backend"))

from ultralytics import YOLO

def diagnose():
    print("Testing models/weights/best.pt")
    try:
        model = YOLO("models/weights/best.pt")
        print("Classes:", model.names)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    diagnose()
