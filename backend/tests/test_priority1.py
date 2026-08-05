import requests
import json
import os

base_url = "http://localhost:8000"

def test_priority1():
    print("1. Logging in to get token...")
    login_data = {
        "email": "testuser_freshness@example.com",
        "password": "password123"
    }
    r = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if r.status_code != 200:
        print("Login failed:", r.text)
        return
            
    token = r.json().get("access_token")
    if not token:
        token = r.json().get("token")
    print("Token retrieved.")
    
    print("2. Uploading image to /api/scanner/scan...")
    test_img = r"d:\FreshDetect---AI-Food-Freshness\dataset\Freshness44\Apple_Rotten\RottenApple (10)!.jpg"
    if not os.path.exists(test_img):
        print(f"Image not found: {test_img}")
        return
        
    print(f"Using test image: {test_img}")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(test_img, "rb") as f:
        files = {"image": ("test.jpg", f, "image/jpeg")}
        data = {
            "temp": 20.0,
            "humid": 50.0,
            "light": 100.0,
            "co2": 400.0
        }
        r = requests.post(f"{base_url}/api/scanner/scan", headers=headers, files=files, data=data)
        
    print(f"Status Code: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    test_priority1()
