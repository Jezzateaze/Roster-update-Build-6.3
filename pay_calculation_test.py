#!/usr/bin/env python3
"""
CRITICAL PAY CALCULATION BUG TEST
Focus: 12:00PM-8:00PM shifts should calculate at DAY rate ($336) not EVENING rate ($356)

This test specifically addresses the review request to verify the pay calculation fix
after proper backend restart.
"""

import requests
import sys
import json
from datetime import datetime

class PayCalculationTester:
    def __init__(self, base_url="https://care-scheduler-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_tests_passed = 0
        self.critical_tests_total = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.status_code < 400 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_critical_pay_calculation_bug_fix(self):
        """
        CRITICAL TEST: Verify 12:00PM-8:00PM pay calculation bug is fixed
        
        Expected behavior:
        - 12:00PM-8:00PM weekday shifts should use DAY rate ($42/hr) = $336 total
        - 12:00PM-8:01PM weekday shifts should use EVENING rate ($44.50/hr) = $356.89 total
        - 12:00PM-7:59PM weekday shifts should use DAY rate ($42/hr) = $335.16 total
        """
        print(f"\n🎯 CRITICAL PAY CALCULATION BUG FIX TEST")
        print(f"=" * 60)
        print(f"Testing the specific 12:00PM-8:00PM pay calculation issue")
        print(f"Expected: 8 hours × $42/hr = $336.00 (DAY rate, NOT evening rate)")
        
        # Test cases focusing on the critical 8:00 PM boundary
        critical_test_cases = [
            {
                "name": "🎯 CRITICAL: 12:00PM-8:00PM Monday (EXACT boundary test)",
                "date": "2025-01-06",  # Monday
                "start_time": "12:00",
                "end_time": "20:00",
                "expected_hours": 8.0,
                "expected_rate": 42.00,  # DAY rate (NOT evening)
                "expected_pay": 336.00,  # 8 * 42.00
                "shift_type": "WEEKDAY_DAY",
                "is_critical": True,
                "description": "This is the EXACT case reported in the bug - should be DAY rate"
            },
            {
                "name": "🎯 EDGE CASE: 12:00PM-7:59PM Monday (1 minute before boundary)",
                "date": "2025-01-06",  # Monday
                "start_time": "12:00",
                "end_time": "19:59",
                "expected_hours": 7.98,  # 7 hours 59 minutes
                "expected_rate": 42.00,  # DAY rate
                "expected_pay": 335.16,  # 7.98 * 42.00
                "shift_type": "WEEKDAY_DAY",
                "is_critical": True,
                "description": "Should be DAY rate - ends before 8:00 PM"
            },
            {
                "name": "🎯 EDGE CASE: 12:00PM-8:01PM Monday (1 minute after boundary)",
                "date": "2025-01-06",  # Monday
                "start_time": "12:00",
                "end_time": "20:01",
                "expected_hours": 8.02,  # 8 hours 1 minute
                "expected_rate": 44.50,  # EVENING rate
                "expected_pay": 356.89,  # 8.02 * 44.50
                "shift_type": "WEEKDAY_EVENING",
                "is_critical": True,
                "description": "Should be EVENING rate - extends past 8:00 PM"
            }
        ]
        
        self.critical_tests_total = len(critical_test_cases)
        
        print(f"\nRunning {self.critical_tests_total} critical test cases...")
        
        for i, test_case in enumerate(critical_test_cases):
            print(f"\n" + "="*50)
            print(f"TEST {i+1}/{self.critical_tests_total}: {test_case['name']}")
            print(f"Description: {test_case['description']}")
            print(f"Expected: {test_case['expected_hours']}h × ${test_case['expected_rate']}/hr = ${test_case['expected_pay']}")
            
            # Create roster entry with FRESH data (as requested)
            roster_entry = {
                "id": "",  # Will be auto-generated
                "date": test_case["date"],
                "shift_template_id": f"critical-test-{i+1}",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None,
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
            
            success, response = self.run_test(
                f"Create NEW roster entry: {test_case['start_time']}-{test_case['end_time']}",
                "POST",
                "api/roster",
                200,
                data=roster_entry
            )
            
            if success:
                # Extract calculation results
                hours_worked = response.get('hours_worked', 0)
                total_pay = response.get('total_pay', 0)
                base_pay = response.get('base_pay', 0)
                
                print(f"\n📊 CALCULATION RESULTS:")
                print(f"   Hours worked: {hours_worked} (expected: {test_case['expected_hours']})")
                print(f"   Total pay: ${total_pay} (expected: ${test_case['expected_pay']})")
                print(f"   Base pay: ${base_pay}")
                
                # Verify calculations with tolerance for floating point precision
                hours_correct = abs(hours_worked - test_case['expected_hours']) < 0.01
                pay_correct = abs(total_pay - test_case['expected_pay']) < 0.01
                
                if hours_correct and pay_correct:
                    print(f"   ✅ CALCULATION CORRECT!")
                    print(f"   ✅ Shift type determination: {test_case['shift_type']}")
                    self.critical_tests_passed += 1
                    
                    if test_case['is_critical']:
                        print(f"   🎉 CRITICAL TEST PASSED - Bug fix is working!")
                else:
                    print(f"   ❌ CALCULATION INCORRECT!")
                    
                    if not hours_correct:
                        print(f"      Hours mismatch: got {hours_worked}, expected {test_case['expected_hours']}")
                    
                    if not pay_correct:
                        print(f"      Pay mismatch: got ${total_pay}, expected ${test_case['expected_pay']}")
                        
                        # Determine what rate was actually used
                        if hours_worked > 0:
                            actual_rate = total_pay / hours_worked
                            print(f"      Actual rate used: ${actual_rate:.2f}/hr")
                            
                            if abs(actual_rate - 44.50) < 0.01:
                                print(f"      🚨 BUG DETECTED: Using EVENING rate (${actual_rate:.2f}) instead of DAY rate ($42.00)")
                            elif abs(actual_rate - 42.00) < 0.01:
                                print(f"      ✅ Using correct DAY rate (${actual_rate:.2f})")
                            else:
                                print(f"      ⚠️  Using unexpected rate: ${actual_rate:.2f}")
                    
                    if test_case['is_critical']:
                        print(f"   🚨 CRITICAL TEST FAILED - Bug fix is NOT working!")
                
                # Store entry ID for potential cleanup
                entry_id = response.get('id')
                if entry_id:
                    print(f"   Created entry ID: {entry_id}")
                    
            else:
                print(f"   ❌ FAILED TO CREATE ROSTER ENTRY")
                if test_case['is_critical']:
                    print(f"   🚨 CRITICAL TEST FAILED - Could not create test data")
        
        # Summary
        print(f"\n" + "="*60)
        print(f"🎯 CRITICAL PAY CALCULATION TEST SUMMARY")
        print(f"="*60)
        print(f"Critical tests passed: {self.critical_tests_passed}/{self.critical_tests_total}")
        print(f"Total tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.critical_tests_passed == self.critical_tests_total:
            print(f"✅ ALL CRITICAL TESTS PASSED!")
            print(f"✅ 12:00PM-8:00PM pay calculation bug fix is WORKING correctly")
            print(f"✅ Backend is correctly applying DAY rate ($42/hr) for shifts ending AT 8:00 PM")
            print(f"✅ Backend is correctly applying EVENING rate ($44.50/hr) for shifts ending AFTER 8:00 PM")
            return True
        else:
            failed_tests = self.critical_tests_total - self.critical_tests_passed
            print(f"❌ {failed_tests} CRITICAL TESTS FAILED!")
            print(f"🚨 12:00PM-8:00PM pay calculation bug fix is NOT working correctly")
            print(f"🚨 Backend may still be applying EVENING rate instead of DAY rate")
            print(f"🚨 IMMEDIATE ACTION REQUIRED: Backend logic needs to be fixed")
            return False

    def test_additional_boundary_cases(self):
        """Test additional boundary cases around the 8:00 PM threshold"""
        print(f"\n🔍 ADDITIONAL BOUNDARY CASE TESTING")
        print(f"Testing various shift patterns around the 8:00 PM boundary")
        
        boundary_test_cases = [
            {
                "name": "Morning to exactly 8:00 PM",
                "date": "2025-01-07",  # Tuesday
                "start_time": "08:00",
                "end_time": "20:00",
                "expected_rate": 42.00,  # DAY rate
                "expected_hours": 12.0,
                "expected_pay": 504.00
            },
            {
                "name": "Afternoon to exactly 8:00 PM",
                "date": "2025-01-08",  # Wednesday
                "start_time": "14:00",
                "end_time": "20:00",
                "expected_rate": 42.00,  # DAY rate
                "expected_hours": 6.0,
                "expected_pay": 252.00
            },
            {
                "name": "Evening shift starting at 8:00 PM",
                "date": "2025-01-09",  # Thursday
                "start_time": "20:00",
                "end_time": "22:00",
                "expected_rate": 44.50,  # EVENING rate
                "expected_hours": 2.0,
                "expected_pay": 89.00
            },
            {
                "name": "Late evening shift starting after 8:00 PM",
                "date": "2025-01-10",  # Friday
                "start_time": "21:00",
                "end_time": "23:00",
                "expected_rate": 44.50,  # EVENING rate
                "expected_hours": 2.0,
                "expected_pay": 89.00
            }
        ]
        
        boundary_tests_passed = 0
        
        for test_case in boundary_test_cases:
            print(f"\n📋 Testing: {test_case['name']}")
            print(f"   {test_case['start_time']}-{test_case['end_time']} on {test_case['date']}")
            
            roster_entry = {
                "id": "",
                "date": test_case["date"],
                "shift_template_id": f"boundary-test",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None,
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
            
            success, response = self.run_test(
                f"Create boundary test shift",
                "POST",
                "api/roster",
                200,
                data=roster_entry
            )
            
            if success:
                hours_worked = response.get('hours_worked', 0)
                total_pay = response.get('total_pay', 0)
                
                hours_correct = abs(hours_worked - test_case['expected_hours']) < 0.01
                pay_correct = abs(total_pay - test_case['expected_pay']) < 0.01
                
                if hours_correct and pay_correct:
                    print(f"   ✅ Correct: {hours_worked}h × ${test_case['expected_rate']}/hr = ${total_pay}")
                    boundary_tests_passed += 1
                else:
                    print(f"   ❌ Incorrect: {hours_worked}h, ${total_pay} (expected: {test_case['expected_hours']}h, ${test_case['expected_pay']})")
                    if hours_worked > 0:
                        actual_rate = total_pay / hours_worked
                        print(f"      Actual rate: ${actual_rate:.2f}/hr (expected: ${test_case['expected_rate']}/hr)")
        
        print(f"\n📊 Boundary tests passed: {boundary_tests_passed}/{len(boundary_test_cases)}")
        return boundary_tests_passed == len(boundary_test_cases)

    def run_all_tests(self):
        """Run all pay calculation tests"""
        print(f"🚀 STARTING CRITICAL PAY CALCULATION BUG VERIFICATION")
        print(f"Focus: 12:00PM-8:00PM shifts should calculate at DAY rate ($336) not EVENING rate ($356)")
        print(f"Backend URL: {self.base_url}")
        print(f"=" * 80)
        
        # Test 1: Critical bug fix verification
        critical_success = self.test_critical_pay_calculation_bug_fix()
        
        # Test 2: Additional boundary cases
        boundary_success = self.test_additional_boundary_cases()
        
        # Final summary
        print(f"\n" + "="*80)
        print(f"🏁 FINAL TEST RESULTS")
        print(f"="*80)
        print(f"Total tests run: {self.tests_run}")
        print(f"Total tests passed: {self.tests_passed}")
        print(f"Critical tests passed: {self.critical_tests_passed}/{self.critical_tests_total}")
        
        if critical_success:
            print(f"✅ CRITICAL BUG FIX VERIFICATION: PASSED")
            print(f"✅ 12:00PM-8:00PM shifts correctly calculate at DAY rate ($336)")
            print(f"✅ Backend restart and fix are working correctly")
        else:
            print(f"❌ CRITICAL BUG FIX VERIFICATION: FAILED")
            print(f"🚨 12:00PM-8:00PM shifts still calculating incorrectly")
            print(f"🚨 Backend fix is NOT working - immediate attention required")
        
        if boundary_success:
            print(f"✅ BOUNDARY CASE TESTING: PASSED")
        else:
            print(f"⚠️  BOUNDARY CASE TESTING: Some issues detected")
        
        overall_success = critical_success and boundary_success
        
        if overall_success:
            print(f"\n🎉 ALL TESTS PASSED - PAY CALCULATION BUG IS FIXED!")
        else:
            print(f"\n🚨 TESTS FAILED - PAY CALCULATION BUG STILL EXISTS!")
        
        return overall_success

if __name__ == "__main__":
    tester = PayCalculationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)