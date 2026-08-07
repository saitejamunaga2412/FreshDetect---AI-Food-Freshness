import os
import sys

# Add current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import assess_freshness

# We need a dummy image. Let's create one.
import numpy as np
import cv2

dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
# Save it to a bytes object as JPEG
is_success, buffer = cv2.imencode(".jpg", dummy_img)
image_bytes = buffer.tobytes()

print("Calling assess_freshness...")
result = assess_freshness(image_bytes)
print("Result:")
print(result)
