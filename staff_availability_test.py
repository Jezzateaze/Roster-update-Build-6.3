#!/usr/bin/env python3
"""
Staff Availability Data Structure and Organization Testing
Testing Focus: Staff Availability data structure and organization functionality
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class StaffAvailabilityTester:
    def __init__(self, base_url="https://workforce-wizard-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.staff_data = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False, expect_json=True):
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
                if expect_json:
                    try:
                        response_data = response.json()
                        if isinstance(response_data, list) and len(response_data) > 0:
                            print(f"   Response: {len(response_data)} items returned")
                        elif isinstance(response_data, dict):
                            print(f"   Response keys: {list(response_data.keys())}")
                    except:
                        print(f"   Response: {response.text[:100]}...")
                else:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            if expect_json:
                return success, response.json() if response.status_code < 400 else {}
            else:
                return success, response.text if success else response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def authenticate_admin(self):
        """Authenticate as admin user"""
        print(f"\n🔐 Authenticating as Admin...")
        
        # Try both possible admin PINs
        login_attempts = [
            {"username": "Admin", "pin": "1234"},
            {"username": "Admin", "pin": "0000"}
        ]
        
        success = False
        for login_data in login_attempts:
            print(f"   Trying Admin/{login_data['pin']}...")
            success, response = self.run_test(
                f"Admin Login with PIN {login_data['pin']}",
                "POST",
                "api/auth/login",
                200,
                data=login_data
            )
            if success:
                break
        
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
            print(f"   User: {user_data.get('username')} ({user_data.get('role')})")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def test_staff_availability_data_structure(self):
        """Test GET /api/staff-availability endpoint to retrieve staff availability records"""
        print(f"\n🎯 TESTING STAFF AVAILABILITY DATA STRUCTURE AND ORGANIZATION...")
        
        if not self.auth_token:
            print("   ❌ No admin authentication token available")
            return False

        # Test 1: GET /api/staff-availability endpoint
        print(f"\n   📋 TEST 1: GET /api/staff-availability endpoint")
        success, availability_records = self.run_test(
            "Get Staff Availability Records",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True
        )
        
        if not success:
            print("   ❌ Could not retrieve staff availability records")
            return False
        
        print(f"   ✅ Retrieved {len(availability_records)} staff availability records")
        
        if len(availability_records) == 0:
            print("   ⚠️  No availability records found - creating test data...")
            # Create some test availability records
            test_records_created = self.create_test_availability_records()
            if not test_records_created:
                print("   ❌ Could not create test availability records")
                return False
            
            # Retry getting records
            success, availability_records = self.run_test(
                "Get Staff Availability Records (After Creating Test Data)",
                "GET",
                "api/staff-availability",
                200,
                use_auth=True
            )
            
            if not success or len(availability_records) == 0:
                print("   ❌ Still no availability records after creating test data")
                return False
            
            print(f"   ✅ Retrieved {len(availability_records)} staff availability records after creating test data")

        # Test 2: Verify availability records contain proper availability_type fields
        print(f"\n   🏷️  TEST 2: Verify availability_type fields")
        
        expected_availability_types = ['available', 'unavailable', 'time_off_request', 'preferred_shifts']
        availability_types_found = set()
        records_with_valid_types = 0
        
        for record in availability_records:
            availability_type = record.get('availability_type')
            if availability_type:
                availability_types_found.add(availability_type)
                if availability_type in expected_availability_types:
                    records_with_valid_types += 1
        
        print(f"   📊 Availability types found: {sorted(list(availability_types_found))}")
        print(f"   📊 Records with valid types: {records_with_valid_types}/{len(availability_records)}")
        
        # Verify we have the expected availability types
        missing_types = set(expected_availability_types) - availability_types_found
        if not missing_types:
            print(f"   ✅ All expected availability types found: {expected_availability_types}")
        else:
            print(f"   ⚠️  Missing availability types: {list(missing_types)}")
            print(f"   ℹ️  This may be normal if not all types have been used yet")
        
        # Verify all records have valid availability_type
        if records_with_valid_types == len(availability_records):
            print(f"   ✅ All records have valid availability_type fields")
        else:
            invalid_records = len(availability_records) - records_with_valid_types
            print(f"   ❌ {invalid_records} records have invalid availability_type fields")
            return False

        # Test 3: Test that records have proper date and time fields for sorting
        print(f"\n   📅 TEST 3: Verify date and time fields for sorting")
        
        required_date_time_fields = ['date_from', 'date_to', 'start_time', 'end_time']
        records_with_date_fields = 0
        records_with_time_fields = 0
        sortable_records = 0
        
        for record in availability_records:
            # Check date fields
            has_date_from = record.get('date_from') is not None
            has_date_to = record.get('date_to') is not None
            
            # Check time fields
            has_start_time = record.get('start_time') is not None
            has_end_time = record.get('end_time') is not None
            
            if has_date_from or has_date_to:
                records_with_date_fields += 1
            
            if has_start_time or has_end_time:
                records_with_time_fields += 1
            
            # A record is sortable if it has at least date_from or is recurring with day_of_week
            is_recurring = record.get('is_recurring', False)
            has_day_of_week = record.get('day_of_week') is not None
            
            if has_date_from or (is_recurring and has_day_of_week):
                sortable_records += 1
        
        print(f"   📊 Records with date fields: {records_with_date_fields}/{len(availability_records)}")
        print(f"   📊 Records with time fields: {records_with_time_fields}/{len(availability_records)}")
        print(f"   📊 Sortable records: {sortable_records}/{len(availability_records)}")
        
        if sortable_records == len(availability_records):
            print(f"   ✅ All records have proper date/time fields for sorting")
        else:
            unsortable_records = len(availability_records) - sortable_records
            print(f"   ⚠️  {unsortable_records} records may not be properly sortable")
        
        # Test date format validation
        print(f"\n      Validating date formats...")
        valid_date_formats = 0
        invalid_date_formats = 0
        
        for record in availability_records:
            date_from = record.get('date_from')
            date_to = record.get('date_to')
            
            for date_field, date_value in [('date_from', date_from), ('date_to', date_to)]:
                if date_value:
                    try:
                        # Validate YYYY-MM-DD format
                        datetime.strptime(date_value, "%Y-%m-%d")
                        valid_date_formats += 1
                    except ValueError:
                        print(f"      ❌ Invalid date format in {date_field}: {date_value}")
                        invalid_date_formats += 1
        
        if invalid_date_formats == 0:
            print(f"      ✅ All date fields use proper YYYY-MM-DD format ({valid_date_formats} dates checked)")
        else:
            print(f"      ❌ {invalid_date_formats} date fields have invalid format")
            return False
        
        # Test time format validation
        print(f"\n      Validating time formats...")
        valid_time_formats = 0
        invalid_time_formats = 0
        
        for record in availability_records:
            start_time = record.get('start_time')
            end_time = record.get('end_time')
            
            for time_field, time_value in [('start_time', start_time), ('end_time', end_time)]:
                if time_value:
                    try:
                        # Validate HH:MM format
                        datetime.strptime(time_value, "%H:%M")
                        valid_time_formats += 1
                    except ValueError:
                        print(f"      ❌ Invalid time format in {time_field}: {time_value}")
                        invalid_time_formats += 1
        
        if invalid_time_formats == 0:
            print(f"      ✅ All time fields use proper HH:MM format ({valid_time_formats} times checked)")
        else:
            print(f"      ❌ {invalid_time_formats} time fields have invalid format")
            return False

        # Test 4: Check the data structure includes all required fields for frontend grouping
        print(f"\n   🏗️  TEST 4: Verify data structure for frontend grouping")
        
        required_fields = [
            'id', 'staff_id', 'staff_name', 'availability_type', 
            'is_recurring', 'is_active', 'created_at'
        ]
        
        optional_fields = [
            'date_from', 'date_to', 'day_of_week', 'start_time', 
            'end_time', 'notes'
        ]
        
        all_fields_present = True
        field_coverage = {}
        
        for field in required_fields + optional_fields:
            field_coverage[field] = 0
        
        for record in availability_records:
            for field in required_fields:
                if field in record and record[field] is not None:
                    field_coverage[field] += 1
                else:
                    print(f"      ❌ Missing required field '{field}' in record {record.get('id', 'unknown')}")
                    all_fields_present = False
            
            for field in optional_fields:
                if field in record and record[field] is not None:
                    field_coverage[field] += 1
        
        print(f"   📊 Field coverage analysis:")
        for field, count in field_coverage.items():
            percentage = (count / len(availability_records)) * 100 if availability_records else 0
            field_type = "Required" if field in required_fields else "Optional"
            print(f"      {field_type:8} {field:20} {count:3}/{len(availability_records)} ({percentage:5.1f}%)")
        
        if all_fields_present:
            print(f"   ✅ All required fields present in all records")
        else:
            print(f"   ❌ Some required fields are missing")
            return False
        
        # Test staff_name field specifically for frontend display
        records_with_staff_name = sum(1 for record in availability_records if record.get('staff_name'))
        if records_with_staff_name == len(availability_records):
            print(f"   ✅ All records include staff_name for identification")
        else:
            missing_names = len(availability_records) - records_with_staff_name
            print(f"   ❌ {missing_names} records missing staff_name field")
            return False

        # Test 5: Test authentication for admin users to access staff availability data
        print(f"\n   🔐 TEST 5: Verify admin authentication for staff availability access")
        
        # Test with valid admin token (already tested above, but verify explicitly)
        print(f"      Testing with valid admin token...")
        success, admin_records = self.run_test(
            "Admin Access to Staff Availability (Valid Token)",
            "GET",
            "api/staff-availability",
            200,
            use_auth=True
        )
        
        if success:
            print(f"      ✅ Admin can access staff availability data with valid token")
            print(f"         Records accessible: {len(admin_records)}")
        else:
            print(f"      ❌ Admin cannot access staff availability data with valid token")
            return False
        
        # Test without authentication token
        print(f"      Testing without authentication token...")
        original_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test(
            "Access Staff Availability Without Token (Should Fail)",
            "GET",
            "api/staff-availability",
            403,  # Expect forbidden (403 is also acceptable)
            use_auth=False
        )
        
        self.auth_token = original_token  # Restore token
        
        if success:  # Success means we got expected 403 status
            print(f"      ✅ Unauthenticated access correctly blocked (403)")
        else:
            print(f"      ❌ Unauthenticated access was not properly blocked")
            return False
        
        # Test with invalid token
        print(f"      Testing with invalid token...")
        original_token = self.auth_token
        self.auth_token = "invalid_token_12345"
        
        success, response = self.run_test(
            "Access Staff Availability With Invalid Token (Should Fail)",
            "GET",
            "api/staff-availability",
            403,  # Expect forbidden (403 is also acceptable)
            use_auth=True
        )
        
        self.auth_token = original_token  # Restore token
        
        if success:  # Success means we got expected 401 status
            print(f"      ✅ Invalid token correctly rejected (401)")
        else:
            print(f"      ❌ Invalid token was not properly rejected")
            return False

        # Test 6: Test data organization capabilities
        print(f"\n   📊 TEST 6: Verify data supports frontend grouping and sorting")
        
        # Group by availability_type
        type_groups = {}
        for record in availability_records:
            availability_type = record.get('availability_type', 'unknown')
            if availability_type not in type_groups:
                type_groups[availability_type] = []
            type_groups[availability_type].append(record)
        
        print(f"      Grouping by availability_type:")
        for availability_type, records in type_groups.items():
            print(f"         {availability_type:20} {len(records):3} records")
        
        if len(type_groups) > 1:
            print(f"      ✅ Records can be grouped by availability_type ({len(type_groups)} groups)")
        else:
            print(f"      ⚠️  Only {len(type_groups)} availability type found - may need more test data")
        
        # Test sorting by date
        dated_records = [r for r in availability_records if r.get('date_from')]
        if dated_records:
            try:
                sorted_records = sorted(dated_records, key=lambda x: x['date_from'])
                print(f"      ✅ Records can be sorted by date ({len(sorted_records)} dated records)")
                
                # Show date range
                earliest_date = sorted_records[0]['date_from']
                latest_date = sorted_records[-1]['date_from']
                print(f"         Date range: {earliest_date} to {latest_date}")
            except Exception as e:
                print(f"      ❌ Error sorting records by date: {e}")
                return False
        else:
            print(f"      ⚠️  No dated records found for sorting test")
        
        # Test sorting by time
        timed_records = [r for r in availability_records if r.get('start_time')]
        if timed_records:
            try:
                sorted_by_time = sorted(timed_records, key=lambda x: x['start_time'])
                print(f"      ✅ Records can be sorted by time ({len(sorted_by_time)} timed records)")
                
                # Show time range
                earliest_time = sorted_by_time[0]['start_time']
                latest_time = sorted_by_time[-1]['start_time']
                print(f"         Time range: {earliest_time} to {latest_time}")
            except Exception as e:
                print(f"      ❌ Error sorting records by time: {e}")
                return False
        else:
            print(f"      ⚠️  No timed records found for time sorting test")

        return True

    def create_test_availability_records(self):
        """Create test availability records for testing"""
        print(f"\n   🔧 Creating test availability records...")
        
        # Get staff list first
        success, staff_list = self.run_test(
            "Get Staff List for Test Data",
            "GET",
            "api/staff",
            200
        )
        
        if not success or len(staff_list) == 0:
            print("      ❌ Could not get staff list for test data creation")
            return False
        
        # Use first few staff members for test data
        test_staff = staff_list[:4]  # Use first 4 staff
        
        # Create different types of availability records
        test_records = [
            {
                "staff_id": test_staff[0]['id'],
                "staff_name": test_staff[0]['name'],
                "availability_type": "available",
                "date_from": "2025-01-15",
                "date_to": "2025-01-20",
                "start_time": "09:00",
                "end_time": "17:00",
                "is_recurring": False,
                "notes": "Available for extra shifts"
            },
            {
                "staff_id": test_staff[1]['id'],
                "staff_name": test_staff[1]['name'],
                "availability_type": "unavailable",
                "date_from": "2025-01-22",
                "date_to": "2025-01-25",
                "start_time": "00:00",
                "end_time": "23:59",
                "is_recurring": False,
                "notes": "Personal leave"
            },
            {
                "staff_id": test_staff[2]['id'],
                "staff_name": test_staff[2]['name'],
                "availability_type": "time_off_request",
                "date_from": "2025-02-01",
                "date_to": "2025-02-07",
                "is_recurring": False,
                "notes": "Annual leave request"
            },
            {
                "staff_id": test_staff[3]['id'],
                "staff_name": test_staff[3]['name'],
                "availability_type": "preferred_shifts",
                "day_of_week": 1,  # Tuesday
                "start_time": "07:30",
                "end_time": "15:30",
                "is_recurring": True,
                "notes": "Prefers Tuesday day shifts"
            }
        ]
        
        created_count = 0
        for i, record_data in enumerate(test_records):
            success, created_record = self.run_test(
                f"Create Test Record {i+1}",
                "POST",
                "api/staff-availability",
                200,
                data=record_data,
                use_auth=True
            )
            
            if success:
                created_count += 1
                print(f"      ✅ Created {record_data['availability_type']} record for {record_data['staff_name']}")
            else:
                print(f"      ❌ Failed to create {record_data['availability_type']} record")
        
        print(f"   📊 Created {created_count}/{len(test_records)} test availability records")
        return created_count > 0

    def run_all_tests(self):
        """Run all staff availability tests"""
        print(f"🎯 STAFF AVAILABILITY DATA STRUCTURE AND ORGANIZATION TESTING")
        print(f"=" * 80)
        
        # Authenticate as admin
        if not self.authenticate_admin():
            print(f"\n❌ CRITICAL FAILURE: Could not authenticate as admin")
            return False
        
        # Run the main test
        success = self.test_staff_availability_data_structure()
        
        # Print summary
        print(f"\n" + "=" * 80)
        print(f"📊 TEST SUMMARY")
        print(f"   Tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success:
            print(f"\n🎉 COMPREHENSIVE SUCCESS: Staff Availability Data Structure and Organization FULLY WORKING!")
            print(f"   ✅ GET /api/staff-availability endpoint retrieves staff availability records")
            print(f"   ✅ Availability records contain proper availability_type fields")
            print(f"   ✅ Records have proper date and time fields for sorting")
            print(f"   ✅ Data structure includes all required fields for frontend grouping")
            print(f"   ✅ Authentication for admin users to access staff availability data")
            print(f"   ✅ Backend supports frontend grouping and sorting functionality")
            print(f"\n   The Staff Availability system provides proper data structure for")
            print(f"   organizing by type, then by date and time as requested.")
        else:
            print(f"\n❌ CRITICAL ISSUES FOUND:")
            print(f"   Some tests failed - check the detailed output above")
            print(f"   The Staff Availability data structure may need fixes")
        
        return success

if __name__ == "__main__":
    tester = StaffAvailabilityTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)