import os
import sys

from ultralytics import YOLO

def test():
    model = YOLO(r"weights\best.pt")
    image = r"dataset\SplitDataset\test\carrot\fresh\freshCarrot (1).jpeg"
    res = model.predict(image)[0]
    print("Boxes:", res.boxes)
    print("Probs:", res.probs)

if __name__ == "__main__":
    test()
