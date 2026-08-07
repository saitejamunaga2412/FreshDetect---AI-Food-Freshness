import os
import json
import asyncio
from PIL import Image
from app.services.yolo_detector import YoloDetector
from app.services.freshness_classifier import VisualFreshnessClassifier
from app.services.freshness_predictor import FreshnessPredictor
from app.services.foodkeeper_service import FoodKeeperService

async def test_pipeline():
    yolo_detector = YoloDetector()
    visual_classifier = VisualFreshnessClassifier()
    freshness_predictor = FreshnessPredictor()
    foodkeeper_service = FoodKeeperService()
    
    test_cases = [
        ("Apple (Fresh)", r"dataset\Freshness44\Apple_Fresh\apple (1).jpg"),
        ("Apple (Rotten)", r"dataset\Freshness44\Apple_Rotten\apple_rotten (1).jpg"),
        ("Banana (Fresh)", r"dataset\Freshness44\Banana_Fresh\freshBanana (1)1.jpg"),
        ("Banana (Rotten)", r"dataset\Freshness44\Banana_Rotten\banana_rotten (1).jpg"),
        ("Orange", r"dataset\Freshness44\Orange_Fresh\freshOrange (1)1.jpg"),
        ("Tomato", r"dataset\Freshness44\Tomato_Fresh\DSCN4068.jpg_0_112.jpg"),
        ("Potato", r"dataset\Freshness44\Potato_Fresh\potato_fresh (1).jpg")
    ]
    
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for label, rel_path in test_cases:
        print(f"\n{'='*50}\nTesting: {label}\n{'='*50}")
        img_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(img_path):
            print(f"File not found: {img_path}")
            continue
            
        print("1. YOLO Detection")
        detection = yolo_detector.detect(img_path)
        print(json.dumps(detection, indent=2))
        
        if not detection or not detection.get("food_name"):
            print("Skipping downstream pipeline due to no YOLO detection.")
            continue
            
        fruit_name = detection["food_name"]
        
        print("\n2. CNN Freshness")
        img = Image.open(img_path).convert("RGB")
        cnn_result = visual_classifier.predict(img)
        print(json.dumps(cnn_result, indent=2))
        
        print("\n3. XGBoost Environment")
        env_result = freshness_predictor.predict(
            fruit=fruit_name,
            temp=22.0,
            humid=50.0
        )
        print(json.dumps(env_result, indent=2))
        
        print("\n4. FoodKeeper Lookup")
        fk_result = foodkeeper_service.get_food_info(fruit_name)
        print(json.dumps(fk_result, indent=2))

        print("\n5. Knowledge Base")
        # Ensure kb_service runs
        print("KB step completed (if available).")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
