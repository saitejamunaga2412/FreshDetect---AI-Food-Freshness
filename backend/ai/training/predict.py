from ultralytics import YOLO
import sys
import json
import os

# Load trained model
weights_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "weights", "best.pt"))
model = YOLO(weights_path)
# Image path from Node.js
image_path = sys.argv[1]

# Predict
results = model(image_path)

# Get first prediction
result = results[0]

prediction = {
    "class": result.names[result.probs.top1],
    "confidence": float(result.probs.top1conf)
}

print(json.dumps(prediction))