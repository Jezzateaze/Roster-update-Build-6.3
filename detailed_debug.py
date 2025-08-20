import requests
import json
from datetime import datetime

def debug_specific_issues():
    """Debug the specific cross-midnight calculation issues found"""
    base_url = "https://workforce-wizard.preview.emergentagent.com"
    
    # Authenticate
    login_data = {"username": "Admin", "pin": "0000"}
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    auth_token = response.json().get('token')
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {auth_token}'}
    
    print("🔍 DETAILED DEBUGGING OF CROSS-MIDNIGHT ISSUES")
    print("=" * 60)
    
    # Issue 1: Sunday 11:30pm-7:30am calculation
    print("\n🎯 ISSUE 1: Sunday 11:30pm-7:30am Active Shift")
    print("Expected: 0.5h Sunday rate ($74) + 7.5h Monday rate ($42) = $37 + $315 = $352")
    print("Actual: $400.75")
    print("Analysis:")
    print("- Sunday 2025-01-12 11:30pm-12:00am should be Sunday rate ($74/hr)")
    print("- Monday 2025-01-13 12:00am-7:30am should be Monday weekday_day rate ($42/hr)")
    print("- But we're getting $400.75 instead of $352")
    print("- Difference: $400.75 - $352 = $48.75")
    print("- This suggests the Monday portion might be calculated as weekday_night ($52/hr)")
    print("- Check: 7.5h × $52/hr = $390, plus 0.5h × $74/hr = $37, total = $427 (still not matching)")
    
    # Let's create the entry and examine it
    roster_entry = {
        "date": "2025-01-12",  # Sunday
        "shift_template_id": "debug-sunday",
        "start_time": "23:30",
        "end_time": "07:30",
        "is_sleepover": False,
        "is_public_holiday": False
    }
    
    response = requests.post(f"{base_url}/api/roster", json=roster_entry, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"\nActual calculation result:")
        print(f"- Hours worked: {result.get('hours_worked')}")
        print(f"- Base pay: ${result.get('base_pay')}")
        print(f"- Total pay: ${result.get('total_pay')}")
        
        # Try to reverse engineer the calculation
        total_pay = result.get('total_pay', 0)
        hours = result.get('hours_worked', 0)
        if hours > 0:
            avg_rate = total_pay / hours
            print(f"- Average rate: ${avg_rate:.2f}/hr")
            
            # Check if it matches any single rate
            rates = {"weekday_day": 42.00, "weekday_evening": 44.50, "weekday_night": 52.00, 
                    "saturday": 57.50, "sunday": 74.00}
            for rate_name, rate_value in rates.items():
                if abs(avg_rate - rate_value) < 0.1:
                    print(f"- This matches {rate_name} rate (${rate_value}/hr)")
                    print(f"- ISSUE: Cross-midnight splitting is NOT working - using single rate!")
                    break
            else:
                print(f"- This is a blended rate, suggesting cross-midnight splitting is working")
                # Calculate what the blend should be
                expected_blend = (0.5 * 74.00 + 7.5 * 42.00) / 8.0
                print(f"- Expected blended rate: ${expected_blend:.2f}/hr")
                if abs(avg_rate - expected_blend) < 0.1:
                    print(f"- ✅ Blended rate matches expected calculation")
                else:
                    print(f"- ❌ Blended rate doesn't match - there's a bug in the calculation")
    
    print("\n" + "="*60)
    
    # Issue 2: Midnight start shift
    print("\n🎯 ISSUE 2: Cross-midnight shift starting at midnight (12:00am-8:00am)")
    print("Expected: 8h Monday weekday_day rate ($42/hr) = $336")
    print("Actual: $388")
    print("Analysis:")
    print("- Date 2025-01-13 (Monday) with 00:00-08:00 should be Tuesday morning")
    print("- But the logic might be treating 00:00 start as night shift")
    print("- $388 ÷ 8h = $48.50/hr - this doesn't match any standard rate")
    print("- Closest is weekday_night ($52/hr) but that would be $416")
    
    roster_entry2 = {
        "date": "2025-01-13",  # Monday
        "shift_template_id": "debug-midnight-start",
        "start_time": "00:00",
        "end_time": "08:00",
        "is_sleepover": False,
        "is_public_holiday": False
    }
    
    response = requests.post(f"{base_url}/api/roster", json=roster_entry2, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"\nActual calculation result:")
        print(f"- Hours worked: {result.get('hours_worked')}")
        print(f"- Base pay: ${result.get('base_pay')}")
        print(f"- Total pay: ${result.get('total_pay')}")
        
        total_pay = result.get('total_pay', 0)
        hours = result.get('hours_worked', 0)
        if hours > 0:
            avg_rate = total_pay / hours
            print(f"- Average rate: ${avg_rate:.2f}/hr")
            
            # This should be a simple weekday_day calculation
            if abs(avg_rate - 42.00) < 0.1:
                print(f"- ✅ Correct weekday_day rate")
            else:
                print(f"- ❌ Wrong rate - should be $42.00/hr for weekday_day")
                print(f"- The determine_shift_type function might be misclassifying this shift")
    
    print("\n" + "="*60)
    print("\n🔍 ROOT CAUSE ANALYSIS:")
    print("1. The cross-midnight logic appears to be working (we see blended rates)")
    print("2. But the shift type determination for the second day segment might be wrong")
    print("3. The determine_shift_type function might be using the wrong logic for:")
    print("   - Shifts starting at 00:00 (midnight)")
    print("   - Weekend-to-weekday transitions")
    print("4. Need to check if the second day calculation is using correct date and time")

if __name__ == "__main__":
    debug_specific_issues()