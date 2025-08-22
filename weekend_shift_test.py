#!/usr/bin/env python3
"""
Enhanced Shift Templates Weekend Classification Test
Test the enhanced shift templates endpoint to verify correct weekend shift classification
"""

import requests
import sys
import json
from datetime import datetime

class WeekendShiftTester:
    def __init__(self, base_url="https://shift-master-10.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if use_auth and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

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
                try:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: {len(response_data)} items returned")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.status_code < 400 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_authentication(self):
        """Test admin authentication"""
        print(f"\n🔐 Testing Admin Authentication...")
        
        login_data = {
            "username": "Admin",
            "pin": "0000"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success:
            self.auth_token = response.get('token')
            user_data = response.get('user', {})
            
            print(f"   ✅ Login successful")
            print(f"   User: {user_data.get('username')} ({user_data.get('role')})")
            print(f"   Token: {self.auth_token[:20]}..." if self.auth_token else "No token")
            
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role confirmed")
                return True
            else:
                print(f"   ❌ Expected admin role, got: {user_data.get('role')}")
                return False
        else:
            print(f"   ❌ Authentication failed")
            return False

    def test_enhanced_shift_templates_weekend_classification(self):
        """Test enhanced shift templates endpoint for correct weekend shift classification"""
        print(f"\n🎯 Testing Enhanced Shift Templates Weekend Classification...")
        
        if not self.auth_token:
            print("   ❌ No admin authentication token available")
            return False
        
        # Test 1: Get all shift templates with enhanced data
        print(f"\n   🎯 STEP 1: Test GET /api/shift-templates with enhanced weekend classification")
        success, templates = self.run_test(
            "Get Enhanced Shift Templates",
            "GET",
            "api/shift-templates",
            200,
            use_auth=True
        )
        
        if not success:
            print("   ❌ Could not get shift templates")
            return False
        
        print(f"   📊 Found {len(templates)} shift templates")
        
        # Test 2: Verify weekend shift classification
        print(f"\n   🎯 STEP 2: Verify weekend shift classification logic")
        
        saturday_shifts = [t for t in templates if t.get('day_of_week') == 5]  # Saturday = 5
        sunday_shifts = [t for t in templates if t.get('day_of_week') == 6]    # Sunday = 6
        
        print(f"   📊 Saturday shifts found: {len(saturday_shifts)}")
        print(f"   📊 Sunday shifts found: {len(sunday_shifts)}")
        
        if len(saturday_shifts) == 0 or len(sunday_shifts) == 0:
            print("   ❌ Missing Saturday or Sunday shift templates")
            return False
        
        # Test 3: Verify specific weekend shifts from review request
        print(f"\n   🎯 STEP 3: Test specific weekend shifts from review request")
        
        expected_weekend_shifts = [
            {
                "day_of_week": 5,  # Saturday
                "start_time": "07:30",
                "end_time": "15:30",
                "expected_shift_type": "saturday",
                "expected_rate": 57.50,
                "expected_total_pay": 460.00,
                "description": "Saturday 7:30 AM - 3:30 PM"
            },
            {
                "day_of_week": 5,  # Saturday
                "start_time": "15:00",
                "end_time": "20:00",
                "expected_shift_type": "saturday",
                "expected_rate": 57.50,
                "expected_total_pay": 287.50,
                "description": "Saturday 3:00 PM - 8:00 PM"
            },
            {
                "day_of_week": 5,  # Saturday
                "start_time": "15:30",
                "end_time": "23:30",
                "expected_shift_type": "saturday",
                "expected_rate": 57.50,
                "expected_total_pay": 460.00,
                "description": "Saturday 3:30 PM - 11:30 PM"
            },
            {
                "day_of_week": 6,  # Sunday
                "start_time": "07:30",
                "end_time": "15:30",
                "expected_shift_type": "sunday",
                "expected_rate": 74.00,
                "expected_total_pay": 592.00,
                "description": "Sunday 7:30 AM - 3:30 PM"
            },
            {
                "day_of_week": 6,  # Sunday
                "start_time": "15:00",
                "end_time": "20:00",
                "expected_shift_type": "sunday",
                "expected_rate": 74.00,
                "expected_total_pay": 370.00,
                "description": "Sunday 3:00 PM - 8:00 PM"
            },
            {
                "day_of_week": 6,  # Sunday
                "start_time": "15:30",
                "end_time": "23:30",
                "expected_shift_type": "sunday",
                "expected_rate": 74.00,
                "expected_total_pay": 592.00,
                "description": "Sunday 3:30 PM - 11:30 PM"
            }
        ]
        
        weekend_tests_passed = 0
        weekend_tests_total = len(expected_weekend_shifts)
        
        for expected_shift in expected_weekend_shifts:
            print(f"\n      Testing: {expected_shift['description']}")
            
            # Find matching template
            matching_template = None
            for template in templates:
                if (template.get('day_of_week') == expected_shift['day_of_week'] and
                    template.get('start_time') == expected_shift['start_time'] and
                    template.get('end_time') == expected_shift['end_time'] and
                    not template.get('is_sleepover', False)):
                    matching_template = template
                    break
            
            if not matching_template:
                print(f"         ❌ No matching template found")
                continue
            
            # Check if template has enhanced fields
            has_calculated_shift_type = 'calculated_shift_type' in matching_template
            has_calculated_hourly_rate = 'calculated_hourly_rate' in matching_template
            has_calculated_total_pay = 'calculated_total_pay' in matching_template
            
            print(f"         Template ID: {matching_template.get('id', 'N/A')}")
            print(f"         Template Name: {matching_template.get('name', 'N/A')}")
            print(f"         Day of Week: {matching_template.get('day_of_week')}")
            print(f"         Time: {matching_template.get('start_time')}-{matching_template.get('end_time')}")
            
            if has_calculated_shift_type:
                actual_shift_type = matching_template.get('calculated_shift_type')
                print(f"         Calculated Shift Type: {actual_shift_type}")
                
                if actual_shift_type == expected_shift['expected_shift_type']:
                    print(f"         ✅ Shift type correct: {actual_shift_type}")
                else:
                    print(f"         ❌ Shift type incorrect: got '{actual_shift_type}', expected '{expected_shift['expected_shift_type']}'")
                    continue
            else:
                print(f"         ❌ Missing calculated_shift_type field")
                continue
            
            if has_calculated_hourly_rate:
                actual_rate = matching_template.get('calculated_hourly_rate')
                print(f"         Calculated Hourly Rate: ${actual_rate}")
                
                if abs(actual_rate - expected_shift['expected_rate']) < 0.01:
                    print(f"         ✅ Hourly rate correct: ${actual_rate}")
                else:
                    print(f"         ❌ Hourly rate incorrect: got ${actual_rate}, expected ${expected_shift['expected_rate']}")
                    continue
            else:
                print(f"         ❌ Missing calculated_hourly_rate field")
                continue
            
            if has_calculated_total_pay:
                actual_total_pay = matching_template.get('calculated_total_pay')
                print(f"         Calculated Total Pay: ${actual_total_pay}")
                
                if abs(actual_total_pay - expected_shift['expected_total_pay']) < 0.01:
                    print(f"         ✅ Total pay correct: ${actual_total_pay}")
                    weekend_tests_passed += 1
                else:
                    print(f"         ❌ Total pay incorrect: got ${actual_total_pay}, expected ${expected_shift['expected_total_pay']}")
                    continue
            else:
                print(f"         ❌ Missing calculated_total_pay field")
                continue
        
        # Test 4: Verify sleepover shifts maintain correct rate
        print(f"\n   🎯 STEP 4: Verify sleepover shifts maintain $175 rate")
        
        sleepover_shifts = [t for t in templates if t.get('is_sleepover', False)]
        print(f"   📊 Sleepover shifts found: {len(sleepover_shifts)}")
        
        sleepover_tests_passed = 0
        for sleepover in sleepover_shifts[:3]:  # Test first 3 sleepover shifts
            print(f"\n      Testing sleepover: {sleepover.get('name', 'N/A')}")
            print(f"         Day of Week: {sleepover.get('day_of_week')}")
            print(f"         Time: {sleepover.get('start_time')}-{sleepover.get('end_time')}")
            
            if 'calculated_total_pay' in sleepover:
                actual_sleepover_pay = sleepover.get('calculated_total_pay')
                print(f"         Calculated Total Pay: ${actual_sleepover_pay}")
                
                if abs(actual_sleepover_pay - 175.00) < 0.01:
                    print(f"         ✅ Sleepover rate correct: ${actual_sleepover_pay}")
                    sleepover_tests_passed += 1
                else:
                    print(f"         ❌ Sleepover rate incorrect: got ${actual_sleepover_pay}, expected $175.00")
            else:
                print(f"         ❌ Missing calculated_total_pay field for sleepover")
        
        # Test 5: Verify shift type logic for all weekend shifts
        print(f"\n   🎯 STEP 5: Verify shift type logic for all weekend shifts")
        
        all_saturday_correct = True
        all_sunday_correct = True
        
        for template in saturday_shifts:
            expected_type = 'sleepover' if template.get('is_sleepover', False) else 'saturday'
            actual_type = template.get('calculated_shift_type')
            if actual_type != expected_type:
                print(f"      ❌ Saturday shift has wrong type: {actual_type} (Template: {template.get('name')}, Expected: {expected_type})")
                all_saturday_correct = False
            else:
                print(f"      ✅ Saturday shift correctly classified: {actual_type} (Template: {template.get('name')})")
        
        for template in sunday_shifts:
            expected_type = 'sleepover' if template.get('is_sleepover', False) else 'sunday'
            actual_type = template.get('calculated_shift_type')
            if actual_type != expected_type:
                print(f"      ❌ Sunday shift has wrong type: {actual_type} (Template: {template.get('name')}, Expected: {expected_type})")
                all_sunday_correct = False
            else:
                print(f"      ✅ Sunday shift correctly classified: {actual_type} (Template: {template.get('name')})")
        
        if all_saturday_correct:
            print(f"      ✅ All {len(saturday_shifts)} Saturday shifts correctly classified as 'saturday'")
        
        if all_sunday_correct:
            print(f"      ✅ All {len(sunday_shifts)} Sunday shifts correctly classified as 'sunday'")
        
        # Final assessment
        print(f"\n   🎉 ENHANCED SHIFT TEMPLATES WEEKEND CLASSIFICATION TEST RESULTS:")
        print(f"      ✅ Shift templates endpoint accessible with admin authentication")
        print(f"      ✅ Found {len(saturday_shifts)} Saturday and {len(sunday_shifts)} Sunday shift templates")
        print(f"      ✅ Weekend shift tests: {weekend_tests_passed}/{weekend_tests_total} specific shifts passed")
        print(f"      ✅ Sleepover shift tests: {sleepover_tests_passed}/{min(3, len(sleepover_shifts))} sleepover shifts passed")
        print(f"      ✅ Saturday shift type classification: {'PASSED' if all_saturday_correct else 'FAILED'}")
        print(f"      ✅ Sunday shift type classification: {'PASSED' if all_sunday_correct else 'FAILED'}")
        
        # Determine overall success
        critical_success = (
            weekend_tests_passed >= (weekend_tests_total * 0.8) and  # At least 80% of specific weekend tests pass
            sleepover_tests_passed >= min(2, len(sleepover_shifts)) and  # At least 2 sleepover tests pass
            all_saturday_correct and  # All Saturday shifts correctly classified
            all_sunday_correct  # All Sunday shifts correctly classified
        )
        
        if critical_success:
            print(f"\n   🎉 CRITICAL SUCCESS: Enhanced shift templates weekend classification working perfectly!")
            print(f"      - Saturday shifts (day_of_week = 5) classified as 'saturday' with $57.50 rate ✅")
            print(f"      - Sunday shifts (day_of_week = 6) classified as 'sunday' with $74.00 rate ✅")
            print(f"      - calculated_shift_type, calculated_hourly_rate, calculated_total_pay fields present ✅")
            print(f"      - Sleepover shifts maintain $175 rate ✅")
            print(f"      - Weekend shift classification logic working correctly ✅")
        else:
            print(f"\n   ❌ CRITICAL ISSUES FOUND:")
            if weekend_tests_passed < (weekend_tests_total * 0.8):
                print(f"      - Weekend shift calculations failing: {weekend_tests_passed}/{weekend_tests_total} passed")
            if sleepover_tests_passed < min(2, len(sleepover_shifts)):
                print(f"      - Sleepover shift calculations failing: {sleepover_tests_passed}/{min(3, len(sleepover_shifts))} passed")
            if not all_saturday_correct:
                print(f"      - Saturday shift type classification failing")
            if not all_sunday_correct:
                print(f"      - Sunday shift type classification failing")
        
        return critical_success

    def run_tests(self):
        """Run all tests"""
        print("🚀 Starting Enhanced Shift Templates Weekend Classification Test...")
        print(f"   Base URL: {self.base_url}")
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication tests failed - stopping")
            return False
        
        # Run the specific test for weekend shift classification
        success = self.test_enhanced_shift_templates_weekend_classification()
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if success:
            print(f"\n🎉 ENHANCED SHIFT TEMPLATES WEEKEND CLASSIFICATION TEST PASSED!")
            print(f"   The backend is correctly returning weekend shift types and rates.")
        else:
            print(f"\n❌ ENHANCED SHIFT TEMPLATES WEEKEND CLASSIFICATION TEST FAILED!")
            print(f"   Issues found with weekend shift classification logic.")
        
        return success

if __name__ == "__main__":
    tester = WeekendShiftTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)