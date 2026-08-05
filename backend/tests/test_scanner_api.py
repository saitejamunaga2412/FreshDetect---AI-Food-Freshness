import requests
import os
import json

BASE_URL = "http://127.0.0.1:8001/api"

import uuid

def get_token():
    # Register/Login
    rand_id = uuid.uuid4().hex[:6]
    email = f"test_{rand_id}@example.com"
    creds = {"email": email, "password": "password123", "role": "consumer", "name": "Test User"}
    requests.post(f"{BASE_URL}/auth/register", json=creds)
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": "password123"})
    resp_json = r.json()
    if "access_token" not in resp_json:
        print("Auth failed:", resp_json)
    return resp_json.get("access_token")

def run_scan_test(image_path, token):
    headers = {"Authorization": f"Bearer {token}"}
    with open(image_path, "rb") as f:
        files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
        data = {"temp": 20.0, "humid": 50.0, "light": 100.0, "co2": 400.0}
        r = requests.post(f"{BASE_URL}/scanner/scan", files=files, data=data, headers=headers)
        return r.status_code, r.json()

images = {
    "carrot": r"dataset\SplitDataset\test\carrot\fresh\freshCarrot (1).jpeg",
    "apple": r"dataset\SplitDataset\test\apple\fresh\FreshApple (10).jpg",
    "banana": r"dataset\SplitDataset\test\banana\fresh\Banana__Healthy_augmented_10.jpg",
    "potato": r"dataset\SplitDataset\test\potato\fresh\freshPotato (100).jpg",
    "tomato": r"dataset\SplitDataset\test\tomato\fresh\freshTomato (101).jpg",
}

if __name__ == "__main__":
    token = get_token()
    print(f"Got Token: {token[:10]}...")
    
    for name, path in images.items():
        print(f"\n--- Testing {name.upper()} ---")
        status, response = test_scan(path, token)
        print(f"HTTP Status: {status}")
        print(f"Response: {json.dumps(response, indent=2)}")
