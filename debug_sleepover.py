import requests
import json

# Test the sleepover calculation specifically
base_url = "https://workforce-wizard-1.preview.emergentagent.com"

# First authenticate
login_data = {
    "username": "Admin",
    "pin": "0000"
}

response = requests.post(f"{base_url}/api/auth/login", json=login_data)
if response.status_code == 200:
    auth_token = response.json().get('token')
    print(f"✅ Authenticated successfully")
else:
    print(f"❌ Authentication failed")
    exit(1)

# Create sleepover shift with 3 wake hours
sleepover_shift = {
    "id": "",
    "date": "2025-01-06",  # Monday
    "shift_template_id": "debug-sleepover",
    "start_time": "23:30",
    "end_time": "07:30",
    "is_sleepover": True,
    "is_public_holiday": False,
    "wake_hours": 3.0,  # 3 total wake hours (1 extra beyond 2-hour base)
    "staff_id": None,
    "staff_name": None
}

headers = {'Content-Type': 'application/json'}
response = requests.post(f"{base_url}/api/roster", json=sleepover_shift, headers=headers)

if response.status_code == 200:
    result = response.json()
    print(f"\n🛏️ SLEEPOVER CALCULATION DEBUG:")
    print(f"   Date: {result.get('date')}")
    print(f"   Time: {result.get('start_time')}-{result.get('end_time')}")
    print(f"   Is sleepover: {result.get('is_sleepover')}")
    print(f"   Wake hours: {result.get('wake_hours')}")
    print(f"   Hours worked: {result.get('hours_worked')}")
    
    print(f"\n💰 STAFF PAY:")
    print(f"   Base pay: ${result.get('base_pay')}")
    print(f"   Sleepover allowance: ${result.get('sleepover_allowance')}")
    print(f"   Total pay: ${result.get('total_pay')}")
    
    print(f"\n💰 NDIS CHARGES:")
    print(f"   NDIS hourly charge: ${result.get('ndis_hourly_charge')}")
    print(f"   NDIS shift charge: ${result.get('ndis_shift_charge')}")
    print(f"   NDIS total charge: ${result.get('ndis_total_charge')}")
    print(f"   NDIS line item code: {result.get('ndis_line_item_code')}")
    print(f"   NDIS description: {result.get('ndis_description')}")
    
    # Calculate expected values
    base_sleepover = 286.56
    extra_wake_hours = 1.0  # 3 total - 2 base = 1 extra
    weekday_day_rate = 70.23
    expected_extra_charge = extra_wake_hours * weekday_day_rate
    expected_total = base_sleepover + expected_extra_charge
    
    print(f"\n🎯 EXPECTED CALCULATION:")
    print(f"   Base sleepover: ${base_sleepover}")
    print(f"   Extra wake hours: {extra_wake_hours} × ${weekday_day_rate} = ${expected_extra_charge}")
    print(f"   Expected total: ${expected_total}")
    
    actual_total = result.get('ndis_total_charge', 0)
    difference = actual_total - expected_total
    
    print(f"\n📊 COMPARISON:")
    print(f"   Actual NDIS total: ${actual_total}")
    print(f"   Expected NDIS total: ${expected_total}")
    print(f"   Difference: ${difference}")
    
    if abs(difference) < 0.01:
        print(f"   ✅ CALCULATION CORRECT")
    else:
        print(f"   ❌ CALCULATION INCORRECT")
        
        # Try to figure out what rate was used
        if abs(difference - 8.58) < 0.01:  # 78.81 - 70.23 = 8.58
            print(f"   🔍 Appears to be using weekday_night rate (${78.81}) instead of weekday_day rate (${70.23})")
        
else:
    print(f"❌ Failed to create sleepover shift: {response.status_code}")
    print(f"   Response: {response.text}")