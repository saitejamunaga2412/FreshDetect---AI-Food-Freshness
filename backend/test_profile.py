import requests
import os

base_url = "http://localhost:8001/api"

def test_profile():
    print("1. Registering/Logging in...")
    login_data = {"email": "profiletest@example.com", "password": "password123"}
    r = requests.post(f"{base_url}/auth/login", json=login_data)
    if r.status_code != 200:
        reg_data = {
            "name": "Profile User",
            "email": "profiletest@example.com",
            "password": "password123",
            "role": "User"
        }
        requests.post(f"{base_url}/auth/register", json=reg_data)
        r = requests.post(f"{base_url}/auth/login", json=login_data)
        
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    print("2. Getting current profile...")
    r_me = requests.get(f"{base_url}/auth/me", headers=headers)
    print("Me:", r_me.json())

    print("3. Updating profile text...")
    r_update = requests.put(f"{base_url}/auth/me", headers=headers, json={"dob": "1990-01-01", "bio": "Hello world!"})
    print("Updated:", r_update.json())

    print("4. Uploading profile picture...")
    with open("dummy_apple.jpg", "rb") as f:
        files = {"file": ("dummy_apple.jpg", f, "image/jpeg")}
        r_upload = requests.post(f"{base_url}/auth/profile-picture", headers=headers, files=files)
        print("Upload Status:", r_upload.status_code)
        print("Upload Response:", r_upload.json())
        
    print("5. Removing profile picture...")
    r_remove = requests.delete(f"{base_url}/auth/profile-picture", headers=headers)
    print("Remove Response:", r_remove.json())

if __name__ == "__main__":
    test_profile()
