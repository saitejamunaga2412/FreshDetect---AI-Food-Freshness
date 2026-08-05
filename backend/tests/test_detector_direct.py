import os
import sys

sys.path.append(os.path.abspath("."))

from app.services.yolo_detector import YoloDetector

def test():
    yd = YoloDetector()
    image = r"dataset\SplitDataset\test\carrot\fresh\freshCarrot (1).jpeg"
    print("Testing image:", image)
    res = yd.detect(image)
    print("Result:", res)

if __name__ == "__main__":
    test()
