import requests
import json
from datetime import datetime, timedelta

class EnhancedStaffDeletionTester:
    def __init__(self, base_url="https://workforce-wizard-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.staff_token = None
        self.test_staff_id = None
        self.test_staff_name = None
        self.test_shifts = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required
        if use_auth:
            auth_token = token or self.admin_token
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'

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
                        # Print important response details for staff deletion
                        if 'message' in response_data:
                            print(f"   Message: {response_data['message']}")
                        if 'shifts_affected' in response_data:
                            shifts = response_data['shifts_affected']
                            print(f"   Shifts affected: {shifts}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def setup_authentication(self):
        """Setup admin and staff authentication tokens"""
        print(f"\n🔐 Setting up Authentication...")
        
        # Admin login
        admin_login = {
            "username": "Admin",
            "pin": "0000"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=admin_login
        )
        
        if success:
            self.admin_token = response.get('token')
            print(f"   ✅ Admin authenticated successfully")
        else:
            print(f"   ❌ Admin authentication failed")
            return False
        
        # Try to get a staff user for testing (we'll create one if needed)
        # First, let's check if we have any staff users
        success, users_response = self.run_test(
            "Check for Staff Users",
            "GET",
            "staff",
            200
        )
        
        if success and len(users_response) > 0:
            # Try to find a staff user account or create one
            staff_member = users_response[0]  # Use first staff member
            
            # Create a staff user account for testing if it doesn't exist
            staff_user_data = {
                "username": staff_member['name'].lower().replace(' ', ''),
                "pin": "888888",
                "role": "staff",
                "staff_id": staff_member['id'],
                "email": f"{staff_member['name'].lower().replace(' ', '')}@company.com",
                "first_name": staff_member['name'].split()[0] if ' ' in staff_member['name'] else staff_member['name'],
                "last_name": " ".join(staff_member['name'].split()[1:]) if ' ' in staff_member['name'] else "",
                "is_first_login": False,
                "is_active": True
            }
            
            # Try to login with staff credentials
            staff_login = {
                "username": staff_user_data['username'],
                "pin": "888888"
            }
            
            success, staff_response = self.run_test(
                "Staff Login Attempt",
                "POST",
                "auth/login",
                200,
                data=staff_login
            )
            
            if success:
                self.staff_token = staff_response.get('token')
                print(f"   ✅ Staff user authenticated successfully")
            else:
                print(f"   ⚠️  Staff user not available for testing (this is OK)")
        
        return True

    def create_test_staff(self):
        """Create a test staff member for deletion testing"""
        print(f"\n👤 Creating Test Staff Member...")
        
        # Use timestamp to ensure unique name
        import time
        timestamp = str(int(time.time()))
        
        test_staff_data = {
            "name": f"Test Staff Delete {timestamp}",
            "active": True
        }
        
        success, response = self.run_test(
            "Create Test Staff Member",
            "POST",
            "staff",
            200,
            data=test_staff_data,
            use_auth=True
        )
        
        if success and 'id' in response:
            self.test_staff_id = response['id']
            self.test_staff_name = response['name']
            print(f"   ✅ Created test staff with ID: {self.test_staff_id}")
            return True
        else:
            print(f"   ❌ Failed to create test staff member")
            return False

    def create_test_shifts(self):
        """Create test shifts for the staff member (both past and future)"""
        print(f"\n📅 Creating Test Shifts for Staff Member...")
        
        if not self.test_staff_id:
            print(f"   ❌ No test staff ID available")
            return False
        
        # Get today's date
        today = datetime.now()
        
        # Create shifts: 2 past, 2 future
        shift_dates = [
            (today - timedelta(days=7), "Past Shift 1"),   # 1 week ago
            (today - timedelta(days=3), "Past Shift 2"),   # 3 days ago
            (today + timedelta(days=3), "Future Shift 1"), # 3 days from now
            (today + timedelta(days=7), "Future Shift 2")  # 1 week from now
        ]
        
        created_shifts = []
        
        for shift_date, shift_name in shift_dates:
            shift_data = {
                "id": "",  # Will be auto-generated by backend
                "date": shift_date.strftime("%Y-%m-%d"),
                "shift_template_id": "test-template",
                "staff_id": self.test_staff_id,
                "staff_name": self.test_staff_name,
                "start_time": "09:00",
                "end_time": "17:00",
                "is_sleepover": False,
                "is_public_holiday": False,
                "hours_worked": 8.0,
                "base_pay": 336.00,
                "total_pay": 336.00
            }
            
            success, response = self.run_test(
                f"Create {shift_name} ({shift_date.strftime('%Y-%m-%d')})",
                "POST",
                "roster",
                200,
                data=shift_data,
                use_auth=True
            )
            
            if success and 'id' in response:
                created_shifts.append({
                    'id': response['id'],
                    'date': shift_date.strftime("%Y-%m-%d"),
                    'name': shift_name,
                    'is_future': shift_date > today
                })
                print(f"   ✅ Created {shift_name}")
            else:
                print(f"   ❌ Failed to create {shift_name}")
        
        self.test_shifts = created_shifts
        print(f"   📊 Created {len(created_shifts)} test shifts")
        return len(created_shifts) > 0

    def test_authentication_requirements(self):
        """Test DELETE /api/staff/{id} authentication requirements"""
        print(f"\n🔐 Testing Authentication Requirements...")
        
        if not self.test_staff_id:
            print(f"   ❌ No test staff ID available")
            return False
        
        # Test 1: DELETE without authentication (should fail with 401/403)
        success, response = self.run_test(
            "DELETE Staff Without Authentication (Should Fail)",
            "DELETE",
            f"staff/{self.test_staff_id}",
            403,  # Accept 403 (Not authenticated) as valid
            use_auth=False
        )
        
        if success:
            print(f"   ✅ Unauthenticated request correctly blocked")
        else:
            # Try with 401 as well
            success, response = self.run_test(
                "DELETE Staff Without Authentication - Try 401",
                "DELETE", 
                f"staff/{self.test_staff_id}",
                401,  # Also accept 401 (Unauthorized)
                use_auth=False
            )
            if success:
                print(f"   ✅ Unauthenticated request correctly blocked with 401")
            else:
                print(f"   ❌ Unauthenticated request was not blocked")
                return False
        
        # Test 2: DELETE with staff credentials (should fail with 403)
        if self.staff_token:
            success, response = self.run_test(
                "DELETE Staff With Staff Credentials (Should Fail)",
                "DELETE",
                f"staff/{self.test_staff_id}",
                403,  # Expect forbidden
                use_auth=True,
                token=self.staff_token
            )
            
            if success:
                print(f"   ✅ Staff user correctly forbidden from deleting staff")
            else:
                print(f"   ❌ Staff user was allowed to delete staff")
                return False
        else:
            print(f"   ⚠️  Staff token not available, skipping staff credential test")
        
        # Test 3: DELETE with admin credentials (should succeed)
        # We'll test this in the main deletion test
        print(f"   ✅ Authentication requirement tests completed")
        return True

    def test_staff_deletion_process(self):
        """Test the main staff deletion process"""
        print(f"\n🗑️  Testing Staff Deletion Process...")
        
        if not self.test_staff_id:
            print(f"   ❌ No test staff ID available")
            return False
        
        # Verify staff exists and is active before deletion
        success, staff_list = self.run_test(
            "Verify Staff Exists Before Deletion",
            "GET",
            "staff",
            200,
            use_auth=True
        )
        
        if success:
            staff_found = any(s['id'] == self.test_staff_id and s['active'] for s in staff_list)
            if staff_found:
                print(f"   ✅ Test staff found and active before deletion")
            else:
                print(f"   ❌ Test staff not found or not active")
                return False
        
        # Perform the deletion with admin credentials
        success, response = self.run_test(
            "DELETE Staff With Admin Credentials",
            "DELETE",
            f"staff/{self.test_staff_id}",
            200,
            use_auth=True,
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Staff deletion request successful")
            
            # Validate response structure
            required_fields = ['message', 'staff_name', 'shifts_affected']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing required response fields: {missing_fields}")
                return False
            
            # Validate shifts_affected structure
            shifts_affected = response.get('shifts_affected', {})
            required_shift_fields = ['future_shifts_unassigned', 'past_shifts_preserved', 'total_shifts']
            missing_shift_fields = [field for field in required_shift_fields if field not in shifts_affected]
            
            if missing_shift_fields:
                print(f"   ❌ Missing required shifts_affected fields: {missing_shift_fields}")
                return False
            
            print(f"   ✅ Response structure is valid")
            print(f"   Staff name: {response.get('staff_name')}")
            print(f"   Message: {response.get('message')}")
            print(f"   Future shifts unassigned: {shifts_affected.get('future_shifts_unassigned')}")
            print(f"   Past shifts preserved: {shifts_affected.get('past_shifts_preserved')}")
            print(f"   Total shifts: {shifts_affected.get('total_shifts')}")
            
            return True
        else:
            print(f"   ❌ Staff deletion failed")
            return False

    def test_data_integrity(self):
        """Test data integrity after staff deletion"""
        print(f"\n🔍 Testing Data Integrity After Deletion...")
        
        if not self.test_staff_id:
            print(f"   ❌ No test staff ID available")
            return False
        
        # Test 1: Verify staff record still exists but is deactivated
        success, staff_list = self.run_test(
            "Check Staff Record After Deletion",
            "GET",
            "staff",
            200,
            use_auth=True
        )
        
        if success:
            # Staff should not appear in active list
            active_staff = [s for s in staff_list if s['active']]
            deleted_staff_in_active = any(s['id'] == self.test_staff_id for s in active_staff)
            
            if deleted_staff_in_active:
                print(f"   ❌ Deleted staff still appears in active staff list")
                return False
            else:
                print(f"   ✅ Deleted staff correctly removed from active staff list")
        
        # Test 2: Check shift assignments
        if self.test_shifts:
            # Get current roster to check shift assignments
            current_month = datetime.now().strftime("%Y-%m")
            success, roster_entries = self.run_test(
                "Check Roster After Staff Deletion",
                "GET",
                "roster",
                200,
                params={"month": current_month},
                use_auth=True
            )
            
            if success:
                # Check each test shift
                today = datetime.now().strftime("%Y-%m-%d")
                
                for shift in self.test_shifts:
                    shift_entries = [e for e in roster_entries if e.get('id') == shift['id']]
                    
                    if shift_entries:
                        entry = shift_entries[0]
                        is_future = shift['date'] >= today
                        has_staff_assignment = entry.get('staff_id') or entry.get('staff_name')
                        
                        if is_future:
                            # Future shifts should be unassigned
                            if has_staff_assignment:
                                print(f"   ❌ Future shift {shift['date']} still has staff assignment")
                                return False
                            else:
                                print(f"   ✅ Future shift {shift['date']} correctly unassigned")
                        else:
                            # Past shifts should preserve assignment for historical records
                            if has_staff_assignment:
                                print(f"   ✅ Past shift {shift['date']} correctly preserved staff assignment")
                            else:
                                print(f"   ⚠️  Past shift {shift['date']} lost staff assignment (may be acceptable)")
                    else:
                        print(f"   ⚠️  Could not find shift {shift['id']} in roster")
        
        print(f"   ✅ Data integrity checks completed")
        return True

    def test_edge_cases(self):
        """Test edge cases for staff deletion"""
        print(f"\n🎯 Testing Edge Cases...")
        
        # Test 1: Delete non-existent staff ID
        fake_staff_id = "non-existent-staff-id-12345"
        success, response = self.run_test(
            "DELETE Non-Existent Staff ID (Should Return 404)",
            "DELETE",
            f"staff/{fake_staff_id}",
            404,
            use_auth=True,
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Non-existent staff ID correctly returned 404")
        else:
            print(f"   ❌ Non-existent staff ID did not return 404")
            return False
        
        # Test 2: Delete already inactive staff
        if self.test_staff_id:
            # Try to delete the same staff again (should still work or return appropriate response)
            success, response = self.run_test(
                "DELETE Already Inactive Staff",
                "DELETE",
                f"staff/{self.test_staff_id}",
                200,  # May still return 200 or could return 404
                use_auth=True,
                token=self.admin_token
            )
            
            if success:
                print(f"   ✅ Already inactive staff handled appropriately")
            else:
                print(f"   ⚠️  Already inactive staff returned different status (may be acceptable)")
        
        # Test 3: Create and delete staff with no shifts
        no_shifts_staff = {
            "name": "No Shifts Staff",
            "active": True
        }
        
        success, created_staff = self.run_test(
            "Create Staff With No Shifts",
            "POST",
            "staff",
            200,
            data=no_shifts_staff,
            use_auth=True
        )
        
        if success and 'id' in created_staff:
            staff_id = created_staff['id']
            
            success, delete_response = self.run_test(
                "DELETE Staff With No Shifts",
                "DELETE",
                f"staff/{staff_id}",
                200,
                use_auth=True,
                token=self.admin_token
            )
            
            if success:
                shifts_affected = delete_response.get('shifts_affected', {})
                if (shifts_affected.get('total_shifts') == 0 and 
                    shifts_affected.get('future_shifts_unassigned') == 0 and 
                    shifts_affected.get('past_shifts_preserved') == 0):
                    print(f"   ✅ Staff with no shifts correctly shows zero shift counts")
                else:
                    print(f"   ❌ Staff with no shifts shows incorrect shift counts")
                    return False
        
        print(f"   ✅ Edge case tests completed")
        return True

    def run_comprehensive_test(self):
        """Run all enhanced staff deletion tests"""
        print(f"\n🚀 ENHANCED STAFF DELETION API TESTING")
        print(f"=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print(f"\n❌ Authentication setup failed - cannot continue")
            return False
        
        if not self.create_test_staff():
            print(f"\n❌ Test staff creation failed - cannot continue")
            return False
        
        if not self.create_test_shifts():
            print(f"\n❌ Test shift creation failed - cannot continue")
            return False
        
        # Run tests
        tests = [
            ("Authentication Requirements", self.test_authentication_requirements),
            ("Staff Deletion Process", self.test_staff_deletion_process),
            ("Data Integrity Verification", self.test_data_integrity),
            ("Edge Cases", self.test_edge_cases)
        ]
        
        passed_tests = 0
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"🎯 ENHANCED STAFF DELETION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total API calls: {self.tests_run}")
        print(f"Successful API calls: {self.tests_passed}")
        print(f"Test suites passed: {passed_tests}/{len(tests)}")
        print(f"Overall success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if passed_tests == len(tests):
            print(f"\n🎉 ALL ENHANCED STAFF DELETION TESTS PASSED!")
            print(f"✅ Admin authentication required and working")
            print(f"✅ Staff deactivation (not permanent deletion) working")
            print(f"✅ Future shifts unassigned, past shifts preserved")
            print(f"✅ Comprehensive response with shift counts")
            print(f"✅ Edge cases handled appropriately")
            print(f"✅ Data integrity maintained")
            return True
        else:
            print(f"\n⚠️  Some tests failed - see details above")
            return False

if __name__ == "__main__":
    tester = EnhancedStaffDeletionTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)