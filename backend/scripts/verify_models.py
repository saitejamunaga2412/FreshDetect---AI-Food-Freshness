import os
import sys

sys.path.append(os.path.abspath("backend"))

try:
    print("--- Testing FreshnessPredictor ---")
    from app.services.freshness_predictor import FreshnessPredictor
    fp = FreshnessPredictor()
    print("FreshnessPredictor instantiated successfully.")
    res = fp.predict(25.0, 50.0, 200.0, 400.0)
    print("Freshness prediction:", res)

    print("\n--- Testing YoloDetector ---")
    from app.services.yolo_detector import YoloDetector
    yd = YoloDetector()
    print("YoloDetector instantiated successfully.")
    res_yolo = yd.detect("corrupt.jpg")
    print("YOLO detection:", res_yolo)

    print("\nALL VERIFICATIONS SUCCESSFUL")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("VERIFICATION ERROR:", e)
