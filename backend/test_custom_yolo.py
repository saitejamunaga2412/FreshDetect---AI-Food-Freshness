from app.services.yolo_detector import YoloDetector
import json

def test():
    print("Initializing YoloDetector...")
    detector = YoloDetector()
    print("Running detection on dummy_apple.jpg...")
    result = detector.detect("dummy_apple.jpg")
    print("Detection Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test()
