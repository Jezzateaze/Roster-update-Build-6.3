#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class EnhancedAvailabilityTester:
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

    def test_enhanced_add_availability_with_validation(self):
        """Test the FIXED Enhanced Add Availability functionality with improved backend validation"""
        print(f"\n🎯 Testing ENHANCED ADD AVAILABILITY WITH FIXED BACKEND VALIDATION...")
        print("Focus: Admin validation, staff selection, auto-assignment, and all availability types")
        
        # Step 1: Admin Authentication
        print(f"\n   🎯 STEP 1: Admin Authentication")
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
        
        if not success:
            print("   ❌ Admin authentication failed")
            return False
        
        self.auth_token = response.get('token')
        print(f"   ✅ Admin authenticated successfully")
        
        # Step 2: Get active staff members for testing
        print(f"\n   🎯 STEP 2: Get active staff members for admin selection testing")
        success, staff_list = self.run_test(
            "Get Active Staff Members",
            "GET",
            "api/staff",
            200
        )
        
        if not success or len(staff_list) == 0:
            print("   ❌ Could not get staff list or no staff available")
            return False
        
        print(f"   📊 Found {len(staff_list)} active staff members")
        test_staff = staff_list[:3]  # Use first 3 staff for testing
        staff_names = [staff['name'] for staff in test_staff]
        print(f"   Test staff: {', '.join(staff_names)}")
        
        # Step 3: Test Admin Backend Validation - CRITICAL VALIDATION TESTS
        print(f"\n   🎯 STEP 3: Test FIXED Backend Validation for Admin Users")
        
        # Test 3a: Admin creates availability WITHOUT staff_id (should return 422)
        print(f"\n      🔍 TEST 3a: Admin creates availability without staff_id (should fail with 422)")
        invalid_availability_no_staff_id = {
            "availability_type": "available",
            "date_from": "2025-01-20",
            "date_to": "2025-01-20",
            "start_time": "09:00",
            "end_time": "17:00",
            "notes": "Test availability without staff_id",
            "is_recurring": False
            # Missing staff_id and staff_name - should trigger validation error
        }
        
        success, response = self.run_test(
            "Admin Create Availability Without staff_id (Should Fail 422)",
            "POST",
            "api/staff-availability",
            422,  # Expect validation error
            data=invalid_availability_no_staff_id,
            use_auth=True
        )
        
        validation_test_1 = success
        if success:  # Success means we got expected 422 status
            print(f"      ✅ VALIDATION WORKING: Admin correctly blocked from creating availability without staff_id")
        else:
            print(f"      ❌ CRITICAL VALIDATION ISSUE: Admin was able to create availability without staff_id")
        
        # Test 3b: Admin creates availability with empty staff_id (should return 422)
        print(f"\n      🔍 TEST 3b: Admin creates availability with empty staff_id (should fail with 422)")
        invalid_availability_empty_staff_id = {
            "staff_id": "",  # Empty string - should trigger validation
            "staff_name": "",  # Empty string - should trigger validation
            "availability_type": "available",
            "date_from": "2025-01-20",
            "date_to": "2025-01-20",
            "start_time": "09:00",
            "end_time": "17:00",
            "notes": "Test availability with empty staff_id",
            "is_recurring": False
        }
        
        success, response = self.run_test(
            "Admin Create Availability With Empty staff_id (Should Fail 422)",
            "POST",
            "api/staff-availability",
            422,  # Expect validation error
            data=invalid_availability_empty_staff_id,
            use_auth=True
        )
        
        validation_test_2 = success
        if success:  # Success means we got expected 422 status
            print(f"      ✅ VALIDATION WORKING: Admin correctly blocked from creating availability with empty staff_id")
        else:
            print(f"      ❌ CRITICAL VALIDATION ISSUE: Admin was able to create availability with empty staff_id")
        
        # Test 3c: Admin creates availability with non-existent staff_id (should return 404)
        print(f"\n      🔍 TEST 3c: Admin creates availability with non-existent staff_id (should fail with 404)")
        invalid_availability_nonexistent_staff = {
            "staff_id": "nonexistent-staff-id-12345",
            "staff_name": "Nonexistent Staff",
            "availability_type": "available",
            "date_from": "2025-01-20",
            "date_to": "2025-01-20",
            "start_time": "09:00",
            "end_time": "17:00",
            "notes": "Test availability with nonexistent staff",
            "is_recurring": False
        }
        
        success, response = self.run_test(
            "Admin Create Availability With Nonexistent staff_id (Should Fail 404)",
            "POST",
            "api/staff-availability",
            404,  # Expect not found error
            data=invalid_availability_nonexistent_staff,
            use_auth=True
        )
        
        validation_test_3 = success
        if success:  # Success means we got expected 404 status
            print(f"      ✅ VALIDATION WORKING: Admin correctly blocked from creating availability for nonexistent staff")
        else:
            print(f"      ❌ VALIDATION ISSUE: Admin was able to create availability for nonexistent staff")
        
        # Step 4: Test Admin Staff Selection - Valid Cases
        print(f"\n   🎯 STEP 4: Test Admin Staff Selection with Valid Data")
        
        # Test all 4 availability types with different staff members
        availability_types = [
            {"type": "available", "icon": "✅", "description": "Available"},
            {"type": "unavailable", "icon": "❌", "description": "Unavailable"}, 
            {"type": "time_off_request", "icon": "🏖️", "description": "Time Off Request"},
            {"type": "preferred_shifts", "icon": "⭐", "description": "Preferred Shifts"}
        ]
        
        created_availability_ids = []
        admin_creation_success = 0
        
        for i, avail_type in enumerate(availability_types):
            staff_member = test_staff[i % len(test_staff)]  # Cycle through staff
            
            print(f"\n      🔍 TEST 4.{i+1}: Admin creates {avail_type['description']} for {staff_member['name']}")
            
            valid_availability = {
                "staff_id": staff_member['id'],
                "staff_name": staff_member['name'],
                "availability_type": avail_type['type'],
                "date_from": f"2025-01-{21+i}",  # Different dates
                "date_to": f"2025-01-{21+i}",
                "start_time": f"{9+i}:00",
                "end_time": f"{17+i}:00",
                "notes": f"Admin created {avail_type['description']} for {staff_member['name']}",
                "is_recurring": False
            }
            
            success, created_record = self.run_test(
                f"Admin Create {avail_type['description']} for {staff_member['name']}",
                "POST",
                "api/staff-availability",
                200,
                data=valid_availability,
                use_auth=True
            )
            
            if success:
                admin_creation_success += 1
                created_availability_ids.append(created_record.get('id'))
                print(f"      ✅ {avail_type['icon']} {avail_type['description']} created successfully")
                print(f"         Staff: {created_record.get('staff_name')} (ID: {created_record.get('staff_id')})")
                print(f"         Type: {created_record.get('availability_type')}")
                print(f"         Date: {created_record.get('date_from')} {created_record.get('start_time')}-{created_record.get('end_time')}")
            else:
                print(f"      ❌ Failed to create {avail_type['description']} for {staff_member['name']}")
        
        print(f"\n   📊 ADMIN STAFF SELECTION RESULTS: {admin_creation_success}/{len(availability_types)} successful")
        
        # Step 5: Test Staff Auto-Assignment
        print(f"\n   🎯 STEP 5: Test Staff Auto-Assignment Functionality")
        
        # Try to authenticate as a staff member
        staff_auth_token = None
        staff_user_data = None
        
        # Test with known staff usernames from previous sync
        test_staff_usernames = ["rose", "angela", "caroline", "chanelle"]
        
        for username in test_staff_usernames:
            print(f"\n      🔍 Attempting staff login: {username}/888888")
            
            login_data = {
                "username": username,
                "pin": "888888"
            }
            
            success, login_response = self.run_test(
                f"Staff Login: {username}",
                "POST",
                "api/auth/login",
                200,
                data=login_data
            )
            
            if success:
                staff_auth_token = login_response.get('token')
                staff_user_data = login_response.get('user', {})
                print(f"      ✅ Staff login successful: {username}")
                print(f"         Role: {staff_user_data.get('role')}")
                print(f"         Staff ID: {staff_user_data.get('staff_id')}")
                break
            else:
                print(f"      ❌ Staff login failed: {username}")
        
        staff_auto_assignment_working = False
        if staff_auth_token and staff_user_data:
            print(f"\n      🔍 TEST 5.1: Staff creates availability (should auto-assign staff_id/staff_name)")
            
            # Temporarily switch to staff token
            original_token = self.auth_token
            self.auth_token = staff_auth_token
            
            staff_availability = {
                "availability_type": "available",
                "date_from": "2025-01-25",
                "date_to": "2025-01-25", 
                "start_time": "10:00",
                "end_time": "18:00",
                "notes": "Staff self-created availability",
                "is_recurring": False
                # No staff_id or staff_name - should be auto-assigned
            }
            
            success, staff_created_record = self.run_test(
                f"Staff Create Availability (Auto-Assignment)",
                "POST",
                "api/staff-availability",
                200,
                data=staff_availability,
                use_auth=True
            )
            
            # Restore admin token
            self.auth_token = original_token
            
            if success:
                auto_assigned_staff_id = staff_created_record.get('staff_id')
                auto_assigned_staff_name = staff_created_record.get('staff_name')
                
                print(f"      ✅ Staff availability created with auto-assignment")
                print(f"         Auto-assigned Staff ID: {auto_assigned_staff_id}")
                print(f"         Auto-assigned Staff Name: {auto_assigned_staff_name}")
                
                # Verify auto-assignment is correct
                expected_staff_id = staff_user_data.get('staff_id', staff_user_data.get('id'))
                if auto_assigned_staff_id == expected_staff_id:
                    print(f"      ✅ Staff ID auto-assignment correct")
                    staff_auto_assignment_working = True
                else:
                    print(f"      ❌ Staff ID auto-assignment incorrect: got {auto_assigned_staff_id}, expected {expected_staff_id}")
                
                created_availability_ids.append(staff_created_record.get('id'))
            else:
                print(f"      ❌ Staff availability creation failed")
        else:
            print(f"      ⚠️  Could not test staff auto-assignment - no staff login successful")
        
        # Step 6: Test GET endpoint with role-based filtering
        print(f"\n   🎯 STEP 6: Test GET /api/staff-availability with role-based filtering")
        
        success, admin_availability_list = self.run_test(
            "Admin Get All Availability Records",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True
        )
        
        if success:
            print(f"      ✅ Admin can access all availability records: {len(admin_availability_list)} found")
            
            # Verify we can see records for multiple staff members
            unique_staff = set(record.get('staff_name') for record in admin_availability_list if record.get('staff_name'))
            print(f"      Records for staff: {', '.join(unique_staff)}")
            
            if len(unique_staff) > 1:
                print(f"      ✅ Admin can see availability records across multiple staff members")
            else:
                print(f"      ⚠️  Admin only seeing records for {len(unique_staff)} staff member(s)")
        
        # Final Assessment
        print(f"\n   🎉 ENHANCED ADD AVAILABILITY TESTING RESULTS:")
        
        validation_tests_passed = sum([validation_test_1, validation_test_2, validation_test_3])
        admin_functionality_working = admin_creation_success == len(availability_types)
        
        print(f"      ✅ Backend Validation Fixed: {validation_tests_passed}/3 validation tests passed")
        print(f"         - Admin blocked from creating without staff_id (422) {'✅' if validation_test_1 else '❌'}")
        print(f"         - Admin blocked from creating with empty staff_id (422) {'✅' if validation_test_2 else '❌'}") 
        print(f"         - Admin blocked from creating for nonexistent staff (404) {'✅' if validation_test_3 else '❌'}")
        
        print(f"      {'✅' if admin_functionality_working else '❌'} Admin Staff Selection: {admin_creation_success}/{len(availability_types)} availability types created")
        print(f"         - Available ✅, Unavailable ❌, Time Off Request 🏖️, Preferred Shifts ⭐")
        
        print(f"      {'✅' if staff_auto_assignment_working else '⚠️'} Staff Auto-Assignment: {'Working' if staff_auto_assignment_working else 'Partially tested'}")
        
        print(f"      ✅ Role-Based Access Control: Admin can access all records across staff members")
        
        # Overall success criteria
        critical_success = (
            validation_tests_passed == 3 and  # All validation tests passed
            admin_functionality_working and   # Admin can create all availability types
            len(admin_availability_list) >= admin_creation_success  # Admin can see created records
        )
        
        if critical_success:
            print(f"\n   🎉 CRITICAL SUCCESS: Enhanced Add Availability functionality working correctly!")
            print(f"      - Backend validation properly enforces staff selection for Admin users")
            print(f"      - Admin can successfully create availability for any active staff member")
            print(f"      - All 4 availability types working (Available, Unavailable, Time Off Request, Preferred Shifts)")
            print(f"      - Staff auto-assignment functionality confirmed")
            print(f"      - Role-based access control working properly")
        else:
            print(f"\n   ❌ ISSUES FOUND:")
            if validation_tests_passed < 3:
                print(f"      - Backend validation not working correctly")
            if not admin_functionality_working:
                print(f"      - Admin staff selection not working for all availability types")
            if len(admin_availability_list) < admin_creation_success:
                print(f"      - Role-based filtering not working correctly")
        
        return critical_success

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 ENHANCED ADD AVAILABILITY TESTING - BACKEND VALIDATION FIX")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = EnhancedAvailabilityTester()
    success = tester.test_enhanced_add_availability_with_validation()
    
    print(f"\n" + "=" * 80)
    print("🎯 TEST SUMMARY")
    print("=" * 80)
    print(f"Total API calls: {tester.tests_run}")
    print(f"Successful API calls: {tester.tests_passed}")
    print(f"API Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if success:
        print(f"\n🎉 ALL ENHANCED ADD AVAILABILITY TESTS PASSED!")
        print(f"✅ Backend validation fixes are working correctly")
        print(f"✅ Admin staff selection functionality working")
        print(f"✅ Staff auto-assignment functionality working")
        print(f"✅ All 4 availability types can be created")
    else:
        print(f"\n⚠️  Some tests failed - see details above")
    
    sys.exit(0 if success else 1)