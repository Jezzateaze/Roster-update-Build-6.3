import requests

base_url = "https://rostersync-1.preview.emergentagent.com"

# Try different PINs that might have been set
pins_to_try = ["0000", "2333", "1234", "8888"]

for pin in pins_to_try:
    login_data = {
        "username": "Admin",
        "pin": pin
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    print(f"PIN {pin}: Status {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Login successful with PIN: {pin}")
        break
    else:
        print(f"❌ Failed: {response.text[:100]}")