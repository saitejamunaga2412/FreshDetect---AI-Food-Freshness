import requests
import json
import datetime

base_url = "http://localhost:8001"

def test_inventory():
    print("1. Logging in as Retailer...")
    login_data = {
        "email": "retailtest2@example.com",
        "password": "password123"
    }
    r = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if r.status_code != 200:
        print("Login failed, attempting register...")
        reg_data = {
            "name": "Retail User",
            "email": "retailtest2@example.com",
            "password": "password123",
            "role": "Retailer"
        }
        requests.post(f"{base_url}/api/auth/register", json=reg_data)
        r = requests.post(f"{base_url}/api/auth/login", json=login_data)
    
    token = r.json().get("access_token")
    if not token: token = r.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("2. Create batch with Meat (should fail)...")
    bad_batch = {
        "batch_id": "BATCH-001",
        "fruit_name": "Chicken",
        "category": "Meat",
        "quantity": 100
    }
    r2 = requests.post(f"{base_url}/api/inventory/batches", headers=headers, json=bad_batch)
    print(f"Status Code: {r2.status_code}, Output: {r2.text}")
    
    print("3. Create batch with Fruit (should succeed)...")
    good_batch = {
        "batch_id": "BATCH-002",
        "fruit_name": "Apple",
        "category": "Fruit",
        "quantity": 5
    }
    r3 = requests.post(f"{base_url}/api/inventory/batches", headers=headers, json=good_batch)
    print(f"Status Code: {r3.status_code}, Output: {r3.text}")
    
    print("4. Fetch Stats...")
    r4 = requests.get(f"{base_url}/api/inventory/stats", headers=headers)
    print(f"Status Code: {r4.status_code}")
    print(json.dumps(r4.json(), indent=2))

if __name__ == "__main__":
    test_inventory()
