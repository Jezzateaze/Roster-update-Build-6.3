import requests
import sys
import json
from datetime import datetime, timedelta

class ComprehensiveShiftAvailabilityTester:
    def __init__(self, base_url="https://shift-master-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.staff_token = None
        self.staff_data = []
        self.shift_requests = []
        self.staff_availability = []
        self.unassigned_shifts = []
        self.test_staff_user = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False, auth_token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use specific token if provided, otherwise use admin token
        token_to_use = auth_token if auth_token else (self.admin_token if use_auth else None)
        
        if use_auth and token_to_use:
            headers['Authorization'] = f'Bearer {token_to_use}'

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

    def authenticate_admin(self):
        """Authenticate as Admin user"""
        print(f"\n🔐 Authenticating as Admin...")
        
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
            self.admin_token = response.get('token')
            user_data = response.get('user', {})
            
            print(f"   ✅ Admin login successful")
            print(f"   User: {user_data.get('username')} ({user_data.get('role')})")
            print(f"   Token: {self.admin_token[:20]}..." if self.admin_token else "No token")
            
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role confirmed")
                return True
            else:
                print(f"   ❌ Expected admin role, got: {user_data.get('role')}")
                return False
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def authenticate_staff(self):
        """Authenticate as a staff user"""
        print(f"\n👤 Authenticating as Staff...")
        
        # Try to authenticate with a known staff user
        staff_usernames = ["rose", "angela", "caroline", "chanelle"]
        
        for username in staff_usernames:
            login_data = {
                "username": username,
                "pin": "888888"
            }
            
            success, response = self.run_test(
                f"Staff Login ({username})",
                "POST",
                "api/auth/login",
                200,
                data=login_data
            )
            
            if success:
                self.staff_token = response.get('token')
                self.test_staff_user = response.get('user', {})
                
                print(f"   ✅ Staff login successful")
                print(f"   User: {self.test_staff_user.get('username')} ({self.test_staff_user.get('role')})")
                print(f"   Staff ID: {self.test_staff_user.get('staff_id')}")
                print(f"   Token: {self.staff_token[:20]}..." if self.staff_token else "No token")
                
                if self.test_staff_user.get('role') == 'staff':
                    print(f"   ✅ Staff role confirmed")
                    return True
                else:
                    print(f"   ❌ Expected staff role, got: {self.test_staff_user.get('role')}")
            else:
                print(f"   ⚠️  {username} login failed, trying next...")
        
        print(f"   ❌ Could not authenticate any staff user")
        return False

    def get_staff_data(self):
        """Get staff data for testing"""
        print(f"\n👥 Getting Staff Data...")
        
        success, response = self.run_test(
            "Get All Staff",
            "GET",
            "api/staff",
            200
        )
        
        if success:
            self.staff_data = response
            print(f"   ✅ Found {len(response)} staff members")
            staff_names = [staff['name'] for staff in response if staff.get('name')]
            print(f"   Staff names: {', '.join(staff_names[:5])}{'...' if len(staff_names) > 5 else ''}")
            return True
        else:
            print(f"   ❌ Could not get staff data")
            return False

    def get_unassigned_shifts(self):
        """Get unassigned shifts for testing shift requests"""
        print(f"\n📋 Getting Unassigned Shifts...")
        
        success, response = self.run_test(
            "Get Unassigned Shifts",
            "GET",
            "api/unassigned-shifts",
            200,
            use_auth=True
        )
        
        if success:
            self.unassigned_shifts = response
            print(f"   ✅ Found {len(response)} unassigned shifts")
            if response:
                sample_shift = response[0]
                print(f"   Sample: {sample_shift.get('date')} {sample_shift.get('start_time')}-{sample_shift.get('end_time')}")
            return True
        else:
            print(f"   ❌ Could not get unassigned shifts")
            return False

    def test_phase_2_shift_requests_crud(self):
        """Test Phase 2: Admin CRUD for Shift Requests Management"""
        print(f"\n🎯 PHASE 2 TESTING - ADMIN CRUD FOR SHIFT REQUESTS (FIXED)")
        print(f"=" * 70)
        
        if not self.admin_token:
            print("   ❌ No admin authentication token available")
            return False

        phase2_tests_passed = 0
        phase2_tests_total = 5

        # Test 1: CREATE - Staff creates request, then admin can manage it
        print(f"\n   ➕ TEST 1: CREATE - POST /api/shift-requests (Staff creates, Admin manages)")
        
        if not self.staff_token or not self.unassigned_shifts:
            print("   ⚠️  No staff token or unassigned shifts available for testing")
        else:
            # Staff creates a shift request
            test_shift = self.unassigned_shifts[0]
            create_request_data = {
                "roster_entry_id": test_shift['id'],
                "notes": "Staff created request for testing"
            }
            
            success, created_request = self.run_test(
                "Staff Create Shift Request",
                "POST",
                "api/shift-requests",
                200,
                data=create_request_data,
                use_auth=True,
                auth_token=self.staff_token
            )
            
            if success:
                print(f"   ✅ Staff can create shift requests")
                print(f"   Created request ID: {created_request.get('id')}")
                phase2_tests_passed += 1
                
                # Store for later tests
                self.shift_requests.append(created_request)
            else:
                print(f"   ❌ Staff cannot create shift requests")

        # Test 2: READ - Test GET /api/shift-requests (Admin viewing all requests)
        print(f"\n   📖 TEST 2: READ - GET /api/shift-requests (Admin viewing all requests)")
        success, shift_requests = self.run_test(
            "Admin View All Shift Requests",
            "GET",
            "api/shift-requests",
            200,
            use_auth=True
        )
        
        if success:
            self.shift_requests = shift_requests
            print(f"   ✅ Admin can view all shift requests: {len(shift_requests)} found")
            phase2_tests_passed += 1
            
            if shift_requests:
                sample_request = shift_requests[0]
                print(f"   Sample request: Staff={sample_request.get('staff_name')}, Status={sample_request.get('status')}")
        else:
            print(f"   ❌ Admin cannot view shift requests")

        # Test 3: UPDATE - Test PUT /api/shift-requests/{id} (Admin updating existing requests)
        print(f"\n   ✏️  TEST 3: UPDATE - PUT /api/shift-requests/{{id}} (Admin updating existing requests)")
        
        if self.shift_requests:
            # Use first available shift request for update test
            test_request = self.shift_requests[0]
            request_id = test_request.get('id')
            
            if request_id:
                update_data = {
                    **test_request,
                    "admin_notes": "Updated by admin via API test",
                    "notes": "Request updated during testing"
                }
                
                success, updated_request = self.run_test(
                    "Admin Update Shift Request",
                    "PUT",
                    f"api/shift-requests/{request_id}",
                    200,
                    data=update_data,
                    use_auth=True
                )
                
                if success:
                    print(f"   ✅ Admin can update existing shift requests")
                    print(f"   Updated admin notes: {updated_request.get('message', 'Updated successfully')}")
                    phase2_tests_passed += 1
                else:
                    print(f"   ❌ Admin cannot update shift requests")
            else:
                print(f"   ⚠️  No valid request ID found for update test")
        else:
            print(f"   ⚠️  No shift requests available for update test")

        # Test 4: DELETE - Test DELETE /api/shift-requests/{id} (Admin deleting individual requests)
        print(f"\n   🗑️  TEST 4: DELETE - DELETE /api/shift-requests/{{id}} (Admin deleting individual requests)")
        
        if self.shift_requests and len(self.shift_requests) > 1:
            # Use last shift request for deletion test
            test_request = self.shift_requests[-1]
            request_id = test_request.get('id')
            
            if request_id:
                success, delete_response = self.run_test(
                    "Admin Delete Individual Shift Request",
                    "DELETE",
                    f"api/shift-requests/{request_id}",
                    200,
                    use_auth=True
                )
                
                if success:
                    print(f"   ✅ Admin can delete individual shift requests")
                    print(f"   Delete response: {delete_response.get('message', 'Deleted successfully')}")
                    phase2_tests_passed += 1
                else:
                    print(f"   ❌ Admin cannot delete individual shift requests")
            else:
                print(f"   ⚠️  No valid request ID found for delete test")
        else:
            print(f"   ⚠️  Not enough shift requests available for delete test")

        # Test 5: BULK CLEAR - Test DELETE /api/shift-requests (Admin clearing all requests)
        print(f"\n   🧹 TEST 5: BULK CLEAR - DELETE /api/shift-requests (Admin clearing all requests)")
        
        success, bulk_delete_response = self.run_test(
            "Admin Bulk Clear All Shift Requests",
            "DELETE",
            "api/shift-requests",
            200,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ Admin can bulk clear all shift requests")
            print(f"   Bulk clear response: {bulk_delete_response.get('message', 'All requests cleared')}")
            print(f"   Cleared count: {bulk_delete_response.get('deleted_count', 0)}")
            phase2_tests_passed += 1
        else:
            print(f"   ❌ Admin cannot bulk clear shift requests")

        # Phase 2 Summary
        print(f"\n   📊 PHASE 2 RESULTS: {phase2_tests_passed}/{phase2_tests_total} tests passed")
        
        if phase2_tests_passed == phase2_tests_total:
            print(f"   🎉 PHASE 2 COMPLETE: All Admin CRUD operations for Shift Requests working!")
        else:
            print(f"   ⚠️  PHASE 2 PARTIAL: {phase2_tests_total - phase2_tests_passed} operations missing or failing")
            
        return phase2_tests_passed == phase2_tests_total

    def test_phase_3_staff_availability_crud(self):
        """Test Phase 3: Staff Availability CRUD (ENHANCED)"""
        print(f"\n🎯 PHASE 3 TESTING - STAFF AVAILABILITY CRUD (ENHANCED)")
        print(f"=" * 70)
        
        if not self.admin_token:
            print("   ❌ No admin authentication token available")
            return False

        phase3_tests_passed = 0
        phase3_tests_total = 5

        # Test 1: CREATE - Test POST /api/staff-availability (Admin creating for any staff)
        print(f"\n   ➕ TEST 1: CREATE - POST /api/staff-availability (Admin creating for any staff)")
        
        if not self.staff_data:
            print("   ⚠️  No staff data available for testing")
        else:
            # Test all 4 availability types
            availability_types = [
                {"type": "available", "emoji": "✅", "description": "Available"},
                {"type": "unavailable", "emoji": "❌", "description": "Unavailable"},
                {"type": "time_off_request", "emoji": "🏖️", "description": "Time Off Request"},
                {"type": "preferred_shifts", "emoji": "⭐", "description": "Preferred Shifts"}
            ]
            
            create_success_count = 0
            created_records = []
            
            for i, avail_type in enumerate(availability_types):
                test_staff = self.staff_data[i % len(self.staff_data)]  # Rotate through staff
                
                create_availability_data = {
                    "staff_id": test_staff['id'],
                    "staff_name": test_staff['name'],
                    "availability_type": avail_type["type"],
                    "date_from": "2025-01-20",
                    "date_to": "2025-01-25",
                    "start_time": "09:00",
                    "end_time": "17:00",
                    "is_recurring": False,
                    "notes": f"Admin created {avail_type['description']} for {test_staff['name']}"
                }
                
                success, created_availability = self.run_test(
                    f"Admin Create {avail_type['description']} ({avail_type['emoji']})",
                    "POST",
                    "api/staff-availability",
                    200,
                    data=create_availability_data,
                    use_auth=True
                )
                
                if success:
                    create_success_count += 1
                    created_records.append(created_availability)
                    print(f"      ✅ Created {avail_type['description']} for {test_staff['name']}")
                    print(f"      ID: {created_availability.get('id')}")
                else:
                    print(f"      ❌ Failed to create {avail_type['description']}")
            
            if create_success_count == len(availability_types):
                print(f"   ✅ Admin can create availability for any staff - All 4 types working ({create_success_count}/4)")
                phase3_tests_passed += 1
                self.staff_availability.extend(created_records)
            else:
                print(f"   ❌ Admin availability creation partially working ({create_success_count}/4)")

        # Test 2: READ - Test GET /api/staff-availability (Admin viewing all records)
        print(f"\n   📖 TEST 2: READ - GET /api/staff-availability (Admin viewing all records)")
        
        success, staff_availability = self.run_test(
            "Admin View All Staff Availability",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True
        )
        
        if success:
            self.staff_availability = staff_availability
            print(f"   ✅ Admin can view all staff availability records: {len(staff_availability)} found")
            phase3_tests_passed += 1
            
            if staff_availability:
                # Show distribution by type
                type_counts = {}
                for record in staff_availability:
                    avail_type = record.get('availability_type', 'unknown')
                    type_counts[avail_type] = type_counts.get(avail_type, 0) + 1
                
                print(f"   Availability types: {type_counts}")
                
                sample_record = staff_availability[0]
                print(f"   Sample: {sample_record.get('staff_name')} - {sample_record.get('availability_type')}")
        else:
            print(f"   ❌ Admin cannot view staff availability records")

        # Test 3: UPDATE - Test PUT /api/staff-availability/{id} (Admin updating records)
        print(f"\n   ✏️  TEST 3: UPDATE - PUT /api/staff-availability/{{id}} (Admin updating records)")
        
        if self.staff_availability:
            # Use first available record for update test
            test_record = self.staff_availability[0]
            record_id = test_record.get('id')
            
            if record_id:
                update_data = {
                    **test_record,
                    "notes": "Updated by admin via API test",
                    "start_time": "10:00",  # Change start time
                    "end_time": "18:00"     # Change end time
                }
                
                success, updated_record = self.run_test(
                    "Admin Update Staff Availability",
                    "PUT",
                    f"api/staff-availability/{record_id}",
                    200,
                    data=update_data,
                    use_auth=True
                )
                
                if success:
                    print(f"   ✅ Admin can update staff availability records")
                    print(f"   Updated times: {updated_record.get('start_time')}-{updated_record.get('end_time')}")
                    print(f"   Updated notes: {updated_record.get('notes')}")
                    phase3_tests_passed += 1
                else:
                    print(f"   ❌ Admin cannot update staff availability records")
            else:
                print(f"   ⚠️  No valid record ID found for update test")
        else:
            print(f"   ⚠️  No staff availability records available for update test")

        # Test 4: DELETE - Test DELETE /api/staff-availability/{id} (Admin deleting records)
        print(f"\n   🗑️  TEST 4: DELETE - DELETE /api/staff-availability/{{id}} (Admin deleting records)")
        
        if self.staff_availability and len(self.staff_availability) > 1:
            # Use last record for deletion test
            test_record = self.staff_availability[-1]
            record_id = test_record.get('id')
            
            if record_id:
                success, delete_response = self.run_test(
                    "Admin Delete Individual Staff Availability",
                    "DELETE",
                    f"api/staff-availability/{record_id}",
                    200,
                    use_auth=True
                )
                
                if success:
                    print(f"   ✅ Admin can delete individual staff availability records")
                    print(f"   Delete response: {delete_response.get('message', 'Deleted successfully')}")
                    phase3_tests_passed += 1
                else:
                    print(f"   ❌ Admin cannot delete individual staff availability records")
            else:
                print(f"   ⚠️  No valid record ID found for delete test")
        else:
            print(f"   ⚠️  Not enough staff availability records for delete test")

        # Test 5: BULK CLEAR - Test DELETE /api/staff-availability (Admin clearing all records - NEWLY ADDED)
        print(f"\n   🧹 TEST 5: BULK CLEAR - DELETE /api/staff-availability (Admin clearing all records - NEWLY ADDED)")
        
        success, bulk_delete_response = self.run_test(
            "Admin Bulk Clear All Staff Availability",
            "DELETE",
            "api/staff-availability",
            200,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ Admin can bulk clear all staff availability records")
            print(f"   Bulk clear response: {bulk_delete_response.get('message', 'All records cleared')}")
            print(f"   Cleared count: {bulk_delete_response.get('cleared_count', 0)}")
            phase3_tests_passed += 1
        else:
            print(f"   ❌ Admin cannot bulk clear staff availability records")

        # Phase 3 Summary
        print(f"\n   📊 PHASE 3 RESULTS: {phase3_tests_passed}/{phase3_tests_total} tests passed")
        
        if phase3_tests_passed == phase3_tests_total:
            print(f"   🎉 PHASE 3 COMPLETE: All Admin CRUD operations for Staff Availability working!")
        else:
            print(f"   ⚠️  PHASE 3 PARTIAL: {phase3_tests_total - phase3_tests_passed} operations missing or failing")
            
        return phase3_tests_passed == phase3_tests_total

    def test_authentication_and_authorization(self):
        """Test role-based access control verification"""
        print(f"\n🔒 TESTING AUTHENTICATION & AUTHORIZATION")
        print(f"=" * 70)
        
        auth_tests_passed = 0
        auth_tests_total = 4

        # Test 1: Admin authentication working
        print(f"\n   🔑 TEST 1: Admin Authentication (Admin/0000)")
        if self.admin_token:
            print(f"   ✅ Admin authentication successful")
            auth_tests_passed += 1
        else:
            print(f"   ❌ Admin authentication failed")

        # Test 2: Protected endpoints require authentication
        print(f"\n   🚫 TEST 2: Protected endpoints require authentication")
        
        # Test without token
        success, response = self.run_test(
            "Access Shift Requests Without Auth (Should Fail)",
            "GET",
            "api/shift-requests",
            401,  # Expect unauthorized
            use_auth=False
        )
        
        if success:  # Success means we got expected 401
            print(f"   ✅ Protected endpoints correctly require authentication")
            auth_tests_passed += 1
        else:
            print(f"   ❌ Protected endpoints accessible without authentication")

        # Test 3: Admin role required for admin operations
        print(f"\n   👑 TEST 3: Admin role verification")
        
        # Test admin-only endpoint with admin token
        success, response = self.run_test(
            "Admin Access to Staff Availability (Should Work)",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ Admin role can access admin-only endpoints")
            auth_tests_passed += 1
        else:
            print(f"   ❌ Admin role cannot access admin-only endpoints")

        # Test 4: Proper error handling
        print(f"\n   ⚠️  TEST 4: Proper error handling for invalid requests")
        
        # Test with invalid data
        invalid_data = {
            "staff_id": "",  # Empty staff_id should fail
            "availability_type": "invalid_type"
        }
        
        success, response = self.run_test(
            "Create Availability with Invalid Data (Should Fail)",
            "POST",
            "api/staff-availability",
            422,  # Expect validation error
            data=invalid_data,
            use_auth=True
        )
        
        if success:  # Success means we got expected 422
            print(f"   ✅ Proper validation and error handling working")
            auth_tests_passed += 1
        else:
            print(f"   ❌ Validation and error handling not working properly")

        # Authentication Summary
        print(f"\n   📊 AUTHENTICATION RESULTS: {auth_tests_passed}/{auth_tests_total} tests passed")
        
        return auth_tests_passed == auth_tests_total

    def run_comprehensive_test(self):
        """Run all comprehensive tests for Shift & Staff Availability CRUD"""
        print(f"\n🚀 COMPREHENSIVE SHIFT & STAFF AVAILABILITY CRUD TESTING")
        print(f"=" * 80)
        print(f"Testing COMPLETE enhanced 'Shift & Staff Availability' section with all newly added CRUD endpoints")
        print(f"Focus: Phase 2 (Shift Requests) + Phase 3 (Staff Availability) + Authentication")
        print(f"=" * 80)

        # Step 1: Authenticate as Admin
        if not self.authenticate_admin():
            print(f"\n❌ CRITICAL FAILURE: Cannot authenticate as Admin - stopping tests")
            return False

        # Step 2: Authenticate as Staff (for shift request creation)
        staff_auth_success = self.authenticate_staff()
        if not staff_auth_success:
            print(f"\n⚠️  WARNING: Cannot authenticate as Staff - some tests may be limited")

        # Step 3: Get staff data
        if not self.get_staff_data():
            print(f"\n❌ CRITICAL FAILURE: Cannot get staff data - stopping tests")
            return False

        # Step 4: Get unassigned shifts
        if not self.get_unassigned_shifts():
            print(f"\n⚠️  WARNING: Cannot get unassigned shifts - shift request tests may be limited")

        # Step 5: Test Authentication & Authorization
        auth_success = self.test_authentication_and_authorization()

        # Step 6: Test Phase 2 - Shift Requests CRUD
        phase2_success = self.test_phase_2_shift_requests_crud()

        # Step 7: Test Phase 3 - Staff Availability CRUD
        phase3_success = self.test_phase_3_staff_availability_crud()

        # Final Summary
        print(f"\n🎯 FINAL COMPREHENSIVE TEST RESULTS")
        print(f"=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Total Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"")
        print(f"📊 COMPONENT RESULTS:")
        print(f"   🔒 Authentication & Authorization: {'✅ PASS' if auth_success else '❌ FAIL'}")
        print(f"   📋 Phase 2 - Shift Requests CRUD: {'✅ PASS' if phase2_success else '❌ FAIL'}")
        print(f"   👥 Phase 3 - Staff Availability CRUD: {'✅ PASS' if phase3_success else '❌ FAIL'}")
        print(f"")
        
        overall_success = auth_success and phase2_success and phase3_success
        
        if overall_success:
            print(f"🎉 COMPREHENSIVE SUCCESS: ALL backend CRUD endpoints working correctly!")
            print(f"   ✅ Admin authentication (Admin/0000) working")
            print(f"   ✅ All CRUD operations for shift requests working")
            print(f"   ✅ All CRUD operations for staff availability working")
            print(f"   ✅ Proper validation and error handling")
            print(f"   ✅ Role-based access control verification")
            print(f"   🚀 System ready for frontend integration!")
        else:
            print(f"⚠️  PARTIAL SUCCESS: Some components need attention")
            if not auth_success:
                print(f"   ❌ Authentication/Authorization issues found")
            if not phase2_success:
                print(f"   ❌ Shift Requests CRUD has missing/failing operations")
            if not phase3_success:
                print(f"   ❌ Staff Availability CRUD has missing/failing operations")
            print(f"   🔧 Review failed tests above for specific issues")

        return overall_success

if __name__ == "__main__":
    print("🧪 Comprehensive Shift & Staff Availability CRUD Testing Suite")
    print("=" * 60)
    
    tester = ComprehensiveShiftAvailabilityTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print(f"\n✅ All tests passed! System is ready.")
        sys.exit(0)
    else:
        print(f"\n❌ Some tests failed. Check output above.")
        sys.exit(1)