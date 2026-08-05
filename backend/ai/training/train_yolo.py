from ultralytics import YOLO
from pathlib import Path

# -----------------------------
# Project Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent.parent

DATASET_PATH = PROJECT_ROOT / "dataset" / "Fruits-detection"
DATA_YAML = DATASET_PATH / "data.yaml"

print("=" * 60)
print("YOLOv8 Fruit Detection Training")
print("=" * 60)
print(f"Dataset : {DATASET_PATH}")

# Check dataset
if not DATASET_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

if not DATA_YAML.exists():
    raise FileNotFoundError(f"data.yaml not found: {DATA_YAML}")

print("Dataset Found")
print("Loading YOLOv8 Model...")

# -----------------------------
# Load Pretrained YOLOv8 Nano
# -----------------------------
model = YOLO("yolov8n.pt")

# -----------------------------
# Train
# -----------------------------
results = model.train(
    data=str(DATA_YAML),
    epochs=1,
    imgsz=640,
    batch=8,
    workers=2,
    device="cpu",
    project=str(BASE_DIR / "models"),
    name="fruit_detector",
    exist_ok=True,
    pretrained=True,
    optimizer="AdamW",
    patience=10,
    verbose=True
)

print("=" * 60)
print("Training Completed Successfully!")
print("=" * 60)

# -----------------------------
# Validation
# -----------------------------
metrics = model.val()

print("\nValidation Results")
print(metrics)

print("\nBest model saved at:")

best_model = PROJECT_ROOT / "weights" / "best.pt"

print(best_model)

print("\nTraining Finished Successfully.")