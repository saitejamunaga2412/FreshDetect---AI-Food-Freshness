import asyncio
import os
import sys
import json
from pathlib import Path
from fastapi import UploadFile

# Set environment variables for the FastAPI app settings
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/test_db"
os.environ["JWT_SECRET"] = "dummy_secret"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["UPLOAD_DIR"] = "./uploads"

# Add backend dir to pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.api.scanner import scan_food
from app.core.database import connect_db, close_db

class MockUploadFile:
    def __init__(self, filename, path):
        self.filename = filename
        self.file = open(path, "rb")
        self.content_type = "image/jpeg"
        
    async def read(self, size=-1):
        return self.file.read(size)
        
    async def seek(self, offset, whence=0):
        self.file.seek(offset, whence)

async def test_e2e():
    print("Running E2E Pipeline Tests...")
    connect_db()
    
    # We will just grab one fresh and one rotten image for Apple, Banana, Tomato, Potato if available.
    test_cases = [
        ("Fresh Orange", "dataset/Freshness44/Orange_Fresh"),
        ("Rotten Apple", "dataset/Freshness44/Apple_Rotten"),
        ("Fresh Banana", "dataset/Freshness44/Banana_Fresh"),
        ("Rotten Banana", "dataset/Freshness44/Banana_Rotten"),
        ("Fresh Tomato", "dataset/Freshness44/Tomato_Fresh"),
        ("Rotten Tomato", "dataset/Freshness44/Tomato_Rotten"),
        ("Fresh Potato", "dataset/Freshness44/Potato_Fresh"),
        ("Rotten Potato", "dataset/Freshness44/Potato_Rotten")
    ]
    
    mock_user = {"id": "test_user_123"}
    
    for case_name, dir_path in test_cases:
        print(f"\n--- Testing {case_name} ---")
        if not os.path.exists(dir_path):
            print(f"Skipping: Directory {dir_path} does not exist.")
            continue
            
        files = [f for f in os.listdir(dir_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not files:
            print(f"Skipping: No images in {dir_path}.")
            continue
            
        test_image_path = os.path.join(dir_path, files[0])
        upload_file = MockUploadFile(files[0], test_image_path)
        
        try:
            result = await scan_food(upload_file, temp=20.0, humid=50.0, current_user=mock_user)
            res_data = result["result"]
            print(f"YOLO Detected: {res_data.get('yolo_class')} -> {res_data.get('fruit')}")
            print(f"CNN Visual Condition: {res_data['weighted_scores'].get('visual_condition')}")
            print(f"Storage Score (Env): {res_data['weighted_scores'].get('storage')}")
            print(f"Shelf-Life Score: {res_data['weighted_scores'].get('shelf_life')}")
            print(f"Overall Score: {res_data.get('overall_score')}")
            print(f"Final Status: {res_data.get('freshness_category')}")
        except Exception as e:
            print(f"Error testing {case_name}: {e}")
            
    close_db()
            
if __name__ == "__main__":
    asyncio.run(test_e2e())
