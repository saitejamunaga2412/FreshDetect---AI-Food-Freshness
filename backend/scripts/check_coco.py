import os
import sys

from ultralytics import YOLO

def diagnose():
    print("Testing yolov8n.pt")
    try:
        model = YOLO("yolov8n.pt")
        print("Classes:", model.names)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    diagnose()
