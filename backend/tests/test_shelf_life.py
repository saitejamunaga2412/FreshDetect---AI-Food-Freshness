import requests
import json

base_url = "http://localhost:8001"

def test_shelf_life():
    print("1. Logging in as Administrator...")
    login_data = {
        "email": "admintest2@example.com",
        "password": "password123"
    }
    r = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if r.status_code != 200:
        reg_data = {
            "name": "Admin User",
            "email": "admintest2@example.com",
            "password": "password123",
            "role": "Administrator"
        }
        requests.post(f"{base_url}/api/auth/register", json=reg_data)
        r = requests.post(f"{base_url}/api/auth/login", json=login_data)
    token = r.json().get("access_token")
    if not token: token = r.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("2. Create a Banana batch in Refrigerator...")
    batch_data = {
        "batch_id": "BATCH-SHELF-BANANA",
        "fruit_name": "Banana",
        "category": "Fruit",
        "quantity": 10,
        "storage_location": "Refrigerator"
    }
    r2 = requests.post(f"{base_url}/api/inventory/batches", headers=headers, json=batch_data)
    batch_info = r2.json()
    print("Batch Response Status:", r2.status_code)
    print("Batch Response Body:", r2.text)
    print("Created ID:", batch_info.get("_id"))
    
    print("3. Fetching Inventory to check calculations...")
    r3 = requests.get(f"{base_url}/api/inventory/batches", headers=headers)
    batches = r3.json()
    target = next((b for b in batches if b["_id"] == batch_info["_id"]), None)
    if target:
        print("Initial Expiry Date:", target.get("estimated_expiry_date"))
        print("Days Remaining:", target.get("days_remaining"))
        print("Risk Forecast:", target.get("risk_forecast"))
        print("Storage Recomm:", target.get("storage_recommendation"))

if __name__ == "__main__":
    test_shelf_life()
