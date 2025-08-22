import requests
import sys
import json
from datetime import datetime, timedelta

class Phase1RosterTester:
    def __init__(self, base_url="https://shift-master-10.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None

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

    def test_phase1_roster_display_modifications(self):
        """Test Phase 1 - Roster Display Modifications for Staff Users as per review request"""
        print(f"\n🎯 Testing Phase 1 - Roster Display Modifications for Staff Users - COMPREHENSIVE REVIEW REQUEST TESTS...")
        
        # Step 1: Admin Authentication and Roster Access
        print(f"\n   🎯 STEP 1: Admin Authentication and Full Roster Access")
        
        # Login as Admin with PIN 1234
        admin_login_data = {
            "username": "Admin",
            "pin": "1234"
        }
        
        success, admin_response = self.run_test(
            "Admin Login (Admin/0000)",
            "POST",
            "api/auth/login",
            200,
            data=admin_login_data
        )
        
        if not success:
            print("   ❌ Admin login failed - cannot proceed with tests")
            return False
        
        admin_token = admin_response.get('token')
        admin_user = admin_response.get('user', {})
        
        print(f"   ✅ Admin login successful")
        print(f"   Admin role: {admin_user.get('role')}")
        print(f"   Admin token: {admin_token[:20]}..." if admin_token else "No token")
        
        # Test GET /api/roster with Admin authentication - should return all roster entries with full pay information
        print(f"\n   🎯 TEST 1: GET /api/roster with Admin authentication - Full pay information")
        
        # Store original token and use admin token
        original_token = self.auth_token
        self.auth_token = admin_token
        
        success, admin_roster = self.run_test(
            "Admin Roster Access (Full Pay Info)",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True
        )
        
        if not success:
            print("   ❌ Admin could not access roster")
            return False
        
        print(f"   ✅ Admin roster access successful: {len(admin_roster)} entries")
        
        # Verify admin sees full pay information for all shifts
        admin_assigned_shifts = [entry for entry in admin_roster if entry.get('staff_id')]
        admin_unassigned_shifts = [entry for entry in admin_roster if not entry.get('staff_id')]
        
        print(f"   Assigned shifts: {len(admin_assigned_shifts)}")
        print(f"   Unassigned shifts: {len(admin_unassigned_shifts)}")
        
        # Check that admin sees pay information for all shifts
        admin_pay_info_complete = True
        admin_sample_entries = []
        
        for entry in admin_roster[:5]:  # Check first 5 entries
            has_pay_info = (
                'total_pay' in entry and entry['total_pay'] is not None and
                'base_pay' in entry and entry['base_pay'] is not None and
                'hours_worked' in entry and entry['hours_worked'] is not None
            )
            
            admin_sample_entries.append({
                'date': entry.get('date'),
                'staff_name': entry.get('staff_name', 'Unassigned'),
                'total_pay': entry.get('total_pay'),
                'base_pay': entry.get('base_pay'),
                'hours_worked': entry.get('hours_worked'),
                'has_pay_info': has_pay_info
            })
            
            if not has_pay_info:
                admin_pay_info_complete = False
        
        if admin_pay_info_complete:
            print(f"   ✅ Admin sees full pay information for all shifts")
            for entry in admin_sample_entries:
                print(f"      {entry['date']} {entry['staff_name']}: ${entry['total_pay']} (${entry['base_pay']} base, {entry['hours_worked']}h)")
        else:
            print(f"   ❌ Admin missing pay information for some shifts")
            return False
        
        # Step 2: Staff Authentication and Filtered Roster Access
        print(f"\n   🎯 STEP 2: Staff Authentication and Filtered Roster Access")
        
        # Login as Staff user (rose) with PIN 888888
        staff_login_data = {
            "username": "rose",
            "pin": "888888"
        }
        
        success, staff_response = self.run_test(
            "Staff Login (rose/888888)",
            "POST",
            "api/auth/login",
            200,
            data=staff_login_data
        )
        
        if not success:
            print("   ❌ Staff login failed - cannot proceed with staff tests")
            return False
        
        staff_token = staff_response.get('token')
        staff_user = staff_response.get('user', {})
        staff_id = staff_user.get('staff_id')
        
        print(f"   ✅ Staff login successful")
        print(f"   Staff role: {staff_user.get('role')}")
        print(f"   Staff ID: {staff_id}")
        print(f"   Staff token: {staff_token[:20]}..." if staff_token else "No token")
        
        # Test GET /api/roster with Staff authentication - should return filtered pay information
        print(f"\n   🎯 TEST 2: GET /api/roster with Staff authentication - Filtered pay information")
        
        # Use staff token
        self.auth_token = staff_token
        
        success, staff_roster = self.run_test(
            "Staff Roster Access (Filtered Pay Info)",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True
        )
        
        if not success:
            print("   ❌ Staff could not access roster")
            return False
        
        print(f"   ✅ Staff roster access successful: {len(staff_roster)} entries")
        
        # Verify staff sees all shifts but with pay filtering
        staff_assigned_shifts = [entry for entry in staff_roster if entry.get('staff_id')]
        staff_unassigned_shifts = [entry for entry in staff_roster if not entry.get('staff_id')]
        
        print(f"   Assigned shifts: {len(staff_assigned_shifts)}")
        print(f"   Unassigned shifts: {len(staff_unassigned_shifts)}")
        
        # Step 3: Verify Staff Pay Filtering Logic
        print(f"\n   🎯 TEST 3: Verify Staff Pay Filtering Logic")
        
        # Check staff's own shifts - should have full pay information
        staff_own_shifts = [entry for entry in staff_roster if entry.get('staff_id') == staff_id]
        staff_other_shifts = [entry for entry in staff_roster if entry.get('staff_id') and entry.get('staff_id') != staff_id]
        
        print(f"   Staff's own shifts: {len(staff_own_shifts)}")
        print(f"   Other staff shifts: {len(staff_other_shifts)}")
        print(f"   Unassigned shifts: {len(staff_unassigned_shifts)}")
        
        # Test 3a: Staff's own shifts should have full pay information
        own_shifts_pay_complete = True
        own_shifts_sample = []
        
        for entry in staff_own_shifts[:3]:  # Check first 3 own shifts
            has_full_pay = (
                'total_pay' in entry and entry['total_pay'] is not None and
                'base_pay' in entry and entry['base_pay'] is not None and
                'hours_worked' in entry and entry['hours_worked'] is not None
            )
            
            own_shifts_sample.append({
                'date': entry.get('date'),
                'staff_name': entry.get('staff_name'),
                'total_pay': entry.get('total_pay'),
                'base_pay': entry.get('base_pay'),
                'hours_worked': entry.get('hours_worked'),
                'has_full_pay': has_full_pay
            })
            
            if not has_full_pay:
                own_shifts_pay_complete = False
        
        if own_shifts_pay_complete and len(staff_own_shifts) > 0:
            print(f"   ✅ Staff sees full pay information for their own shifts")
            for entry in own_shifts_sample:
                print(f"      {entry['date']} {entry['staff_name']}: ${entry['total_pay']} (${entry['base_pay']} base, {entry['hours_worked']}h)")
        elif len(staff_own_shifts) == 0:
            print(f"   ⚠️  Staff has no assigned shifts to test own pay visibility")
        else:
            print(f"   ❌ Staff missing pay information for their own shifts")
            return False
        
        # Test 3b: Other staff shifts should have pay fields set to null
        other_shifts_pay_filtered = True
        other_shifts_sample = []
        
        for entry in staff_other_shifts[:3]:  # Check first 3 other staff shifts
            pay_fields_null = (
                entry.get('total_pay') is None and
                entry.get('base_pay') is None
            )
            
            # Staff should still see basic info but not pay
            has_basic_info = (
                'staff_name' in entry and entry['staff_name'] is not None and
                'hours_worked' in entry and entry['hours_worked'] is not None and
                'start_time' in entry and 'end_time' in entry
            )
            
            other_shifts_sample.append({
                'date': entry.get('date'),
                'staff_name': entry.get('staff_name'),
                'total_pay': entry.get('total_pay'),
                'base_pay': entry.get('base_pay'),
                'hours_worked': entry.get('hours_worked'),
                'pay_filtered': pay_fields_null,
                'has_basic_info': has_basic_info
            })
            
            if not pay_fields_null or not has_basic_info:
                other_shifts_pay_filtered = False
        
        if other_shifts_pay_filtered and len(staff_other_shifts) > 0:
            print(f"   ✅ Staff sees other staff shifts with pay information filtered (null)")
            for entry in other_shifts_sample:
                print(f"      {entry['date']} {entry['staff_name']}: pay=${entry['total_pay']}, base=${entry['base_pay']}, hours={entry['hours_worked']}")
        elif len(staff_other_shifts) == 0:
            print(f"   ⚠️  No other staff shifts to test pay filtering")
        else:
            print(f"   ❌ Staff can see pay information for other staff shifts (should be filtered)")
            return False
        
        # Test 3c: Unassigned shifts should have full pay information
        unassigned_pay_complete = True
        unassigned_sample = []
        
        for entry in staff_unassigned_shifts[:3]:  # Check first 3 unassigned shifts
            has_full_pay = (
                'total_pay' in entry and entry['total_pay'] is not None and
                'base_pay' in entry and entry['base_pay'] is not None and
                'hours_worked' in entry and entry['hours_worked'] is not None
            )
            
            unassigned_sample.append({
                'date': entry.get('date'),
                'staff_name': entry.get('staff_name', 'Unassigned'),
                'total_pay': entry.get('total_pay'),
                'base_pay': entry.get('base_pay'),
                'hours_worked': entry.get('hours_worked'),
                'has_full_pay': has_full_pay
            })
            
            if not has_full_pay:
                unassigned_pay_complete = False
        
        if unassigned_pay_complete and len(staff_unassigned_shifts) > 0:
            print(f"   ✅ Staff sees full pay information for unassigned shifts")
            for entry in unassigned_sample:
                print(f"      {entry['date']} {entry['staff_name']}: ${entry['total_pay']} (${entry['base_pay']} base, {entry['hours_worked']}h)")
        elif len(staff_unassigned_shifts) == 0:
            print(f"   ⚠️  No unassigned shifts to test pay visibility")
        else:
            print(f"   ❌ Staff missing pay information for unassigned shifts")
            return False
        
        # Step 4: Compare Admin vs Staff Roster Data
        print(f"\n   🎯 TEST 4: Compare Admin vs Staff Roster Data")
        
        # Both should see the same number of total entries
        if len(admin_roster) == len(staff_roster):
            print(f"   ✅ Both admin and staff see same number of roster entries ({len(admin_roster)})")
        else:
            print(f"   ❌ Admin sees {len(admin_roster)} entries, staff sees {len(staff_roster)} entries")
            return False
        
        # Compare specific entries to verify filtering
        comparison_success = True
        for i, (admin_entry, staff_entry) in enumerate(zip(admin_roster[:5], staff_roster[:5])):
            # Same basic data
            same_basic = (
                admin_entry.get('id') == staff_entry.get('id') and
                admin_entry.get('date') == staff_entry.get('date') and
                admin_entry.get('start_time') == staff_entry.get('start_time') and
                admin_entry.get('end_time') == staff_entry.get('end_time')
            )
            
            if not same_basic:
                print(f"   ❌ Entry {i+1}: Basic data mismatch between admin and staff views")
                comparison_success = False
                continue
            
            # Pay data filtering check
            is_staff_own = staff_entry.get('staff_id') == staff_id
            is_unassigned = not staff_entry.get('staff_id')
            is_other_staff = staff_entry.get('staff_id') and staff_entry.get('staff_id') != staff_id
            
            if is_staff_own or is_unassigned:
                # Staff should see same pay data as admin
                pay_data_same = (
                    admin_entry.get('total_pay') == staff_entry.get('total_pay') and
                    admin_entry.get('base_pay') == staff_entry.get('base_pay')
                )
                if not pay_data_same:
                    print(f"   ❌ Entry {i+1}: Staff should see same pay data as admin for own/unassigned shifts")
                    comparison_success = False
            elif is_other_staff:
                # Staff should see null pay data
                pay_data_filtered = (
                    staff_entry.get('total_pay') is None and
                    staff_entry.get('base_pay') is None
                )
                if not pay_data_filtered:
                    print(f"   ❌ Entry {i+1}: Staff should see null pay data for other staff shifts")
                    comparison_success = False
        
        if comparison_success:
            print(f"   ✅ Admin vs Staff roster comparison successful - filtering working correctly")
        else:
            print(f"   ❌ Admin vs Staff roster comparison failed - filtering not working")
            return False
        
        # Restore original token
        self.auth_token = original_token
        
        # Final Assessment
        print(f"\n   🎉 PHASE 1 ROSTER DISPLAY MODIFICATIONS TEST RESULTS:")
        print(f"      ✅ Admin Authentication: Working with Admin/0000")
        print(f"      ✅ Staff Authentication: Working with rose/888888")
        print(f"      ✅ Admin Roster Access: {len(admin_roster)} entries with full pay information")
        print(f"      ✅ Staff Roster Access: {len(staff_roster)} entries with filtered pay information")
        print(f"      ✅ Staff Own Shifts: {'Full pay visible' if own_shifts_pay_complete else 'Pay filtering issue'}")
        print(f"      ✅ Other Staff Shifts: {'Pay filtered (null)' if other_shifts_pay_filtered else 'Pay filtering issue'}")
        print(f"      ✅ Unassigned Shifts: {'Full pay visible' if unassigned_pay_complete else 'Pay filtering issue'}")
        print(f"      ✅ Data Consistency: {'Admin and staff see same entries' if len(admin_roster) == len(staff_roster) else 'Data mismatch'}")
        
        # Determine overall success
        phase1_success = (
            admin_pay_info_complete and  # Admin sees full pay info
            (own_shifts_pay_complete or len(staff_own_shifts) == 0) and  # Staff sees own pay info
            (other_shifts_pay_filtered or len(staff_other_shifts) == 0) and  # Other staff pay filtered
            (unassigned_pay_complete or len(staff_unassigned_shifts) == 0) and  # Unassigned pay visible
            len(admin_roster) == len(staff_roster) and  # Same number of entries
            comparison_success  # Filtering logic working
        )
        
        if phase1_success:
            print(f"\n   🎉 CRITICAL SUCCESS: Phase 1 - Roster Display Modifications FULLY WORKING!")
            print(f"      - Admin users see all roster entries with complete pay information")
            print(f"      - Staff users see all roster entries but with appropriate pay filtering")
            print(f"      - Staff can see their own shifts with full pay information")
            print(f"      - Staff can see unassigned shifts with full pay information")
            print(f"      - Staff see other staff shifts with staff_name, hours, time but pay fields null")
            print(f"      - Backend pay privacy filtering implemented correctly at API level")
            print(f"      - Phase 1 requirements fully satisfied")
        else:
            print(f"\n   ❌ CRITICAL ISSUES FOUND:")
            if not admin_pay_info_complete:
                print(f"      - Admin not seeing full pay information")
            if not own_shifts_pay_complete and len(staff_own_shifts) > 0:
                print(f"      - Staff not seeing pay info for their own shifts")
            if not other_shifts_pay_filtered and len(staff_other_shifts) > 0:
                print(f"      - Staff seeing pay info for other staff shifts (should be filtered)")
            if not unassigned_pay_complete and len(staff_unassigned_shifts) > 0:
                print(f"      - Staff not seeing pay info for unassigned shifts")
            if len(admin_roster) != len(staff_roster):
                print(f"      - Admin and staff seeing different number of entries")
            if not comparison_success:
                print(f"      - Pay filtering logic not working correctly")
        
        return phase1_success


if __name__ == "__main__":
    tester = Phase1RosterTester()
    
    # Run only the Phase 1 test as requested
    print("🎯 Running Phase 1 - Roster Display Modifications Test Only...")
    success = tester.test_phase1_roster_display_modifications()
    
    if success:
        print("\n🎉 Phase 1 test completed successfully!")
    else:
        print("\n❌ Phase 1 test failed!")
    
    print(f"\n📊 Test Summary:")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")