import requests
import json
from datetime import datetime, timedelta
import uuid

class ShiftAvailabilityAPITester:
    def __init__(self, base_url="https://roster-master-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.staff_token = None
        self.staff_user_id = None
        self.staff_id = None  # Actual staff ID for filtering
        self.test_data = {
            'unassigned_shifts': [],
            'shift_requests': [],
            'availability_records': [],
            'notifications': []
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False, auth_token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required
        if use_auth:
            token = auth_token or self.admin_token
            if token:
                headers['Authorization'] = f'Bearer {token}'

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
                    if isinstance(response_data, list):
                        print(f"   Response: {len(response_data)} items returned")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.status_code < 400 else response.text

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
            "api/auth/login",
            200,
            data=admin_login
        )
        
        if success:
            self.admin_token = response.get('token')
            print(f"   ✅ Admin authenticated - Token: {self.admin_token[:20]}...")
        else:
            print(f"   ❌ Admin authentication failed")
            return False
        
        # Try to login with existing staff user (angela with reset PIN)
        staff_login = {
            "username": "angela",
            "pin": "888888"
        }
        
        success, staff_response = self.run_test(
            "Staff Login (angela)",
            "POST",
            "api/auth/login",
            200,
            data=staff_login
        )
        
        if success:
            self.staff_token = staff_response.get('token')
            self.staff_user_id = staff_response.get('user', {}).get('id')
            self.staff_id = staff_response.get('user', {}).get('staff_id')  # This is the actual staff ID
            staff_user_data = staff_response.get('user', {})
            print(f"   ✅ Staff authenticated - Username: angela")
            print(f"   User ID: {self.staff_user_id}")
            print(f"   Staff ID: {self.staff_id}")
            print(f"   Staff Role: {staff_user_data.get('role')}")
        else:
            print(f"   ❌ Could not authenticate staff user")
            return False
        
        return self.admin_token and self.staff_token

    def create_test_data(self):
        """Create some unassigned shifts for testing"""
        print(f"\n📋 Creating Test Data...")
        
        # Create some unassigned shifts
        test_shifts = [
            {
                "id": str(uuid.uuid4()),
                "date": "2025-01-15",
                "start_time": "09:00",
                "end_time": "17:00",
                "shift_template_id": "test-unassigned-1",
                "is_sleepover": False,
                "staff_id": None,
                "staff_name": None
            },
            {
                "id": str(uuid.uuid4()),
                "date": "2025-01-16", 
                "start_time": "15:00",
                "end_time": "23:00",
                "shift_template_id": "test-unassigned-2",
                "is_sleepover": False,
                "staff_id": None,
                "staff_name": None
            },
            {
                "id": str(uuid.uuid4()),
                "date": "2025-01-17",
                "start_time": "23:00",
                "end_time": "07:00",
                "shift_template_id": "test-unassigned-3",
                "is_sleepover": True,
                "staff_id": None,
                "staff_name": None
            }
        ]
        
        for i, shift in enumerate(test_shifts):
            success, created_shift = self.run_test(
                f"Create Unassigned Shift {i+1}",
                "POST",
                "api/roster",
                200,
                data=shift,
                use_auth=True
            )
            
            if success:
                self.test_data['unassigned_shifts'].append(created_shift)
                print(f"   ✅ Created shift: {shift['date']} {shift['start_time']}-{shift['end_time']}")
        
        print(f"   Created {len(self.test_data['unassigned_shifts'])} unassigned shifts")
        return len(self.test_data['unassigned_shifts']) > 0

    def test_unassigned_shifts_api(self):
        """Test GET /api/unassigned-shifts endpoint"""
        print(f"\n🎯 Testing Unassigned Shifts API...")
        
        # Test 1: Get unassigned shifts as admin
        success, unassigned_shifts = self.run_test(
            "Get Unassigned Shifts (Admin)",
            "GET",
            "api/unassigned-shifts",
            200,
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Found {len(unassigned_shifts)} unassigned shifts")
            
            # Verify shifts are actually unassigned
            assigned_count = 0
            for shift in unassigned_shifts:
                if shift.get('staff_id') or shift.get('staff_name'):
                    assigned_count += 1
            
            if assigned_count == 0:
                print(f"   ✅ All returned shifts are properly unassigned")
            else:
                print(f"   ❌ Found {assigned_count} shifts with staff assignments")
                return False
            
            # Store for later tests
            self.test_data['unassigned_shifts'].extend(unassigned_shifts[:3])
        else:
            print(f"   ❌ Failed to get unassigned shifts")
            return False
        
        # Test 2: Get unassigned shifts as staff (should also work)
        success, staff_unassigned = self.run_test(
            "Get Unassigned Shifts (Staff)",
            "GET",
            "api/unassigned-shifts",
            200,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            print(f"   ✅ Staff can also access unassigned shifts: {len(staff_unassigned)} shifts")
        
        # Test 3: Test without authentication (should fail)
        success, response = self.run_test(
            "Get Unassigned Shifts (No Auth - Should Fail)",
            "GET",
            "api/unassigned-shifts",
            401,
            use_auth=False
        )
        
        if success:
            print(f"   ✅ Properly blocked unauthenticated access")
        
        return True

    def test_shift_requests_api(self):
        """Test Shift Requests API endpoints"""
        print(f"\n🎯 Testing Shift Requests API...")
        
        if not self.test_data['unassigned_shifts']:
            print(f"   ⚠️  No unassigned shifts available for testing")
            return False
        
        # Test 1: Staff creates a shift request
        unassigned_shift = self.test_data['unassigned_shifts'][0]
        shift_request_data = {
            "roster_entry_id": unassigned_shift['id'],
            "staff_id": self.staff_id,  # Use actual staff_id
            "staff_name": "Angela",
            "request_date": datetime.utcnow().isoformat(),
            "notes": "I would like to work this shift"
        }
        
        success, created_request = self.run_test(
            "Create Shift Request (Staff)",
            "POST",
            "api/shift-requests",
            200,
            data=shift_request_data,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            request_id = created_request.get('id')
            print(f"   ✅ Staff created shift request - ID: {request_id}")
            self.test_data['shift_requests'].append(created_request)
        else:
            print(f"   ❌ Failed to create shift request")
            return False
        
        # Test 2: Get shift requests as staff (should see own requests only)
        success, staff_requests = self.run_test(
            "Get Shift Requests (Staff - Own Only)",
            "GET",
            "api/shift-requests",
            200,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            print(f"   ✅ Staff sees {len(staff_requests)} own requests")
            
            # Verify all requests belong to this staff member
            for request in staff_requests:
                if request.get('staff_id') != self.staff_id:
                    print(f"   ❌ Staff seeing other staff's requests")
                    return False
            print(f"   ✅ Staff only sees own requests")
        
        # Test 3: Get shift requests as admin (should see all requests)
        success, admin_requests = self.run_test(
            "Get Shift Requests (Admin - All)",
            "GET",
            "api/shift-requests",
            200,
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Admin sees {len(admin_requests)} total requests")
            
            # Should be at least as many as staff requests
            if len(admin_requests) >= len(staff_requests):
                print(f"   ✅ Admin sees more or equal requests than staff")
            else:
                print(f"   ❌ Admin sees fewer requests than staff")
                return False
        
        # Test 4: Admin approves a shift request
        if self.test_data['shift_requests']:
            request_id = self.test_data['shift_requests'][0]['id']
            approval_data = {
                "admin_notes": "Approved - good fit for this shift"
            }
            
            success, approved_request = self.run_test(
                "Approve Shift Request (Admin)",
                "PUT",
                f"api/shift-requests/{request_id}/approve",
                200,
                data=approval_data,
                use_auth=True,
                auth_token=self.admin_token
            )
            
            if success:
                status = approved_request.get('status')
                if status == 'approved':
                    print(f"   ✅ Shift request approved successfully")
                else:
                    print(f"   ❌ Request status not updated: {status}")
                    return False
        
        # Test 5: Test staff trying to approve (should fail)
        if len(self.test_data['shift_requests']) > 1:
            request_id = self.test_data['shift_requests'][1]['id'] if len(self.test_data['shift_requests']) > 1 else self.test_data['shift_requests'][0]['id']
            
            success, response = self.run_test(
                "Staff Approve Request (Should Fail)",
                "PUT",
                f"api/shift-requests/{request_id}/approve",
                403,
                data={"admin_notes": "Staff trying to approve"},
                use_auth=True,
                auth_token=self.staff_token
            )
            
            if success:
                print(f"   ✅ Staff properly blocked from approving requests")
        
        # Test 6: Admin rejects a shift request
        if len(self.test_data['unassigned_shifts']) > 1:
            # Create another request to reject
            unassigned_shift = self.test_data['unassigned_shifts'][1]
            reject_request_data = {
                "roster_entry_id": unassigned_shift['id'],
                "staff_id": self.staff_user_id,
                "staff_name": "Test Staff",
                "request_date": datetime.utcnow().isoformat(),
                "notes": "Another shift request"
            }
            
            success, reject_request = self.run_test(
                "Create Request to Reject",
                "POST",
                "api/shift-requests",
                200,
                data=reject_request_data,
                use_auth=True,
                auth_token=self.staff_token
            )
            
            if success:
                request_id = reject_request.get('id')
                rejection_data = {
                    "admin_notes": "Sorry, this shift is no longer available"
                }
                
                success, rejected_request = self.run_test(
                    "Reject Shift Request (Admin)",
                    "PUT",
                    f"api/shift-requests/{request_id}/reject",
                    200,
                    data=rejection_data,
                    use_auth=True,
                    auth_token=self.admin_token
                )
                
                if success:
                    status = rejected_request.get('status')
                    if status == 'rejected':
                        print(f"   ✅ Shift request rejected successfully")
                    else:
                        print(f"   ❌ Request status not updated: {status}")
                        return False
        
        return True

    def test_staff_availability_api(self):
        """Test Staff Availability API endpoints"""
        print(f"\n🎯 Testing Staff Availability API...")
        
        # Test 1: Staff creates availability record
        availability_data = {
            "staff_id": self.staff_id,  # Use actual staff_id
            "staff_name": "Angela",
            "availability_type": "available",
            "date_from": "2025-01-20",
            "date_to": "2025-01-25",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_recurring": False,
            "notes": "Available for day shifts this week"
        }
        
        success, created_availability = self.run_test(
            "Create Availability Record (Staff)",
            "POST",
            "api/staff-availability",
            200,
            data=availability_data,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            availability_id = created_availability.get('id')
            print(f"   ✅ Staff created availability record - ID: {availability_id}")
            self.test_data['availability_records'].append(created_availability)
        else:
            print(f"   ❌ Failed to create availability record")
            return False
        
        # Test 2: Create unavailable record
        unavailable_data = {
            "staff_id": self.staff_user_id,
            "staff_name": "Test Staff",
            "availability_type": "unavailable",
            "date_from": "2025-01-26",
            "date_to": "2025-01-27",
            "notes": "Not available - personal appointment"
        }
        
        success, unavailable_record = self.run_test(
            "Create Unavailable Record",
            "POST",
            "api/staff-availability",
            200,
            data=unavailable_data,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            print(f"   ✅ Created unavailable record")
            self.test_data['availability_records'].append(unavailable_record)
        
        # Test 3: Create time off request
        time_off_data = {
            "staff_id": self.staff_user_id,
            "staff_name": "Test Staff",
            "availability_type": "time_off_request",
            "date_from": "2025-02-01",
            "date_to": "2025-02-03",
            "notes": "Requesting time off for family event"
        }
        
        success, time_off_record = self.run_test(
            "Create Time Off Request",
            "POST",
            "api/staff-availability",
            200,
            data=time_off_data,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            print(f"   ✅ Created time off request")
            self.test_data['availability_records'].append(time_off_record)
        
        # Test 4: Create preferred shifts record
        preferred_data = {
            "staff_id": self.staff_user_id,
            "staff_name": "Test Staff",
            "availability_type": "preferred_shifts",
            "day_of_week": 1,  # Tuesday
            "start_time": "15:00",
            "end_time": "23:00",
            "is_recurring": True,
            "notes": "Prefer evening shifts on Tuesdays"
        }
        
        success, preferred_record = self.run_test(
            "Create Preferred Shifts Record",
            "POST",
            "api/staff-availability",
            200,
            data=preferred_data,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            print(f"   ✅ Created preferred shifts record")
            self.test_data['availability_records'].append(preferred_record)
        
        # Test 5: Get availability as staff (should see own records only)
        success, staff_availability = self.run_test(
            "Get Staff Availability (Staff - Own Only)",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            print(f"   ✅ Staff sees {len(staff_availability)} own availability records")
            
            # Verify all records belong to this staff member
            for record in staff_availability:
                if record.get('staff_id') != self.staff_user_id:
                    print(f"   ❌ Staff seeing other staff's availability")
                    return False
            print(f"   ✅ Staff only sees own availability records")
        
        # Test 6: Get availability as admin (should see all records)
        success, admin_availability = self.run_test(
            "Get Staff Availability (Admin - All)",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Admin sees {len(admin_availability)} total availability records")
            
            # Should be at least as many as staff records
            if len(admin_availability) >= len(staff_availability):
                print(f"   ✅ Admin sees more or equal records than staff")
            else:
                print(f"   ❌ Admin sees fewer records than staff")
                return False
        
        # Test 7: Update availability record
        if self.test_data['availability_records']:
            record_id = self.test_data['availability_records'][0]['id']
            update_data = {
                **self.test_data['availability_records'][0],
                "notes": "Updated availability notes",
                "end_time": "18:00"  # Changed end time
            }
            
            success, updated_record = self.run_test(
                "Update Availability Record",
                "PUT",
                f"api/staff-availability/{record_id}",
                200,
                data=update_data,
                use_auth=True,
                auth_token=self.staff_token
            )
            
            if success:
                if updated_record.get('notes') == "Updated availability notes":
                    print(f"   ✅ Availability record updated successfully")
                else:
                    print(f"   ❌ Update not reflected in response")
                    return False
        
        # Test 8: Delete/deactivate availability record
        if len(self.test_data['availability_records']) > 1:
            record_id = self.test_data['availability_records'][1]['id']
            
            success, response = self.run_test(
                "Delete Availability Record",
                "DELETE",
                f"api/staff-availability/{record_id}",
                200,
                use_auth=True,
                auth_token=self.staff_token
            )
            
            if success:
                print(f"   ✅ Availability record deleted/deactivated successfully")
        
        return True

    def test_notifications_api(self):
        """Test Notifications API endpoints"""
        print(f"\n🎯 Testing Notifications API...")
        
        # Test 1: Get notifications for staff user
        success, staff_notifications = self.run_test(
            "Get Notifications (Staff)",
            "GET",
            "api/notifications",
            200,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            print(f"   ✅ Staff sees {len(staff_notifications)} notifications")
            
            # Store notification for read test
            if staff_notifications:
                self.test_data['notifications'] = staff_notifications
        else:
            print(f"   ❌ Failed to get staff notifications")
            return False
        
        # Test 2: Get notifications for admin user
        success, admin_notifications = self.run_test(
            "Get Notifications (Admin)",
            "GET",
            "api/notifications",
            200,
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Admin sees {len(admin_notifications)} notifications")
        
        # Test 3: Mark notification as read (if we have any)
        if self.test_data['notifications']:
            notification_id = self.test_data['notifications'][0]['id']
            
            success, response = self.run_test(
                "Mark Notification as Read",
                "PUT",
                f"api/notifications/{notification_id}/read",
                200,
                use_auth=True,
                auth_token=self.staff_token
            )
            
            if success:
                print(f"   ✅ Notification marked as read successfully")
            else:
                print(f"   ❌ Failed to mark notification as read")
                return False
        else:
            print(f"   ⚠️  No notifications available to test read functionality")
        
        # Test 4: Test unauthorized access
        success, response = self.run_test(
            "Get Notifications (No Auth - Should Fail)",
            "GET",
            "api/notifications",
            401,
            use_auth=False
        )
        
        if success:
            print(f"   ✅ Properly blocked unauthenticated access to notifications")
        
        return True

    def test_assignment_conflicts_api(self):
        """Test Assignment Conflicts API endpoint"""
        print(f"\n🎯 Testing Assignment Conflicts API...")
        
        if not self.test_data['unassigned_shifts']:
            print(f"   ⚠️  No unassigned shifts available for conflict testing")
            return False
        
        # Test 1: Check for conflicts when assigning staff to shift
        unassigned_shift = self.test_data['unassigned_shifts'][0]
        conflict_check_data = {
            "staff_id": self.staff_user_id,
            "roster_entry_id": unassigned_shift['id'],
            "date": unassigned_shift['date'],
            "start_time": unassigned_shift['start_time'],
            "end_time": unassigned_shift['end_time']
        }
        
        success, conflict_result = self.run_test(
            "Check Assignment Conflicts (Admin)",
            "POST",
            "api/check-assignment-conflicts",
            200,
            data=conflict_check_data,
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if success:
            has_conflicts = conflict_result.get('has_conflicts', False)
            conflicts = conflict_result.get('conflicts', [])
            print(f"   ✅ Conflict check completed - Has conflicts: {has_conflicts}")
            if conflicts:
                print(f"   Found {len(conflicts)} conflicts:")
                for conflict in conflicts:
                    print(f"      - {conflict.get('type', 'Unknown')}: {conflict.get('message', 'No details')}")
        else:
            print(f"   ❌ Failed to check assignment conflicts")
            return False
        
        # Test 2: Test with overlapping shift scenario
        if len(self.test_data['unassigned_shifts']) > 1:
            # Create a scenario where staff might have conflicting availability
            overlapping_shift = self.test_data['unassigned_shifts'][1]
            overlap_check_data = {
                "staff_id": self.staff_user_id,
                "roster_entry_id": overlapping_shift['id'],
                "date": overlapping_shift['date'],
                "start_time": overlapping_shift['start_time'],
                "end_time": overlapping_shift['end_time']
            }
            
            success, overlap_result = self.run_test(
                "Check Overlapping Assignment Conflicts",
                "POST",
                "api/check-assignment-conflicts",
                200,
                data=overlap_check_data,
                use_auth=True,
                auth_token=self.admin_token
            )
            
            if success:
                print(f"   ✅ Overlap conflict check completed")
        
        # Test 3: Test staff trying to check conflicts (should fail - admin only)
        success, response = self.run_test(
            "Staff Check Conflicts (Should Fail)",
            "POST",
            "api/check-assignment-conflicts",
            403,
            data=conflict_check_data,
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            print(f"   ✅ Staff properly blocked from checking assignment conflicts")
        
        return True

    def run_comprehensive_tests(self):
        """Run all shift and staff availability tests"""
        print(f"\n🚀 Starting Comprehensive Shift & Staff Availability API Tests...")
        print(f"=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print(f"\n❌ Authentication setup failed - cannot continue")
            return False
        
        if not self.create_test_data():
            print(f"\n❌ Test data creation failed - cannot continue")
            return False
        
        # Run all tests
        test_results = []
        
        test_results.append(("Unassigned Shifts API", self.test_unassigned_shifts_api()))
        test_results.append(("Shift Requests API", self.test_shift_requests_api()))
        test_results.append(("Staff Availability API", self.test_staff_availability_api()))
        test_results.append(("Notifications API", self.test_notifications_api()))
        test_results.append(("Assignment Conflicts API", self.test_assignment_conflicts_api()))
        
        # Summary
        print(f"\n" + "=" * 80)
        print(f"🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print(f"=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\n📊 Overall Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Test Suites Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL SHIFT & STAFF AVAILABILITY API TESTS PASSED!")
            print(f"✅ Unassigned Shifts API: Returns shifts without assigned staff")
            print(f"✅ Shift Requests API: Staff can request shifts, admin can approve/reject")
            print(f"✅ Staff Availability API: CRUD operations for availability records")
            print(f"✅ Notifications API: User notifications with read functionality")
            print(f"✅ Assignment Conflicts API: Conflict checking for admin assignments")
        else:
            print(f"\n⚠️  Some tests failed - see details above")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = ShiftAvailabilityAPITester()
    tester.run_comprehensive_tests()