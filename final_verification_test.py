#!/usr/bin/env python3
"""
FINAL VERIFICATION testing of the cross-midnight shift pay calculation fixes
Testing the exact scenarios from the review request:

1. Sunday 11:30pm-7:30am Active Shift - Should be $352.00 (FIXED)
2. Midnight-start shift 00:00-08:00 - Should be $336.00 (8h × $42 weekday_day) 
3. Friday 11:30pm-7:30am - Should be $453.50 (still working)
4. Saturday 11:30pm-7:30am - Should be $583.75 (still working)
5. Very short cross-midnight 11:50pm-12:10am - Check calculation accuracy
"""

import requests
import json
from datetime import datetime

class FinalVerificationTester:
    def __init__(self, base_url="https://workforce-wizard-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.auth_token = None
        self.test_results = []
        
    def authenticate(self):
        """Authenticate as admin"""
        print("🔐 Authenticating as Admin...")
        
        login_data = {"username": "Admin", "pin": "0000"}
        
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
    
    def create_and_test_shift(self, name, date, start_time, end_time, expected_pay, is_sleepover=False):
        """Create a roster entry and test the pay calculation"""
        print(f"\n🔍 Testing: {name}")
        print(f"   Date: {date} ({self.get_day_name(date)})")
        print(f"   Time: {start_time} - {end_time}")
        print(f"   Expected Pay: ${expected_pay:.2f}")
        
        roster_entry = {
            "id": "",
            "date": date,
            "shift_template_id": "final-verification-test",
            "start_time": start_time,
            "end_time": end_time,
            "is_sleepover": is_sleepover,
            "is_public_holiday": False,
            "staff_id": None,
            "staff_name": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        headers = {'Content-Type': 'application/json'}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        try:
            response = requests.post(
                f"{self.base_url}/api/roster",
                json=roster_entry,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                hours_worked = data.get('hours_worked', 0)
                total_pay = data.get('total_pay', 0)
                base_pay = data.get('base_pay', 0)
                sleepover_allowance = data.get('sleepover_allowance', 0)
                
                print(f"   📊 Results:")
                print(f"      Hours worked: {hours_worked}")
                print(f"      Base pay: ${base_pay:.2f}")
                print(f"      Sleepover allowance: ${sleepover_allowance:.2f}")
                print(f"      Total pay: ${total_pay:.2f}")
                
                # Check if pay matches expected (within small tolerance for floating point)
                pay_correct = abs(total_pay - expected_pay) <= 0.01
                
                if pay_correct:
                    print(f"   ✅ PASSED: Pay calculation correct")
                    result = {'name': name, 'status': 'PASSED', 'expected': expected_pay, 'actual': total_pay}
                else:
                    print(f"   ❌ FAILED: Pay calculation incorrect")
                    print(f"      Expected: ${expected_pay:.2f}")
                    print(f"      Actual: ${total_pay:.2f}")
                    print(f"      Difference: ${abs(total_pay - expected_pay):.2f}")
                    result = {'name': name, 'status': 'FAILED', 'expected': expected_pay, 'actual': total_pay}
                
                self.test_results.append(result)
                return pay_correct
                
            else:
                print(f"   ❌ FAILED: Could not create roster entry (HTTP {response.status_code})")
                print(f"      Response: {response.text[:200]}")
                self.test_results.append({'name': name, 'status': 'ERROR', 'expected': expected_pay, 'actual': 0})
                return False
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.test_results.append({'name': name, 'status': 'ERROR', 'expected': expected_pay, 'actual': 0})
            return False
    
    def get_day_name(self, date_str):
        """Get day name from date string"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%A")
        except:
            return "Unknown"
    
    def run_final_verification(self):
        """Run the final verification tests for the review request scenarios"""
        print("🎯 FINAL VERIFICATION TESTING - CROSS-MIDNIGHT SHIFT PAY CALCULATION FIXES")
        print("=" * 90)
        print("Testing the exact scenarios from the review request:")
        print("1. Sunday 11:30pm-7:30am Active Shift - Should be $352.00 (FIXED)")
        print("2. Midnight-start shift 00:00-08:00 - Should be $336.00 (8h × $42 weekday_day)")
        print("3. Friday 11:30pm-7:30am - Should be $453.50 (still working)")
        print("4. Saturday 11:30pm-7:30am - Should be $583.75 (still working)")
        print("5. Very short cross-midnight 11:50pm-12:10am - Check calculation accuracy")
        print("=" * 90)
        
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Test the exact scenarios from the review request
        test_scenarios = [
            {
                'name': '1. Sunday 11:30pm-7:30am Active Shift (CRITICAL FIX)',
                'date': '2025-01-12',  # Sunday
                'start_time': '23:30',
                'end_time': '07:30',
                'expected_pay': 352.00,
                'description': 'Should be $352.00 (0.5h Sunday $74 + 7.5h Monday $42)'
            },
            {
                'name': '2. Midnight-start shift 00:00-08:00 (CRITICAL FIX)',
                'date': '2025-01-13',  # Monday (starts at midnight)
                'start_time': '00:00',
                'end_time': '08:00',
                'expected_pay': 336.00,
                'description': 'Should be $336.00 (8h × $42 weekday_day)'
            },
            {
                'name': '3. Friday 11:30pm-7:30am (SHOULD STILL WORK)',
                'date': '2025-01-10',  # Friday
                'start_time': '23:30',
                'end_time': '07:30',
                'expected_pay': 453.50,
                'description': 'Should be $453.50 (0.5h Friday evening $44.50 + 7.5h Saturday $57.50)'
            },
            {
                'name': '4. Saturday 11:30pm-7:30am (SHOULD STILL WORK)',
                'date': '2025-01-11',  # Saturday
                'start_time': '23:30',
                'end_time': '07:30',
                'expected_pay': 583.75,
                'description': 'Should be $583.75 (0.5h Saturday $57.50 + 7.5h Sunday $74.00)'
            },
            {
                'name': '5. Very short cross-midnight 11:50pm-12:10am',
                'date': '2025-01-13',  # Monday
                'start_time': '23:50',
                'end_time': '00:10',
                'expected_pay': 14.71,  # Calculated: 10min Monday evening $44.50 + 10min Tuesday day $42.00
                'description': 'Check calculation accuracy for very short cross-midnight shifts'
            }
        ]
        
        print(f"\nRunning {len(test_scenarios)} final verification tests...\n")
        
        # Run each test scenario
        passed_tests = 0
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"📋 Scenario {i}: {scenario['description']}")
            
            success = self.create_and_test_shift(
                scenario['name'],
                scenario['date'],
                scenario['start_time'],
                scenario['end_time'],
                scenario['expected_pay']
            )
            
            if success:
                passed_tests += 1
        
        # Summary
        print(f"\n" + "=" * 90)
        print("📊 FINAL VERIFICATION TEST RESULTS")
        print("=" * 90)
        
        print(f"\n🎯 TEST RESULTS SUMMARY:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"   {i}. {status_icon} {result['name']}")
            if result['status'] == 'FAILED':
                print(f"      Expected: ${result['expected']:.2f}, Actual: ${result['actual']:.2f}")
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Tests passed: {passed_tests}/{len(test_scenarios)}")
        print(f"   Success rate: {passed_tests/len(test_scenarios)*100:.1f}%")
        
        # Critical assessment for the review request
        critical_tests = [0, 1]  # Sunday 11:30pm-7:30am and Midnight-start 00:00-08:00
        critical_passed = sum(1 for i in critical_tests if self.test_results[i]['status'] == 'PASSED')
        
        working_tests = [2, 3]  # Friday and Saturday (should still work)
        working_passed = sum(1 for i in working_tests if self.test_results[i]['status'] == 'PASSED')
        
        print(f"\n🚨 CRITICAL FIXES ASSESSMENT:")
        print(f"   Critical scenarios fixed: {critical_passed}/{len(critical_tests)}")
        if critical_passed == len(critical_tests):
            print(f"   ✅ ALL CRITICAL FIXES WORKING!")
        else:
            print(f"   ❌ CRITICAL ISSUES REMAIN")
        
        print(f"\n✅ PREVIOUSLY WORKING SCENARIOS:")
        print(f"   Still working: {working_passed}/{len(working_tests)}")
        if working_passed == len(working_tests):
            print(f"   ✅ All previously working scenarios still functional")
        else:
            print(f"   ❌ Some previously working scenarios broken")
        
        # Final deployment readiness assessment
        print(f"\n🎯 DEPLOYMENT READINESS:")
        if passed_tests == len(test_scenarios):
            print(f"   🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT!")
            print(f"   ✅ Cross-midnight shift pay calculation fixes verified")
            print(f"   ✅ All scenarios working correctly")
        elif critical_passed == len(critical_tests) and working_passed == len(working_tests):
            print(f"   ✅ CRITICAL FIXES SUCCESSFUL - MINOR ISSUES REMAIN")
            print(f"   ✅ Main functionality restored")
            print(f"   ⚠️  Edge cases may need refinement")
        elif critical_passed > 0:
            print(f"   ⚠️  PARTIAL SUCCESS - CONTINUE DEBUGGING")
            print(f"   🔧 Some critical fixes working, others need attention")
        else:
            print(f"   ❌ CRITICAL FIXES NOT WORKING")
            print(f"   🚨 Major issues remain with cross-midnight calculation logic")
        
        return passed_tests == len(test_scenarios)

def main():
    """Main test execution"""
    tester = FinalVerificationTester()
    success = tester.run_final_verification()
    
    if success:
        print(f"\n🎉 FINAL VERIFICATION SUCCESSFUL!")
        exit(0)
    else:
        print(f"\n❌ FINAL VERIFICATION FAILED - ISSUES REMAIN")
        exit(1)

if __name__ == "__main__":
    main()