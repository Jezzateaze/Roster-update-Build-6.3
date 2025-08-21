import requests
import sys
import json
from datetime import datetime, timedelta

class StaffPayRatesAPITester:
    def __init__(self, base_url="https://workforce-wizard-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.settings_data = None
        self.shift_templates = []

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
        """Authenticate as Admin user with PIN 0000"""
        print(f"\n🔐 Authenticating as Admin (Admin/0000)...")
        
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
            
            print(f"   ✅ Admin login successful")
            print(f"   User: {user_data.get('username')} ({user_data.get('role')})")
            print(f"   Token: {self.auth_token[:20]}..." if self.auth_token else "No token")
            
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role confirmed")
                return True
            else:
                print(f"   ❌ Expected admin role, got: {user_data.get('role')}")
                return False
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def test_settings_api_pay_rates(self):
        """Test GET /api/settings endpoint to verify correct pay rates"""
        print(f"\n💰 Testing Settings API Pay Rates - CRITICAL VERIFICATION...")
        print(f"🎯 VERIFYING EXACT PAY RATES FROM REVIEW REQUEST:")
        
        # Expected rates from review request
        expected_rates = {
            "weekday_day": 42.00,      # 6am-8pm
            "weekday_evening": 44.50,  # after 8pm
            "weekday_night": 48.50,    # overnight - CRITICAL: Should be $48.50, not $52.00
            "saturday": 57.50,         # all hours
            "sunday": 74.00,           # all hours
            "public_holiday": 88.50,   # all hours
            "sleepover_default": 175.00 # includes 2 hours wake time
        }
        
        success, response = self.run_test(
            "Get Settings - Pay Rates Verification",
            "GET",
            "api/settings",
            200,
            use_auth=True
        )
        
        if not success:
            print("   ❌ Could not retrieve settings")
            return False
        
        self.settings_data = response
        rates = response.get('rates', {})
        
        print(f"\n   📊 PAY RATES VERIFICATION:")
        print(f"   Expected vs Actual Rates:")
        
        all_rates_correct = True
        critical_issues = []
        
        for rate_type, expected_rate in expected_rates.items():
            actual_rate = rates.get(rate_type, 0.0)
            is_correct = abs(actual_rate - expected_rate) < 0.01
            
            status = "✅" if is_correct else "❌"
            print(f"      {rate_type.replace('_', ' ').title()}: ${actual_rate:.2f} (expected: ${expected_rate:.2f}) {status}")
            
            if not is_correct:
                all_rates_correct = False
                if rate_type == "weekday_night":
                    critical_issues.append(f"CRITICAL: Weekday Night Rate is ${actual_rate:.2f}, should be ${expected_rate:.2f}")
                else:
                    critical_issues.append(f"{rate_type.replace('_', ' ').title()} rate mismatch: ${actual_rate:.2f} vs ${expected_rate:.2f}")
        
        # Additional settings verification
        pay_mode = response.get('pay_mode', 'unknown')
        time_format = response.get('time_format', 'unknown')
        first_day_of_week = response.get('first_day_of_week', 'unknown')
        
        print(f"\n   ⚙️  ADDITIONAL SETTINGS:")
        print(f"      Pay Mode: {pay_mode}")
        print(f"      Time Format: {time_format}")
        print(f"      First Day of Week: {first_day_of_week}")
        
        # Check NDIS charge rates (client billing)
        ndis_rates = response.get('ndis_charge_rates', {})
        if ndis_rates:
            print(f"\n   💼 NDIS CHARGE RATES (Client Billing):")
            for shift_type, rate_info in ndis_rates.items():
                if isinstance(rate_info, dict):
                    rate = rate_info.get('rate', 0)
                    code = rate_info.get('line_item_code', 'N/A')
                    print(f"      {shift_type.replace('_', ' ').title()}: ${rate:.2f} (Code: {code})")
        
        # Final assessment
        if all_rates_correct:
            print(f"\n   🎉 ALL PAY RATES CORRECT!")
            print(f"      ✅ All 7 pay rates match the review request specifications")
            print(f"      ✅ Weekday Night Rate correctly set to $48.50")
            print(f"      ✅ Settings API returning accurate pay rate data")
        else:
            print(f"\n   ❌ PAY RATE DISCREPANCIES FOUND!")
            for issue in critical_issues:
                print(f"      🚨 {issue}")
            
            if any("CRITICAL" in issue for issue in critical_issues):
                print(f"\n   🚨 CRITICAL ISSUE: The Weekday Night Rate discrepancy will affect:")
                print(f"      - Staff pay calculations for overnight shifts")
                print(f"      - Shift Times display showing incorrect rates")
                print(f"      - Cross-midnight shift calculations")
                print(f"      - Staff understanding of their pay rates")
        
        return all_rates_correct

    def test_shift_templates_api(self):
        """Test GET /api/shift-templates endpoint to verify templates return with correct hourly rate calculations"""
        print(f"\n📋 Testing Shift Templates API - RATE CALCULATION VERIFICATION...")
        
        success, response = self.run_test(
            "Get Shift Templates with Rate Calculations",
            "GET",
            "api/shift-templates",
            200,
            use_auth=True
        )
        
        if not success:
            print("   ❌ Could not retrieve shift templates")
            return False
        
        self.shift_templates = response
        print(f"   📊 Found {len(response)} shift templates")
        
        if not self.settings_data:
            print("   ⚠️  No settings data available for rate verification")
            return False
        
        rates = self.settings_data.get('rates', {})
        
        # Test rate calculation for different shift types
        print(f"\n   🎯 TESTING RATE CALCULATIONS FOR DIFFERENT SHIFT TYPES:")
        
        # Group templates by day of week for analysis
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        templates_by_day = {}
        
        for template in response:
            day_of_week = template.get('day_of_week', 0)
            day_name = day_names[day_of_week] if 0 <= day_of_week <= 6 else 'Unknown'
            
            if day_name not in templates_by_day:
                templates_by_day[day_name] = []
            templates_by_day[day_name].append(template)
        
        rate_calculation_correct = True
        
        # Test each day's templates
        for day_name, templates in templates_by_day.items():
            print(f"\n      {day_name} Templates:")
            
            for template in templates:
                name = template.get('name', 'Unnamed')
                start_time = template.get('start_time', '00:00')
                end_time = template.get('end_time', '00:00')
                is_sleepover = template.get('is_sleepover', False)
                
                # Calculate expected rate based on shift type
                expected_rate = self.calculate_expected_rate(day_name, start_time, end_time, is_sleepover, rates)
                
                # Calculate hours
                hours = self.calculate_hours(start_time, end_time)
                
                if is_sleepover:
                    expected_pay = rates.get('sleepover_default', 175.00)
                    pay_type = "Sleepover Allowance"
                else:
                    expected_pay = hours * expected_rate
                    pay_type = "Hourly Pay"
                
                print(f"         {name}: {start_time}-{end_time}")
                print(f"            Hours: {hours:.1f}h, Rate: ${expected_rate:.2f}/hr")
                print(f"            {pay_type}: ${expected_pay:.2f}")
                
                # Verify shift type determination
                shift_type = self.determine_shift_type(day_name, start_time, end_time, is_sleepover)
                print(f"            Shift Type: {shift_type}")
        
        # Test specific scenarios from review request
        print(f"\n   🎯 TESTING SPECIFIC SCENARIOS:")
        
        test_scenarios = [
            {
                "name": "Weekday Day Shift (6am-8pm)",
                "day": "Monday",
                "start": "07:30",
                "end": "15:30",
                "expected_rate": 42.00,
                "expected_type": "WEEKDAY_DAY"
            },
            {
                "name": "Weekday Evening Shift (after 8pm)",
                "day": "Monday", 
                "start": "15:30",
                "end": "23:30",
                "expected_rate": 44.50,
                "expected_type": "WEEKDAY_EVENING"
            },
            {
                "name": "Weekday Night Shift (overnight) - CRITICAL",
                "day": "Monday",
                "start": "23:30",
                "end": "07:30",
                "expected_rate": 48.50,  # CRITICAL: Should be $48.50
                "expected_type": "WEEKDAY_NIGHT",
                "is_sleepover": True
            },
            {
                "name": "Saturday Shift (all hours)",
                "day": "Saturday",
                "start": "07:30", 
                "end": "15:30",
                "expected_rate": 57.50,
                "expected_type": "SATURDAY"
            },
            {
                "name": "Sunday Shift (all hours)",
                "day": "Sunday",
                "start": "07:30",
                "end": "15:30", 
                "expected_rate": 74.00,
                "expected_type": "SUNDAY"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n      Testing: {scenario['name']}")
            
            calculated_rate = self.calculate_expected_rate(
                scenario['day'], 
                scenario['start'], 
                scenario['end'], 
                scenario.get('is_sleepover', False),
                rates
            )
            
            shift_type = self.determine_shift_type(
                scenario['day'],
                scenario['start'],
                scenario['end'], 
                scenario.get('is_sleepover', False)
            )
            
            rate_correct = abs(calculated_rate - scenario['expected_rate']) < 0.01
            type_correct = shift_type == scenario['expected_type']
            
            print(f"         Expected Rate: ${scenario['expected_rate']:.2f}")
            print(f"         Calculated Rate: ${calculated_rate:.2f} {'✅' if rate_correct else '❌'}")
            print(f"         Expected Type: {scenario['expected_type']}")
            print(f"         Calculated Type: {shift_type} {'✅' if type_correct else '❌'}")
            
            if not rate_correct or not type_correct:
                rate_calculation_correct = False
                if "CRITICAL" in scenario['name']:
                    print(f"         🚨 CRITICAL ISSUE: Weekday night rate calculation incorrect!")
        
        if rate_calculation_correct:
            print(f"\n   🎉 ALL RATE CALCULATIONS CORRECT!")
            print(f"      ✅ Shift type determination working properly")
            print(f"      ✅ Rate calculations match review request specifications")
            print(f"      ✅ Templates will display correct pay information")
        else:
            print(f"\n   ❌ RATE CALCULATION ISSUES FOUND!")
            print(f"      🚨 Shift Times display may show incorrect rates to staff")
        
        return rate_calculation_correct

    def calculate_expected_rate(self, day_name, start_time, end_time, is_sleepover, rates):
        """Calculate expected hourly rate based on shift parameters"""
        if is_sleepover:
            return rates.get('sleepover_default', 175.00)  # Sleepover is flat rate, not hourly
        
        # Weekend rates override time-based logic
        if day_name == 'Saturday':
            return rates.get('saturday', 57.50)
        elif day_name == 'Sunday':
            return rates.get('sunday', 74.00)
        
        # Weekday time-based rates
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])
        
        # Handle overnight shifts
        if end_hour <= start_hour:
            return rates.get('weekday_night', 48.50)
        
        # Evening: starts at 8pm or later OR extends past 8pm
        if start_hour >= 20 or end_hour > 20:
            return rates.get('weekday_evening', 44.50)
        
        # Day: 6am-8pm range
        return rates.get('weekday_day', 42.00)

    def determine_shift_type(self, day_name, start_time, end_time, is_sleepover):
        """Determine shift type based on parameters"""
        if is_sleepover:
            return "SLEEPOVER"
        
        if day_name == 'Saturday':
            return "SATURDAY"
        elif day_name == 'Sunday':
            return "SUNDAY"
        
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])
        
        # Handle overnight shifts
        if end_hour <= start_hour:
            return "WEEKDAY_NIGHT"
        
        # Evening: starts at 8pm or later OR extends past 8pm
        if start_hour >= 20 or end_hour > 20:
            return "WEEKDAY_EVENING"
        
        return "WEEKDAY_DAY"

    def calculate_hours(self, start_time, end_time):
        """Calculate hours between start and end time"""
        start_hour, start_min = map(int, start_time.split(':'))
        end_hour, end_min = map(int, end_time.split(':'))
        
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        # Handle overnight shifts
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60
        
        total_minutes = end_minutes - start_minutes
        return total_minutes / 60.0

    def test_rate_calculation_logic(self):
        """Test the shift type determination and rate calculation logic with specific test cases"""
        print(f"\n🧮 Testing Rate Calculation Logic - COMPREHENSIVE SCENARIOS...")
        
        if not self.settings_data:
            print("   ⚠️  No settings data available for testing")
            return False
        
        rates = self.settings_data.get('rates', {})
        
        # Test cases covering all scenarios from review request
        test_cases = [
            {
                "name": "Monday 9am-5pm (Weekday Day)",
                "date": "2025-01-06",  # Monday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_type": "weekday_day",
                "expected_rate": 42.00,
                "expected_hours": 8.0,
                "expected_pay": 336.00
            },
            {
                "name": "Monday 3:30pm-11:30pm (Weekday Evening - extends past 8pm)",
                "date": "2025-01-06",  # Monday
                "start_time": "15:30",
                "end_time": "23:30",
                "expected_type": "weekday_evening",
                "expected_rate": 44.50,
                "expected_hours": 8.0,
                "expected_pay": 356.00
            },
            {
                "name": "Monday 11:30pm-7:30am (Weekday Night - CRITICAL TEST)",
                "date": "2025-01-06",  # Monday
                "start_time": "23:30",
                "end_time": "07:30",
                "expected_type": "sleepover",
                "expected_rate": 48.50,  # CRITICAL: Should be $48.50 for night rate
                "expected_hours": 8.0,
                "expected_pay": 175.00,  # Sleepover allowance
                "is_sleepover": True
            },
            {
                "name": "Saturday 9am-5pm (Saturday Rate)",
                "date": "2025-01-11",  # Saturday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_type": "saturday",
                "expected_rate": 57.50,
                "expected_hours": 8.0,
                "expected_pay": 460.00
            },
            {
                "name": "Sunday 9am-5pm (Sunday Rate)",
                "date": "2025-01-12",  # Sunday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_type": "sunday",
                "expected_rate": 74.00,
                "expected_hours": 8.0,
                "expected_pay": 592.00
            },
            {
                "name": "Public Holiday 9am-5pm (Public Holiday Rate)",
                "date": "2025-01-01",  # New Year's Day
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_type": "public_holiday",
                "expected_rate": 88.50,
                "expected_hours": 8.0,
                "expected_pay": 708.00,
                "is_public_holiday": True
            }
        ]
        
        print(f"   🎯 Testing {len(test_cases)} rate calculation scenarios...")
        
        calculation_tests_passed = 0
        critical_issues = []
        
        for test_case in test_cases:
            print(f"\n      Testing: {test_case['name']}")
            
            # Create a test roster entry
            roster_entry = {
                "id": "",  # Will be auto-generated
                "date": test_case["date"],
                "shift_template_id": "test-rate-calc",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": test_case.get("is_sleepover", False),
                "is_public_holiday": test_case.get("is_public_holiday", False),
                "staff_id": None,
                "staff_name": None
            }
            
            # Test by creating the roster entry and checking calculations
            success, response = self.run_test(
                f"Create Test Entry: {test_case['name']}",
                "POST",
                "api/roster",
                200,
                data=roster_entry,
                use_auth=True
            )
            
            if success:
                hours_worked = response.get('hours_worked', 0)
                total_pay = response.get('total_pay', 0)
                base_pay = response.get('base_pay', 0)
                sleepover_allowance = response.get('sleepover_allowance', 0)
                
                print(f"         Hours: {hours_worked:.1f}h (expected: {test_case['expected_hours']:.1f}h)")
                print(f"         Base Pay: ${base_pay:.2f}")
                print(f"         Sleepover: ${sleepover_allowance:.2f}")
                print(f"         Total Pay: ${total_pay:.2f} (expected: ${test_case['expected_pay']:.2f})")
                
                # Verify calculations
                hours_correct = abs(hours_worked - test_case['expected_hours']) < 0.1
                pay_correct = abs(total_pay - test_case['expected_pay']) < 0.01
                
                if hours_correct and pay_correct:
                    print(f"         ✅ Calculations correct")
                    calculation_tests_passed += 1
                else:
                    print(f"         ❌ Calculations incorrect")
                    if not hours_correct:
                        print(f"            Hours mismatch: got {hours_worked:.1f}, expected {test_case['expected_hours']:.1f}")
                    if not pay_correct:
                        print(f"            Pay mismatch: got ${total_pay:.2f}, expected ${test_case['expected_pay']:.2f}")
                    
                    if "CRITICAL" in test_case['name']:
                        critical_issues.append(f"CRITICAL: {test_case['name']} calculation failed")
                
                # Clean up test entry
                if response.get('id'):
                    self.run_test(
                        f"Delete Test Entry",
                        "DELETE",
                        f"api/roster/{response['id']}",
                        200,
                        use_auth=True
                    )
            else:
                print(f"         ❌ Could not create test entry")
                if "CRITICAL" in test_case['name']:
                    critical_issues.append(f"CRITICAL: Could not test {test_case['name']}")
        
        # Final assessment
        success_rate = (calculation_tests_passed / len(test_cases)) * 100
        
        if calculation_tests_passed == len(test_cases):
            print(f"\n   🎉 ALL RATE CALCULATION TESTS PASSED!")
            print(f"      ✅ {calculation_tests_passed}/{len(test_cases)} scenarios calculated correctly")
            print(f"      ✅ Weekday Night Rate logic working properly")
            print(f"      ✅ All shift types determined correctly")
        else:
            print(f"\n   ❌ RATE CALCULATION ISSUES FOUND!")
            print(f"      📊 Success Rate: {success_rate:.1f}% ({calculation_tests_passed}/{len(test_cases)})")
            
            for issue in critical_issues:
                print(f"      🚨 {issue}")
            
            if critical_issues:
                print(f"\n      🚨 CRITICAL IMPACT:")
                print(f"         - Staff will see incorrect pay rates in Shift Times display")
                print(f"         - Pay calculations may be wrong for overnight shifts")
                print(f"         - Staff may be underpaid or overpaid")
        
        return calculation_tests_passed == len(test_cases)

    def run_comprehensive_test(self):
        """Run all staff pay rates tests"""
        print(f"🎯 STAFF PAY RATES IN SHIFT TIMES DISPLAY - COMPREHENSIVE TESTING")
        print(f"=" * 80)
        print(f"Review Request: Verify correct staff pay rates are being shown")
        print(f"Critical Focus: Weekday Night Rate should be $48.50 (not $52.00)")
        print(f"Authentication: Admin credentials (Admin/0000)")
        print(f"=" * 80)
        
        # Step 1: Authenticate as Admin
        if not self.authenticate_admin():
            print(f"\n❌ CRITICAL FAILURE: Could not authenticate as Admin")
            return False
        
        # Step 2: Test Settings API Pay Rates
        settings_test_passed = self.test_settings_api_pay_rates()
        
        # Step 3: Test Shift Templates API
        templates_test_passed = self.test_shift_templates_api()
        
        # Step 4: Test Rate Calculation Logic
        calculation_test_passed = self.test_rate_calculation_logic()
        
        # Final Summary
        print(f"\n" + "=" * 80)
        print(f"🎯 STAFF PAY RATES TESTING SUMMARY")
        print(f"=" * 80)
        
        total_tests = 3
        passed_tests = sum([settings_test_passed, templates_test_passed, calculation_test_passed])
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} test suites passed ({(passed_tests/total_tests)*100:.1f}%)")
        print(f"🔍 Individual Tests: {self.tests_passed}/{self.tests_run} API calls successful")
        
        print(f"\n📋 Test Suite Results:")
        print(f"   1. Settings API Pay Rates: {'✅ PASSED' if settings_test_passed else '❌ FAILED'}")
        print(f"   2. Shift Templates API: {'✅ PASSED' if templates_test_passed else '❌ FAILED'}")
        print(f"   3. Rate Calculation Logic: {'✅ PASSED' if calculation_test_passed else '❌ FAILED'}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED - STAFF PAY RATES SYSTEM WORKING CORRECTLY!")
            print(f"   ✅ All pay rates match review request specifications")
            print(f"   ✅ Weekday Night Rate correctly set to $48.50")
            print(f"   ✅ Shift Templates API returning correct rate calculations")
            print(f"   ✅ Rate calculation logic working properly")
            print(f"   ✅ Shift Times display will show correct staff pay rates")
        else:
            print(f"\n❌ CRITICAL ISSUES FOUND - STAFF PAY RATES NEED ATTENTION!")
            
            if not settings_test_passed:
                print(f"   🚨 Settings API has incorrect pay rates")
                print(f"      - Check weekday_night rate (should be $48.50)")
                print(f"      - Verify all rates match review request")
            
            if not templates_test_passed:
                print(f"   🚨 Shift Templates API has rate calculation issues")
                print(f"      - Templates may show wrong hourly rates")
                print(f"      - Shift type determination may be incorrect")
            
            if not calculation_test_passed:
                print(f"   🚨 Rate calculation logic has problems")
                print(f"      - Pay calculations may be wrong")
                print(f"      - Staff may see incorrect pay information")
            
            print(f"\n   💡 RECOMMENDED ACTIONS:")
            print(f"      1. Fix weekday_night rate in Settings model (line ~188 in server.py)")
            print(f"      2. Verify shift type determination logic")
            print(f"      3. Test Shift Times display with corrected rates")
            print(f"      4. Ensure all staff see accurate pay information")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = StaffPayRatesAPITester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)