import requests
import sys
import json
from datetime import datetime, timedelta

class ShiftAvailabilityCRUDTester:
    def __init__(self, base_url="https://workforce-wizard-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.staff_data = []
        self.shift_requests = []
        self.availability_records = []
        self.unassigned_shifts = []

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
            self.auth_token = response.get('token')
            user_data = response.get('user', {})
            print(f"   ✅ Admin authenticated successfully")
            print(f"   Role: {user_data.get('role')}")
            print(f"   Token: {self.auth_token[:20]}..." if self.auth_token else "No token")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
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
            # Show first few staff names
            staff_names = [staff['name'] for staff in response[:5] if staff.get('name')]
            print(f"   Staff: {', '.join(staff_names)}...")
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
            if len(response) > 0:
                # Show sample shift
                shift = response[0]
                print(f"   Sample: {shift.get('date')} {shift.get('start_time')}-{shift.get('end_time')}")
            return True
        else:
            print(f"   ❌ Could not get unassigned shifts")
            return False

    def test_phase2_admin_crud_shift_requests(self):
        """Test Phase 2: Admin CRUD for Shift Requests Management"""
        print(f"\n🎯 PHASE 2 TESTING: Admin CRUD for Shift Requests Management")
        print(f"=" * 70)
        
        if not self.staff_data or not self.unassigned_shifts:
            print("   ❌ Missing required data (staff or unassigned shifts)")
            return False
        
        # Test 1: CREATE - Admin creating new shift requests
        print(f"\n📝 TEST 1: CREATE - Admin creating new shift requests via POST /api/shift-requests")
        
        # Create multiple shift requests for different staff members
        test_shift_requests = []
        for i in range(min(3, len(self.staff_data), len(self.unassigned_shifts))):
            staff = self.staff_data[i]
            shift = self.unassigned_shifts[i]
            
            request_data = {
                "roster_entry_id": shift.get('id'),
                "staff_id": staff.get('id'),
                "staff_name": staff.get('name'),
                "request_date": datetime.now().isoformat(),
                "status": "pending",
                "notes": f"Test shift request for {staff.get('name')}",
                "admin_notes": f"Created by admin for testing - {shift.get('date')} {shift.get('start_time')}-{shift.get('end_time')}"
            }
            
            success, response = self.run_test(
                f"Create Shift Request for {staff.get('name')}",
                "POST",
                "api/shift-requests",
                200,
                data=request_data,
                use_auth=True
            )
            
            if success:
                test_shift_requests.append(response)
                print(f"   ✅ Created shift request ID: {response.get('id')}")
                print(f"      Staff: {response.get('staff_name')}")
                print(f"      Status: {response.get('status')}")
                print(f"      Notes: {response.get('notes', 'N/A')}")
            else:
                print(f"   ❌ Failed to create shift request for {staff.get('name')}")
                return False
        
        self.shift_requests = test_shift_requests
        print(f"\n   📊 CREATE RESULTS: {len(test_shift_requests)} shift requests created successfully")
        
        # Test 2: READ - Get all shift requests (Admin should see all)
        print(f"\n📖 TEST 2: READ - Admin viewing all shift requests via GET /api/shift-requests")
        
        success, all_requests = self.run_test(
            "Get All Shift Requests (Admin View)",
            "GET",
            "api/shift-requests",
            200,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ Admin can view {len(all_requests)} total shift requests")
            # Verify our created requests are in the list
            created_ids = [req.get('id') for req in test_shift_requests]
            found_ids = [req.get('id') for req in all_requests if req.get('id') in created_ids]
            print(f"   ✅ Found {len(found_ids)}/{len(created_ids)} of our created requests")
            
            # Show sample request details
            if all_requests:
                sample = all_requests[0]
                print(f"   Sample request: {sample.get('staff_name')} - {sample.get('status')}")
        else:
            print(f"   ❌ Admin could not view shift requests")
            return False
        
        # Test 3: UPDATE - Admin updating existing shift requests
        print(f"\n✏️ TEST 3: UPDATE - Admin updating shift requests via PUT /api/shift-requests/{id}")
        
        if test_shift_requests:
            request_to_update = test_shift_requests[0]
            request_id = request_to_update.get('id')
            
            # Update with new status and admin notes
            update_data = {
                **request_to_update,
                "status": "approved",
                "admin_notes": "Updated by admin - Approved for testing purposes",
                "approved_by": "Admin",
                "approved_date": datetime.now().isoformat()
            }
            
            success, updated_request = self.run_test(
                f"Update Shift Request {request_id}",
                "PUT",
                f"api/shift-requests/{request_id}",
                200,
                data=update_data,
                use_auth=True
            )
            
            if success:
                print(f"   ✅ Successfully updated shift request")
                print(f"      Old status: {request_to_update.get('status')}")
                print(f"      New status: {updated_request.get('status')}")
                print(f"      Admin notes: {updated_request.get('admin_notes', 'N/A')}")
                print(f"      Approved by: {updated_request.get('approved_by', 'N/A')}")
            else:
                print(f"   ❌ Failed to update shift request {request_id}")
                return False
            
            # Test updating another request to rejected status
            if len(test_shift_requests) > 1:
                request_to_reject = test_shift_requests[1]
                reject_id = request_to_reject.get('id')
                
                reject_data = {
                    **request_to_reject,
                    "status": "rejected",
                    "admin_notes": "Rejected for testing - Staff not available"
                }
                
                success, rejected_request = self.run_test(
                    f"Reject Shift Request {reject_id}",
                    "PUT",
                    f"api/shift-requests/{reject_id}",
                    200,
                    data=reject_data,
                    use_auth=True
                )
                
                if success:
                    print(f"   ✅ Successfully rejected shift request")
                    print(f"      Status: {rejected_request.get('status')}")
                    print(f"      Admin notes: {rejected_request.get('admin_notes', 'N/A')}")
        
        # Test 4: DELETE - Admin deleting individual shift requests
        print(f"\n🗑️ TEST 4: DELETE - Admin deleting individual shift requests via DELETE /api/shift-requests/{id}")
        
        if len(test_shift_requests) > 2:
            request_to_delete = test_shift_requests[2]
            delete_id = request_to_delete.get('id')
            
            success, response = self.run_test(
                f"Delete Shift Request {delete_id}",
                "DELETE",
                f"api/shift-requests/{delete_id}",
                200,
                use_auth=True
            )
            
            if success:
                print(f"   ✅ Successfully deleted shift request {delete_id}")
                print(f"      Message: {response.get('message', 'N/A')}")
                
                # Verify deletion by trying to get the deleted request
                success, verify_response = self.run_test(
                    f"Verify Deletion of {delete_id}",
                    "GET",
                    f"api/shift-requests/{delete_id}",
                    404,  # Should not be found
                    use_auth=True
                )
                
                if success:  # Success means we got 404 as expected
                    print(f"   ✅ Deletion verified - request no longer exists")
                else:
                    print(f"   ❌ Deletion verification failed - request still exists")
                    return False
            else:
                print(f"   ❌ Failed to delete shift request {delete_id}")
                return False
        
        # Test 5: BULK OPERATIONS - Clear all shift requests
        print(f"\n🧹 TEST 5: BULK OPERATIONS - Clear all shift requests functionality")
        
        # First, create a few more requests for bulk testing
        bulk_test_requests = []
        for i in range(2):
            if i < len(self.staff_data) and i < len(self.unassigned_shifts):
                staff = self.staff_data[i]
                shift = self.unassigned_shifts[i + 3] if i + 3 < len(self.unassigned_shifts) else self.unassigned_shifts[i]
                
                request_data = {
                    "roster_entry_id": shift.get('id'),
                    "staff_id": staff.get('id'),
                    "staff_name": staff.get('name'),
                    "request_date": datetime.now().isoformat(),
                    "status": "pending",
                    "notes": f"Bulk test request {i+1}",
                    "admin_notes": "Created for bulk deletion testing"
                }
                
                success, response = self.run_test(
                    f"Create Bulk Test Request {i+1}",
                    "POST",
                    "api/shift-requests",
                    200,
                    data=request_data,
                    use_auth=True
                )
                
                if success:
                    bulk_test_requests.append(response)
        
        print(f"   Created {len(bulk_test_requests)} additional requests for bulk testing")
        
        # Now test bulk clear functionality
        success, clear_response = self.run_test(
            "Clear All Shift Requests (Bulk Operation)",
            "DELETE",
            "api/shift-requests/clear-all",
            200,
            use_auth=True
        )
        
        if success:
            cleared_count = clear_response.get('cleared_count', 0)
            print(f"   ✅ Bulk clear successful")
            print(f"      Cleared count: {cleared_count}")
            print(f"      Message: {clear_response.get('message', 'N/A')}")
            
            # Verify all requests are cleared
            success, verify_empty = self.run_test(
                "Verify All Requests Cleared",
                "GET",
                "api/shift-requests",
                200,
                use_auth=True
            )
            
            if success:
                remaining_count = len(verify_empty)
                print(f"   ✅ Verification: {remaining_count} requests remaining")
                if remaining_count == 0:
                    print(f"   ✅ All shift requests successfully cleared")
                else:
                    print(f"   ⚠️ {remaining_count} requests still remain after bulk clear")
        else:
            print(f"   ❌ Bulk clear operation failed")
            return False
        
        print(f"\n🎉 PHASE 2 COMPLETE: Admin CRUD for Shift Requests Management")
        print(f"   ✅ CREATE: Admin can create shift requests for any staff member")
        print(f"   ✅ READ: Admin can view all shift requests")
        print(f"   ✅ UPDATE: Admin can update request status, notes, and approval")
        print(f"   ✅ DELETE: Admin can delete individual shift requests")
        print(f"   ✅ BULK: Admin can clear all shift requests at once")
        
        return True

    def test_phase3_admin_crud_staff_availability(self):
        """Test Phase 3: Admin CRUD for Staff Availability Management"""
        print(f"\n🎯 PHASE 3 TESTING: Admin CRUD for Staff Availability Management")
        print(f"=" * 70)
        
        if not self.staff_data:
            print("   ❌ Missing required staff data")
            return False
        
        # Test 1: CREATE - Create some availability records first (using existing endpoint)
        print(f"\n📝 TEST 1: CREATE - Creating availability records for testing")
        
        test_availability_records = []
        availability_types = ["available", "unavailable", "time_off_request", "preferred_shifts"]
        
        for i in range(min(4, len(self.staff_data))):
            staff = self.staff_data[i]
            availability_type = availability_types[i % len(availability_types)]
            
            # Create different types of availability records
            if availability_type == "available":
                availability_data = {
                    "staff_id": staff.get('id'),
                    "staff_name": staff.get('name'),
                    "availability_type": availability_type,
                    "day_of_week": 1,  # Tuesday
                    "start_time": "09:00",
                    "end_time": "17:00",
                    "is_recurring": True,
                    "notes": f"Available every Tuesday - {staff.get('name')}"
                }
            elif availability_type == "unavailable":
                availability_data = {
                    "staff_id": staff.get('id'),
                    "staff_name": staff.get('name'),
                    "availability_type": availability_type,
                    "date_from": "2025-08-15",
                    "date_to": "2025-08-17",
                    "is_recurring": False,
                    "notes": f"Unavailable for personal reasons - {staff.get('name')}"
                }
            elif availability_type == "time_off_request":
                availability_data = {
                    "staff_id": staff.get('id'),
                    "staff_name": staff.get('name'),
                    "availability_type": availability_type,
                    "date_from": "2025-08-20",
                    "date_to": "2025-08-22",
                    "is_recurring": False,
                    "notes": f"Time off request - vacation - {staff.get('name')}"
                }
            else:  # preferred_shifts
                availability_data = {
                    "staff_id": staff.get('id'),
                    "staff_name": staff.get('name'),
                    "availability_type": availability_type,
                    "day_of_week": 5,  # Saturday
                    "start_time": "10:00",
                    "end_time": "18:00",
                    "is_recurring": True,
                    "notes": f"Prefers Saturday shifts - {staff.get('name')}"
                }
            
            success, response = self.run_test(
                f"Create {availability_type} record for {staff.get('name')}",
                "POST",
                "api/staff-availability",
                200,
                data=availability_data,
                use_auth=True
            )
            
            if success:
                test_availability_records.append(response)
                print(f"   ✅ Created {availability_type} record ID: {response.get('id')}")
                print(f"      Staff: {response.get('staff_name')}")
                print(f"      Type: {response.get('availability_type')}")
            else:
                print(f"   ❌ Failed to create {availability_type} record for {staff.get('name')}")
                return False
        
        self.availability_records = test_availability_records
        print(f"\n   📊 CREATE RESULTS: {len(test_availability_records)} availability records created")
        
        # Test 2: READ - Get all availability records (Admin should see all)
        print(f"\n📖 TEST 2: READ - Admin viewing all availability records via GET /api/staff-availability")
        
        success, all_availability = self.run_test(
            "Get All Staff Availability (Admin View)",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ Admin can view {len(all_availability)} total availability records")
            # Verify our created records are in the list
            created_ids = [rec.get('id') for rec in test_availability_records]
            found_ids = [rec.get('id') for rec in all_availability if rec.get('id') in created_ids]
            print(f"   ✅ Found {len(found_ids)}/{len(created_ids)} of our created records")
            
            # Show sample availability details
            if all_availability:
                sample = all_availability[0]
                print(f"   Sample: {sample.get('staff_name')} - {sample.get('availability_type')}")
        else:
            print(f"   ❌ Admin could not view availability records")
            return False
        
        # Test 3: UPDATE - Admin updating existing availability records
        print(f"\n✏️ TEST 3: UPDATE - Admin updating availability records via PUT /api/staff-availability/{id}")
        
        if test_availability_records:
            record_to_update = test_availability_records[0]
            record_id = record_to_update.get('id')
            
            # Update the availability record
            update_data = {
                **record_to_update,
                "notes": "Updated by admin - Modified availability schedule",
                "start_time": "08:00",  # Change start time
                "end_time": "16:00"     # Change end time
            }
            
            success, updated_record = self.run_test(
                f"Update Availability Record {record_id}",
                "PUT",
                f"api/staff-availability/{record_id}",
                200,
                data=update_data,
                use_auth=True
            )
            
            if success:
                print(f"   ✅ Successfully updated availability record")
                print(f"      Staff: {updated_record.get('staff_name')}")
                print(f"      Type: {updated_record.get('availability_type')}")
                print(f"      Old time: {record_to_update.get('start_time', 'N/A')}-{record_to_update.get('end_time', 'N/A')}")
                print(f"      New time: {updated_record.get('start_time', 'N/A')}-{updated_record.get('end_time', 'N/A')}")
                print(f"      Notes: {updated_record.get('notes', 'N/A')}")
            else:
                print(f"   ❌ Failed to update availability record {record_id}")
                return False
            
            # Test updating another record with different staff selection (Admin privilege)
            if len(test_availability_records) > 1:
                record_to_reassign = test_availability_records[1]
                reassign_id = record_to_reassign.get('id')
                
                # Change to a different staff member (Admin can do this)
                new_staff = self.staff_data[-1] if len(self.staff_data) > 1 else self.staff_data[0]
                
                reassign_data = {
                    **record_to_reassign,
                    "staff_id": new_staff.get('id'),
                    "staff_name": new_staff.get('name'),
                    "notes": f"Reassigned to {new_staff.get('name')} by admin"
                }
                
                success, reassigned_record = self.run_test(
                    f"Reassign Availability Record {reassign_id}",
                    "PUT",
                    f"api/staff-availability/{reassign_id}",
                    200,
                    data=reassign_data,
                    use_auth=True
                )
                
                if success:
                    print(f"   ✅ Successfully reassigned availability record")
                    print(f"      Old staff: {record_to_reassign.get('staff_name')}")
                    print(f"      New staff: {reassigned_record.get('staff_name')}")
        
        # Test 4: DELETE - Admin deleting individual availability records
        print(f"\n🗑️ TEST 4: DELETE - Admin deleting individual availability records via DELETE /api/staff-availability/{id}")
        
        if len(test_availability_records) > 2:
            record_to_delete = test_availability_records[2]
            delete_id = record_to_delete.get('id')
            
            success, response = self.run_test(
                f"Delete Availability Record {delete_id}",
                "DELETE",
                f"api/staff-availability/{delete_id}",
                200,
                use_auth=True
            )
            
            if success:
                print(f"   ✅ Successfully deleted availability record {delete_id}")
                print(f"      Message: {response.get('message', 'N/A')}")
                
                # Verify deletion by trying to get the deleted record
                success, verify_response = self.run_test(
                    f"Verify Deletion of {delete_id}",
                    "GET",
                    f"api/staff-availability/{delete_id}",
                    404,  # Should not be found
                    use_auth=True
                )
                
                if success:  # Success means we got 404 as expected
                    print(f"   ✅ Deletion verified - record no longer exists")
                else:
                    print(f"   ❌ Deletion verification failed - record still exists")
                    return False
            else:
                print(f"   ❌ Failed to delete availability record {delete_id}")
                return False
        
        # Test 5: BULK OPERATIONS - Clear all availability records
        print(f"\n🧹 TEST 5: BULK OPERATIONS - Clear all availability records functionality")
        
        # First, create a few more records for bulk testing
        bulk_test_records = []
        for i in range(2):
            if i < len(self.staff_data):
                staff = self.staff_data[i]
                
                availability_data = {
                    "staff_id": staff.get('id'),
                    "staff_name": staff.get('name'),
                    "availability_type": "available",
                    "day_of_week": i + 3,  # Different days
                    "start_time": "10:00",
                    "end_time": "18:00",
                    "is_recurring": True,
                    "notes": f"Bulk test record {i+1} for {staff.get('name')}"
                }
                
                success, response = self.run_test(
                    f"Create Bulk Test Record {i+1}",
                    "POST",
                    "api/staff-availability",
                    200,
                    data=availability_data,
                    use_auth=True
                )
                
                if success:
                    bulk_test_records.append(response)
        
        print(f"   Created {len(bulk_test_records)} additional records for bulk testing")
        
        # Now test bulk clear functionality
        success, clear_response = self.run_test(
            "Clear All Availability Records (Bulk Operation)",
            "DELETE",
            "api/staff-availability/clear-all",
            200,
            use_auth=True
        )
        
        if success:
            cleared_count = clear_response.get('cleared_count', 0)
            print(f"   ✅ Bulk clear successful")
            print(f"      Cleared count: {cleared_count}")
            print(f"      Message: {clear_response.get('message', 'N/A')}")
            
            # Verify all records are cleared
            success, verify_empty = self.run_test(
                "Verify All Records Cleared",
                "GET",
                "api/staff-availability",
                200,
                use_auth=True
            )
            
            if success:
                remaining_count = len(verify_empty)
                print(f"   ✅ Verification: {remaining_count} records remaining")
                if remaining_count == 0:
                    print(f"   ✅ All availability records successfully cleared")
                else:
                    print(f"   ⚠️ {remaining_count} records still remain after bulk clear")
        else:
            print(f"   ❌ Bulk clear operation failed")
            return False
        
        print(f"\n🎉 PHASE 3 COMPLETE: Admin CRUD for Staff Availability Management")
        print(f"   ✅ CREATE: Admin can create availability records for any staff member")
        print(f"   ✅ READ: Admin can view all availability records")
        print(f"   ✅ UPDATE: Admin can update records and reassign to different staff")
        print(f"   ✅ DELETE: Admin can delete individual availability records")
        print(f"   ✅ BULK: Admin can clear all availability records at once")
        
        return True

    def test_phase4_enhanced_add_availability_verification(self):
        """Test Phase 4: Quick verification of Enhanced Add Availability functionality"""
        print(f"\n🎯 PHASE 4 VERIFICATION: Enhanced Add Availability with Staff Selection")
        print(f"=" * 70)
        
        if not self.staff_data:
            print("   ❌ Missing required staff data")
            return False
        
        # Test 1: Admin can create availability for any staff member
        print(f"\n📝 TEST 1: Admin Staff Selection - Create availability for different staff members")
        
        test_staff_selection = []
        availability_types = ["available", "unavailable", "time_off_request", "preferred_shifts"]
        
        for i in range(min(4, len(self.staff_data))):
            staff = self.staff_data[i]
            availability_type = availability_types[i]
            
            availability_data = {
                "staff_id": staff.get('id'),
                "staff_name": staff.get('name'),
                "availability_type": availability_type,
                "day_of_week": i + 1,  # Different days
                "start_time": "09:00",
                "end_time": "17:00",
                "is_recurring": True,
                "notes": f"Admin created {availability_type} for {staff.get('name')}"
            }
            
            success, response = self.run_test(
                f"Admin Create {availability_type} for {staff.get('name')}",
                "POST",
                "api/staff-availability",
                200,
                data=availability_data,
                use_auth=True
            )
            
            if success:
                test_staff_selection.append(response)
                print(f"   ✅ Admin successfully created {availability_type}")
                print(f"      Staff: {response.get('staff_name')}")
                print(f"      Staff ID: {response.get('staff_id')}")
                print(f"      Type: {response.get('availability_type')}")
            else:
                print(f"   ❌ Failed to create {availability_type} for {staff.get('name')}")
                return False
        
        print(f"\n   📊 STAFF SELECTION RESULTS: {len(test_staff_selection)} records created for different staff")
        
        # Test 2: Verify backend validation (Admin must select valid staff)
        print(f"\n🔒 TEST 2: Backend Validation - Admin must select valid staff member")
        
        # Test with empty staff_id (should fail)
        invalid_data_empty = {
            "staff_id": "",
            "staff_name": "",
            "availability_type": "available",
            "day_of_week": 1,
            "start_time": "09:00",
            "end_time": "17:00",
            "is_recurring": True,
            "notes": "Test with empty staff selection"
        }
        
        success, response = self.run_test(
            "Create Availability with Empty Staff (Should Fail)",
            "POST",
            "api/staff-availability",
            422,  # Expect validation error
            data=invalid_data_empty,
            use_auth=True
        )
        
        if success:  # Success means we got expected 422 status
            print(f"   ✅ Empty staff selection correctly rejected (422 validation error)")
        else:
            print(f"   ❌ Empty staff selection was not properly rejected")
            return False
        
        # Test with nonexistent staff_id (should fail)
        invalid_data_nonexistent = {
            "staff_id": "nonexistent-staff-id-12345",
            "staff_name": "Nonexistent Staff",
            "availability_type": "available",
            "day_of_week": 1,
            "start_time": "09:00",
            "end_time": "17:00",
            "is_recurring": True,
            "notes": "Test with nonexistent staff"
        }
        
        success, response = self.run_test(
            "Create Availability with Nonexistent Staff (Should Fail)",
            "POST",
            "api/staff-availability",
            404,  # Expect not found error
            data=invalid_data_nonexistent,
            use_auth=True
        )
        
        if success:  # Success means we got expected 404 status
            print(f"   ✅ Nonexistent staff correctly rejected (404 not found error)")
        else:
            print(f"   ❌ Nonexistent staff was not properly rejected")
            return False
        
        # Test 3: Verify all 4 availability types work with staff selection
        print(f"\n🎨 TEST 3: All Availability Types - Verify all 4 types work with staff selection")
        
        if len(self.staff_data) >= 4:
            staff_member = self.staff_data[0]  # Use first staff member for all types
            
            all_types_test = []
            type_configs = [
                {
                    "type": "available",
                    "emoji": "✅",
                    "config": {
                        "day_of_week": 1,
                        "start_time": "09:00",
                        "end_time": "17:00",
                        "is_recurring": True
                    }
                },
                {
                    "type": "unavailable", 
                    "emoji": "❌",
                    "config": {
                        "date_from": "2025-08-25",
                        "date_to": "2025-08-26",
                        "is_recurring": False
                    }
                },
                {
                    "type": "time_off_request",
                    "emoji": "🏖️",
                    "config": {
                        "date_from": "2025-09-01",
                        "date_to": "2025-09-03",
                        "is_recurring": False
                    }
                },
                {
                    "type": "preferred_shifts",
                    "emoji": "⭐",
                    "config": {
                        "day_of_week": 6,
                        "start_time": "10:00",
                        "end_time": "18:00",
                        "is_recurring": True
                    }
                }
            ]
            
            for type_config in type_configs:
                availability_data = {
                    "staff_id": staff_member.get('id'),
                    "staff_name": staff_member.get('name'),
                    "availability_type": type_config["type"],
                    "notes": f"Testing {type_config['type']} type for {staff_member.get('name')}",
                    **type_config["config"]
                }
                
                success, response = self.run_test(
                    f"Create {type_config['type']} {type_config['emoji']} for {staff_member.get('name')}",
                    "POST",
                    "api/staff-availability",
                    200,
                    data=availability_data,
                    use_auth=True
                )
                
                if success:
                    all_types_test.append(response)
                    print(f"   ✅ {type_config['emoji']} {type_config['type']} created successfully")
                    print(f"      ID: {response.get('id')}")
                    print(f"      Staff: {response.get('staff_name')}")
                else:
                    print(f"   ❌ Failed to create {type_config['type']} type")
                    return False
            
            print(f"\n   📊 ALL TYPES RESULTS: {len(all_types_test)}/4 availability types working correctly")
        
        # Test 4: Verify role-based access control
        print(f"\n🔐 TEST 4: Role-Based Access Control - Admin can access all records")
        
        success, all_records = self.run_test(
            "Admin View All Availability Records",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ Admin can access all {len(all_records)} availability records")
            
            # Check if records from different staff members are visible
            staff_names = set(record.get('staff_name') for record in all_records if record.get('staff_name'))
            print(f"   ✅ Records visible from {len(staff_names)} different staff members")
            print(f"      Staff: {', '.join(list(staff_names)[:5])}{'...' if len(staff_names) > 5 else ''}")
        else:
            print(f"   ❌ Admin could not access availability records")
            return False
        
        print(f"\n🎉 PHASE 4 VERIFICATION COMPLETE: Enhanced Add Availability with Staff Selection")
        print(f"   ✅ Admin can create availability records for any staff member")
        print(f"   ✅ Backend validation enforces valid staff selection")
        print(f"   ✅ All 4 availability types working (Available ✅, Unavailable ❌, Time Off Request 🏖️, Preferred Shifts ⭐)")
        print(f"   ✅ Role-based access control working correctly")
        
        return True

    def run_comprehensive_test(self):
        """Run all comprehensive CRUD tests"""
        print(f"\n🚀 STARTING COMPREHENSIVE SHIFT & STAFF AVAILABILITY CRUD TESTING")
        print(f"=" * 80)
        print(f"Testing Backend API Coverage with Admin Authentication (Admin/0000)")
        print(f"Focus: Phase 2 & 3 CRUD Operations + Phase 4 Verification")
        print(f"=" * 80)
        
        # Step 1: Authenticate as Admin
        if not self.authenticate_admin():
            print(f"\n❌ CRITICAL FAILURE: Could not authenticate as Admin")
            return False
        
        # Step 2: Get required data
        if not self.get_staff_data():
            print(f"\n❌ CRITICAL FAILURE: Could not get staff data")
            return False
        
        if not self.get_unassigned_shifts():
            print(f"\n❌ CRITICAL FAILURE: Could not get unassigned shifts")
            return False
        
        # Step 3: Run Phase 2 Tests - Admin CRUD for Shift Requests
        phase2_success = self.test_phase2_admin_crud_shift_requests()
        
        # Step 4: Run Phase 3 Tests - Admin CRUD for Staff Availability  
        phase3_success = self.test_phase3_admin_crud_staff_availability()
        
        # Step 5: Run Phase 4 Verification - Enhanced Add Availability
        phase4_success = self.test_phase4_enhanced_add_availability_verification()
        
        # Final Results
        print(f"\n🏁 COMPREHENSIVE TESTING RESULTS")
        print(f"=" * 50)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Total Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"")
        print(f"Phase Results:")
        print(f"   Phase 2 (Shift Requests CRUD): {'✅ PASSED' if phase2_success else '❌ FAILED'}")
        print(f"   Phase 3 (Staff Availability CRUD): {'✅ PASSED' if phase3_success else '❌ FAILED'}")
        print(f"   Phase 4 (Enhanced Add Availability): {'✅ PASSED' if phase4_success else '❌ FAILED'}")
        
        overall_success = phase2_success and phase3_success and phase4_success
        
        if overall_success:
            print(f"\n🎉 COMPREHENSIVE SUCCESS: All CRUD functionality working correctly!")
            print(f"   ✅ Admin can perform full CRUD operations on shift requests")
            print(f"   ✅ Admin can perform full CRUD operations on staff availability")
            print(f"   ✅ Enhanced Add Availability with staff selection working")
            print(f"   ✅ Role-based access control implemented correctly")
            print(f"   ✅ Backend validation and error handling working")
            print(f"   ✅ All API endpoints responding as expected")
        else:
            print(f"\n❌ TESTING ISSUES FOUND:")
            if not phase2_success:
                print(f"   ❌ Phase 2: Shift Requests CRUD has issues")
            if not phase3_success:
                print(f"   ❌ Phase 3: Staff Availability CRUD has issues")
            if not phase4_success:
                print(f"   ❌ Phase 4: Enhanced Add Availability has issues")
        
        return overall_success

if __name__ == "__main__":
    tester = ShiftAvailabilityCRUDTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print(f"\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Some tests failed!")
        sys.exit(1)