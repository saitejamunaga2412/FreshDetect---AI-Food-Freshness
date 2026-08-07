import requests
import json
import os

def test():
    print("Testing /api/scanner/scan endpoint...")
    url = "http://localhost:8001/api/scanner/scan"
    
    # Try finding an image in dataset
    img_path = r"d:\FreshDetect---AI-Food-Freshness\backend\dataset\Freshness44\Tomato_Fresh\DSCN4068.jpg_0_112.jpg"
    
    if not os.path.exists(img_path):
        print(f"Image not found: {img_path}")
        return

    with open(img_path, 'rb') as f:
        files = {'image': ('test_image.jpg', f, 'image/jpeg')}
        data = {'temp': 22.0, 'humid': 50.0}
        
        # NOTE: We might get auth error if there's no JWT.
        # Let's see if scanner endpoint allows unauthenticated requests.
        try:
            response = requests.post(url, files=files, data=data)
            print(f"Status Code: {response.status_code}")
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test()
