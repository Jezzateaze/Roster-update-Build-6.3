import requests
import sys
import json
from datetime import datetime, timedelta

class NDISChargeRateIntegrationTester:
    def __init__(self, base_url="https://workforce-wizard-1.preview.emergentagent.com"):
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
            print(f"   ✅ Admin authenticated successfully")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def test_ndis_charge_fields_in_new_entries(self):
        """Test that new roster entries include all 5 NDIS charge fields"""
        print(f"\n🎯 TEST 1: NDIS Charge Fields Present in New Entries...")
        
        # Create a new roster entry to test NDIS fields
        test_entry = {
            "id": "",  # Will be auto-generated
            "date": "2025-01-20",  # Monday
            "shift_template_id": "ndis-test-template",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "staff_id": None,
            "staff_name": None
        }
        
        success, response = self.run_test(
            "Create New Roster Entry for NDIS Testing",
            "POST",
            "api/roster",
            200,
            data=test_entry
        )
        
        if not success:
            print("   ❌ Could not create roster entry for NDIS testing")
            return False
        
        # Check for all 5 required NDIS fields
        required_ndis_fields = [
            'ndis_hourly_charge',
            'ndis_shift_charge', 
            'ndis_total_charge',
            'ndis_line_item_code',
            'ndis_description'
        ]
        
        fields_present = 0
        for field in required_ndis_fields:
            if field in response:
                fields_present += 1
                value = response[field]
                print(f"   ✅ {field}: {value}")
            else:
                print(f"   ❌ Missing field: {field}")
        
        if fields_present == len(required_ndis_fields):
            print(f"   🎉 SUCCESS: All {len(required_ndis_fields)} NDIS fields present in new entries")
            return True
        else:
            print(f"   ❌ FAILURE: Only {fields_present}/{len(required_ndis_fields)} NDIS fields present")
            return False

    def test_regular_shift_ndis_charges(self):
        """Test NDIS charge calculations for regular shifts"""
        print(f"\n🎯 TEST 2: Regular Shift NDIS Charges Calculated Correctly...")
        
        # Test cases for different shift types with expected NDIS rates
        test_cases = [
            {
                "name": "Weekday Day Shift",
                "date": "2025-01-20",  # Monday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_ndis_rate": 70.23,
                "expected_code": "01_801_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Standard - Weekday Daytime"
            },
            {
                "name": "Weekday Evening Shift",
                "date": "2025-01-20",  # Monday
                "start_time": "18:00",
                "end_time": "22:00",
                "expected_ndis_rate": 77.38,
                "expected_code": "01_802_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Standard - Weekday Evening"
            },
            {
                "name": "Saturday Shift",
                "date": "2025-01-25",  # Saturday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_ndis_rate": 98.83,
                "expected_code": "01_804_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Standard - Saturday"
            },
            {
                "name": "Sunday Shift",
                "date": "2025-01-26",  # Sunday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_ndis_rate": 122.59,
                "expected_code": "01_805_0115_1_1",
                "expected_description": "Assistance in Supported Independent Living - Standard - Sunday"
            }
        ]
        
        regular_shift_tests_passed = 0
        
        for test_case in test_cases:
            print(f"\n   Testing: {test_case['name']}")
            
            test_entry = {
                "id": "",
                "date": test_case["date"],
                "shift_template_id": f"ndis-test-{test_case['name'].lower().replace(' ', '-')}",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None
            }
            
            success, response = self.run_test(
                f"Create {test_case['name']}",
                "POST",
                "api/roster",
                200,
                data=test_entry
            )
            
            if success:
                # Calculate expected hours and total charge
                start_hour = int(test_case["start_time"].split(":")[0])
                start_min = int(test_case["start_time"].split(":")[1])
                end_hour = int(test_case["end_time"].split(":")[0])
                end_min = int(test_case["end_time"].split(":")[1])
                
                hours = (end_hour * 60 + end_min - start_hour * 60 - start_min) / 60.0
                expected_total_charge = hours * test_case["expected_ndis_rate"]
                
                # Verify NDIS calculations
                ndis_hourly_charge = response.get('ndis_hourly_charge', 0)
                ndis_total_charge = response.get('ndis_total_charge', 0)
                ndis_code = response.get('ndis_line_item_code', '')
                ndis_description = response.get('ndis_description', '')
                
                print(f"      Hours: {hours}")
                print(f"      NDIS Hourly Rate: ${ndis_hourly_charge} (expected: ${test_case['expected_ndis_rate']})")
                print(f"      NDIS Total Charge: ${ndis_total_charge:.2f} (expected: ${expected_total_charge:.2f})")
                print(f"      NDIS Code: {ndis_code} (expected: {test_case['expected_code']})")
                print(f"      NDIS Description: {ndis_description[:50]}...")
                
                # Check if calculations are correct
                rate_correct = abs(ndis_hourly_charge - test_case["expected_ndis_rate"]) < 0.01
                total_correct = abs(ndis_total_charge - expected_total_charge) < 0.01
                code_correct = ndis_code == test_case["expected_code"]
                description_correct = test_case["expected_description"] in ndis_description
                
                if rate_correct and total_correct and code_correct and description_correct:
                    print(f"      ✅ All NDIS calculations correct")
                    regular_shift_tests_passed += 1
                else:
                    print(f"      ❌ NDIS calculation errors:")
                    if not rate_correct:
                        print(f"         Rate mismatch: got ${ndis_hourly_charge}, expected ${test_case['expected_ndis_rate']}")
                    if not total_correct:
                        print(f"         Total mismatch: got ${ndis_total_charge:.2f}, expected ${expected_total_charge:.2f}")
                    if not code_correct:
                        print(f"         Code mismatch: got '{ndis_code}', expected '{test_case['expected_code']}'")
                    if not description_correct:
                        print(f"         Description mismatch")
            else:
                print(f"      ❌ Could not create {test_case['name']}")
        
        print(f"\n   📊 Regular Shift NDIS Tests: {regular_shift_tests_passed}/{len(test_cases)} passed")
        
        if regular_shift_tests_passed == len(test_cases):
            print(f"   🎉 SUCCESS: All regular shift NDIS charges calculated correctly")
            return True
        else:
            print(f"   ❌ FAILURE: {len(test_cases) - regular_shift_tests_passed} regular shift NDIS calculations failed")
            return False

    def test_sleepover_extra_wake_hours_fix(self):
        """Test the critical sleepover extra wake hours calculation fix"""
        print(f"\n🎯 TEST 3: Sleepover Extra Wake Hours Fix (CRITICAL)...")
        print("   This test verifies the fix for sleepover shifts with extra wake hours")
        print("   Previous issue: $365.37 but expected $356.79 for 3-hour wake sleepover")
        
        # Create sleepover shift with 3 hours of wake time (1 extra hour beyond 2)
        sleepover_entry = {
            "id": "",
            "date": "2025-01-20",  # Monday (weekday)
            "shift_template_id": "ndis-sleepover-test",
            "start_time": "23:30",
            "end_time": "07:30",
            "is_sleepover": True,
            "is_public_holiday": False,
            "wake_hours": 3.0,  # 3 hours wake time (1 extra beyond 2)
            "staff_id": None,
            "staff_name": None
        }
        
        success, response = self.run_test(
            "Create Sleepover with 3 Hours Wake Time",
            "POST",
            "api/roster",
            200,
            data=sleepover_entry
        )
        
        if not success:
            print("   ❌ Could not create sleepover entry for testing")
            return False
        
        # Extract NDIS charge information
        ndis_shift_charge = response.get('ndis_shift_charge', 0)
        ndis_total_charge = response.get('ndis_total_charge', 0)
        ndis_code = response.get('ndis_line_item_code', '')
        ndis_description = response.get('ndis_description', '')
        wake_hours = response.get('wake_hours', 0)
        
        print(f"   Sleepover Details:")
        print(f"      Wake Hours: {wake_hours}")
        print(f"      NDIS Shift Charge (base): ${ndis_shift_charge}")
        print(f"      NDIS Total Charge: ${ndis_total_charge:.2f}")
        print(f"      NDIS Code: {ndis_code}")
        print(f"      NDIS Description: {ndis_description[:60]}...")
        
        # Calculate expected charges
        # Base sleepover charge: $286.56
        # Extra wake hours: 1 hour (3 - 2) at weekday_night rate $78.81
        expected_base_charge = 286.56
        expected_extra_wake_charge = 1.0 * 78.81  # 1 extra hour at $78.81/hr
        expected_total_charge = expected_base_charge + expected_extra_wake_charge
        
        print(f"\n   Expected Calculation:")
        print(f"      Base sleepover charge: ${expected_base_charge}")
        print(f"      Extra wake hours: 1 hour × $78.81/hr = ${expected_extra_wake_charge}")
        print(f"      Expected total: ${expected_total_charge:.2f}")
        
        # Verify the fix
        base_correct = abs(ndis_shift_charge - expected_base_charge) < 0.01
        total_correct = abs(ndis_total_charge - expected_total_charge) < 0.01
        
        # Check if this matches the expected fix value from review request
        review_expected = 356.79  # Value mentioned in review request
        matches_review_expectation = abs(ndis_total_charge - review_expected) < 0.01
        
        print(f"\n   Verification Results:")
        print(f"      Base charge correct: {'✅' if base_correct else '❌'}")
        print(f"      Total charge correct: {'✅' if total_correct else '❌'}")
        print(f"      Matches review expectation (${review_expected}): {'✅' if matches_review_expectation else '❌'}")
        
        if base_correct and total_correct and matches_review_expectation:
            print(f"   🎉 SUCCESS: Sleepover extra wake hours calculation FIXED!")
            print(f"      Previous issue: $365.37")
            print(f"      Current result: ${ndis_total_charge:.2f}")
            print(f"      Expected result: ${review_expected}")
            print(f"      ✅ Fix verified - using weekday_night rate ($78.81/hr) for extra wake hours")
            return True
        else:
            print(f"   ❌ FAILURE: Sleepover extra wake hours calculation still incorrect")
            if not base_correct:
                print(f"      Base charge error: got ${ndis_shift_charge}, expected ${expected_base_charge}")
            if not total_correct:
                print(f"      Total charge error: got ${ndis_total_charge:.2f}, expected ${expected_total_charge:.2f}")
            if not matches_review_expectation:
                print(f"      Review expectation error: got ${ndis_total_charge:.2f}, expected ${review_expected}")
            return False

    def test_ndis_vs_staff_pay_coexistence(self):
        """Test that NDIS charges and staff pay calculations coexist correctly"""
        print(f"\n🎯 TEST 4: NDIS vs Staff Pay Calculations Coexisting...")
        
        # Create a regular weekday shift to test both calculations
        test_entry = {
            "id": "",
            "date": "2025-01-20",  # Monday
            "shift_template_id": "ndis-staff-pay-test",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "staff_id": None,
            "staff_name": None
        }
        
        success, response = self.run_test(
            "Create Shift for NDIS vs Staff Pay Testing",
            "POST",
            "api/roster",
            200,
            data=test_entry
        )
        
        if not success:
            print("   ❌ Could not create shift for NDIS vs staff pay testing")
            return False
        
        # Extract both NDIS and staff pay information
        hours_worked = response.get('hours_worked', 0)
        
        # Staff pay fields
        base_pay = response.get('base_pay', 0)
        total_pay = response.get('total_pay', 0)
        
        # NDIS charge fields
        ndis_hourly_charge = response.get('ndis_hourly_charge', 0)
        ndis_total_charge = response.get('ndis_total_charge', 0)
        ndis_code = response.get('ndis_line_item_code', '')
        
        print(f"   Shift Details:")
        print(f"      Hours worked: {hours_worked}")
        print(f"      Date: {test_entry['date']} (Monday)")
        print(f"      Time: {test_entry['start_time']}-{test_entry['end_time']}")
        
        print(f"\n   Staff Pay Calculation:")
        print(f"      Staff hourly rate: $42.00 (weekday day)")
        print(f"      Staff base pay: ${base_pay}")
        print(f"      Staff total pay: ${total_pay}")
        
        print(f"\n   NDIS Charge Calculation:")
        print(f"      NDIS hourly rate: ${ndis_hourly_charge}")
        print(f"      NDIS total charge: ${ndis_total_charge}")
        print(f"      NDIS code: {ndis_code}")
        
        # Expected values
        expected_hours = 8.0
        expected_staff_rate = 42.00
        expected_staff_pay = expected_hours * expected_staff_rate  # $336.00
        expected_ndis_rate = 70.23
        expected_ndis_charge = expected_hours * expected_ndis_rate  # $561.84
        
        # Verify calculations
        hours_correct = abs(hours_worked - expected_hours) < 0.1
        staff_pay_correct = abs(total_pay - expected_staff_pay) < 0.01
        ndis_rate_correct = abs(ndis_hourly_charge - expected_ndis_rate) < 0.01
        ndis_charge_correct = abs(ndis_total_charge - expected_ndis_charge) < 0.01
        
        print(f"\n   Verification:")
        print(f"      Hours calculation: {'✅' if hours_correct else '❌'} ({hours_worked} vs {expected_hours})")
        print(f"      Staff pay calculation: {'✅' if staff_pay_correct else '❌'} (${total_pay} vs ${expected_staff_pay})")
        print(f"      NDIS rate calculation: {'✅' if ndis_rate_correct else '❌'} (${ndis_hourly_charge} vs ${expected_ndis_rate})")
        print(f"      NDIS charge calculation: {'✅' if ndis_charge_correct else '❌'} (${ndis_total_charge:.2f} vs ${expected_ndis_charge:.2f})")
        
        # Check that both calculations are independent
        calculations_independent = (
            staff_pay_correct and 
            ndis_charge_correct and 
            abs(total_pay - ndis_total_charge) > 100  # Should be significantly different
        )
        
        if calculations_independent:
            print(f"   ✅ Independent calculations verified:")
            print(f"      Staff gets paid: ${total_pay} (at $42/hr)")
            print(f"      Client gets charged: ${ndis_total_charge:.2f} (at $70.23/hr)")
            print(f"      Difference: ${ndis_total_charge - total_pay:.2f}")
        
        if hours_correct and staff_pay_correct and ndis_rate_correct and ndis_charge_correct and calculations_independent:
            print(f"   🎉 SUCCESS: NDIS and staff pay calculations coexist correctly")
            return True
        else:
            print(f"   ❌ FAILURE: Issues with coexisting calculations")
            return False

    def test_ndis_migration_endpoint(self):
        """Test the new NDIS migration endpoint"""
        print(f"\n🎯 TEST 5: NDIS Migration Endpoint...")
        
        if not self.auth_token:
            print("   ❌ No admin authentication token available")
            return False
        
        # Test the migration endpoint
        success, response = self.run_test(
            "NDIS Migration Endpoint",
            "POST",
            "api/admin/migrate-ndis-charges",
            200,
            use_auth=True
        )
        
        if not success:
            print("   ❌ NDIS migration endpoint failed")
            return False
        
        # Analyze migration results
        entries_updated = response.get('entries_updated', 0)
        total_entries = response.get('total_entries', 0)
        errors = response.get('errors', [])
        message = response.get('message', '')
        
        print(f"   Migration Results:")
        print(f"      Message: {message}")
        print(f"      Entries updated: {entries_updated}")
        print(f"      Total entries: {total_entries}")
        print(f"      Errors: {len(errors)}")
        
        if errors:
            print(f"   Migration Errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"      - {error}")
        
        # Verify migration was successful
        migration_successful = (
            entries_updated >= 0 and  # Should update some entries or none if all already have NDIS data
            len(errors) == 0 and  # Should have no errors
            total_entries > 0  # Should have some entries to process
        )
        
        if migration_successful:
            print(f"   🎉 SUCCESS: NDIS migration endpoint working correctly")
            if entries_updated > 0:
                print(f"      ✅ Updated {entries_updated} existing entries with NDIS data")
            else:
                print(f"      ✅ All {total_entries} entries already have NDIS data")
            return True
        else:
            print(f"   ❌ FAILURE: NDIS migration endpoint issues")
            return False

    def test_api_responses_include_ndis_fields(self):
        """Test that API responses include NDIS fields for all entries"""
        print(f"\n🎯 TEST 6: API Responses Include NDIS Fields...")
        
        # Get roster entries for current month
        current_month = datetime.now().strftime("%Y-%m")
        success, roster_entries = self.run_test(
            f"Get Roster Entries for {current_month}",
            "GET",
            "api/roster",
            200,
            params={"month": current_month}
        )
        
        if not success:
            print("   ❌ Could not retrieve roster entries")
            return False
        
        if len(roster_entries) == 0:
            print("   ⚠️  No roster entries found for testing")
            return True  # Not a failure, just no data
        
        print(f"   Analyzing {len(roster_entries)} roster entries...")
        
        # Check NDIS fields in existing entries
        required_ndis_fields = [
            'ndis_hourly_charge',
            'ndis_shift_charge', 
            'ndis_total_charge',
            'ndis_line_item_code',
            'ndis_description'
        ]
        
        entries_with_ndis = 0
        entries_without_ndis = 0
        field_analysis = {field: 0 for field in required_ndis_fields}
        
        for entry in roster_entries[:10]:  # Check first 10 entries
            has_all_ndis_fields = True
            
            for field in required_ndis_fields:
                if field in entry and entry[field] is not None:
                    field_analysis[field] += 1
                else:
                    has_all_ndis_fields = False
            
            if has_all_ndis_fields:
                entries_with_ndis += 1
            else:
                entries_without_ndis += 1
        
        print(f"   NDIS Field Analysis (first 10 entries):")
        for field, count in field_analysis.items():
            print(f"      {field}: {count}/10 entries")
        
        print(f"   Summary:")
        print(f"      Entries with all NDIS fields: {entries_with_ndis}/10")
        print(f"      Entries missing NDIS fields: {entries_without_ndis}/10")
        
        # Check if most entries have NDIS fields (allowing for some legacy entries)
        ndis_coverage_good = entries_with_ndis >= (len(roster_entries[:10]) * 0.5)  # At least 50% coverage
        
        if ndis_coverage_good:
            print(f"   🎉 SUCCESS: Good NDIS field coverage in API responses")
            if entries_without_ndis > 0:
                print(f"      ℹ️  {entries_without_ndis} entries may be legacy entries without NDIS data")
                print(f"      💡 Run migration endpoint to populate NDIS fields for all entries")
            return True
        else:
            print(f"   ❌ FAILURE: Poor NDIS field coverage in API responses")
            print(f"      Most entries are missing NDIS fields - migration may be needed")
            return False

    def run_comprehensive_ndis_tests(self):
        """Run all NDIS charge rate integration tests"""
        print("🎯 COMPREHENSIVE NDIS CHARGE RATE INTEGRATION TESTING")
        print("=" * 60)
        print("Testing the fixes for sleepover extra wake hours and NDIS migration endpoint")
        print("Focus areas from review request:")
        print("1. Sleepover Extra Wake Hours Fix")
        print("2. NDIS Migration Endpoint")
        print("3. Full NDIS Integration Verification")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate_admin():
            print("\n❌ CRITICAL: Could not authenticate as admin - aborting tests")
            return False
        
        # Run all NDIS tests
        test_results = []
        
        # Test 1: NDIS Charge Fields in New Entries
        test_results.append(self.test_ndis_charge_fields_in_new_entries())
        
        # Test 2: Regular Shift NDIS Charges
        test_results.append(self.test_regular_shift_ndis_charges())
        
        # Test 3: Sleepover Extra Wake Hours Fix (CRITICAL)
        test_results.append(self.test_sleepover_extra_wake_hours_fix())
        
        # Test 4: NDIS vs Staff Pay Coexistence
        test_results.append(self.test_ndis_vs_staff_pay_coexistence())
        
        # Test 5: NDIS Migration Endpoint
        test_results.append(self.test_ndis_migration_endpoint())
        
        # Test 6: API Responses Include NDIS Fields
        test_results.append(self.test_api_responses_include_ndis_fields())
        
        # Calculate results
        tests_passed = sum(test_results)
        total_tests = len(test_results)
        success_rate = (tests_passed / total_tests) * 100
        
        print(f"\n" + "=" * 60)
        print(f"🎯 NDIS CHARGE RATE INTEGRATION TEST RESULTS")
        print(f"=" * 60)
        print(f"Tests Passed: {tests_passed}/{total_tests} ({success_rate:.1f}%)")
        print(f"Individual API Tests: {self.tests_passed}/{self.tests_run}")
        
        # Detailed results
        test_names = [
            "NDIS Charge Fields Present",
            "Regular Shift NDIS Charges", 
            "Sleepover Extra Wake Hours Fix (CRITICAL)",
            "NDIS vs Staff Pay Coexistence",
            "NDIS Migration Endpoint",
            "API Responses Include NDIS Fields"
        ]
        
        print(f"\nDetailed Results:")
        for i, (name, result) in enumerate(zip(test_names, test_results)):
            status = "✅ PASS" if result else "❌ FAIL"
            critical = " (CRITICAL)" if i == 2 else ""  # Sleepover fix is critical
            print(f"  {i+1}. {name}{critical}: {status}")
        
        # Critical assessment
        critical_sleepover_fix = test_results[2]  # Index 2 is sleepover fix
        migration_endpoint = test_results[4]  # Index 4 is migration endpoint
        
        print(f"\n🎯 CRITICAL FIXES ASSESSMENT:")
        print(f"  Sleepover Extra Wake Hours Fix: {'✅ FIXED' if critical_sleepover_fix else '❌ STILL BROKEN'}")
        print(f"  NDIS Migration Endpoint: {'✅ WORKING' if migration_endpoint else '❌ NOT WORKING'}")
        
        if critical_sleepover_fix and migration_endpoint:
            print(f"\n🎉 SUCCESS: Both critical fixes are working correctly!")
            print(f"  - Sleepover calculation now uses weekday_night rate ($78.81/hr) for extra wake hours")
            print(f"  - Migration endpoint can populate NDIS fields for existing roster entries")
        elif critical_sleepover_fix:
            print(f"\n⚠️  PARTIAL SUCCESS: Sleepover fix working but migration endpoint has issues")
        elif migration_endpoint:
            print(f"\n⚠️  PARTIAL SUCCESS: Migration endpoint working but sleepover fix still broken")
        else:
            print(f"\n❌ FAILURE: Both critical fixes need attention")
        
        # Overall assessment
        if success_rate >= 80:
            print(f"\n🎉 OVERALL: NDIS Integration is working well ({success_rate:.1f}% success rate)")
        elif success_rate >= 60:
            print(f"\n⚠️  OVERALL: NDIS Integration has some issues ({success_rate:.1f}% success rate)")
        else:
            print(f"\n❌ OVERALL: NDIS Integration needs significant work ({success_rate:.1f}% success rate)")
        
        return success_rate >= 80

if __name__ == "__main__":
    print("🚀 Starting NDIS Charge Rate Integration Testing...")
    
    tester = NDISChargeRateIntegrationTester()
    success = tester.run_comprehensive_ndis_tests()
    
    if success:
        print(f"\n✅ NDIS testing completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ NDIS testing completed with issues!")
        sys.exit(1)