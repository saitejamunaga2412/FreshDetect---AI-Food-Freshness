import os
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.freshness_predictor import FreshnessPredictor

predictor = FreshnessPredictor()
fruits = ["Apple", "Banana", "Tomato", "Potato"]

for fruit in fruits:
    res = predictor.predict(fruit, 20.0, 50.0)
    print(f"{fruit} -> {res}")
