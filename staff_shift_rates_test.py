import requests
import sys
import json
from datetime import datetime, timedelta

class StaffShiftRatesAPITester:
    def __init__(self, base_url="https://workforce-wizard-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.staff_token = None
        self.staff_user_data = None
        self.settings_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if use_auth:
            auth_token = token or self.admin_token
            if auth_token:
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
            self.admin_token = response.get('token')
            print(f"   ✅ Admin authenticated successfully")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def authenticate_staff(self, username="rose", pin="888888"):
        """Authenticate as staff user"""
        print(f"\n👤 Authenticating as Staff User: {username}...")
        
        login_data = {
            "username": username,
            "pin": pin
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
            self.staff_user_data = response.get('user', {})
            print(f"   ✅ Staff authenticated successfully")
            print(f"   Staff ID: {self.staff_user_data.get('staff_id')}")
            print(f"   Role: {self.staff_user_data.get('role')}")
            return True
        else:
            print(f"   ❌ Staff authentication failed")
            return False

    def get_current_settings(self):
        """Get current settings to verify rates"""
        print(f"\n⚙️ Getting Current Settings...")
        
        success, response = self.run_test(
            "Get Settings",
            "GET",
            "api/settings",
            200
        )
        
        if success:
            self.settings_data = response
            rates = response.get('rates', {})
            print(f"   ✅ Settings retrieved successfully")
            print(f"   Saturday rate: ${rates.get('saturday', 0)}")
            print(f"   Sunday rate: ${rates.get('sunday', 0)}")
            print(f"   Weekday day rate: ${rates.get('weekday_day', 0)}")
            print(f"   Weekday evening rate: ${rates.get('weekday_evening', 0)}")
            print(f"   Weekday night rate: ${rates.get('weekday_night', 0)}")
            return True
        else:
            print(f"   ❌ Could not retrieve settings")
            return False

    def test_staff_shift_templates_access(self):
        """Test what shift templates staff users see and their rates"""
        print(f"\n📋 Testing Staff Access to Shift Templates...")
        
        if not self.staff_token:
            print("   ❌ No staff authentication token available")
            return False
        
        success, templates = self.run_test(
            "Get Shift Templates as Staff User",
            "GET",
            "api/shift-templates",
            200,
            use_auth=True,
            token=self.staff_token
        )
        
        if not success:
            print("   ❌ Staff cannot access shift templates")
            return False
        
        print(f"   ✅ Staff can access {len(templates)} shift templates")
        
        # Filter for Saturday and Sunday templates
        saturday_templates = [t for t in templates if t['day_of_week'] == 5]  # Saturday = 5
        sunday_templates = [t for t in templates if t['day_of_week'] == 6]    # Sunday = 6
        
        print(f"   Found {len(saturday_templates)} Saturday templates")
        print(f"   Found {len(sunday_templates)} Sunday templates")
        
        # Test specific weekend shifts mentioned in review request
        weekend_test_cases = [
            {
                "day": "Saturday",
                "templates": saturday_templates,
                "expected_rate": 57.50,
                "test_shifts": [
                    {"start": "07:30", "end": "15:30", "hours": 8, "expected_pay": 460.00},
                    {"start": "15:00", "end": "20:00", "hours": 5, "expected_pay": 287.50},
                    {"start": "15:30", "end": "23:30", "hours": 8, "expected_pay": 460.00}
                ]
            },
            {
                "day": "Sunday", 
                "templates": sunday_templates,
                "expected_rate": 74.00,
                "test_shifts": [
                    {"start": "07:30", "end": "15:30", "hours": 8, "expected_pay": 592.00},
                    {"start": "15:00", "end": "20:00", "hours": 5, "expected_pay": 370.00},
                    {"start": "15:30", "end": "23:30", "hours": 8, "expected_pay": 592.00}
                ]
            }
        ]
        
        all_tests_passed = True
        
        for day_test in weekend_test_cases:
            print(f"\n   🎯 Testing {day_test['day']} Shift Templates:")
            
            for template in day_test['templates']:
                # Find matching test shift
                matching_test = None
                for test_shift in day_test['test_shifts']:
                    if (template['start_time'] == test_shift['start'] and 
                        template['end_time'] == test_shift['end']):
                        matching_test = test_shift
                        break
                
                if matching_test:
                    print(f"      📍 {template['name']}: {template['start_time']}-{template['end_time']}")
                    
                    # Calculate expected hours and pay
                    start_hour, start_min = map(int, template['start_time'].split(':'))
                    end_hour, end_min = map(int, template['end_time'].split(':'))
                    
                    start_minutes = start_hour * 60 + start_min
                    end_minutes = end_hour * 60 + end_min
                    
                    # Handle overnight shifts
                    if end_minutes <= start_minutes:
                        end_minutes += 24 * 60
                    
                    actual_hours = (end_minutes - start_minutes) / 60.0
                    expected_pay = actual_hours * day_test['expected_rate']
                    
                    print(f"         Hours: {actual_hours} (expected: {matching_test['hours']})")
                    print(f"         Expected rate: ${day_test['expected_rate']}/hr")
                    print(f"         Expected pay: ${expected_pay:.2f}")
                    
                    # Verify calculations match expectations
                    hours_correct = abs(actual_hours - matching_test['hours']) < 0.1
                    pay_correct = abs(expected_pay - matching_test['expected_pay']) < 0.01
                    
                    if hours_correct and pay_correct:
                        print(f"         ✅ Calculations correct")
                    else:
                        print(f"         ❌ Calculation mismatch")
                        if not hours_correct:
                            print(f"            Hours: got {actual_hours}, expected {matching_test['hours']}")
                        if not pay_correct:
                            print(f"            Pay: got ${expected_pay:.2f}, expected ${matching_test['expected_pay']:.2f}")
                        all_tests_passed = False
                else:
                    print(f"      📍 {template['name']}: {template['start_time']}-{template['end_time']} (not in test cases)")
        
        return all_tests_passed

    def test_specific_weekend_shifts(self):
        """Test the exact weekend shifts mentioned in the review request"""
        print(f"\n🎯 Testing Specific Weekend Shifts from Review Request...")
        
        if not self.staff_token:
            print("   ❌ No staff authentication token available")
            return False
        
        # Test cases from review request
        test_shifts = [
            {
                "name": "Saturday 7:30 AM - 3:30 PM",
                "date": "2025-01-11",  # Saturday
                "start_time": "07:30",
                "end_time": "15:30",
                "expected_hours": 8,
                "expected_rate": 57.50,
                "expected_pay": 460.00,
                "shift_type": "Saturday"
            },
            {
                "name": "Saturday 3:00 PM - 8:00 PM", 
                "date": "2025-01-11",  # Saturday
                "start_time": "15:00",
                "end_time": "20:00",
                "expected_hours": 5,
                "expected_rate": 57.50,
                "expected_pay": 287.50,  # 5h × $57.50 = $287.50 (not $230 as in request - that was 4h calc)
                "shift_type": "Saturday"
            },
            {
                "name": "Saturday 3:30 PM - 11:30 PM",
                "date": "2025-01-11",  # Saturday
                "start_time": "15:30", 
                "end_time": "23:30",
                "expected_hours": 8,
                "expected_rate": 57.50,
                "expected_pay": 460.00,
                "shift_type": "Saturday"
            },
            {
                "name": "Sunday 7:30 AM - 3:30 PM",
                "date": "2025-01-12",  # Sunday
                "start_time": "07:30",
                "end_time": "15:30", 
                "expected_hours": 8,
                "expected_rate": 74.00,
                "expected_pay": 592.00,
                "shift_type": "Sunday"
            },
            {
                "name": "Sunday 3:00 PM - 8:00 PM",
                "date": "2025-01-12",  # Sunday
                "start_time": "15:00",
                "end_time": "20:00",
                "expected_hours": 5,
                "expected_rate": 74.00,
                "expected_pay": 370.00,  # 5h × $74.00 = $370.00 (not $296 as in request - that was 4h calc)
                "shift_type": "Sunday"
            },
            {
                "name": "Sunday 3:30 PM - 11:30 PM",
                "date": "2025-01-12",  # Sunday
                "start_time": "15:30",
                "end_time": "23:30",
                "expected_hours": 8,
                "expected_rate": 74.00,
                "expected_pay": 592.00,
                "shift_type": "Sunday"
            }
        ]
        
        tests_passed = 0
        
        for test_case in test_shifts:
            print(f"\n   🎯 Testing: {test_case['name']}")
            
            # Create roster entry to test calculation
            roster_entry = {
                "id": "",  # Will be auto-generated
                "date": test_case["date"],
                "shift_template_id": f"test-{test_case['shift_type'].lower()}",
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
            
            # Create the shift using staff authentication
            success, response = self.run_test(
                f"Create {test_case['name']} as Staff",
                "POST",
                "api/roster",
                200,
                data=roster_entry,
                use_auth=True,
                token=self.staff_token
            )
            
            if success:
                actual_hours = response.get('hours_worked', 0)
                actual_total_pay = response.get('total_pay', 0)
                actual_base_pay = response.get('base_pay', 0)
                
                print(f"      Date: {test_case['date']} ({test_case['shift_type']})")
                print(f"      Time: {test_case['start_time']} - {test_case['end_time']}")
                print(f"      Hours worked: {actual_hours} (expected: {test_case['expected_hours']})")
                print(f"      Base pay: ${actual_base_pay:.2f}")
                print(f"      Total pay: ${actual_total_pay:.2f} (expected: ${test_case['expected_pay']:.2f})")
                
                # Calculate expected hourly rate from actual calculation
                if actual_hours > 0:
                    actual_rate = actual_base_pay / actual_hours
                    print(f"      Actual rate: ${actual_rate:.2f}/hr (expected: ${test_case['expected_rate']:.2f}/hr)")
                
                # Verify calculations
                hours_correct = abs(actual_hours - test_case['expected_hours']) < 0.1
                pay_correct = abs(actual_total_pay - test_case['expected_pay']) < 0.01
                rate_correct = actual_hours > 0 and abs((actual_base_pay / actual_hours) - test_case['expected_rate']) < 0.01
                
                if hours_correct and pay_correct and rate_correct:
                    print(f"      ✅ All calculations correct for {test_case['shift_type']} shift")
                    tests_passed += 1
                else:
                    print(f"      ❌ Calculation errors detected:")
                    if not hours_correct:
                        print(f"         Hours: got {actual_hours}, expected {test_case['expected_hours']}")
                    if not rate_correct and actual_hours > 0:
                        actual_rate = actual_base_pay / actual_hours
                        print(f"         Rate: got ${actual_rate:.2f}/hr, expected ${test_case['expected_rate']:.2f}/hr")
                    if not pay_correct:
                        print(f"         Pay: got ${actual_total_pay:.2f}, expected ${test_case['expected_pay']:.2f}")
            else:
                print(f"      ❌ Could not create shift for testing")
        
        print(f"\n   📊 Weekend Shift Tests: {tests_passed}/{len(test_shifts)} passed")
        
        if tests_passed == len(test_shifts):
            print(f"   🎉 ALL WEEKEND SHIFT CALCULATIONS CORRECT!")
            print(f"      ✅ Saturday shifts using $57.50 rate")
            print(f"      ✅ Sunday shifts using $74.00 rate")
            print(f"      ✅ Staff users see correct rates")
        else:
            print(f"   ❌ WEEKEND SHIFT CALCULATION ISSUES FOUND!")
            print(f"      Some shifts not calculating with expected rates")
        
        return tests_passed == len(test_shifts)

    def test_shift_type_classification(self):
        """Test that shifts are correctly classified as Saturday/Sunday types"""
        print(f"\n🏷️ Testing Shift Type Classification...")
        
        if not self.staff_token:
            print("   ❌ No staff authentication token available")
            return False
        
        # Test classification scenarios
        classification_tests = [
            {
                "name": "Saturday Morning Shift",
                "date": "2025-01-11",  # Saturday
                "start_time": "07:30",
                "end_time": "15:30",
                "expected_type": "Saturday",
                "expected_rate": 57.50
            },
            {
                "name": "Saturday Afternoon Shift", 
                "date": "2025-01-11",  # Saturday
                "start_time": "15:00",
                "end_time": "20:00",
                "expected_type": "Saturday",
                "expected_rate": 57.50
            },
            {
                "name": "Saturday Evening Shift",
                "date": "2025-01-11",  # Saturday
                "start_time": "15:30",
                "end_time": "23:30",
                "expected_type": "Saturday", 
                "expected_rate": 57.50
            },
            {
                "name": "Sunday Morning Shift",
                "date": "2025-01-12",  # Sunday
                "start_time": "07:30",
                "end_time": "15:30",
                "expected_type": "Sunday",
                "expected_rate": 74.00
            },
            {
                "name": "Sunday Afternoon Shift",
                "date": "2025-01-12",  # Sunday
                "start_time": "15:00", 
                "end_time": "20:00",
                "expected_type": "Sunday",
                "expected_rate": 74.00
            },
            {
                "name": "Sunday Evening Shift",
                "date": "2025-01-12",  # Sunday
                "start_time": "15:30",
                "end_time": "23:30",
                "expected_type": "Sunday",
                "expected_rate": 74.00
            }
        ]
        
        classification_passed = 0
        
        for test_case in classification_tests:
            print(f"\n   🔍 Testing: {test_case['name']}")
            
            # Create a test roster entry
            roster_entry = {
                "id": "",
                "date": test_case["date"],
                "shift_template_id": f"test-{test_case['expected_type'].lower()}",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": self.staff_user_data.get('staff_id'),
                "staff_name": "Test Staff",
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
            
            success, response = self.run_test(
                f"Create {test_case['name']} for Classification Test",
                "POST",
                "api/roster",
                200,
                data=roster_entry,
                use_auth=True,
                token=self.staff_token
            )
            
            if success:
                actual_hours = response.get('hours_worked', 0)
                actual_base_pay = response.get('base_pay', 0)
                
                if actual_hours > 0:
                    actual_rate = actual_base_pay / actual_hours
                    rate_correct = abs(actual_rate - test_case['expected_rate']) < 0.01
                    
                    print(f"      Date: {test_case['date']} ({test_case['expected_type']})")
                    print(f"      Actual rate: ${actual_rate:.2f}/hr")
                    print(f"      Expected rate: ${test_case['expected_rate']:.2f}/hr")
                    
                    if rate_correct:
                        print(f"      ✅ Correct {test_case['expected_type']} rate applied")
                        classification_passed += 1
                    else:
                        print(f"      ❌ Incorrect rate - expected ${test_case['expected_rate']:.2f}, got ${actual_rate:.2f}")
                else:
                    print(f"      ❌ No hours calculated")
            else:
                print(f"      ❌ Could not create shift for classification test")
        
        print(f"\n   📊 Classification Tests: {classification_passed}/{len(classification_tests)} passed")
        
        return classification_passed == len(classification_tests)

    def compare_admin_vs_staff_rates(self):
        """Compare what admin sees vs what staff sees for rates"""
        print(f"\n🔄 Comparing Admin vs Staff Rate Visibility...")
        
        if not self.admin_token or not self.staff_token:
            print("   ❌ Missing authentication tokens")
            return False
        
        # Get settings as admin
        success, admin_settings = self.run_test(
            "Get Settings as Admin",
            "GET",
            "api/settings",
            200,
            use_auth=True,
            token=self.admin_token
        )
        
        if not success:
            print("   ❌ Admin cannot access settings")
            return False
        
        # Get settings as staff (if accessible)
        success, staff_settings = self.run_test(
            "Get Settings as Staff",
            "GET", 
            "api/settings",
            200,
            use_auth=True,
            token=self.staff_token
        )
        
        if success:
            print("   ✅ Staff can access settings")
            
            # Compare rates
            admin_rates = admin_settings.get('rates', {})
            staff_rates = staff_settings.get('rates', {})
            
            print(f"\n   Rate Comparison:")
            rate_keys = ['saturday', 'sunday', 'weekday_day', 'weekday_evening', 'weekday_night']
            
            for rate_key in rate_keys:
                admin_rate = admin_rates.get(rate_key, 0)
                staff_rate = staff_rates.get(rate_key, 0)
                
                if admin_rate == staff_rate:
                    print(f"      {rate_key}: ${admin_rate:.2f} ✅ (same for both)")
                else:
                    print(f"      {rate_key}: Admin ${admin_rate:.2f}, Staff ${staff_rate:.2f} ❌")
            
            # Check NDIS rates visibility
            admin_ndis = admin_settings.get('ndis_charge_rates', {})
            staff_ndis = staff_settings.get('ndis_charge_rates', {})
            
            print(f"\n   NDIS Rates Visibility:")
            print(f"      Admin sees NDIS rates: {'Yes' if admin_ndis else 'No'}")
            print(f"      Staff sees NDIS rates: {'Yes' if staff_ndis else 'No'}")
            
            if admin_ndis and not staff_ndis:
                print(f"      ✅ Correct - Staff should not see NDIS rates")
            elif admin_ndis and staff_ndis:
                print(f"      ⚠️ Staff can see NDIS rates (may be intentional)")
            else:
                print(f"      ❌ Neither admin nor staff can see NDIS rates")
        else:
            print("   ⚠️ Staff cannot access settings (may be restricted)")
        
        return True

    def test_staff_shift_creation_with_rates(self):
        """Test staff creating shifts and verify they see correct rates"""
        print(f"\n💼 Testing Staff Shift Creation with Rate Verification...")
        
        if not self.staff_token:
            print("   ❌ No staff authentication token available")
            return False
        
        # Test creating shifts as staff user and verify rates
        staff_test_shifts = [
            {
                "name": "Staff Saturday Shift Test",
                "date": "2025-01-18",  # Saturday
                "start_time": "09:00",
                "end_time": "17:00",
                "expected_rate": 57.50,
                "expected_hours": 8,
                "expected_pay": 460.00
            },
            {
                "name": "Staff Sunday Shift Test", 
                "date": "2025-01-19",  # Sunday
                "start_time": "10:00",
                "end_time": "18:00",
                "expected_rate": 74.00,
                "expected_hours": 8,
                "expected_pay": 592.00
            }
        ]
        
        staff_tests_passed = 0
        
        for test_case in staff_test_shifts:
            print(f"\n   👤 {test_case['name']}:")
            
            roster_entry = {
                "id": "",
                "date": test_case["date"],
                "shift_template_id": "staff-test",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": self.staff_user_data.get('staff_id'),
                "staff_name": self.staff_user_data.get('username', 'Test Staff'),
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
            
            success, response = self.run_test(
                f"Staff Create {test_case['name']}",
                "POST",
                "api/roster",
                200,
                data=roster_entry,
                use_auth=True,
                token=self.staff_token
            )
            
            if success:
                actual_hours = response.get('hours_worked', 0)
                actual_total_pay = response.get('total_pay', 0)
                actual_base_pay = response.get('base_pay', 0)
                
                if actual_hours > 0:
                    actual_rate = actual_base_pay / actual_hours
                    
                    print(f"      Staff sees:")
                    print(f"         Hours: {actual_hours}")
                    print(f"         Rate: ${actual_rate:.2f}/hr")
                    print(f"         Pay: ${actual_total_pay:.2f}")
                    
                    # Verify against expected values
                    hours_ok = abs(actual_hours - test_case['expected_hours']) < 0.1
                    rate_ok = abs(actual_rate - test_case['expected_rate']) < 0.01
                    pay_ok = abs(actual_total_pay - test_case['expected_pay']) < 0.01
                    
                    if hours_ok and rate_ok and pay_ok:
                        print(f"      ✅ Staff sees correct rates and calculations")
                        staff_tests_passed += 1
                    else:
                        print(f"      ❌ Staff sees incorrect rates:")
                        if not rate_ok:
                            print(f"         Rate mismatch: got ${actual_rate:.2f}, expected ${test_case['expected_rate']:.2f}")
                        if not pay_ok:
                            print(f"         Pay mismatch: got ${actual_total_pay:.2f}, expected ${test_case['expected_pay']:.2f}")
                else:
                    print(f"      ❌ No hours calculated")
            else:
                print(f"      ❌ Staff could not create shift")
        
        return staff_tests_passed == len(staff_test_shifts)

    def run_comprehensive_staff_rates_test(self):
        """Run comprehensive test of staff shift rates display"""
        print("🎯 COMPREHENSIVE STAFF SHIFT RATES TESTING")
        print("=" * 60)
        print("Testing actual shift times display rates that staff users see")
        print("Focus: Weekend shift templates with rate calculations")
        print("=" * 60)
        
        # Step 1: Authenticate as admin
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Get current settings
        if not self.get_current_settings():
            print("❌ Cannot proceed without settings data")
            return False
        
        # Step 3: Authenticate as staff user
        staff_users_to_test = ["rose", "chanelle", "caroline"]
        staff_authenticated = False
        
        for username in staff_users_to_test:
            if self.authenticate_staff(username, "888888"):
                staff_authenticated = True
                break
        
        if not staff_authenticated:
            print("❌ Cannot proceed without staff authentication")
            return False
        
        # Step 4: Test staff access to shift templates
        templates_test = self.test_staff_shift_templates_access()
        
        # Step 5: Test specific weekend shifts from review request
        weekend_test = self.test_specific_weekend_shifts()
        
        # Step 6: Test shift type classification
        classification_test = self.test_shift_type_classification()
        
        # Step 7: Compare admin vs staff rate visibility
        comparison_test = self.compare_admin_vs_staff_rates()
        
        # Step 8: Test staff shift creation with rates
        creation_test = self.test_staff_shift_creation_with_rates()
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"STAFF SHIFT RATES TESTING SUMMARY")
        print(f"=" * 60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Total tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"")
        print(f"Test Results:")
        print(f"   Staff Templates Access: {'✅' if templates_test else '❌'}")
        print(f"   Weekend Shift Calculations: {'✅' if weekend_test else '❌'}")
        print(f"   Shift Type Classification: {'✅' if classification_test else '❌'}")
        print(f"   Admin vs Staff Comparison: {'✅' if comparison_test else '❌'}")
        print(f"   Staff Shift Creation: {'✅' if creation_test else '❌'}")
        
        overall_success = all([templates_test, weekend_test, classification_test, comparison_test, creation_test])
        
        if overall_success:
            print(f"\n🎉 ALL STAFF SHIFT RATES TESTS PASSED!")
            print(f"   ✅ Staff users see correct Saturday rate: $57.50")
            print(f"   ✅ Staff users see correct Sunday rate: $74.00")
            print(f"   ✅ Weekend shifts classified correctly")
            print(f"   ✅ Rate calculations working properly")
        else:
            print(f"\n❌ STAFF SHIFT RATES ISSUES FOUND!")
            print(f"   Staff users may be seeing incorrect rates")
            print(f"   Weekend shift calculations may be wrong")
        
        return overall_success

if __name__ == "__main__":
    tester = StaffShiftRatesAPITester()
    success = tester.run_comprehensive_staff_rates_test()
    
    if success:
        print(f"\n🎉 All staff shift rates tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ Some staff shift rates tests failed!")
        sys.exit(1)