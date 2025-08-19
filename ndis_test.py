import requests
import sys
import json
from datetime import datetime, timedelta

class NDISChargeRateIntegrationTester:
    def __init__(self, base_url="https://workforce-mgmt-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_roster_entries = []

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
        """Authenticate as admin user"""
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
            print(f"   ✅ Authenticated as {user_data.get('username')} ({user_data.get('role')})")
            return True
        else:
            print(f"   ❌ Authentication failed")
            return False

    def test_ndis_charge_calculation_fields(self):
        """Test that roster entries include the new NDIS charge fields"""
        print(f"\n💰 Testing NDIS Charge Calculation Fields...")
        
        # Create a test roster entry to verify NDIS fields are included
        test_entry = {
            "id": "",  # Will be auto-generated
            "date": "2025-01-20",  # Monday
            "shift_template_id": "test-ndis-fields",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "staff_id": None,
            "staff_name": None
        }
        
        success, created_entry = self.run_test(
            "Create Regular Shift for NDIS Field Testing",
            "POST",
            "api/roster",
            200,
            data=test_entry
        )
        
        if not success:
            print("   ❌ Could not create test roster entry")
            return False
        
        # Verify all required NDIS fields are present
        required_ndis_fields = [
            'ndis_hourly_charge',
            'ndis_shift_charge', 
            'ndis_total_charge',
            'ndis_line_item_code',
            'ndis_description'
        ]
        
        fields_present = 0
        for field in required_ndis_fields:
            if field in created_entry:
                fields_present += 1
                value = created_entry[field]
                print(f"   ✅ {field}: {value}")
            else:
                print(f"   ❌ Missing field: {field}")
        
        if fields_present == len(required_ndis_fields):
            print(f"   ✅ All {len(required_ndis_fields)} NDIS charge fields present")
            self.test_roster_entries.append(created_entry)
            return True
        else:
            print(f"   ❌ Only {fields_present}/{len(required_ndis_fields)} NDIS fields present")
            return False

    def test_regular_shift_ndis_charges(self):
        """Test that regular (non-sleepover) shifts calculate NDIS charges correctly"""
        print(f"\n🏢 Testing Regular Shift NDIS Charges...")
        
        # Test cases for different shift types and expected NDIS rates
        test_cases = [
            {
                "name": "Weekday Day Shift (9AM-5PM Monday)",
                "date": "2025-01-20",  # Monday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_ndis_hourly_rate": 70.23,
                "expected_ndis_code": "01_801_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Standard - Weekday Daytime",
                "expected_hours": 8.0
            },
            {
                "name": "Weekday Evening Shift (3PM-11PM Monday)",
                "date": "2025-01-20",  # Monday
                "start_time": "15:00",
                "end_time": "23:00",
                "expected_ndis_hourly_rate": 77.38,
                "expected_ndis_code": "01_802_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Standard - Weekday Evening",
                "expected_hours": 8.0
            },
            {
                "name": "Weekend Saturday Shift (9AM-5PM)",
                "date": "2025-01-25",  # Saturday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_ndis_hourly_rate": 98.83,
                "expected_ndis_code": "01_804_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Standard - Saturday",
                "expected_hours": 8.0
            },
            {
                "name": "Weekend Sunday Shift (9AM-5PM)",
                "date": "2025-01-26",  # Sunday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_ndis_hourly_rate": 122.59,
                "expected_ndis_code": "01_805_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Standard - Sunday",
                "expected_hours": 8.0
            }
        ]
        
        regular_tests_passed = 0
        
        for test_case in test_cases:
            print(f"\n   🎯 Testing: {test_case['name']}")
            
            test_entry = {
                "id": "",
                "date": test_case["date"],
                "shift_template_id": f"test-ndis-{test_case['name'].lower().replace(' ', '-')}",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None
            }
            
            success, created_entry = self.run_test(
                f"Create {test_case['name']}",
                "POST",
                "api/roster",
                200,
                data=test_entry
            )
            
            if success:
                # Verify NDIS calculations
                ndis_hourly_charge = created_entry.get('ndis_hourly_charge', 0)
                ndis_shift_charge = created_entry.get('ndis_shift_charge', 0)
                ndis_total_charge = created_entry.get('ndis_total_charge', 0)
                ndis_code = created_entry.get('ndis_line_item_code', '')
                ndis_description = created_entry.get('ndis_description', '')
                hours_worked = created_entry.get('hours_worked', 0)
                
                print(f"      Hours worked: {hours_worked}")
                print(f"      NDIS hourly rate: ${ndis_hourly_charge}")
                print(f"      NDIS shift charge: ${ndis_shift_charge}")
                print(f"      NDIS total charge: ${ndis_total_charge}")
                print(f"      NDIS code: {ndis_code}")
                print(f"      NDIS description: {ndis_description[:50]}...")
                
                # Validate calculations
                expected_total = test_case["expected_hours"] * test_case["expected_ndis_hourly_rate"]
                
                tests_passed = 0
                total_tests = 6
                
                # Test 1: Hours calculation
                if abs(hours_worked - test_case["expected_hours"]) < 0.1:
                    print(f"      ✅ Hours calculation correct: {hours_worked}")
                    tests_passed += 1
                else:
                    print(f"      ❌ Hours calculation incorrect: got {hours_worked}, expected {test_case['expected_hours']}")
                
                # Test 2: NDIS hourly rate
                if abs(ndis_hourly_charge - test_case["expected_ndis_hourly_rate"]) < 0.01:
                    print(f"      ✅ NDIS hourly rate correct: ${ndis_hourly_charge}")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS hourly rate incorrect: got ${ndis_hourly_charge}, expected ${test_case['expected_ndis_hourly_rate']}")
                
                # Test 3: NDIS shift charge should be 0 for regular shifts
                if ndis_shift_charge == 0:
                    print(f"      ✅ NDIS shift charge correct for regular shift: ${ndis_shift_charge}")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS shift charge should be 0 for regular shifts: got ${ndis_shift_charge}")
                
                # Test 4: NDIS total charge
                if abs(ndis_total_charge - expected_total) < 0.01:
                    print(f"      ✅ NDIS total charge correct: ${ndis_total_charge}")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS total charge incorrect: got ${ndis_total_charge}, expected ${expected_total}")
                
                # Test 5: NDIS line item code
                if ndis_code == test_case["expected_ndis_code"]:
                    print(f"      ✅ NDIS code correct: {ndis_code}")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS code incorrect: got '{ndis_code}', expected '{test_case['expected_ndis_code']}'")
                
                # Test 6: NDIS description
                if test_case["expected_description"] in ndis_description:
                    print(f"      ✅ NDIS description correct")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS description incorrect: got '{ndis_description}'")
                
                if tests_passed == total_tests:
                    print(f"      🎉 All NDIS calculations correct for {test_case['name']}")
                    regular_tests_passed += 1
                    self.test_roster_entries.append(created_entry)
                else:
                    print(f"      ❌ {tests_passed}/{total_tests} NDIS calculations correct")
            else:
                print(f"      ❌ Could not create test entry for {test_case['name']}")
        
        print(f"\n   📊 Regular Shift NDIS Tests: {regular_tests_passed}/{len(test_cases)} passed")
        return regular_tests_passed == len(test_cases)

    def test_sleepover_ndis_charges(self):
        """Test that sleepover shifts calculate NDIS charges correctly"""
        print(f"\n🌙 Testing Sleepover NDIS Charges...")
        
        # Test cases for sleepover shifts
        test_cases = [
            {
                "name": "Standard Sleepover (11:30PM-7:30AM)",
                "date": "2025-01-20",  # Monday night
                "start_time": "23:30",
                "end_time": "07:30",
                "wake_hours": None,  # No extra wake hours
                "expected_ndis_hourly_rate": 0.0,  # Should be 0 for sleepovers
                "expected_ndis_shift_charge": 286.56,
                "expected_ndis_total_charge": 286.56,
                "expected_ndis_code": "01_832_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Night-Time Sleepover"
            },
            {
                "name": "Sleepover with Extra Wake Hours (11:30PM-7:30AM + 3 wake hours)",
                "date": "2025-01-21",  # Tuesday night
                "start_time": "23:30",
                "end_time": "07:30",
                "wake_hours": 3.0,  # 3 hours total, 1 extra beyond the included 2
                "expected_ndis_hourly_rate": 0.0,  # Should be 0 for base sleepover
                "expected_ndis_shift_charge": 286.56,
                "expected_ndis_total_charge": 286.56 + (1.0 * 70.23),  # Base + 1 extra hour at weekday day rate
                "expected_ndis_code": "01_832_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Night-Time Sleepover"
            }
        ]
        
        sleepover_tests_passed = 0
        
        for test_case in test_cases:
            print(f"\n   🎯 Testing: {test_case['name']}")
            
            test_entry = {
                "id": "",
                "date": test_case["date"],
                "shift_template_id": f"test-sleepover-{test_case['name'].lower().replace(' ', '-')}",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": True,
                "is_public_holiday": False,
                "wake_hours": test_case.get("wake_hours"),
                "staff_id": None,
                "staff_name": None
            }
            
            success, created_entry = self.run_test(
                f"Create {test_case['name']}",
                "POST",
                "api/roster",
                200,
                data=test_entry
            )
            
            if success:
                # Verify NDIS calculations for sleepover
                ndis_hourly_charge = created_entry.get('ndis_hourly_charge', 0)
                ndis_shift_charge = created_entry.get('ndis_shift_charge', 0)
                ndis_total_charge = created_entry.get('ndis_total_charge', 0)
                ndis_code = created_entry.get('ndis_line_item_code', '')
                ndis_description = created_entry.get('ndis_description', '')
                wake_hours = created_entry.get('wake_hours', 0)
                
                print(f"      Wake hours: {wake_hours}")
                print(f"      NDIS hourly rate: ${ndis_hourly_charge}")
                print(f"      NDIS shift charge: ${ndis_shift_charge}")
                print(f"      NDIS total charge: ${ndis_total_charge}")
                print(f"      NDIS code: {ndis_code}")
                print(f"      NDIS description: {ndis_description[:50]}...")
                
                tests_passed = 0
                total_tests = 5
                
                # Test 1: NDIS hourly rate should be 0 for sleepovers
                if ndis_hourly_charge == test_case["expected_ndis_hourly_rate"]:
                    print(f"      ✅ NDIS hourly rate correct for sleepover: ${ndis_hourly_charge}")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS hourly rate incorrect: got ${ndis_hourly_charge}, expected ${test_case['expected_ndis_hourly_rate']}")
                
                # Test 2: NDIS shift charge
                if abs(ndis_shift_charge - test_case["expected_ndis_shift_charge"]) < 0.01:
                    print(f"      ✅ NDIS shift charge correct: ${ndis_shift_charge}")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS shift charge incorrect: got ${ndis_shift_charge}, expected ${test_case['expected_ndis_shift_charge']}")
                
                # Test 3: NDIS total charge (includes extra wake hours if applicable)
                if abs(ndis_total_charge - test_case["expected_ndis_total_charge"]) < 0.01:
                    print(f"      ✅ NDIS total charge correct: ${ndis_total_charge}")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS total charge incorrect: got ${ndis_total_charge}, expected ${test_case['expected_ndis_total_charge']}")
                
                # Test 4: NDIS line item code
                if ndis_code == test_case["expected_ndis_code"]:
                    print(f"      ✅ NDIS code correct: {ndis_code}")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS code incorrect: got '{ndis_code}', expected '{test_case['expected_ndis_code']}'")
                
                # Test 5: NDIS description
                if test_case["expected_description"] in ndis_description:
                    print(f"      ✅ NDIS description correct")
                    tests_passed += 1
                else:
                    print(f"      ❌ NDIS description incorrect: got '{ndis_description}'")
                
                if tests_passed == total_tests:
                    print(f"      🎉 All NDIS sleepover calculations correct for {test_case['name']}")
                    sleepover_tests_passed += 1
                    self.test_roster_entries.append(created_entry)
                else:
                    print(f"      ❌ {tests_passed}/{total_tests} NDIS sleepover calculations correct")
            else:
                print(f"      ❌ Could not create sleepover test entry for {test_case['name']}")
        
        print(f"\n   📊 Sleepover NDIS Tests: {sleepover_tests_passed}/{len(test_cases)} passed")
        return sleepover_tests_passed == len(test_cases)

    def test_ndis_vs_staff_pay(self):
        """Test that NDIS charges and staff pay calculations coexist correctly"""
        print(f"\n⚖️ Testing NDIS vs Staff Pay Calculations...")
        
        if not self.test_roster_entries:
            print("   ⚠️ No test roster entries available for comparison")
            return False
        
        # Test with a regular weekday shift
        test_entry = {
            "id": "",
            "date": "2025-01-22",  # Wednesday
            "shift_template_id": "test-ndis-vs-staff",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "staff_id": None,
            "staff_name": None
        }
        
        success, created_entry = self.run_test(
            "Create Shift for NDIS vs Staff Pay Comparison",
            "POST",
            "api/roster",
            200,
            data=test_entry
        )
        
        if not success:
            print("   ❌ Could not create test entry for comparison")
            return False
        
        # Extract both NDIS and staff pay data
        # Staff pay fields
        hours_worked = created_entry.get('hours_worked', 0)
        base_pay = created_entry.get('base_pay', 0)
        total_pay = created_entry.get('total_pay', 0)
        sleepover_allowance = created_entry.get('sleepover_allowance', 0)
        
        # NDIS charge fields
        ndis_hourly_charge = created_entry.get('ndis_hourly_charge', 0)
        ndis_shift_charge = created_entry.get('ndis_shift_charge', 0)
        ndis_total_charge = created_entry.get('ndis_total_charge', 0)
        ndis_code = created_entry.get('ndis_line_item_code', '')
        ndis_description = created_entry.get('ndis_description', '')
        
        print(f"   📊 Staff Pay Calculations:")
        print(f"      Hours worked: {hours_worked}")
        print(f"      Base pay: ${base_pay}")
        print(f"      Sleepover allowance: ${sleepover_allowance}")
        print(f"      Total staff pay: ${total_pay}")
        
        print(f"   💰 NDIS Charge Calculations:")
        print(f"      NDIS hourly rate: ${ndis_hourly_charge}")
        print(f"      NDIS shift charge: ${ndis_shift_charge}")
        print(f"      NDIS total charge: ${ndis_total_charge}")
        print(f"      NDIS code: {ndis_code}")
        print(f"      NDIS description: {ndis_description[:50]}...")
        
        # Verify both calculations are present and different
        tests_passed = 0
        total_tests = 6
        
        # Test 1: Staff pay calculations are working
        expected_staff_hourly_rate = 42.00  # Weekday day rate
        expected_staff_total = hours_worked * expected_staff_hourly_rate
        if abs(total_pay - expected_staff_total) < 0.01:
            print(f"   ✅ Staff pay calculation correct: ${total_pay}")
            tests_passed += 1
        else:
            print(f"   ❌ Staff pay calculation incorrect: got ${total_pay}, expected ${expected_staff_total}")
        
        # Test 2: NDIS charge calculations are working
        expected_ndis_hourly_rate = 70.23  # Weekday day NDIS rate
        expected_ndis_total = hours_worked * expected_ndis_hourly_rate
        if abs(ndis_total_charge - expected_ndis_total) < 0.01:
            print(f"   ✅ NDIS charge calculation correct: ${ndis_total_charge}")
            tests_passed += 1
        else:
            print(f"   ❌ NDIS charge calculation incorrect: got ${ndis_total_charge}, expected ${expected_ndis_total}")
        
        # Test 3: NDIS rates are different from staff rates
        if abs(ndis_hourly_charge - expected_staff_hourly_rate) > 0.01:
            print(f"   ✅ NDIS rates different from staff rates: ${ndis_hourly_charge} vs ${expected_staff_hourly_rate}")
            tests_passed += 1
        else:
            print(f"   ❌ NDIS rates same as staff rates - should be different")
        
        # Test 4: Both calculations coexist (both have values > 0)
        if total_pay > 0 and ndis_total_charge > 0:
            print(f"   ✅ Both staff pay and NDIS charges calculated: ${total_pay} and ${ndis_total_charge}")
            tests_passed += 1
        else:
            print(f"   ❌ Missing calculations: staff pay=${total_pay}, NDIS charge=${ndis_total_charge}")
        
        # Test 5: NDIS code is populated
        if ndis_code and len(ndis_code) > 0:
            print(f"   ✅ NDIS line item code populated: {ndis_code}")
            tests_passed += 1
        else:
            print(f"   ❌ NDIS line item code missing or empty")
        
        # Test 6: NDIS description is populated
        if ndis_description and len(ndis_description) > 0:
            print(f"   ✅ NDIS description populated")
            tests_passed += 1
        else:
            print(f"   ❌ NDIS description missing or empty")
        
        print(f"\n   📊 NDIS vs Staff Pay Tests: {tests_passed}/{total_tests} passed")
        
        if tests_passed == total_tests:
            print(f"   🎉 NDIS and staff pay calculations working independently and correctly!")
            return True
        else:
            print(f"   ❌ Issues found with NDIS vs staff pay calculations")
            return False

    def test_api_response_ndis_fields(self):
        """Test GET /api/roster endpoint returns the new NDIS fields populated correctly"""
        print(f"\n🔌 Testing API Response NDIS Fields...")
        
        # Get roster entries for the current month
        current_month = "2025-01"
        success, roster_entries = self.run_test(
            f"Get Roster with NDIS Fields for {current_month}",
            "GET",
            "api/roster",
            200,
            params={"month": current_month}
        )
        
        if not success:
            print("   ❌ Could not retrieve roster entries")
            return False
        
        if not roster_entries:
            print("   ⚠️ No roster entries found for testing")
            return False
        
        print(f"   📊 Analyzing {len(roster_entries)} roster entries...")
        
        # Check first few entries for NDIS fields
        entries_with_ndis = 0
        entries_checked = min(10, len(roster_entries))  # Check up to 10 entries
        
        required_ndis_fields = [
            'ndis_hourly_charge',
            'ndis_shift_charge', 
            'ndis_total_charge',
            'ndis_line_item_code',
            'ndis_description'
        ]
        
        for i, entry in enumerate(roster_entries[:entries_checked]):
            print(f"\n   🔍 Checking entry {i+1}: {entry.get('date')} {entry.get('start_time')}-{entry.get('end_time')}")
            
            fields_present = 0
            for field in required_ndis_fields:
                if field in entry:
                    fields_present += 1
                    value = entry[field]
                    if field in ['ndis_hourly_charge', 'ndis_shift_charge', 'ndis_total_charge']:
                        print(f"      {field}: ${value}")
                    else:
                        print(f"      {field}: {value}")
                else:
                    print(f"      ❌ Missing: {field}")
            
            if fields_present == len(required_ndis_fields):
                entries_with_ndis += 1
                print(f"      ✅ All NDIS fields present")
                
                # Verify NDIS calculations make sense
                ndis_hourly = entry.get('ndis_hourly_charge', 0)
                ndis_shift = entry.get('ndis_shift_charge', 0)
                ndis_total = entry.get('ndis_total_charge', 0)
                hours = entry.get('hours_worked', 0)
                is_sleepover = entry.get('is_sleepover', False)
                
                if is_sleepover:
                    # For sleepovers, shift charge should be > 0, hourly should be 0
                    if ndis_shift > 0 and ndis_hourly == 0:
                        print(f"      ✅ Sleepover NDIS charges correct: shift=${ndis_shift}, hourly=${ndis_hourly}")
                    else:
                        print(f"      ❌ Sleepover NDIS charges incorrect: shift=${ndis_shift}, hourly=${ndis_hourly}")
                else:
                    # For regular shifts, hourly should be > 0, shift should be 0
                    if ndis_hourly > 0 and ndis_shift == 0:
                        expected_total = hours * ndis_hourly
                        if abs(ndis_total - expected_total) < 0.01:
                            print(f"      ✅ Regular shift NDIS charges correct: {hours}h × ${ndis_hourly} = ${ndis_total}")
                        else:
                            print(f"      ❌ Regular shift total incorrect: got ${ndis_total}, expected ${expected_total}")
                    else:
                        print(f"      ❌ Regular shift NDIS charges incorrect: hourly=${ndis_hourly}, shift=${ndis_shift}")
            else:
                print(f"      ❌ Only {fields_present}/{len(required_ndis_fields)} NDIS fields present")
        
        print(f"\n   📊 API Response NDIS Fields Summary:")
        print(f"      Entries checked: {entries_checked}")
        print(f"      Entries with all NDIS fields: {entries_with_ndis}")
        print(f"      Success rate: {entries_with_ndis}/{entries_checked} ({100*entries_with_ndis/entries_checked:.1f}%)")
        
        if entries_with_ndis == entries_checked:
            print(f"   🎉 All roster entries have complete NDIS field data!")
            return True
        else:
            print(f"   ❌ Some roster entries missing NDIS field data")
            return False

    def run_comprehensive_ndis_tests(self):
        """Run all NDIS charge rate integration tests"""
        print(f"\n🎯 COMPREHENSIVE NDIS CHARGE RATE INTEGRATION TESTING")
        print(f"=" * 60)
        
        # Authenticate first
        if not self.authenticate_admin():
            print(f"\n❌ CRITICAL: Could not authenticate - aborting tests")
            return False
        
        # Run all test suites
        test_results = []
        
        # Test 1: NDIS Charge Calculation Fields
        print(f"\n" + "="*60)
        print(f"TEST SUITE 1: NDIS Charge Calculation Fields")
        print(f"="*60)
        result1 = self.test_ndis_charge_calculation_fields()
        test_results.append(("NDIS Charge Fields", result1))
        
        # Test 2: Regular Shift NDIS Charges
        print(f"\n" + "="*60)
        print(f"TEST SUITE 2: Regular Shift NDIS Charges")
        print(f"="*60)
        result2 = self.test_regular_shift_ndis_charges()
        test_results.append(("Regular Shift NDIS Charges", result2))
        
        # Test 3: Sleepover NDIS Charges
        print(f"\n" + "="*60)
        print(f"TEST SUITE 3: Sleepover NDIS Charges")
        print(f"="*60)
        result3 = self.test_sleepover_ndis_charges()
        test_results.append(("Sleepover NDIS Charges", result3))
        
        # Test 4: NDIS vs Staff Pay
        print(f"\n" + "="*60)
        print(f"TEST SUITE 4: NDIS vs Staff Pay Calculations")
        print(f"="*60)
        result4 = self.test_ndis_vs_staff_pay()
        test_results.append(("NDIS vs Staff Pay", result4))
        
        # Test 5: API Response Testing
        print(f"\n" + "="*60)
        print(f"TEST SUITE 5: API Response NDIS Fields")
        print(f"="*60)
        result5 = self.test_api_response_ndis_fields()
        test_results.append(("API Response NDIS Fields", result5))
        
        # Final Results Summary
        print(f"\n" + "="*60)
        print(f"🎯 NDIS CHARGE RATE INTEGRATION TEST RESULTS")
        print(f"="*60)
        
        passed_suites = 0
        total_suites = len(test_results)
        
        for suite_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {suite_name}")
            if result:
                passed_suites += 1
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Test Suites Passed: {passed_suites}/{total_suites}")
        print(f"   Individual Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"   Success Rate: {100*passed_suites/total_suites:.1f}%")
        
        if passed_suites == total_suites:
            print(f"\n🎉 ALL NDIS CHARGE RATE INTEGRATION TESTS PASSED!")
            print(f"   ✅ NDIS charge fields are present in roster entries")
            print(f"   ✅ Regular shift NDIS charges calculate correctly")
            print(f"   ✅ Sleepover NDIS charges calculate correctly")
            print(f"   ✅ NDIS and staff pay calculations coexist properly")
            print(f"   ✅ API responses include all NDIS fields")
            print(f"\n🚀 NDIS Charge Rate Integration is PRODUCTION READY!")
            return True
        else:
            print(f"\n❌ NDIS CHARGE RATE INTEGRATION HAS ISSUES")
            failed_suites = [name for name, result in test_results if not result]
            print(f"   Failed test suites: {', '.join(failed_suites)}")
            print(f"\n🔧 REQUIRES FIXES BEFORE PRODUCTION")
            return False

if __name__ == "__main__":
    tester = NDISChargeRateIntegrationTester()
    success = tester.run_comprehensive_ndis_tests()
    sys.exit(0 if success else 1)