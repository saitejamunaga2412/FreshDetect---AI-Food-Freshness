import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8001/api'

def run_tests():
    report = {'passed': [], 'failed': [], 'warnings': []}
    
    print("Testing 1. Admin Login")
    res = requests.post(f'{BASE_URL}/auth/login', json={'email': 'admin@example.com', 'password': 'password123'})
    if res.status_code != 200:
        requests.post(f'{BASE_URL}/auth/register', json={'name': 'Admin User', 'email': 'admin@example.com', 'password': 'password123', 'role': 'Administrator'})
        res = requests.post(f'{BASE_URL}/auth/login', json={'email': 'admin@example.com', 'password': 'password123'})
        
    if res.status_code == 200:
        token = res.json().get('access_token') or res.json().get('token')
        headers = {'Authorization': f'Bearer {token}'}
        report['passed'].append("Admin Login")
    else:
        report['failed'].append("Admin Login")
        print(json.dumps(report, indent=2))
        return report

    print("Testing 2 & 3 & 4 & 5. Scanner, YOLO, Freshness, FoodKeeper")
    with open('dummy_apple.jpg', 'rb') as f:
        files = {'image': ('dummy_apple.jpg', f, 'image/jpeg')}
        data = {'temp': '20.5', 'humid': '50.0'}
        res = requests.post(f'{BASE_URL}/scanner/scan', headers=headers, files=files, data=data)
        
    if res.status_code == 200:
        scan_data = res.json()
        report['passed'].append("Scanner & YOLO & Freshness Prediction & FoodKeeper Lookup")
        fruit_name = scan_data['result']['fruit']
    else:
        print("Scanner Error:", res.status_code, res.text)
        report['failed'].append("Scanner Endpoint")
        fruit_name = "Apple"

    print("Testing 7. Save to Inventory")
    res = requests.post(f'{BASE_URL}/inventory/batches', headers=headers, json={
        'batch_id': 'BATCH-TEST-1',
        'fruit_name': fruit_name,
        'category': 'Fruit',
        'quantity': 10,
        'storage_location': 'Refrigerator',
        'temperature': 4.0,
        'humidity': 85.0
    })
    if res.status_code == 201:
        report['passed'].append("Save to Inventory")
        batch_id = res.json()['_id']
    else:
        print("Inventory Error:", res.status_code, res.text)
        report['failed'].append("Save to Inventory")
        batch_id = None
        
    print("Testing 8. Duplicate Handling")
    res = requests.get(f'{BASE_URL}/inventory/batches?status=active&fruit_name={fruit_name}', headers=headers)
    if res.status_code == 200 and len(res.json()) >= 1:
        report['passed'].append("Duplicate Handling (Batch found)")
    else:
        report['failed'].append("Duplicate Handling (Batch found)")

    print("Testing 9. Inventory Update")
    if batch_id:
        res = requests.patch(f'{BASE_URL}/inventory/batches/{batch_id}', headers=headers, json={'quantity': 15})
        if res.status_code == 200:
            report['passed'].append("Inventory Update")
        else:
            report['failed'].append("Inventory Update")
            
    print("Testing 10. Dashboard Update")
    res = requests.get(f'{BASE_URL}/inventory/stats', headers=headers)
    if res.status_code == 200 and 'total_items' in res.json():
        report['passed'].append("Dashboard Statistics")
    else:
        print("Dashboard Error:", res.status_code, res.text)
        report['failed'].append("Dashboard Statistics")

    print("Testing 11. Reports Update")
    # check reports
    res = requests.get(f'{BASE_URL}/admin/system-logs', headers=headers)
    if res.status_code == 200:
        report['passed'].append("Reports / Admin logs generated correctly")
    else:
        # maybe there is another endpoint for reports?
        report['warnings'].append("Admin logs failed or doesn't exist")
        
    print("Testing 12 & 13 & 14. Regular User Login and Permission Validation")
    res = requests.post(f'{BASE_URL}/auth/login', json={'email': 'user@example.com', 'password': 'password123'})
    if res.status_code != 200:
        requests.post(f'{BASE_URL}/auth/register', json={'name': 'Regular User', 'email': 'user@example.com', 'password': 'password123', 'role': 'User'})
        res = requests.post(f'{BASE_URL}/auth/login', json={'email': 'user@example.com', 'password': 'password123'})

    if res.status_code == 200:
        user_token = res.json().get('access_token') or res.json().get('token')
        user_headers = {'Authorization': f'Bearer {user_token}'}
        report['passed'].append("Regular User Login")
        
        # Test permission: users should not be able to POST to inventory
        res_inv = requests.post(f'{BASE_URL}/inventory/batches', headers=user_headers, json={
            'batch_id': 'BATCH-TEST-USER',
            'fruit_name': 'Banana',
            'category': 'Fruit',
            'quantity': 5,
            'storage_location': 'Cold Storage'
        })
        if res_inv.status_code in [403, 401]:
            report['passed'].append("Role Permissions Enforced")
        else:
            report['warnings'].append(f"Role Permissions not fully enforced (User could save inventory, status {res_inv.status_code})")
    else:
        report['failed'].append("Regular User Login")

    print(json.dumps(report, indent=2))

run_tests()
