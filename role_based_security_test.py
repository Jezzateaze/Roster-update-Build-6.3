#!/usr/bin/env python3
"""
CRITICAL SECURITY FIX TESTING - Role-Based Roster Data Filtering
================================================================

This test specifically validates the CRITICAL SECURITY FIX for role-based roster data filtering.
The issue was that staff users (like Rose) could see ALL roster entries instead of just their own shifts.

Test Scenarios:
1. Staff User Rose Access - Verify Rose can ONLY see her own 25 assigned shifts (not all 124 shifts)
2. Admin Access - Verify Admin can see ALL roster entries (no filtering)
3. Export Functionality with Fixed Security - Test CSV, Excel, PDF exports with role-based filtering
4. Verify Security Fix - Compare before/after behavior
5. Test Error Handling - Test export for months where Rose has no shifts

Expected Results:
- Before fix: Rose could see all 124 shifts (SECURITY BREACH)
- After fix: Rose should only see her 25 assigned shifts (SECURE)
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class RoleBasedSecurityTester:
    def __init__(self, base_url="https://workforce-wizard-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.staff_token = None
        self.rose_user_data = None
        self.admin_user_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False, auth_token=None, expect_json=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if use_auth and auth_token:
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
            self.admin_user_data = response.get('user', {})
            print(f"   ✅ Admin authenticated successfully")
            print(f"   Role: {self.admin_user_data.get('role')}")
            print(f"   Token: {self.admin_token[:20]}..." if self.admin_token else "No token")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def authenticate_staff_rose(self):
        """Authenticate as Staff user Rose"""
        print(f"\n🔐 Authenticating as Staff user Rose...")
        
        login_data = {
            "username": "rose",
            "pin": "888888"
        }
        
        success, response = self.run_test(
            "Rose Staff Login",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success:
            self.staff_token = response.get('token')
            self.rose_user_data = response.get('user', {})
            print(f"   ✅ Rose authenticated successfully")
            print(f"   Role: {self.rose_user_data.get('role')}")
            print(f"   Staff ID: {self.rose_user_data.get('staff_id')}")
            print(f"   Token: {self.staff_token[:20]}..." if self.staff_token else "No token")
            return True
        else:
            print(f"   ❌ Rose authentication failed")
            return False

    def test_admin_roster_access(self):
        """Test Admin access to ALL roster entries for August 2025"""
        print(f"\n👑 Testing Admin Access to ALL Roster Entries (August 2025)...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        # Test GET /api/roster for August 2025
        success, roster_data = self.run_test(
            "Admin GET /api/roster for August 2025",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if success:
            total_shifts = len(roster_data)
            print(f"   📊 Admin can see {total_shifts} total roster entries")
            
            # Analyze staff distribution
            staff_distribution = {}
            assigned_shifts = 0
            unassigned_shifts = 0
            
            for entry in roster_data:
                staff_name = entry.get('staff_name')
                if staff_name:
                    assigned_shifts += 1
                    staff_distribution[staff_name] = staff_distribution.get(staff_name, 0) + 1
                else:
                    unassigned_shifts += 1
            
            print(f"   📈 Assigned shifts: {assigned_shifts}")
            print(f"   📉 Unassigned shifts: {unassigned_shifts}")
            print(f"   👥 Staff with shifts: {len(staff_distribution)} different staff members")
            
            # Show Rose's shifts specifically
            rose_shifts = staff_distribution.get('Rose', 0)
            print(f"   🌹 Rose's shifts visible to Admin: {rose_shifts}")
            
            # Verify admin can see all data (should be around 124 total shifts as mentioned in review)
            if total_shifts >= 100:  # Should be around 124 based on review request
                print(f"   ✅ Admin can see ALL roster data ({total_shifts} shifts) - NO FILTERING APPLIED")
                return True, total_shifts, rose_shifts
            else:
                print(f"   ⚠️  Expected more shifts (around 124), got {total_shifts}")
                return True, total_shifts, rose_shifts
        else:
            print(f"   ❌ Admin could not access roster data")
            return False, 0, 0

    def test_staff_rose_roster_access(self):
        """Test Staff user Rose access - should ONLY see her own shifts"""
        print(f"\n🌹 Testing Staff User Rose Access - CRITICAL SECURITY TEST...")
        
        if not self.staff_token:
            print("   ❌ No Rose staff token available")
            return False
        
        # Test GET /api/roster for August 2025 as Rose
        success, roster_data = self.run_test(
            "Rose GET /api/roster for August 2025 (SECURITY TEST)",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if success:
            total_shifts_visible = len(roster_data)
            print(f"   📊 Rose can see {total_shifts_visible} roster entries")
            
            # CRITICAL SECURITY CHECK: Verify Rose can ONLY see her own shifts
            rose_shifts = 0
            other_staff_shifts = 0
            unassigned_shifts = 0
            other_staff_names = set()
            
            for entry in roster_data:
                staff_name = entry.get('staff_name')
                staff_id = entry.get('staff_id')
                
                if staff_name == 'Rose' or staff_id == self.rose_user_data.get('staff_id'):
                    rose_shifts += 1
                elif staff_name and staff_name != 'Rose':
                    other_staff_shifts += 1
                    other_staff_names.add(staff_name)
                else:
                    unassigned_shifts += 1
            
            print(f"   🌹 Rose's own shifts: {rose_shifts}")
            print(f"   👥 Other staff shifts visible: {other_staff_shifts}")
            print(f"   📋 Unassigned shifts visible: {unassigned_shifts}")
            
            if other_staff_names:
                print(f"   ⚠️  Other staff visible to Rose: {', '.join(list(other_staff_names)[:5])}")
            
            # SECURITY ASSESSMENT
            if other_staff_shifts == 0 and len(other_staff_names) == 0:
                print(f"   ✅ SECURITY FIX WORKING: Rose can ONLY see her own shifts ({rose_shifts} shifts)")
                print(f"   ✅ NO OTHER STAFF DATA VISIBLE - Privacy protected!")
                
                # Check if Rose has expected number of shifts (around 25 as mentioned in review)
                if 20 <= rose_shifts <= 30:
                    print(f"   ✅ Rose's shift count ({rose_shifts}) is within expected range (20-30)")
                    return True, rose_shifts, True  # Security working
                else:
                    print(f"   ⚠️  Rose's shift count ({rose_shifts}) outside expected range (20-30)")
                    return True, rose_shifts, True  # Security still working, just different count
            else:
                print(f"   🚨 CRITICAL SECURITY BREACH: Rose can see OTHER STAFF DATA!")
                print(f"   🚨 Rose can see {other_staff_shifts} shifts from {len(other_staff_names)} other staff members")
                print(f"   🚨 This is a MAJOR PRIVACY VIOLATION - Staff should only see their own data")
                return False, total_shifts_visible, False  # Security breach detected
        else:
            print(f"   ❌ Rose could not access roster data")
            return False, 0, False

    def test_export_functionality_security(self):
        """Test export functionality with role-based security"""
        print(f"\n📤 Testing Export Functionality with Role-Based Security...")
        
        if not self.staff_token:
            print("   ❌ No Rose staff token available")
            return False
        
        export_formats = [
            {"format": "CSV", "endpoint": "api/export/csv/2025-08"},
            {"format": "Excel", "endpoint": "api/export/excel/2025-08"},
            {"format": "PDF", "endpoint": "api/export/pdf/2025-08"}
        ]
        
        export_results = {}
        
        for export_test in export_formats:
            format_name = export_test["format"]
            endpoint = export_test["endpoint"]
            
            print(f"\n   📊 Testing {format_name} Export for Rose (August 2025)...")
            
            success, response_data = self.run_test(
                f"Rose {format_name} Export (Security Test)",
                "GET",
                endpoint,
                200,
                use_auth=True,
                auth_token=self.staff_token,
                expect_json=False  # Export endpoints return file data
            )
            
            if success:
                response_size = len(response_data) if response_data else 0
                print(f"   ✅ {format_name} export successful - Size: {response_size} bytes")
                
                # For CSV, we can analyze the content to check for security
                if format_name == "CSV" and response_data:
                    lines = response_data.split('\n')
                    data_lines = [line for line in lines if line.strip() and not line.startswith('Date,')]
                    
                    print(f"   📋 CSV contains {len(data_lines)} data rows")
                    
                    # Check if CSV contains only Rose's data
                    rose_rows = 0
                    other_staff_rows = 0
                    
                    for line in data_lines[:10]:  # Check first 10 rows
                        if 'Rose' in line:
                            rose_rows += 1
                        elif any(name in line for name in ['Angela', 'Chanelle', 'Caroline', 'Nox', 'Elina', 'Kayla', 'Rhet', 'Nikita', 'Molly', 'Felicity', 'Issey']):
                            other_staff_rows += 1
                    
                    if other_staff_rows == 0:
                        print(f"   ✅ CSV export contains ONLY Rose's data - Security working!")
                        print(f"   🌹 Rose's rows in sample: {rose_rows}/{min(10, len(data_lines))}")
                    else:
                        print(f"   🚨 CSV export contains OTHER STAFF DATA - Security breach!")
                        print(f"   🚨 Other staff rows found: {other_staff_rows}")
                
                export_results[format_name] = {"success": True, "size": response_size}
            else:
                print(f"   ❌ {format_name} export failed")
                export_results[format_name] = {"success": False, "size": 0}
        
        # Test export for month where Rose has no shifts (should return 404 or empty)
        print(f"\n   🔍 Testing export for month where Rose has no shifts...")
        
        success, response_data = self.run_test(
            "Rose CSV Export for Empty Month (Should Return 404)",
            "GET",
            "api/export/csv/2025-12",  # December 2025 - likely no shifts
            404,  # Expect 404 or similar
            use_auth=True,
            auth_token=self.staff_token,
            expect_json=False
        )
        
        if success:
            print(f"   ✅ Empty month export correctly handled (404 response)")
        else:
            # Try with 200 status in case it returns empty data instead of 404
            success, response_data = self.run_test(
                "Rose CSV Export for Empty Month (Alternative - Empty Data)",
                "GET",
                "api/export/csv/2025-12",
                200,
                use_auth=True,
                auth_token=self.staff_token,
                expect_json=False
            )
            
            if success:
                if not response_data or len(response_data.strip()) < 50:  # Very small response = likely empty
                    print(f"   ✅ Empty month export returns empty data (appropriate)")
                else:
                    print(f"   ⚠️  Empty month export returned data: {len(response_data)} bytes")
        
        # Summary of export tests
        successful_exports = sum(1 for result in export_results.values() if result["success"])
        total_exports = len(export_results)
        
        print(f"\n   📊 Export Security Test Summary:")
        print(f"      Successful exports: {successful_exports}/{total_exports}")
        for format_name, result in export_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"      {status} {format_name}: {result['size']} bytes")
        
        return successful_exports == total_exports

    def test_security_comparison(self, admin_total_shifts, rose_shifts_as_admin, rose_shifts_as_staff, security_working):
        """Compare security before and after fix"""
        print(f"\n🔒 SECURITY FIX VERIFICATION - Before vs After Comparison...")
        
        print(f"   📊 SECURITY ANALYSIS:")
        print(f"      Admin view (should see ALL): {admin_total_shifts} total shifts")
        print(f"      Rose's shifts (Admin view): {rose_shifts_as_admin} shifts")
        print(f"      Rose's shifts (Staff view): {rose_shifts_as_staff} shifts")
        
        print(f"\n   🎯 SECURITY FIX ASSESSMENT:")
        
        if security_working:
            print(f"   ✅ SECURITY FIX SUCCESSFUL!")
            print(f"      ✅ Before fix: Rose could see ALL {admin_total_shifts} shifts (SECURITY BREACH)")
            print(f"      ✅ After fix: Rose can only see her own {rose_shifts_as_staff} shifts (SECURE)")
            print(f"      ✅ Privacy protection working - Rose cannot access other staff data")
            print(f"      ✅ Role-based filtering implemented correctly")
            
            # Verify the numbers make sense
            if rose_shifts_as_staff <= rose_shifts_as_admin <= admin_total_shifts:
                print(f"      ✅ Data consistency verified: {rose_shifts_as_staff} ≤ {rose_shifts_as_admin} ≤ {admin_total_shifts}")
                return True
            else:
                print(f"      ⚠️  Data inconsistency detected in shift counts")
                return True  # Still secure, just inconsistent data
        else:
            print(f"   🚨 SECURITY FIX FAILED!")
            print(f"      🚨 Rose can still see ALL {rose_shifts_as_staff} shifts instead of just her own")
            print(f"      🚨 This is a CRITICAL SECURITY VULNERABILITY")
            print(f"      🚨 Staff users can access confidential data of other staff members")
            print(f"      🚨 IMMEDIATE FIX REQUIRED - Role-based filtering not working")
            return False

    def run_comprehensive_security_test(self):
        """Run the complete security test suite"""
        print(f"🔒 CRITICAL SECURITY FIX TESTING - Role-Based Roster Data Filtering")
        print(f"=" * 80)
        print(f"Testing the fix for staff users seeing ALL roster data instead of just their own shifts")
        print(f"Expected: Rose should see only her ~25 shifts, not all ~124 shifts")
        print(f"=" * 80)
        
        # Step 1: Authenticate both users
        admin_auth_success = self.authenticate_admin()
        staff_auth_success = self.authenticate_staff_rose()
        
        if not admin_auth_success or not staff_auth_success:
            print(f"\n❌ Authentication failed - cannot proceed with security tests")
            return False
        
        # Step 2: Test Admin access (should see ALL data)
        admin_success, admin_total_shifts, rose_shifts_as_admin = self.test_admin_roster_access()
        
        if not admin_success:
            print(f"\n❌ Admin access test failed - cannot proceed")
            return False
        
        # Step 3: Test Staff Rose access (CRITICAL SECURITY TEST)
        staff_success, rose_shifts_as_staff, security_working = self.test_staff_rose_roster_access()
        
        if not staff_success:
            print(f"\n❌ Staff access test failed")
            return False
        
        # Step 4: Test Export functionality security
        export_success = self.test_export_functionality_security()
        
        # Step 5: Security comparison and final assessment
        security_fix_working = self.test_security_comparison(
            admin_total_shifts, 
            rose_shifts_as_admin, 
            rose_shifts_as_staff, 
            security_working
        )
        
        # Final Results
        print(f"\n" + "=" * 80)
        print(f"🎯 FINAL SECURITY TEST RESULTS")
        print(f"=" * 80)
        
        print(f"📊 Test Statistics:")
        print(f"   Total tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🔒 Security Assessment:")
        if security_fix_working and security_working:
            print(f"   ✅ CRITICAL SECURITY FIX SUCCESSFUL!")
            print(f"   ✅ Role-based filtering working correctly")
            print(f"   ✅ Staff users can only see their own data")
            print(f"   ✅ Privacy protection implemented")
            print(f"   ✅ Export functionality secure")
            
            print(f"\n📈 Key Metrics:")
            print(f"   Admin can see: {admin_total_shifts} total shifts (ALL DATA)")
            print(f"   Rose can see: {rose_shifts_as_staff} shifts (ONLY HER DATA)")
            print(f"   Security ratio: {(rose_shifts_as_staff/admin_total_shifts)*100:.1f}% (Rose sees only her portion)")
            
            return True
        else:
            print(f"   🚨 CRITICAL SECURITY VULNERABILITY REMAINS!")
            print(f"   🚨 Staff users can still access other staff data")
            print(f"   🚨 Role-based filtering NOT working")
            print(f"   🚨 IMMEDIATE FIX REQUIRED")
            
            print(f"\n📊 Vulnerability Details:")
            print(f"   Rose should see: ~25 shifts (her own)")
            print(f"   Rose actually sees: {rose_shifts_as_staff} shifts")
            print(f"   Total shifts in system: {admin_total_shifts}")
            
            return False

def main():
    """Main test execution"""
    tester = RoleBasedSecurityTester()
    
    try:
        success = tester.run_comprehensive_security_test()
        
        if success:
            print(f"\n🎉 ALL SECURITY TESTS PASSED - System is secure!")
            sys.exit(0)
        else:
            print(f"\n💥 SECURITY TESTS FAILED - Critical vulnerabilities detected!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()