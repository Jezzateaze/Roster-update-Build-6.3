#!/usr/bin/env python3
"""
Focused test for roster update endpoint overlap handling
Testing the specific review request requirements:
1. Test Shift Update with Overlap Control
2. Test 2:1 Shift Functionality  
3. Overlap Detection Bypass
"""

import requests
import sys
import json
from datetime import datetime

class OverlapHandlingTester:
    def __init__(self, base_url="https://shift-master-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.staff_data = []

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
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
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

    def get_staff_data(self):
        """Get staff data for testing"""
        success, response = self.run_test(
            "Get Staff Data",
            "GET",
            "api/staff",
            200
        )
        if success:
            self.staff_data = response
            print(f"   Found {len(response)} staff members")
        return success

    def test_roster_update_overlap_handling(self):
        """Test roster update endpoint specifically for overlap handling as requested"""
        print(f"\n🎯 Testing Roster Update Endpoint Overlap Handling...")
        
        # Test date for overlap testing
        test_date = "2025-12-20"
        
        # Clear any existing shifts for this month first
        success, response = self.run_test(
            "Clear Roster for December 2025",
            "DELETE",
            "api/roster/month/2025-12",
            200
        )
        
        if success:
            print(f"   ✅ Cleared existing roster for December 2025")
        
        # Step 1: Create an initial roster entry to update
        initial_shift = {
            "id": "",  # Will be auto-generated
            "date": test_date,
            "shift_template_id": "test-update-overlap-1",
            "staff_id": None,
            "staff_name": None,
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "allow_overlap": False,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_shift = self.run_test(
            "Create Initial Shift for Update Testing",
            "POST",
            "api/roster/add-shift",
            200,
            data=initial_shift
        )
        
        if not success or 'id' not in created_shift:
            print("   ⚠️  Could not create initial shift for update testing")
            return False
        
        shift_id = created_shift['id']
        print(f"   ✅ Created initial shift with ID: {shift_id}")
        
        # Step 2: Create a conflicting shift to test overlap detection
        conflicting_shift = {
            "id": "",
            "date": test_date,
            "shift_template_id": "test-update-overlap-conflict",
            "staff_id": None,
            "staff_name": None,
            "start_time": "15:00",  # Overlaps with initial shift
            "end_time": "20:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "allow_overlap": True,  # Allow this overlap for testing purposes
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_conflict = self.run_test(
            "Create Conflicting Shift",
            "POST",
            "api/roster/add-shift",
            200,
            data=conflicting_shift
        )
        
        if not success:
            print("   ⚠️  Could not create conflicting shift")
            return False
        
        print(f"   ✅ Created conflicting shift: {conflicting_shift['start_time']}-{conflicting_shift['end_time']}")
        
        # Step 3: Test updating shift without allow_overlap (should fail)
        updated_shift_no_overlap = {
            **created_shift,
            "start_time": "14:00",  # Would overlap with conflicting shift
            "end_time": "18:00",
            "allow_overlap": False
        }
        
        success, response = self.run_test(
            "Update Shift Without Allow Overlap (Should Fail)",
            "PUT",
            f"api/roster/{shift_id}",
            409,  # Expect conflict status
            data=updated_shift_no_overlap
        )
        
        if success:  # Success here means we got the expected 409 status
            print(f"   ✅ Overlap correctly detected and prevented without allow_overlap")
        else:
            print(f"   ❌ Overlap detection failed - update was allowed without allow_overlap")
            return False
        
        # Step 4: Test updating shift with allow_overlap=True (should succeed)
        updated_shift_with_overlap = {
            **created_shift,
            "start_time": "14:00",  # Would overlap with conflicting shift
            "end_time": "18:00",
            "allow_overlap": True  # This should bypass overlap detection
        }
        
        success, response = self.run_test(
            "Update Shift With Allow Overlap=True (Should Succeed)",
            "PUT",
            f"api/roster/{shift_id}",
            200,  # Expect success
            data=updated_shift_with_overlap
        )
        
        if success:
            print(f"   ✅ Update succeeded with allow_overlap=True")
            print(f"   Updated shift: {response.get('start_time')}-{response.get('end_time')}")
            print(f"   Allow overlap flag: {response.get('allow_overlap')}")
        else:
            print(f"   ❌ Update failed even with allow_overlap=True")
            return False
        
        # Step 5: Test 2:1 shift functionality with is_2_to_1 field
        # Note: Backend uses "2:1" in shift name, but testing if is_2_to_1 field is accepted
        shift_2_to_1_test = {
            **created_shift,
            "start_time": "16:00",  # Would overlap with conflicting shift
            "end_time": "22:00",
            "is_2_to_1": True,  # Testing if backend accepts this field
            "allow_overlap": True
        }
        
        success, response = self.run_test(
            "Update Shift With is_2_to_1=True and allow_overlap=True",
            "PUT",
            f"api/roster/{shift_id}",
            200,  # Expect success
            data=shift_2_to_1_test
        )
        
        if success:
            print(f"   ✅ Update succeeded with is_2_to_1=True and allow_overlap=True")
            print(f"   Backend accepted is_2_to_1 field: {response.get('is_2_to_1', 'Field not returned')}")
        else:
            print(f"   ❌ Update failed with is_2_to_1=True")
            return False
        
        # Step 6: Test updating shift name to include "2:1" for automatic overlap bypass
        if self.staff_data:
            staff_member = self.staff_data[0]
            shift_with_2_to_1_name = {
                **created_shift,
                "start_time": "13:00",  # Would overlap with conflicting shift
                "end_time": "19:00",
                "staff_id": staff_member['id'],
                "staff_name": f"{staff_member['name']} - 2:1 Support",  # Include "2:1" in name
                "allow_overlap": False  # Test if "2:1" in name bypasses overlap detection
            }
            
            success, response = self.run_test(
                "Update Shift With '2:1' in Staff Name (Should Bypass Overlap)",
                "PUT",
                f"api/roster/{shift_id}",
                200,  # Expect success due to "2:1" in name
                data=shift_with_2_to_1_name
            )
            
            if success:
                print(f"   ✅ Update succeeded with '2:1' in staff name (automatic bypass)")
                print(f"   Staff assignment: {response.get('staff_name')}")
            else:
                print(f"   ❌ Update failed even with '2:1' in staff name")
                return False
        
        return True

    def run_all_tests(self):
        """Run all overlap handling tests"""
        print("🚀 Starting Roster Update Overlap Handling Tests...")
        print(f"   Base URL: {self.base_url}")
        
        # Get staff data first
        if not self.get_staff_data():
            print("   ⚠️  Could not get staff data, some tests may be limited")
        
        # Run the focused overlap handling test
        success = self.test_roster_update_overlap_handling()
        
        # Print final results
        print(f"\n🏁 Testing Complete!")
        print(f"   Tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success:
            print("   🎉 All overlap handling tests passed!")
            return True
        else:
            print(f"   ⚠️  Some overlap handling tests failed")
            return False

def main():
    print("🎯 FOCUSED TEST: Roster Update Endpoint Overlap Handling")
    print("=" * 60)
    print("Testing specific review request requirements:")
    print("1. Test Shift Update with Overlap Control")
    print("2. Test 2:1 Shift Functionality")
    print("3. Overlap Detection Bypass")
    print("=" * 60)
    
    tester = OverlapHandlingTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())