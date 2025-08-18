import requests
import json

# First authenticate as admin
base_url = "https://rostersync-1.preview.emergentagent.com"
login_data = {
    "username": "Admin",
    "pin": "0000"
}

response = requests.post(f"{base_url}/api/auth/login", json=login_data)
if response.status_code == 200:
    auth_data = response.json()
    token = auth_data.get('token')
    user = auth_data.get('user')
    
    print("Admin user data:")
    print(json.dumps(user, indent=2))
    
    # Try to get all users to see what's available
    headers = {'Authorization': f'Bearer {token}'}
    users_response = requests.get(f"{base_url}/api/users", headers=headers)
    if users_response.status_code == 200:
        users = users_response.json()
        print(f"\nFound {len(users)} users:")
        for user in users:
            print(f"- {user.get('username')}: {user.get('email', 'No email')}")
    else:
        print(f"Failed to get users: {users_response.status_code}")
        print(users_response.text)
else:
    print(f"Login failed: {response.status_code}")
    print(response.text)