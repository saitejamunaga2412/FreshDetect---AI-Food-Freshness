import os

# Dataset path
DATASET_PATH = "../dataset/Freshness44"

# Convert to absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../dataset/Freshness44"))

print("=" * 50)
print("Freshness44 Dataset Analysis")
print("=" * 50)

if not os.path.exists(DATASET_PATH):
    print("Dataset not found!")
    print("Expected Path:", DATASET_PATH)
    exit()

classes = sorted(
    [
        folder
        for folder in os.listdir(DATASET_PATH)
        if os.path.isdir(os.path.join(DATASET_PATH, folder))
    ]
)

print(f"\nTotal Classes : {len(classes)}\n")

total_images = 0
minimum = 999999
maximum = 0

for cls in classes:
    folder = os.path.join(DATASET_PATH, cls)

    images = [
        img
        for img in os.listdir(folder)
        if img.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    count = len(images)

    total_images += count

    minimum = min(minimum, count)
    maximum = max(maximum, count)

    print(f"{cls:<25} : {count}")

print("\n" + "=" * 50)
print(f"Total Images : {total_images}")
print(f"Minimum Images/Class : {minimum}")
print(f"Maximum Images/Class : {maximum}")
print("=" * 50)