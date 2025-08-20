import requests
import sys
import json
from datetime import datetime, timedelta

class CrossMidnightShiftTester:
    def __init__(self, base_url="https://shift-master-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_results = []

    def authenticate(self):
        """Authenticate as admin to get access token"""
        print("🔐 Authenticating as Admin...")
        
        login_data = {
            "username": "Admin",
            "pin": "0000"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                print(f"✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def create_roster_entry(self, test_name, date, start_time, end_time, is_sleepover=False, staff_id=None, staff_name=None):
        """Create a roster entry and return the response"""
        self.tests_run += 1
        
        roster_entry = {
            "id": "",  # Will be auto-generated
            "date": date,
            "shift_template_id": f"test-{test_name.lower().replace(' ', '-')}",
            "start_time": start_time,
            "end_time": end_time,
            "is_sleepover": is_sleepover,
            "is_public_holiday": False,
            "staff_id": staff_id,
            "staff_name": staff_name,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        print(f"\n🔍 Testing: {test_name}")
        print(f"   Date: {date} ({self.get_day_name(date)})")
        print(f"   Time: {start_time} - {end_time}")
        print(f"   Sleepover: {is_sleepover}")
        
        try:
            headers = {'Content-Type': 'application/json'}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            response = requests.post(
                f"{self.base_url}/api/roster",
                json=roster_entry,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Entry created successfully")
                print(f"   Hours worked: {data.get('hours_worked', 0)}")
                print(f"   Base pay: ${data.get('base_pay', 0)}")
                print(f"   Sleepover allowance: ${data.get('sleepover_allowance', 0)}")
                print(f"   Total pay: ${data.get('total_pay', 0)}")
                
                self.tests_passed += 1
                return True, data
            else:
                print(f"❌ Failed to create entry: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Error creating entry: {e}")
            return False, {}

    def get_day_name(self, date_str):
        """Get day name from date string"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%A")

    def test_cross_midnight_active_shifts(self):
        """Test cross-midnight active shifts (NOT sleepover) as specified in review request"""
        print(f"\n🌙 TESTING CROSS-MIDNIGHT ACTIVE SHIFTS (NOT SLEEPOVER)")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Friday 11:30pm-7:30am Active Shift",
                "date": "2025-01-10",  # Friday
                "start_time": "23:30",
                "end_time": "07:30",
                "is_sleepover": False,
                "expected_total_hours": 8.0,
                "expected_segments": [
                    {"period": "11:30pm-12:00am Friday", "hours": 0.5, "rate_type": "weekday_evening"},
                    {"period": "12:00am-7:30am Saturday", "hours": 7.5, "rate_type": "saturday"}
                ]
            },
            {
                "name": "Saturday 11:30pm-7:30am Active Shift", 
                "date": "2025-01-11",  # Saturday
                "start_time": "23:30",
                "end_time": "07:30",
                "is_sleepover": False,
                "expected_total_hours": 8.0,
                "expected_segments": [
                    {"period": "11:30pm-12:00am Saturday", "hours": 0.5, "rate_type": "saturday"},
                    {"period": "12:00am-7:30am Sunday", "hours": 7.5, "rate_type": "sunday"}
                ]
            },
            {
                "name": "Sunday 11:30pm-7:30am Active Shift",
                "date": "2025-01-12",  # Sunday
                "start_time": "23:30", 
                "end_time": "07:30",
                "is_sleepover": False,
                "expected_total_hours": 8.0,
                "expected_segments": [
                    {"period": "11:30pm-12:00am Sunday", "hours": 0.5, "rate_type": "sunday"},
                    {"period": "12:00am-7:30am Monday", "hours": 7.5, "rate_type": "weekday_day"}
                ]
            }
        ]
        
        # Expected rates from settings
        rates = {
            "weekday_day": 42.00,
            "weekday_evening": 44.50,
            "saturday": 57.50,
            "sunday": 74.00
        }
        
        cross_midnight_tests_passed = 0
        
        for test_case in test_cases:
            success, response = self.create_roster_entry(
                test_case["name"],
                test_case["date"],
                test_case["start_time"],
                test_case["end_time"],
                test_case["is_sleepover"]
            )
            
            if success:
                # Verify total hours
                actual_hours = response.get('hours_worked', 0)
                expected_hours = test_case["expected_total_hours"]
                
                hours_correct = abs(actual_hours - expected_hours) < 0.1
                
                # Calculate expected pay based on segments
                expected_total_pay = 0
                print(f"   📊 Expected calculation breakdown:")
                for segment in test_case["expected_segments"]:
                    segment_rate = rates[segment["rate_type"]]
                    segment_pay = segment["hours"] * segment_rate
                    expected_total_pay += segment_pay
                    print(f"      {segment['period']}: {segment['hours']}h × ${segment_rate}/hr = ${segment_pay}")
                
                print(f"   Expected total: {expected_hours}h, ${expected_total_pay}")
                
                actual_total_pay = response.get('total_pay', 0)
                pay_correct = abs(actual_total_pay - expected_total_pay) < 0.01
                
                if hours_correct and pay_correct:
                    print(f"   ✅ Cross-midnight calculation CORRECT")
                    cross_midnight_tests_passed += 1
                    self.test_results.append({
                        "test": test_case["name"],
                        "status": "PASS",
                        "expected_hours": expected_hours,
                        "actual_hours": actual_hours,
                        "expected_pay": expected_total_pay,
                        "actual_pay": actual_total_pay
                    })
                else:
                    print(f"   ❌ Cross-midnight calculation INCORRECT")
                    if not hours_correct:
                        print(f"      Hours mismatch: got {actual_hours}, expected {expected_hours}")
                    if not pay_correct:
                        print(f"      Pay mismatch: got ${actual_total_pay}, expected ${expected_total_pay}")
                    
                    self.test_results.append({
                        "test": test_case["name"],
                        "status": "FAIL",
                        "expected_hours": expected_hours,
                        "actual_hours": actual_hours,
                        "expected_pay": expected_total_pay,
                        "actual_pay": actual_total_pay,
                        "hours_correct": hours_correct,
                        "pay_correct": pay_correct
                    })
            else:
                self.test_results.append({
                    "test": test_case["name"],
                    "status": "ERROR",
                    "error": "Failed to create roster entry"
                })
        
        print(f"\n📊 Cross-midnight Active Shift Results: {cross_midnight_tests_passed}/{len(test_cases)} passed")
        return cross_midnight_tests_passed == len(test_cases)

    def test_regular_shifts_no_midnight_crossing(self):
        """Test regular shifts that don't cross midnight to ensure they still work"""
        print(f"\n☀️ TESTING REGULAR SHIFTS (NO MIDNIGHT CROSSING)")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Regular Day Shift 9:00am-5:00pm",
                "date": "2025-01-13",  # Monday
                "start_time": "09:00",
                "end_time": "17:00",
                "is_sleepover": False,
                "expected_hours": 8.0,
                "expected_rate": 42.00,  # weekday_day
                "expected_pay": 336.00
            },
            {
                "name": "Regular Evening Shift 3:30pm-11:30pm",
                "date": "2025-01-13",  # Monday
                "start_time": "15:30",
                "end_time": "23:30",
                "is_sleepover": False,
                "expected_hours": 8.0,
                "expected_rate": 44.50,  # weekday_evening (extends past 8pm)
                "expected_pay": 356.00
            },
            {
                "name": "Saturday Day Shift 7:30am-3:30pm",
                "date": "2025-01-18",  # Saturday
                "start_time": "07:30",
                "end_time": "15:30",
                "is_sleepover": False,
                "expected_hours": 8.0,
                "expected_rate": 57.50,  # saturday
                "expected_pay": 460.00
            },
            {
                "name": "Sunday Day Shift 7:30am-3:30pm",
                "date": "2025-01-19",  # Sunday
                "start_time": "07:30",
                "end_time": "15:30",
                "is_sleepover": False,
                "expected_hours": 8.0,
                "expected_rate": 74.00,  # sunday
                "expected_pay": 592.00
            }
        ]
        
        regular_tests_passed = 0
        
        for test_case in test_cases:
            success, response = self.create_roster_entry(
                test_case["name"],
                test_case["date"],
                test_case["start_time"],
                test_case["end_time"],
                test_case["is_sleepover"]
            )
            
            if success:
                actual_hours = response.get('hours_worked', 0)
                actual_pay = response.get('total_pay', 0)
                
                hours_correct = abs(actual_hours - test_case["expected_hours"]) < 0.1
                pay_correct = abs(actual_pay - test_case["expected_pay"]) < 0.01
                
                print(f"   Expected: {test_case['expected_hours']}h × ${test_case['expected_rate']}/hr = ${test_case['expected_pay']}")
                
                if hours_correct and pay_correct:
                    print(f"   ✅ Regular shift calculation CORRECT")
                    regular_tests_passed += 1
                    self.test_results.append({
                        "test": test_case["name"],
                        "status": "PASS",
                        "expected_hours": test_case["expected_hours"],
                        "actual_hours": actual_hours,
                        "expected_pay": test_case["expected_pay"],
                        "actual_pay": actual_pay
                    })
                else:
                    print(f"   ❌ Regular shift calculation INCORRECT")
                    if not hours_correct:
                        print(f"      Hours mismatch: got {actual_hours}, expected {test_case['expected_hours']}")
                    if not pay_correct:
                        print(f"      Pay mismatch: got ${actual_pay}, expected ${test_case['expected_pay']}")
                    
                    self.test_results.append({
                        "test": test_case["name"],
                        "status": "FAIL",
                        "expected_hours": test_case["expected_hours"],
                        "actual_hours": actual_hours,
                        "expected_pay": test_case["expected_pay"],
                        "actual_pay": actual_pay
                    })
            else:
                self.test_results.append({
                    "test": test_case["name"],
                    "status": "ERROR",
                    "error": "Failed to create roster entry"
                })
        
        print(f"\n📊 Regular Shift Results: {regular_tests_passed}/{len(test_cases)} passed")
        return regular_tests_passed == len(test_cases)

    def test_sleepover_shifts_not_affected(self):
        """Test that sleepover shifts are NOT affected by new cross-midnight logic"""
        print(f"\n🛏️ TESTING SLEEPOVER SHIFTS (SHOULD NOT BE AFFECTED)")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Sleepover Shift Friday 11:30pm-7:30am",
                "date": "2025-01-10",  # Friday
                "start_time": "23:30",
                "end_time": "07:30",
                "is_sleepover": True,
                "expected_hours": 8.0,
                "expected_sleepover_allowance": 175.00,  # Flat rate
                "expected_total_pay": 175.00  # Should be flat rate, not split
            },
            {
                "name": "Sleepover Shift Saturday 11:30pm-7:30am",
                "date": "2025-01-11",  # Saturday
                "start_time": "23:30",
                "end_time": "07:30",
                "is_sleepover": True,
                "expected_hours": 8.0,
                "expected_sleepover_allowance": 175.00,  # Flat rate
                "expected_total_pay": 175.00  # Should be flat rate, not split
            },
            {
                "name": "Sleepover Shift Sunday 11:30pm-7:30am",
                "date": "2025-01-12",  # Sunday
                "start_time": "23:30",
                "end_time": "07:30",
                "is_sleepover": True,
                "expected_hours": 8.0,
                "expected_sleepover_allowance": 175.00,  # Flat rate
                "expected_total_pay": 175.00  # Should be flat rate, not split
            }
        ]
        
        sleepover_tests_passed = 0
        
        for test_case in test_cases:
            success, response = self.create_roster_entry(
                test_case["name"],
                test_case["date"],
                test_case["start_time"],
                test_case["end_time"],
                test_case["is_sleepover"]
            )
            
            if success:
                actual_hours = response.get('hours_worked', 0)
                actual_sleepover = response.get('sleepover_allowance', 0)
                actual_total = response.get('total_pay', 0)
                
                hours_correct = abs(actual_hours - test_case["expected_hours"]) < 0.1
                sleepover_correct = abs(actual_sleepover - test_case["expected_sleepover_allowance"]) < 0.01
                total_correct = abs(actual_total - test_case["expected_total_pay"]) < 0.01
                
                print(f"   Expected: ${test_case['expected_sleepover_allowance']} flat rate (NOT split by midnight)")
                
                if hours_correct and sleepover_correct and total_correct:
                    print(f"   ✅ Sleepover calculation CORRECT (not affected by cross-midnight logic)")
                    sleepover_tests_passed += 1
                    self.test_results.append({
                        "test": test_case["name"],
                        "status": "PASS",
                        "expected_hours": test_case["expected_hours"],
                        "actual_hours": actual_hours,
                        "expected_pay": test_case["expected_total_pay"],
                        "actual_pay": actual_total,
                        "sleepover_allowance": actual_sleepover
                    })
                else:
                    print(f"   ❌ Sleepover calculation INCORRECT")
                    if not hours_correct:
                        print(f"      Hours mismatch: got {actual_hours}, expected {test_case['expected_hours']}")
                    if not sleepover_correct:
                        print(f"      Sleepover allowance mismatch: got ${actual_sleepover}, expected ${test_case['expected_sleepover_allowance']}")
                    if not total_correct:
                        print(f"      Total pay mismatch: got ${actual_total}, expected ${test_case['expected_total_pay']}")
                    
                    self.test_results.append({
                        "test": test_case["name"],
                        "status": "FAIL",
                        "expected_hours": test_case["expected_hours"],
                        "actual_hours": actual_hours,
                        "expected_pay": test_case["expected_total_pay"],
                        "actual_pay": actual_total,
                        "sleepover_allowance": actual_sleepover
                    })
            else:
                self.test_results.append({
                    "test": test_case["name"],
                    "status": "ERROR",
                    "error": "Failed to create roster entry"
                })
        
        print(f"\n📊 Sleepover Shift Results: {sleepover_tests_passed}/{len(test_cases)} passed")
        return sleepover_tests_passed == len(test_cases)

    def test_edge_cases(self):
        """Test edge cases for cross-midnight functionality"""
        print(f"\n⚡ TESTING EDGE CASES")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Shift ending exactly at midnight (11:30pm-12:00am)",
                "date": "2025-01-13",  # Monday
                "start_time": "23:30",
                "end_time": "00:00",
                "is_sleepover": False,
                "expected_hours": 0.5,
                "expected_rate": 44.50,  # weekday_evening
                "expected_pay": 22.25
            },
            {
                "name": "Very short cross-midnight shift (11:50pm-12:10am)",
                "date": "2025-01-13",  # Monday
                "start_time": "23:50",
                "end_time": "00:10",
                "is_sleepover": False,
                "expected_hours": 0.33,  # 20 minutes
                "expected_segments": [
                    {"period": "11:50pm-12:00am Monday", "hours": 0.17, "rate_type": "weekday_evening"},  # 10 min
                    {"period": "12:00am-12:10am Tuesday", "hours": 0.17, "rate_type": "weekday_day"}   # 10 min
                ]
            },
            {
                "name": "Cross-midnight shift starting at midnight (12:00am-8:00am)",
                "date": "2025-01-13",  # Monday (but shift is actually Tuesday)
                "start_time": "00:00",
                "end_time": "08:00",
                "is_sleepover": False,
                "expected_hours": 8.0,
                "expected_rate": 42.00,  # weekday_day (Tuesday)
                "expected_pay": 336.00
            }
        ]
        
        edge_tests_passed = 0
        
        for test_case in test_cases:
            success, response = self.create_roster_entry(
                test_case["name"],
                test_case["date"],
                test_case["start_time"],
                test_case["end_time"],
                test_case["is_sleepover"]
            )
            
            if success:
                actual_hours = response.get('hours_worked', 0)
                actual_pay = response.get('total_pay', 0)
                
                if "expected_segments" in test_case:
                    # Complex calculation for very short shifts
                    expected_pay = 0
                    rates = {"weekday_day": 42.00, "weekday_evening": 44.50}
                    for segment in test_case["expected_segments"]:
                        expected_pay += segment["hours"] * rates[segment["rate_type"]]
                    
                    hours_correct = abs(actual_hours - test_case["expected_hours"]) < 0.05  # More tolerance for short shifts
                    pay_correct = abs(actual_pay - expected_pay) < 0.05
                    
                    print(f"   Expected segments calculation: ${expected_pay:.2f}")
                else:
                    expected_pay = test_case["expected_pay"]
                    hours_correct = abs(actual_hours - test_case["expected_hours"]) < 0.1
                    pay_correct = abs(actual_pay - expected_pay) < 0.01
                    
                    print(f"   Expected: {test_case['expected_hours']}h × ${test_case['expected_rate']}/hr = ${expected_pay}")
                
                if hours_correct and pay_correct:
                    print(f"   ✅ Edge case calculation CORRECT")
                    edge_tests_passed += 1
                    self.test_results.append({
                        "test": test_case["name"],
                        "status": "PASS",
                        "expected_hours": test_case["expected_hours"],
                        "actual_hours": actual_hours,
                        "expected_pay": expected_pay,
                        "actual_pay": actual_pay
                    })
                else:
                    print(f"   ❌ Edge case calculation INCORRECT")
                    if not hours_correct:
                        print(f"      Hours mismatch: got {actual_hours}, expected {test_case['expected_hours']}")
                    if not pay_correct:
                        print(f"      Pay mismatch: got ${actual_pay}, expected ${expected_pay}")
                    
                    self.test_results.append({
                        "test": test_case["name"],
                        "status": "FAIL",
                        "expected_hours": test_case["expected_hours"],
                        "actual_hours": actual_hours,
                        "expected_pay": expected_pay,
                        "actual_pay": actual_pay
                    })
            else:
                self.test_results.append({
                    "test": test_case["name"],
                    "status": "ERROR",
                    "error": "Failed to create roster entry"
                })
        
        print(f"\n📊 Edge Case Results: {edge_tests_passed}/{len(test_cases)} passed")
        return edge_tests_passed == len(test_cases)

    def print_final_summary(self):
        """Print final test summary"""
        print(f"\n" + "=" * 80)
        print(f"🎯 CROSS-MIDNIGHT SHIFT PAY CALCULATION TEST SUMMARY")
        print(f"=" * 80)
        
        print(f"\n📊 Overall Results:")
        print(f"   Tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Group results by category
        categories = {
            "Cross-midnight Active Shifts": [],
            "Regular Shifts": [],
            "Sleepover Shifts": [],
            "Edge Cases": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Active Shift" in test_name and ("Friday" in test_name or "Saturday" in test_name or "Sunday" in test_name):
                categories["Cross-midnight Active Shifts"].append(result)
            elif "Sleepover" in test_name:
                categories["Sleepover Shifts"].append(result)
            elif "edge" in test_name.lower() or "midnight" in test_name or "short" in test_name:
                categories["Edge Cases"].append(result)
            else:
                categories["Regular Shifts"].append(result)
        
        print(f"\n📋 Detailed Results by Category:")
        for category, results in categories.items():
            if results:
                passed = len([r for r in results if r["status"] == "PASS"])
                total = len(results)
                print(f"\n   {category}: {passed}/{total} passed")
                
                for result in results:
                    status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                    print(f"      {status_icon} {result['test']}")
                    
                    if result["status"] == "FAIL":
                        if "expected_hours" in result and "actual_hours" in result:
                            print(f"         Hours: got {result['actual_hours']}, expected {result['expected_hours']}")
                        if "expected_pay" in result and "actual_pay" in result:
                            print(f"         Pay: got ${result['actual_pay']}, expected ${result['expected_pay']}")

    def run_all_tests(self):
        """Run all cross-midnight shift tests"""
        print(f"🚀 STARTING CROSS-MIDNIGHT SHIFT PAY CALCULATION TESTS")
        print(f"=" * 80)
        
        if not self.authenticate():
            print("❌ Authentication failed - cannot run tests")
            return False
        
        # Run all test categories
        cross_midnight_passed = self.test_cross_midnight_active_shifts()
        regular_shifts_passed = self.test_regular_shifts_no_midnight_crossing()
        sleepover_shifts_passed = self.test_sleepover_shifts_not_affected()
        edge_cases_passed = self.test_edge_cases()
        
        # Print final summary
        self.print_final_summary()
        
        # Determine overall success
        all_categories_passed = (
            cross_midnight_passed and 
            regular_shifts_passed and 
            sleepover_shifts_passed and 
            edge_cases_passed
        )
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        if all_categories_passed:
            print(f"✅ ALL TESTS PASSED - Cross-midnight shift pay calculation is working correctly!")
            print(f"   ✅ Cross-midnight active shifts split correctly at midnight")
            print(f"   ✅ Regular shifts (no midnight crossing) still work properly")
            print(f"   ✅ Sleepover shifts maintain $175 flat rate (not affected by new logic)")
            print(f"   ✅ Edge cases handled correctly")
        else:
            print(f"❌ SOME TESTS FAILED - Cross-midnight functionality needs attention:")
            if not cross_midnight_passed:
                print(f"   ❌ Cross-midnight active shifts not calculating correctly")
            if not regular_shifts_passed:
                print(f"   ❌ Regular shifts broken by new implementation")
            if not sleepover_shifts_passed:
                print(f"   ❌ Sleepover shifts affected by cross-midnight logic (should not be)")
            if not edge_cases_passed:
                print(f"   ❌ Edge cases not handled properly")
        
        return all_categories_passed

if __name__ == "__main__":
    tester = CrossMidnightShiftTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)