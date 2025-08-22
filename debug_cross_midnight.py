import requests
import json

def test_calculate_pay_endpoint():
    """Test the calculate_pay endpoint directly to debug cross-midnight issues"""
    base_url = "https://shift-master-10.preview.emergentagent.com"
    
    # Authenticate first
    login_data = {"username": "Admin", "pin": "0000"}
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Authentication failed")
        return
    
    auth_token = response.json().get('token')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }
    
    # Test cases that failed
    test_cases = [
        {
            "name": "Sunday 11:30pm-7:30am (FAILED)",
            "data": {
                "date": "2025-01-12",  # Sunday
                "start_time": "23:30",
                "end_time": "07:30",
                "is_sleepover": False,
                "is_public_holiday": False
            },
            "expected_breakdown": [
                {"period": "11:30pm-12:00am Sunday", "hours": 0.5, "rate": 74.00, "pay": 37.00},
                {"period": "12:00am-7:30am Monday", "hours": 7.5, "rate": 42.00, "pay": 315.00}
            ],
            "expected_total": 352.00
        },
        {
            "name": "Cross-midnight starting at midnight (FAILED)",
            "data": {
                "date": "2025-01-13",  # Monday (but shift is actually Tuesday)
                "start_time": "00:00",
                "end_time": "08:00",
                "is_sleepover": False,
                "is_public_holiday": False
            },
            "expected_rate": 42.00,  # Should be weekday_day for Tuesday
            "expected_total": 336.00
        }
    ]
    
    print("🔍 DEBUGGING CROSS-MIDNIGHT CALCULATION ISSUES")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n🎯 Testing: {test_case['name']}")
        print(f"   Input: {test_case['data']}")
        
        try:
            response = requests.post(
                f"{base_url}/api/calculate-pay",
                json=test_case['data'],
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Response received:")
                print(f"      Hours worked: {result.get('hours_worked', 'N/A')}")
                print(f"      Base pay: ${result.get('base_pay', 'N/A')}")
                print(f"      Total pay: ${result.get('total_pay', 'N/A')}")
                
                if 'expected_breakdown' in test_case:
                    print(f"   📊 Expected breakdown:")
                    for segment in test_case['expected_breakdown']:
                        print(f"      {segment['period']}: {segment['hours']}h × ${segment['rate']}/hr = ${segment['pay']}")
                    print(f"   Expected total: ${test_case['expected_total']}")
                    
                    actual_total = result.get('total_pay', 0)
                    if abs(actual_total - test_case['expected_total']) > 0.01:
                        print(f"   ❌ MISMATCH: Got ${actual_total}, expected ${test_case['expected_total']}")
                    else:
                        print(f"   ✅ CORRECT: ${actual_total}")
                else:
                    expected_total = test_case['expected_total']
                    actual_total = result.get('total_pay', 0)
                    if abs(actual_total - expected_total) > 0.01:
                        print(f"   ❌ MISMATCH: Got ${actual_total}, expected ${expected_total}")
                    else:
                        print(f"   ✅ CORRECT: ${actual_total}")
                        
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"      Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_calculate_pay_endpoint()