#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Review Request Features
Focus: Pay Calculation Bug Fix, Enhanced Hour Tracking, Tax Calculations, Data Integrity
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class ComprehensiveBackendTester:
    def __init__(self, base_url="https://shift-master-10.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.staff_data = []
        self.roster_entries = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
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
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.status_code < 400 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def authenticate(self):
        """Authenticate with Admin/0000 credentials"""
        print(f"\n🔐 Authenticating...")
        
        login_data = {"username": "Admin", "pin": "0000"}
        success, response = self.run_test(
            "Admin Login", "POST", "api/auth/login", 200, data=login_data
        )
        
        if success:
            self.auth_token = response.get('token')
            print(f"   ✅ Authentication successful")
            return True
        else:
            print(f"   ❌ Authentication failed")
            return False

    def test_12pm_8pm_pay_calculation_bug_fix(self):
        """Test the critical 12:00PM-8:00PM pay calculation bug fix"""
        print(f"\n🎯 CRITICAL TEST: 12:00PM-8:00PM Pay Calculation Bug Fix")
        print("   Expected: 12:00PM-8:00PM weekday shifts should calculate at day rate ($336)")
        
        test_cases = [
            {
                "name": "12:00PM-8:00PM Weekday Shift (CRITICAL BUG FIX)",
                "date": "2025-01-06",  # Monday
                "start_time": "12:00",
                "end_time": "20:00",
                "expected_hours": 8.0,
                "expected_rate": 42.00,  # Day rate (NOT evening rate)
                "expected_pay": 336.00,  # 8 * 42.00
                "critical": True
            },
            {
                "name": "12:00PM-7:59PM Weekday Shift (Edge Case - Day Rate)",
                "date": "2025-01-07",  # Tuesday
                "start_time": "12:00",
                "end_time": "19:59",
                "expected_hours": 7.98,
                "expected_rate": 42.00,  # Day rate
                "expected_pay": 335.16,
                "critical": True
            },
            {
                "name": "12:00PM-8:01PM Weekday Shift (Edge Case - Evening Rate)",
                "date": "2025-01-08",  # Wednesday
                "start_time": "12:00",
                "end_time": "20:01",
                "expected_hours": 8.02,
                "expected_rate": 44.50,  # Evening rate
                "expected_pay": 356.89,
                "critical": True
            },
            {
                "name": "11:00AM-8:00PM Weekday Shift (9 hours ending at 8PM - Day Rate)",
                "date": "2025-01-09",  # Thursday
                "start_time": "11:00",
                "end_time": "20:00",
                "expected_hours": 9.0,
                "expected_rate": 42.00,  # Day rate
                "expected_pay": 378.00,
                "critical": True
            }
        ]
        
        critical_tests_passed = 0
        critical_tests_total = sum(1 for tc in test_cases if tc.get('critical', False))
        
        for test_case in test_cases:
            is_critical = test_case.get('critical', False)
            print(f"\n   {'🎯 CRITICAL: ' if is_critical else ''}Testing: {test_case['name']}")
            
            roster_entry = {
                "id": "",
                "date": test_case["date"],
                "shift_template_id": "bug-fix-test",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None,
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
            
            success, response = self.run_test(
                f"Create {test_case['name']}", "POST", "api/roster", 200, data=roster_entry
            )
            
            if success:
                hours_worked = response.get('hours_worked', 0)
                total_pay = response.get('total_pay', 0)
                
                print(f"      Expected: {test_case['expected_hours']}h × ${test_case['expected_rate']}/hr = ${test_case['expected_pay']}")
                print(f"      Actual: {hours_worked}h, Total pay: ${total_pay}")
                
                hours_correct = abs(hours_worked - test_case['expected_hours']) < 0.1
                pay_correct = abs(total_pay - test_case['expected_pay']) < 0.1
                
                if hours_correct and pay_correct:
                    print(f"      ✅ Pay calculation CORRECT")
                    if is_critical:
                        critical_tests_passed += 1
                else:
                    print(f"      ❌ Pay calculation INCORRECT")
                    if is_critical:
                        print(f"      🚨 CRITICAL BUG FIX TEST FAILED!")
            else:
                if is_critical:
                    print(f"      🚨 CRITICAL TEST FAILED - Could not create roster entry")
        
        print(f"\n   🎯 CRITICAL Bug Fix Tests: {critical_tests_passed}/{critical_tests_total} passed")
        
        if critical_tests_passed < critical_tests_total:
            print(f"   ❌ CRITICAL ISSUE: 12:00PM-8:00PM pay calculation bug fix needs attention!")
        else:
            print(f"   ✅ All critical 12:00PM-8:00PM bug fix tests passed!")
        
        return critical_tests_passed == critical_tests_total

    def test_enhanced_hour_tracking(self):
        """Test enhanced hour tracking features"""
        print(f"\n📊 Testing Enhanced Hour Tracking & Reporting")
        
        # Get existing roster entries
        success, roster_entries = self.run_test(
            "Get Roster for Hour Tracking Analysis", "GET", "api/roster", 200, params={"month": "2025-08"}
        )
        
        if not success or not roster_entries:
            print("   ⚠️  No roster entries found for hour tracking analysis")
            return False
        
        print(f"   Analyzing {len(roster_entries)} roster entries...")
        
        # Test 1: Verify hours_worked field is present and calculated correctly
        hours_tracking_correct = True
        assigned_entries = []
        unassigned_entries = []
        
        for i, entry in enumerate(roster_entries[:20]):
            hours_worked = entry.get('hours_worked', 0)
            start_time = entry.get('start_time', '')
            end_time = entry.get('end_time', '')
            staff_id = entry.get('staff_id')
            staff_name = entry.get('staff_name')
            total_pay = entry.get('total_pay', 0)
            
            # Calculate expected hours manually
            if start_time and end_time:
                start_hour, start_min = map(int, start_time.split(':'))
                end_hour, end_min = map(int, end_time.split(':'))
                
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min
                
                if end_minutes <= start_minutes:
                    end_minutes += 24 * 60
                
                expected_hours = (end_minutes - start_minutes) / 60.0
                
                if abs(hours_worked - expected_hours) > 0.1:
                    print(f"      Entry {i+1}: {start_time}-{end_time} = {hours_worked}h (expected {expected_hours}h) ❌")
                    hours_tracking_correct = False
                elif i < 5:
                    print(f"      Entry {i+1}: {start_time}-{end_time} = {hours_worked}h ✅")
            
            # Categorize entries by assignment status
            if staff_id or staff_name:
                assigned_entries.append(entry)
            else:
                unassigned_entries.append(entry)
        
        print(f"   📈 Hour Tracking Analysis:")
        print(f"      Total entries: {len(roster_entries)}")
        print(f"      Assigned entries: {len(assigned_entries)}")
        print(f"      Unassigned entries: {len(unassigned_entries)}")
        print(f"      Hours calculation accuracy: {'✅ Correct' if hours_tracking_correct else '❌ Issues found'}")
        
        # Test 2: Critical finding - Check if unassigned shifts have pay calculated
        unassigned_with_pay = [e for e in unassigned_entries if e.get('total_pay', 0) > 0]
        if unassigned_with_pay:
            print(f"      🚨 CRITICAL FINDING: {len(unassigned_with_pay)} unassigned shifts have pay calculated!")
            print(f"         This confirms the frontend pay summary bug - backend calculates pay for unassigned shifts")
            print(f"         Frontend should filter out unassigned shifts (staff_id=null) from pay calculations")
            
            for i, entry in enumerate(unassigned_with_pay[:3]):
                print(f"         Example {i+1}: {entry['date']} {entry['start_time']}-{entry['end_time']} = ${entry['total_pay']}")
        else:
            print(f"      ✅ No unassigned shifts have pay calculated")
        
        # Test 3: Daily totals calculation
        daily_totals = {}
        for entry in roster_entries:
            date = entry.get('date', '')
            hours = entry.get('hours_worked', 0)
            pay = entry.get('total_pay', 0)
            
            if date not in daily_totals:
                daily_totals[date] = {'shifts': 0, 'hours': 0, 'pay': 0}
            
            daily_totals[date]['shifts'] += 1
            daily_totals[date]['hours'] += hours
            daily_totals[date]['pay'] += pay
        
        print(f"\n   📅 Daily Totals Sample (first 5 days):")
        for i, (date, totals) in enumerate(sorted(daily_totals.items())[:5]):
            print(f"      {date}: {totals['shifts']} shifts, {totals['hours']:.1f}h, ${totals['pay']:.2f}")
        
        # Test 4: YTD calculations
        ytd_hours = sum(entry.get('hours_worked', 0) for entry in roster_entries)
        ytd_pay = sum(entry.get('total_pay', 0) for entry in roster_entries)
        ytd_assigned_hours = sum(entry.get('hours_worked', 0) for entry in assigned_entries)
        ytd_assigned_pay = sum(entry.get('total_pay', 0) for entry in assigned_entries)
        
        print(f"\n   📈 Year-to-Date (YTD) Calculations:")
        print(f"      Total hours (all shifts): {ytd_hours:.1f}h")
        print(f"      Total pay (all shifts): ${ytd_pay:.2f}")
        print(f"      Assigned hours only: {ytd_assigned_hours:.1f}h")
        print(f"      Assigned pay only: ${ytd_assigned_pay:.2f}")
        
        if ytd_assigned_hours > 0:
            avg_rate = ytd_assigned_pay / ytd_assigned_hours
            print(f"      Average hourly rate (assigned): ${avg_rate:.2f}/hr")
        
        return hours_tracking_correct

    def test_data_integrity_hour_calculations(self):
        """Test data integrity for hour calculations in existing roster entries"""
        print(f"\n🔍 Testing Data Integrity - Hour Calculations")
        
        test_months = ["2025-08", "2025-09", "2025-07"]
        all_entries = []
        
        for month in test_months:
            success, entries = self.run_test(
                f"Get Roster for {month}", "GET", "api/roster", 200, params={"month": month}
            )
            if success:
                all_entries.extend(entries)
                print(f"   Found {len(entries)} entries for {month}")
        
        if not all_entries:
            print("   ⚠️  No roster entries found for data integrity testing")
            return False
        
        print(f"   Analyzing {len(all_entries)} total entries for data integrity...")
        
        # Test 1: Check for missing hours_worked field
        missing_hours = [e for e in all_entries if 'hours_worked' not in e or e.get('hours_worked') is None]
        if missing_hours:
            print(f"   ❌ {len(missing_hours)} entries missing hours_worked field")
            return False
        else:
            print(f"   ✅ All entries have hours_worked field")
        
        # Test 2: Check for zero or negative hours
        invalid_hours = [e for e in all_entries if e.get('hours_worked', 0) <= 0]
        if invalid_hours:
            print(f"   ⚠️  {len(invalid_hours)} entries have zero or negative hours")
            for entry in invalid_hours[:3]:
                print(f"      Example: {entry['date']} {entry['start_time']}-{entry['end_time']} = {entry.get('hours_worked')}h")
        else:
            print(f"   ✅ All entries have positive hours")
        
        # Test 3: Check for reasonable hour ranges
        unreasonable_hours = [e for e in all_entries if e.get('hours_worked', 0) > 24 or e.get('hours_worked', 0) < 0.5]
        if unreasonable_hours:
            print(f"   ⚠️  {len(unreasonable_hours)} entries have unreasonable hours (< 0.5 or > 24)")
        else:
            print(f"   ✅ All entries have reasonable hour ranges")
        
        # Test 4: Check active/inactive staff filtering
        success, staff_list = self.run_test("Get Active Staff", "GET", "api/staff", 200)
        
        if success:
            active_staff_ids = {staff['id'] for staff in staff_list if staff.get('active', True)}
            print(f"   Found {len(active_staff_ids)} active staff members")
            
            entries_with_inactive_staff = []
            for entry in all_entries:
                staff_id = entry.get('staff_id')
                if staff_id and staff_id not in active_staff_ids:
                    entries_with_inactive_staff.append(entry)
            
            if entries_with_inactive_staff:
                print(f"   ⚠️  {len(entries_with_inactive_staff)} entries reference inactive staff")
            else:
                print(f"   ✅ All assigned entries reference active staff")
        
        # Test 5: Check for empty/null data cases
        entries_with_nulls = []
        for entry in all_entries:
            if not entry.get('start_time') or not entry.get('end_time') or not entry.get('date'):
                entries_with_nulls.append(entry)
        
        if entries_with_nulls:
            print(f"   ❌ {len(entries_with_nulls)} entries have missing critical data")
            return False
        else:
            print(f"   ✅ All entries have required date and time data")
        
        return len(missing_hours) == 0 and len(entries_with_nulls) == 0

    def test_api_endpoints_hour_tracking(self):
        """Test API endpoints return correct data with hours_worked field"""
        print(f"\n🔌 Testing API Endpoints for Hour Tracking")
        
        # Test 1: GET /api/roster returns entries with hours_worked
        success, roster_entries = self.run_test(
            "GET /api/roster with hours_worked", "GET", "api/roster", 200, params={"month": "2025-08"}
        )
        
        if success and roster_entries:
            sample_entry = roster_entries[0]
            required_fields = ['hours_worked', 'total_pay', 'base_pay', 'date', 'start_time', 'end_time']
            
            print(f"   Sample roster entry fields:")
            for field in required_fields:
                if field in sample_entry:
                    print(f"      {field}: {sample_entry[field]} ✅")
                else:
                    print(f"      {field}: Missing ❌")
            
            # Check if hours_worked is calculated correctly
            if 'hours_worked' in sample_entry and sample_entry['hours_worked'] > 0:
                print(f"   ✅ hours_worked field present and calculated")
            else:
                print(f"   ❌ hours_worked field missing or zero")
        
        # Test 2: GET /api/staff returns active status correctly
        success, staff_list = self.run_test("GET /api/staff active status", "GET", "api/staff", 200)
        
        if success:
            active_count = sum(1 for staff in staff_list if staff.get('active', True))
            print(f"   ✅ Staff endpoint returns {active_count}/{len(staff_list)} active staff")
        
        # Test 3: Verify CRUD operations still work with enhanced data
        test_entry = {
            "id": "",
            "date": "2025-01-15",
            "shift_template_id": "api-test",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "staff_id": None,
            "staff_name": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_entry = self.run_test(
            "Create entry with hour tracking", "POST", "api/roster", 200, data=test_entry
        )
        
        if success:
            entry_id = created_entry.get('id')
            hours_worked = created_entry.get('hours_worked', 0)
            total_pay = created_entry.get('total_pay', 0)
            
            print(f"   ✅ CRUD operations working: Created entry with {hours_worked}h, ${total_pay}")
            
            # Test update
            updated_entry = {**created_entry, "end_time": "18:00"}
            success, response = self.run_test(
                "Update entry with hour tracking", "PUT", f"api/roster/{entry_id}", 200, data=updated_entry
            )
            
            if success:
                new_hours = response.get('hours_worked', 0)
                new_pay = response.get('total_pay', 0)
                print(f"   ✅ Update working: Updated to {new_hours}h, ${new_pay}")
        
        return True

    def test_edge_cases_pay_calculation(self):
        """Test edge cases around 8:00PM boundary"""
        print(f"\n⚡ Testing Edge Cases Around 8:00PM Boundary")
        
        edge_cases = [
            {
                "name": "Shift ending exactly at 8:00PM",
                "start_time": "12:00",
                "end_time": "20:00",
                "expected_rate": 42.00,  # Day rate
                "expected_pay": 336.00
            },
            {
                "name": "Shift ending 1 minute past 8:00PM",
                "start_time": "12:00", 
                "end_time": "20:01",
                "expected_rate": 44.50,  # Evening rate
                "expected_pay": 356.89
            },
            {
                "name": "Shift starting exactly at 8:00PM",
                "start_time": "20:00",
                "end_time": "22:00",
                "expected_rate": 44.50,  # Evening rate
                "expected_pay": 89.00
            },
            {
                "name": "Shift ending 1 minute before 8:00PM",
                "start_time": "12:00",
                "end_time": "19:59",
                "expected_rate": 42.00,  # Day rate
                "expected_pay": 335.16
            }
        ]
        
        edge_tests_passed = 0
        
        for i, test_case in enumerate(edge_cases):
            print(f"\n   Testing: {test_case['name']}")
            
            roster_entry = {
                "id": "",
                "date": f"2025-01-{10+i}",  # Different dates
                "shift_template_id": f"edge-test-{i}",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None,
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
            
            success, response = self.run_test(
                f"Create {test_case['name']}", "POST", "api/roster", 200, data=roster_entry
            )
            
            if success:
                total_pay = response.get('total_pay', 0)
                hours_worked = response.get('hours_worked', 0)
                
                print(f"      Result: {hours_worked}h, ${total_pay}")
                print(f"      Expected: ${test_case['expected_pay']}")
                
                if abs(total_pay - test_case['expected_pay']) < 0.1:
                    print(f"      ✅ Edge case correct")
                    edge_tests_passed += 1
                else:
                    print(f"      ❌ Edge case incorrect")
        
        print(f"\n   Edge case tests: {edge_tests_passed}/{len(edge_cases)} passed")
        return edge_tests_passed == len(edge_cases)

    def run_comprehensive_tests(self):
        """Run all comprehensive tests for the review request"""
        print("🚀 Starting Comprehensive Backend Testing for Review Request")
        print(f"   Base URL: {self.base_url}")
        print("   Focus: Pay Calculation Bug Fix, Enhanced Hour Tracking, Data Integrity")
        
        if not self.authenticate():
            print("\n❌ Authentication failed - cannot proceed")
            return False
        
        # Core tests for review request
        tests = [
            ("12:00PM-8:00PM Pay Calculation Bug Fix", self.test_12pm_8pm_pay_calculation_bug_fix),
            ("Enhanced Hour Tracking", self.test_enhanced_hour_tracking),
            ("Data Integrity - Hour Calculations", self.test_data_integrity_hour_calculations),
            ("API Endpoints Hour Tracking", self.test_api_endpoints_hour_tracking),
            ("Edge Cases Pay Calculation", self.test_edge_cases_pay_calculation),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*80}")
            print(f"🧪 {test_name}")
            print(f"{'='*80}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
                results[test_name] = False
        
        # Final summary
        print(f"\n{'='*80}")
        print(f"📊 COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        print(f"\n🎯 REVIEW REQUEST TEST RESULTS:")
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        all_passed = all(results.values())
        if all_passed:
            print(f"\n🎉 ALL REVIEW REQUEST TESTS PASSED!")
        else:
            failed_tests = [name for name, result in results.items() if not result]
            print(f"\n⚠️  FAILED TESTS: {', '.join(failed_tests)}")
        
        return all_passed

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)