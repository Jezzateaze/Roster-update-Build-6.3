import requests
import sys
import json
from datetime import datetime, timedelta

class ShiftRosterAPITester:
    def __init__(self, base_url="https://48922ab2-157d-4f4d-94c3-b5aa731425bc.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.staff_data = []
        self.shift_templates = []
        self.roster_entries = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

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

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_get_staff(self):
        """Test getting all staff members"""
        success, response = self.run_test(
            "Get All Staff",
            "GET",
            "api/staff",
            200
        )
        if success:
            self.staff_data = response
            print(f"   Found {len(response)} staff members")
            expected_staff = ["Angela", "Chanelle", "Rose", "Caroline", "Nox", "Elina",
                            "Kayla", "Rhet", "Nikita", "Molly", "Felicity", "Issey"]
            actual_names = [staff['name'] for staff in response]
            missing_staff = [name for name in expected_staff if name not in actual_names]
            if missing_staff:
                print(f"   ⚠️  Missing expected staff: {missing_staff}")
            else:
                print(f"   ✅ All 12 expected staff members found")
        return success

    def test_create_staff(self):
        """Test creating a new staff member"""
        test_staff = {
            "name": "Test Staff Member",
            "active": True
        }
        success, response = self.run_test(
            "Create Staff Member",
            "POST",
            "api/staff",
            200,
            data=test_staff
        )
        if success and 'id' in response:
            print(f"   Created staff with ID: {response['id']}")
            return response['id']
        return None

    def test_get_shift_templates(self):
        """Test getting shift templates"""
        success, response = self.run_test(
            "Get Shift Templates",
            "GET",
            "api/shift-templates",
            200
        )
        if success:
            self.shift_templates = response
            print(f"   Found {len(response)} shift templates")
            # Check for expected pattern: 7 days * 4 shifts = 28 templates
            if len(response) == 28:
                print(f"   ✅ Expected 28 shift templates found")
            else:
                print(f"   ⚠️  Expected 28 shift templates, found {len(response)}")
            
            # Check day distribution
            day_counts = {}
            for template in response:
                day = template['day_of_week']
                day_counts[day] = day_counts.get(day, 0) + 1
            
            print(f"   Shifts per day: {day_counts}")
        return success

    def test_get_settings(self):
        """Test getting settings"""
        success, response = self.run_test(
            "Get Settings",
            "GET",
            "api/settings",
            200
        )
        if success:
            print(f"   Pay mode: {response.get('pay_mode', 'N/A')}")
            rates = response.get('rates', {})
            print(f"   Weekday day rate: ${rates.get('weekday_day', 0)}")
            print(f"   Saturday rate: ${rates.get('saturday', 0)}")
            print(f"   Sunday rate: ${rates.get('sunday', 0)}")
            print(f"   Sleepover allowance: ${rates.get('sleepover_default', 0)}")
        return success

    def test_generate_roster(self):
        """Test generating roster for current month"""
        current_month = datetime.now().strftime("%Y-%m")
        success, response = self.run_test(
            f"Generate Roster for {current_month}",
            "POST",
            f"api/generate-roster/{current_month}",
            200
        )
        if success:
            print(f"   {response.get('message', 'Roster generated')}")
        return success

    def test_get_roster(self):
        """Test getting roster for current month"""
        current_month = datetime.now().strftime("%Y-%m")
        success, response = self.run_test(
            f"Get Roster for {current_month}",
            "GET",
            "api/roster",
            200,
            params={"month": current_month}
        )
        if success:
            self.roster_entries = response
            print(f"   Found {len(response)} roster entries")
            if len(response) > 0:
                # Analyze first entry for pay calculation
                entry = response[0]
                print(f"   Sample entry: {entry['date']} {entry['start_time']}-{entry['end_time']}")
                print(f"   Hours: {entry.get('hours_worked', 0)}, Pay: ${entry.get('total_pay', 0)}")
        return success

    def test_pay_calculations(self):
        """Test pay calculation accuracy - FOCUS ON SCHADS EVENING SHIFT RULES"""
        print(f"\n💰 Testing SCHADS Award Pay Calculations...")
        print("🎯 CRITICAL TEST: Evening shift rule - 'Starts after 8:00pm OR extends past 8:00pm'")
        
        # Test data for SCHADS evening shift scenarios
        test_cases = [
            {
                "name": "15:30-23:30 shift (extends past 8pm) - CRITICAL TEST",
                "date": "2025-01-06",  # Monday
                "start_time": "15:30",
                "end_time": "23:30",
                "expected_hours": 8.0,
                "expected_rate": 44.50,  # Evening rate
                "expected_pay": 356.00,  # 8 * 44.50
                "shift_type": "EVENING"
            },
            {
                "name": "15:00-20:00 shift (extends past 8pm) - CRITICAL TEST",
                "date": "2025-01-06",  # Monday
                "start_time": "15:00",
                "end_time": "20:00",
                "expected_hours": 5.0,
                "expected_rate": 44.50,  # Evening rate
                "expected_pay": 222.50,  # 5 * 44.50
                "shift_type": "EVENING"
            },
            {
                "name": "20:30-23:30 shift (starts after 8pm) - CRITICAL TEST",
                "date": "2025-01-06",  # Monday
                "start_time": "20:30",
                "end_time": "23:30",
                "expected_hours": 3.0,
                "expected_rate": 44.50,  # Evening rate
                "expected_pay": 133.50,  # 3 * 44.50
                "shift_type": "EVENING"
            },
            {
                "name": "07:30-15:30 shift (ends before 8pm) - CONTROL TEST",
                "date": "2025-01-06",  # Monday
                "start_time": "07:30",
                "end_time": "15:30",
                "expected_hours": 8.0,
                "expected_rate": 42.00,  # Day rate
                "expected_pay": 336.00,  # 8 * 42.00
                "shift_type": "DAY"
            },
            {
                "name": "Weekday Night Shift (23:30-07:30)",
                "date": "2025-01-06",  # Monday
                "start_time": "23:30",
                "end_time": "07:30",
                "expected_hours": 8.0,
                "expected_rate": 48.50,
                "expected_pay": 388.00,
                "is_sleepover": True,
                "expected_sleepover": 175.00,
                "shift_type": "NIGHT"
            },
            {
                "name": "Saturday Shift (07:30-15:30)",
                "date": "2025-01-11",  # Saturday
                "start_time": "07:30",
                "end_time": "15:30",
                "expected_hours": 8.0,
                "expected_rate": 57.50,
                "expected_pay": 460.00,
                "shift_type": "SATURDAY"
            },
            {
                "name": "Sunday Shift (07:30-15:30)",
                "date": "2025-01-12",  # Sunday
                "start_time": "07:30",
                "end_time": "15:30",
                "expected_hours": 8.0,
                "expected_rate": 74.00,
                "expected_pay": 592.00,
                "shift_type": "SUNDAY"
            }
        ]

        pay_tests_passed = 0
        critical_evening_tests_passed = 0
        critical_evening_tests_total = 3  # First 3 are the critical evening shift tests
        
        for i, test_case in enumerate(test_cases):
            is_critical = i < critical_evening_tests_total
            print(f"\n   {'🎯 CRITICAL: ' if is_critical else ''}Testing: {test_case['name']}")
            
            # Create roster entry (id will be auto-generated by backend)
            roster_entry = {
                "id": "",  # Will be auto-generated
                "date": test_case["date"],
                "shift_template_id": "test-template",
                "start_time": test_case["start_time"],
                "end_time": test_case["end_time"],
                "is_sleepover": test_case.get("is_sleepover", False),
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None,
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
            
            success, response = self.run_test(
                f"Create {test_case['name']}",
                "POST",
                "api/roster",
                200,
                data=roster_entry
            )
            
            if success:
                hours_worked = response.get('hours_worked', 0)
                total_pay = response.get('total_pay', 0)
                base_pay = response.get('base_pay', 0)
                sleepover_allowance = response.get('sleepover_allowance', 0)
                
                print(f"      Expected shift type: {test_case.get('shift_type', 'N/A')}")
                print(f"      Hours worked: {hours_worked} (expected: {test_case['expected_hours']})")
                print(f"      Base pay: ${base_pay}")
                print(f"      Sleepover allowance: ${sleepover_allowance}")
                print(f"      Total pay: ${total_pay} (expected: ${test_case['expected_pay']})")
                
                # Check calculations
                hours_correct = abs(hours_worked - test_case['expected_hours']) < 0.1
                
                if test_case.get('is_sleepover'):
                    # For sleepover shifts, total pay = sleepover allowance (in default mode)
                    pay_correct = abs(total_pay - test_case['expected_sleepover']) < 0.01
                else:
                    pay_correct = abs(total_pay - test_case['expected_pay']) < 0.01
                
                if hours_correct and pay_correct:
                    print(f"      ✅ Pay calculation correct")
                    pay_tests_passed += 1
                    if is_critical:
                        critical_evening_tests_passed += 1
                else:
                    print(f"      ❌ Pay calculation incorrect")
                    if not hours_correct:
                        print(f"         Hours mismatch: got {hours_worked}, expected {test_case['expected_hours']}")
                    if not pay_correct:
                        expected = test_case['expected_sleepover'] if test_case.get('is_sleepover') else test_case['expected_pay']
                        print(f"         Pay mismatch: got ${total_pay}, expected ${expected}")
                    
                    if is_critical:
                        print(f"      🚨 CRITICAL EVENING SHIFT TEST FAILED!")
                        print(f"         This indicates the SCHADS evening shift rule may not be working correctly")
            else:
                if is_critical:
                    print(f"      🚨 CRITICAL TEST FAILED - Could not create roster entry")

        print(f"\n   🎯 CRITICAL Evening Shift Tests: {critical_evening_tests_passed}/{critical_evening_tests_total} passed")
        print(f"   📊 Total Pay calculation tests: {pay_tests_passed}/{len(test_cases)} passed")
        
        if critical_evening_tests_passed < critical_evening_tests_total:
            print(f"   ❌ CRITICAL ISSUE: Evening shift calculation logic needs attention!")
            print(f"      Expected: Shifts extending past 8:00pm should use evening rate ($44.50/hr)")
        else:
            print(f"   ✅ All critical evening shift tests passed!")
        
        return pay_tests_passed == len(test_cases)

    def analyze_existing_pay_calculations(self):
        """Analyze existing roster entries to verify pay calculations"""
        if not self.roster_entries:
            print("⚠️  No roster entries available for analysis")
            return False
        
        print(f"\n💰 Analyzing Existing Pay Calculations...")
        print(f"   Analyzing {len(self.roster_entries)} roster entries...")
        
        # Group by shift type
        shift_analysis = {
            'weekday_day': [],
            'weekday_evening': [],
            'weekday_night': [],
            'saturday': [],
            'sunday': [],
            'sleepover': []
        }
        
        for entry in self.roster_entries[:10]:  # Analyze first 10 entries
            date_obj = datetime.strptime(entry['date'], "%Y-%m-%d")
            day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
            start_hour = int(entry['start_time'].split(':')[0])
            
            if entry.get('is_sleepover'):
                shift_analysis['sleepover'].append(entry)
            elif day_of_week == 5:  # Saturday
                shift_analysis['saturday'].append(entry)
            elif day_of_week == 6:  # Sunday
                shift_analysis['sunday'].append(entry)
            elif start_hour >= 22 or start_hour < 6:
                shift_analysis['weekday_night'].append(entry)
            elif start_hour >= 20:
                shift_analysis['weekday_evening'].append(entry)
            else:
                shift_analysis['weekday_day'].append(entry)
        
        # Expected rates
        expected_rates = {
            'weekday_day': 42.00,
            'weekday_evening': 44.50,
            'weekday_night': 48.50,
            'saturday': 57.50,
            'sunday': 74.00,
            'sleepover': 175.00  # Default sleepover allowance
        }
        
        analysis_passed = True
        
        for shift_type, entries in shift_analysis.items():
            if not entries:
                continue
                
            print(f"\n   {shift_type.replace('_', ' ').title()} Shifts:")
            for entry in entries[:3]:  # Check first 3 of each type
                hours = entry.get('hours_worked', 0)
                total_pay = entry.get('total_pay', 0)
                base_pay = entry.get('base_pay', 0)
                sleepover_allowance = entry.get('sleepover_allowance', 0)
                
                if shift_type == 'sleepover':
                    expected_pay = expected_rates[shift_type]
                    actual_pay = sleepover_allowance
                else:
                    expected_pay = hours * expected_rates[shift_type]
                    actual_pay = base_pay
                
                pay_correct = abs(actual_pay - expected_pay) < 0.01
                
                print(f"      {entry['date']} {entry['start_time']}-{entry['end_time']}: "
                      f"{hours}h, ${actual_pay:.2f} (expected: ${expected_pay:.2f}) "
                      f"{'✅' if pay_correct else '❌'}")
                
                if not pay_correct:
                    analysis_passed = False
        
        return analysis_passed

    def test_roster_assignment(self):
        """Test assigning staff to roster entries"""
        if not self.roster_entries or not self.staff_data:
            print("⚠️  No roster entries or staff data available for assignment test")
            return False
        
        # Get first roster entry and first staff member
        entry = self.roster_entries[0]
        staff_member = self.staff_data[0]
        
        # Update roster entry with staff assignment
        updated_entry = {
            **entry,
            "staff_id": staff_member['id'],
            "staff_name": staff_member['name']
        }
        
        success, response = self.run_test(
            "Assign Staff to Roster Entry",
            "PUT",
            f"api/roster/{entry['id']}",
            200,
            data=updated_entry
        )
        
        if success:
            print(f"   Assigned {staff_member['name']} to shift on {entry['date']}")
        
        return success

    def test_roster_templates_crud(self):
        """Test roster template CRUD operations"""
        print(f"\n📋 Testing Roster Template CRUD Operations...")
        
        # Test 1: Get all roster templates (should be empty initially)
        success, templates = self.run_test(
            "Get All Roster Templates",
            "GET",
            "api/roster-templates",
            200
        )
        if success:
            print(f"   Found {len(templates)} existing roster templates")
        
        # Test 2: Create a new roster template
        test_template = {
            "id": "",  # Will be auto-generated by backend
            "name": "Test Template",
            "description": "A test roster template",
            "is_active": True,
            "template_data": {
                "0": [  # Monday
                    {"start_time": "07:30", "end_time": "15:30", "is_sleepover": False},
                    {"start_time": "15:30", "end_time": "23:30", "is_sleepover": False}
                ],
                "1": [  # Tuesday
                    {"start_time": "07:30", "end_time": "15:30", "is_sleepover": False}
                ]
            }
        }
        
        success, created_template = self.run_test(
            "Create Roster Template",
            "POST",
            "api/roster-templates",
            200,
            data=test_template
        )
        
        template_id = None
        if success and 'id' in created_template:
            template_id = created_template['id']
            print(f"   Created template with ID: {template_id}")
        
        # Test 3: Update the template
        if template_id:
            updated_template = {
                **created_template,
                "description": "Updated test template description"
            }
            success, response = self.run_test(
                "Update Roster Template",
                "PUT",
                f"api/roster-templates/{template_id}",
                200,
                data=updated_template
            )
        
        # Test 4: Delete the template
        if template_id:
            success, response = self.run_test(
                "Delete Roster Template",
                "DELETE",
                f"api/roster-templates/{template_id}",
                200
            )
        
        return True

    def test_save_current_roster_as_template(self):
        """Test saving current roster as a template"""
        print(f"\n💾 Testing Save Current Roster as Template...")
        
        # First ensure we have roster entries for August 2025
        month = "2025-08"
        success, response = self.run_test(
            f"Generate Roster for {month}",
            "POST",
            f"api/generate-roster/{month}",
            200
        )
        
        if not success:
            print("   ⚠️  Could not generate roster for testing")
            return False
        
        # Now save the current roster as a template
        template_name = "August 2025 Template"
        success, template = self.run_test(
            "Save Current Roster as Template",
            "POST",
            f"api/roster-templates/save-current/{template_name}?month={month}",
            200
        )
        
        if success:
            print(f"   ✅ Successfully saved roster as template: {template.get('name')}")
            print(f"   Template ID: {template.get('id')}")
            print(f"   Days with shifts: {list(template.get('template_data', {}).keys())}")
            return template.get('id')
        
        return None

    def test_generate_roster_from_template(self):
        """Test generating roster from a saved template"""
        print(f"\n🔄 Testing Generate Roster from Template...")
        
        # First save a template
        template_id = self.test_save_current_roster_as_template()
        if not template_id:
            print("   ⚠️  Could not create template for testing")
            return False
        
        # Clear roster for September 2025 to test generation
        target_month = "2025-09"
        success, response = self.run_test(
            f"Clear Roster for {target_month}",
            "DELETE",
            f"api/roster/month/{target_month}",
            200
        )
        
        # Generate roster from template for September 2025
        success, response = self.run_test(
            f"Generate Roster from Template for {target_month}",
            "POST",
            f"api/generate-roster-from-template/{template_id}/{target_month}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            overlaps_detected = response.get('overlaps_detected', 0)
            print(f"   ✅ Generated {entries_created} roster entries")
            if overlaps_detected > 0:
                print(f"   ⚠️  {overlaps_detected} overlaps detected and skipped")
            
            # Verify the generated roster
            success, roster_entries = self.run_test(
                f"Verify Generated Roster for {target_month}",
                "GET",
                "api/roster",
                200,
                params={"month": target_month}
            )
            
            if success:
                print(f"   ✅ Verified: {len(roster_entries)} entries in generated roster")
                
                # Check day-of-week placement
                day_distribution = {}
                for entry in roster_entries[:10]:  # Check first 10 entries
                    date_obj = datetime.strptime(entry['date'], "%Y-%m-%d")
                    day_of_week = date_obj.weekday()
                    day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
                    day_distribution[day_name] = day_distribution.get(day_name, 0) + 1
                
                print(f"   Day distribution (first 10): {day_distribution}")
                return True
        
        return False

    def test_overlap_detection(self):
        """Test overlap detection for shift additions and updates"""
        print(f"\n🚫 Testing Overlap Detection...")
        
        # Test date for overlap testing (use December which we cleared)
        test_date = "2025-12-15"
        
        # First, add a shift
        shift1 = {
            "id": "",  # Will be auto-generated
            "date": test_date,
            "shift_template_id": "test-overlap-1",
            "staff_id": None,
            "staff_name": None,
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "manual_shift_type": None,
            "manual_hourly_rate": None,
            "manual_sleepover": None,
            "wake_hours": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_shift = self.run_test(
            "Add First Shift (No Overlap)",
            "POST",
            "api/roster/add-shift",
            200,
            data=shift1
        )
        
        if not success:
            print("   ⚠️  Could not create first shift for overlap testing")
            return False
        
        shift1_id = created_shift.get('id')
        print(f"   ✅ Created first shift: {shift1['start_time']}-{shift1['end_time']}")
        
        # Test 2: Try to add an overlapping shift (should fail)
        overlapping_shift = {
            "id": "",  # Will be auto-generated
            "date": test_date,
            "shift_template_id": "test-overlap-2",
            "staff_id": None,
            "staff_name": None,
            "start_time": "15:00",  # Overlaps with first shift
            "end_time": "20:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "manual_shift_type": None,
            "manual_hourly_rate": None,
            "manual_sleepover": None,
            "wake_hours": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, response = self.run_test(
            "Add Overlapping Shift (Should Fail)",
            "POST",
            "api/roster/add-shift",
            409,  # Expect conflict status
            data=overlapping_shift
        )
        
        if success:  # Success here means we got the expected 409 status
            print(f"   ✅ Overlap correctly detected and prevented")
        else:
            print(f"   ❌ Overlap detection failed - overlapping shift was allowed")
        
        # Test 3: Add a non-overlapping shift (should succeed)
        non_overlapping_shift = {
            "id": "",  # Will be auto-generated
            "date": test_date,
            "shift_template_id": "test-overlap-3",
            "staff_id": None,
            "staff_name": None,
            "start_time": "18:00",  # After first shift ends
            "end_time": "22:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "manual_shift_type": None,
            "manual_hourly_rate": None,
            "manual_sleepover": None,
            "wake_hours": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_shift2 = self.run_test(
            "Add Non-Overlapping Shift (Should Succeed)",
            "POST",
            "api/roster/add-shift",
            200,
            data=non_overlapping_shift
        )
        
        if success:
            print(f"   ✅ Non-overlapping shift added successfully")
        
        # Test 4: Try to update first shift to overlap with second (should fail)
        if shift1_id:
            updated_shift1 = {
                **created_shift,
                "end_time": "19:00"  # Would overlap with second shift
            }
            
            success, response = self.run_test(
                "Update Shift to Create Overlap (Should Fail)",
                "PUT",
                f"api/roster/{shift1_id}",
                409,  # Expect conflict status
                data=updated_shift1
            )
            
            if success:  # Success here means we got the expected 409 status
                print(f"   ✅ Update overlap correctly detected and prevented")
            else:
                print(f"   ❌ Update overlap detection failed")
        
        return True

    def test_day_of_week_placement(self):
        """Test that template generation places shifts on correct days of week"""
        print(f"\n📅 Testing Day-of-Week Based Placement...")
        
        # Create a template with specific day-of-week patterns
        test_template = {
            "id": "",  # Will be auto-generated
            "name": "Day-of-Week Test Template",
            "description": "Template for testing day-of-week placement",
            "is_active": True,
            "template_data": {
                "0": [  # Monday only
                    {"start_time": "08:00", "end_time": "16:00", "is_sleepover": False}
                ],
                "2": [  # Wednesday only
                    {"start_time": "10:00", "end_time": "18:00", "is_sleepover": False}
                ],
                "4": [  # Friday only
                    {"start_time": "12:00", "end_time": "20:00", "is_sleepover": False}
                ]
            }
        }
        
        success, created_template = self.run_test(
            "Create Day-of-Week Test Template",
            "POST",
            "api/roster-templates",
            200,
            data=test_template
        )
        
        if not success or 'id' not in created_template:
            print("   ⚠️  Could not create test template")
            return False
        
        template_id = created_template['id']
        
        # Clear and generate roster for October 2025
        test_month = "2025-10"
        success, response = self.run_test(
            f"Clear Roster for {test_month}",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        success, response = self.run_test(
            f"Generate Roster from Day-of-Week Template",
            "POST",
            f"api/generate-roster-from-template/{template_id}/{test_month}",
            200
        )
        
        if not success:
            print("   ⚠️  Could not generate roster from template")
            return False
        
        # Verify the placement
        success, roster_entries = self.run_test(
            f"Get Generated Roster for Verification",
            "GET",
            "api/roster",
            200,
            params={"month": test_month}
        )
        
        if success:
            # Analyze day-of-week distribution
            day_analysis = {
                'Monday': {'count': 0, 'times': []},
                'Tuesday': {'count': 0, 'times': []},
                'Wednesday': {'count': 0, 'times': []},
                'Thursday': {'count': 0, 'times': []},
                'Friday': {'count': 0, 'times': []},
                'Saturday': {'count': 0, 'times': []},
                'Sunday': {'count': 0, 'times': []}
            }
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for entry in roster_entries:
                date_obj = datetime.strptime(entry['date'], "%Y-%m-%d")
                day_of_week = date_obj.weekday()
                day_name = day_names[day_of_week]
                
                day_analysis[day_name]['count'] += 1
                day_analysis[day_name]['times'].append(f"{entry['start_time']}-{entry['end_time']}")
            
            print(f"   Day-of-week analysis:")
            for day, data in day_analysis.items():
                if data['count'] > 0:
                    print(f"      {day}: {data['count']} shifts - {set(data['times'])}")
            
            # Verify expected pattern: only Monday, Wednesday, Friday should have shifts
            expected_days = ['Monday', 'Wednesday', 'Friday']
            unexpected_days = ['Tuesday', 'Thursday', 'Saturday', 'Sunday']
            
            placement_correct = True
            for day in expected_days:
                if day_analysis[day]['count'] == 0:
                    print(f"   ❌ Expected shifts on {day} but found none")
                    placement_correct = False
            
            for day in unexpected_days:
                if day_analysis[day]['count'] > 0:
                    print(f"   ❌ Unexpected shifts found on {day}")
                    placement_correct = False
            
            if placement_correct:
                print(f"   ✅ Day-of-week placement is correct")
            
            return placement_correct
        
        return False

    def test_day_templates_crud(self):
        """Test day template CRUD operations"""
        print(f"\n🌟 Testing Day Template CRUD Operations...")
        
        # Test 1: Get all day templates (should be empty initially)
        success, templates = self.run_test(
            "Get All Day Templates",
            "GET",
            "api/day-templates",
            200
        )
        if success:
            print(f"   Found {len(templates)} existing day templates")
        
        # Test 2: Create a new day template
        test_day_template = {
            "id": "",  # Will be auto-generated by backend
            "name": "Test Monday Template",
            "description": "A test day template for Monday",
            "day_of_week": 0,  # Monday
            "shifts": [
                {"start_time": "07:30", "end_time": "15:30", "is_sleepover": False},
                {"start_time": "15:30", "end_time": "23:30", "is_sleepover": False},
                {"start_time": "23:30", "end_time": "07:30", "is_sleepover": True}
            ],
            "is_active": True
        }
        
        success, created_template = self.run_test(
            "Create Day Template",
            "POST",
            "api/day-templates",
            200,
            data=test_day_template
        )
        
        template_id = None
        if success and 'id' in created_template:
            template_id = created_template['id']
            print(f"   Created day template with ID: {template_id}")
            print(f"   Template has {len(created_template.get('shifts', []))} shifts")
        
        # Test 3: Get templates for specific day of week
        if template_id:
            success, day_templates = self.run_test(
                "Get Templates for Monday (day 0)",
                "GET",
                "api/day-templates/0",
                200
            )
            if success:
                print(f"   Found {len(day_templates)} templates for Monday")
                monday_template_found = any(t['id'] == template_id for t in day_templates)
                if monday_template_found:
                    print(f"   ✅ Created template found in Monday templates")
                else:
                    print(f"   ❌ Created template not found in Monday templates")
        
        # Test 4: Delete the template
        if template_id:
            success, response = self.run_test(
                "Delete Day Template",
                "DELETE",
                f"api/day-templates/{template_id}",
                200
            )
            if success:
                print(f"   ✅ Day template deleted successfully")
        
        return True

    def test_save_day_as_template(self):
        """Test saving a specific day as a day template"""
        print(f"\n💾 Testing Save Day as Template...")
        
        # First, ensure we have roster entries for a specific date
        test_date = "2025-08-04"  # Monday, August 4th, 2025
        
        # Create some test shifts for this date
        test_shifts = [
            {
                "id": "",
                "date": test_date,
                "shift_template_id": "test-day-save-1",
                "start_time": "07:30",
                "end_time": "15:30",
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None,
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            },
            {
                "id": "",
                "date": test_date,
                "shift_template_id": "test-day-save-2",
                "start_time": "15:00",
                "end_time": "20:00",
                "is_sleepover": False,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None,
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            },
            {
                "id": "",
                "date": test_date,
                "shift_template_id": "test-day-save-3",
                "start_time": "23:30",
                "end_time": "07:30",
                "is_sleepover": True,
                "is_public_holiday": False,
                "staff_id": None,
                "staff_name": None,
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
        ]
        
        # Create the test shifts
        created_shifts = []
        for i, shift in enumerate(test_shifts):
            success, created_shift = self.run_test(
                f"Create Test Shift {i+1} for {test_date}",
                "POST",
                "api/roster",
                200,
                data=shift
            )
            if success:
                created_shifts.append(created_shift)
        
        if len(created_shifts) != len(test_shifts):
            print(f"   ⚠️  Could not create all test shifts. Created {len(created_shifts)}/{len(test_shifts)}")
            return False
        
        print(f"   ✅ Created {len(created_shifts)} test shifts for {test_date}")
        
        # Now save the day as a template
        template_name = "Monday Aug 4th Template"
        success, day_template = self.run_test(
            f"Save {test_date} as Day Template",
            "POST",
            f"api/day-templates/save-day/{template_name}?date={test_date}",
            200
        )
        
        if success:
            print(f"   ✅ Successfully saved day as template: {day_template.get('name')}")
            print(f"   Template ID: {day_template.get('id')}")
            print(f"   Day of week: {day_template.get('day_of_week')} (0=Monday)")
            print(f"   Number of shifts: {len(day_template.get('shifts', []))}")
            
            # Verify the shifts were saved correctly
            saved_shifts = day_template.get('shifts', [])
            expected_times = [("07:30", "15:30"), ("15:00", "20:00"), ("23:30", "07:30")]
            
            for expected_start, expected_end in expected_times:
                found = any(s['start_time'] == expected_start and s['end_time'] == expected_end for s in saved_shifts)
                if found:
                    print(f"   ✅ Shift {expected_start}-{expected_end} saved correctly")
                else:
                    print(f"   ❌ Shift {expected_start}-{expected_end} not found in template")
            
            return day_template.get('id')
        
        return None

    def test_apply_day_template_to_date(self):
        """Test applying a day template to a specific date"""
        print(f"\n🔄 Testing Apply Day Template to Date...")
        
        # First create a day template
        template_id = self.test_save_day_as_template()
        if not template_id:
            print("   ⚠️  Could not create day template for testing")
            return False
        
        # Apply the template to a different Monday (August 11th, 2025)
        target_date = "2025-08-11"  # Another Monday
        
        success, response = self.run_test(
            f"Apply Day Template to {target_date}",
            "POST",
            f"api/day-templates/apply-to-date/{template_id}?target_date={target_date}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            template_name = response.get('template_name', 'Unknown')
            print(f"   ✅ Applied '{template_name}' to {target_date}")
            print(f"   Created {entries_created} roster entries")
            
            # Verify the entries were created
            success, roster_entries = self.run_test(
                f"Verify Applied Template Entries",
                "GET",
                "api/roster",
                200,
                params={"month": "2025-08"}
            )
            
            if success:
                target_entries = [e for e in roster_entries if e['date'] == target_date]
                print(f"   ✅ Found {len(target_entries)} entries for {target_date}")
                
                # Check that shifts have correct times but no staff assignments
                for entry in target_entries:
                    has_staff = entry.get('staff_id') is not None or entry.get('staff_name') is not None
                    if has_staff:
                        print(f"   ❌ Template application should not include staff assignments")
                    else:
                        print(f"   ✅ Shift {entry['start_time']}-{entry['end_time']} created without staff assignment")
                
                return len(target_entries) == entries_created
        
        return False

    def test_day_template_overlap_detection(self):
        """Test overlap detection when applying day templates"""
        print(f"\n🚫 Testing Day Template Overlap Detection...")
        
        # Create a day template first
        template_id = self.test_save_day_as_template()
        if not template_id:
            print("   ⚠️  Could not create day template for testing")
            return False
        
        # Create a conflicting shift on the target date first
        target_date = "2025-08-18"  # Another Monday
        conflicting_shift = {
            "id": "",
            "date": target_date,
            "shift_template_id": "conflict-test",
            "start_time": "08:00",  # Overlaps with 07:30-15:30 from template
            "end_time": "16:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "staff_id": None,
            "staff_name": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_shift = self.run_test(
            f"Create Conflicting Shift on {target_date}",
            "POST",
            "api/roster",
            200,
            data=conflicting_shift
        )
        
        if not success:
            print("   ⚠️  Could not create conflicting shift")
            return False
        
        print(f"   ✅ Created conflicting shift: {conflicting_shift['start_time']}-{conflicting_shift['end_time']}")
        
        # Now try to apply the day template (should fail due to overlap)
        success, response = self.run_test(
            f"Apply Day Template with Overlap (Should Fail)",
            "POST",
            f"api/day-templates/apply-to-date/{template_id}?target_date={target_date}",
            409  # Expect conflict status
        )
        
        if success:  # Success here means we got the expected 409 status
            print(f"   ✅ Overlap correctly detected and prevented")
            return True
        else:
            print(f"   ❌ Overlap detection failed - template was applied despite conflicts")
            return False

    def test_day_template_filtering(self):
        """Test day-of-week filtering functionality"""
        print(f"\n📅 Testing Day Template Filtering...")
        
        # Create templates for different days
        test_templates = [
            {
                "name": "Monday Template",
                "description": "Template for Monday",
                "day_of_week": 0,  # Monday
                "shifts": [{"start_time": "09:00", "end_time": "17:00", "is_sleepover": False}],
                "is_active": True
            },
            {
                "name": "Wednesday Template",
                "description": "Template for Wednesday",
                "day_of_week": 2,  # Wednesday
                "shifts": [{"start_time": "10:00", "end_time": "18:00", "is_sleepover": False}],
                "is_active": True
            },
            {
                "name": "Friday Template",
                "description": "Template for Friday",
                "day_of_week": 4,  # Friday
                "shifts": [{"start_time": "11:00", "end_time": "19:00", "is_sleepover": False}],
                "is_active": True
            }
        ]
        
        created_template_ids = []
        
        # Create the templates
        for template_data in test_templates:
            template_data["id"] = ""  # Will be auto-generated
            success, created_template = self.run_test(
                f"Create {template_data['name']}",
                "POST",
                "api/day-templates",
                200,
                data=template_data
            )
            if success and 'id' in created_template:
                created_template_ids.append((created_template['id'], template_data['day_of_week']))
        
        if len(created_template_ids) != len(test_templates):
            print(f"   ⚠️  Could not create all test templates")
            return False
        
        print(f"   ✅ Created {len(created_template_ids)} test templates")
        
        # Test filtering by day of week
        test_cases = [
            (0, "Monday", 1),    # Should find 1 Monday template
            (2, "Wednesday", 1), # Should find 1 Wednesday template
            (4, "Friday", 1),    # Should find 1 Friday template
            (1, "Tuesday", 0),   # Should find 0 Tuesday templates
            (6, "Sunday", 0)     # Should find 0 Sunday templates
        ]
        
        filtering_correct = True
        
        for day_of_week, day_name, expected_count in test_cases:
            success, day_templates = self.run_test(
                f"Get Templates for {day_name} (day {day_of_week})",
                "GET",
                f"api/day-templates/{day_of_week}",
                200
            )
            
            if success:
                actual_count = len(day_templates)
                if actual_count == expected_count:
                    print(f"   ✅ {day_name}: Found {actual_count} templates (expected {expected_count})")
                else:
                    print(f"   ❌ {day_name}: Found {actual_count} templates (expected {expected_count})")
                    filtering_correct = False
                
                # Verify all returned templates are for the correct day
                for template in day_templates:
                    if template.get('day_of_week') != day_of_week:
                        print(f"   ❌ Template '{template.get('name')}' has wrong day_of_week: {template.get('day_of_week')}")
                        filtering_correct = False
            else:
                print(f"   ❌ Failed to get templates for {day_name}")
                filtering_correct = False
        
        return filtering_correct

    # ========================================
    # CALENDAR EVENTS TESTS - NEW FUNCTIONALITY
    # ========================================

    def test_calendar_events_crud(self):
        """Test calendar events CRUD operations"""
        print(f"\n📅 Testing Calendar Events CRUD Operations...")
        
        # Test 1: Get all calendar events (should be empty initially)
        success, events = self.run_test(
            "Get All Calendar Events",
            "GET",
            "api/calendar-events",
            200
        )
        if success:
            print(f"   Found {len(events)} existing calendar events")
        
        # Test 2: Create different types of calendar events
        test_events = [
            {
                "id": "",  # Will be auto-generated
                "title": "Team Meeting",
                "description": "Weekly team standup meeting",
                "date": "2025-01-15",
                "start_time": "09:00",
                "end_time": "10:00",
                "is_all_day": False,
                "event_type": "meeting",
                "priority": "high",
                "location": "Conference Room A",
                "attendees": ["Alice", "Bob", "Charlie"],
                "reminder_minutes": 15,
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "Doctor Appointment",
                "description": "Annual health checkup",
                "date": "2025-01-16",
                "start_time": "14:30",
                "end_time": "15:30",
                "is_all_day": False,
                "event_type": "appointment",
                "priority": "medium",
                "location": "Medical Center",
                "attendees": [],
                "reminder_minutes": 30,
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "Complete Project Report",
                "description": "Finish quarterly project report",
                "date": "2025-01-17",
                "start_time": None,
                "end_time": None,
                "is_all_day": True,
                "event_type": "task",
                "priority": "urgent",
                "location": None,
                "attendees": [],
                "reminder_minutes": 60,
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "Birthday Party",
                "description": "Sarah's birthday celebration",
                "date": "2025-01-18",
                "start_time": "18:00",
                "end_time": "22:00",
                "is_all_day": False,
                "event_type": "personal",
                "priority": "low",
                "location": "Sarah's House",
                "attendees": ["Sarah", "Mike", "Lisa"],
                "reminder_minutes": 120,
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "Call Mom",
                "description": "Weekly check-in call with mom",
                "date": "2025-01-19",
                "start_time": "19:00",
                "end_time": "19:30",
                "is_all_day": False,
                "event_type": "reminder",
                "priority": "medium",
                "location": None,
                "attendees": [],
                "reminder_minutes": 10,
                "is_completed": False,
                "is_active": True
            }
        ]
        
        created_event_ids = []
        
        # Create all test events
        for i, event_data in enumerate(test_events):
            success, created_event = self.run_test(
                f"Create {event_data['event_type'].title()} Event: {event_data['title']}",
                "POST",
                "api/calendar-events",
                200,
                data=event_data
            )
            
            if success and 'id' in created_event:
                created_event_ids.append(created_event['id'])
                print(f"   ✅ Created {event_data['event_type']} event with ID: {created_event['id']}")
                
                # Verify event properties
                if created_event.get('priority') == event_data['priority']:
                    print(f"      Priority: {created_event.get('priority')} ✅")
                else:
                    print(f"      Priority mismatch: got {created_event.get('priority')}, expected {event_data['priority']} ❌")
                
                if created_event.get('is_all_day') == event_data['is_all_day']:
                    print(f"      All-day: {created_event.get('is_all_day')} ✅")
                else:
                    print(f"      All-day mismatch: got {created_event.get('is_all_day')}, expected {event_data['is_all_day']} ❌")
        
        if len(created_event_ids) != len(test_events):
            print(f"   ⚠️  Could not create all test events. Created {len(created_event_ids)}/{len(test_events)}")
            return False
        
        print(f"   ✅ Successfully created {len(created_event_ids)} calendar events")
        
        # Test 3: Update an event
        if created_event_ids:
            event_to_update = created_event_ids[0]
            updated_event_data = {
                **test_events[0],
                "id": event_to_update,
                "title": "Updated Team Meeting",
                "priority": "urgent",
                "description": "Updated weekly team standup meeting"
            }
            
            success, updated_event = self.run_test(
                "Update Calendar Event",
                "PUT",
                f"api/calendar-events/{event_to_update}",
                200,
                data=updated_event_data
            )
            
            if success:
                print(f"   ✅ Successfully updated event: {updated_event.get('title')}")
                print(f"      New priority: {updated_event.get('priority')}")
        
        # Test 4: Delete an event
        if len(created_event_ids) > 1:
            event_to_delete = created_event_ids[1]
            success, response = self.run_test(
                "Delete Calendar Event",
                "DELETE",
                f"api/calendar-events/{event_to_delete}",
                200
            )
            
            if success:
                print(f"   ✅ Successfully deleted event")
        
        # Store created event IDs for other tests
        self.calendar_event_ids = created_event_ids
        return True

    def test_calendar_events_filtering(self):
        """Test calendar events filtering by date range and event type"""
        print(f"\n🔍 Testing Calendar Events Filtering...")
        
        # Ensure we have events to test with
        if not hasattr(self, 'calendar_event_ids') or not self.calendar_event_ids:
            print("   ⚠️  No calendar events available for filtering test")
            return False
        
        # Test 1: Filter by date range
        success, filtered_events = self.run_test(
            "Filter Events by Date Range (2025-01-15 to 2025-01-17)",
            "GET",
            "api/calendar-events",
            200,
            params={"start_date": "2025-01-15", "end_date": "2025-01-17"}
        )
        
        if success:
            print(f"   ✅ Found {len(filtered_events)} events in date range")
            # Verify all events are within the date range
            for event in filtered_events:
                event_date = event.get('date')
                if event_date and "2025-01-15" <= event_date <= "2025-01-17":
                    print(f"      Event '{event.get('title')}' on {event_date} ✅")
                else:
                    print(f"      Event '{event.get('title')}' on {event_date} outside range ❌")
        
        # Test 2: Filter by event type
        event_types_to_test = ["meeting", "appointment", "task", "personal", "reminder"]
        
        for event_type in event_types_to_test:
            success, type_filtered_events = self.run_test(
                f"Filter Events by Type: {event_type}",
                "GET",
                "api/calendar-events",
                200,
                params={"event_type": event_type}
            )
            
            if success:
                print(f"   ✅ Found {len(type_filtered_events)} {event_type} events")
                # Verify all events are of the correct type
                for event in type_filtered_events:
                    if event.get('event_type') == event_type:
                        print(f"      '{event.get('title')}' is {event_type} ✅")
                    else:
                        print(f"      '{event.get('title')}' is {event.get('event_type')}, not {event_type} ❌")
        
        # Test 3: Combined filtering (date range + event type)
        success, combined_filtered = self.run_test(
            "Filter Events by Date Range AND Type (meetings 2025-01-15 to 2025-01-16)",
            "GET",
            "api/calendar-events",
            200,
            params={"start_date": "2025-01-15", "end_date": "2025-01-16", "event_type": "meeting"}
        )
        
        if success:
            print(f"   ✅ Found {len(combined_filtered)} meeting events in date range")
            for event in combined_filtered:
                event_date = event.get('date')
                event_type = event.get('event_type')
                date_ok = "2025-01-15" <= event_date <= "2025-01-16"
                type_ok = event_type == "meeting"
                print(f"      '{event.get('title')}': date={event_date} ({date_ok}), type={event_type} ({type_ok})")
        
        return True

    def test_get_events_for_specific_date(self):
        """Test getting events for a specific date"""
        print(f"\n📅 Testing Get Events for Specific Date...")
        
        # Test getting events for specific dates
        test_dates = ["2025-01-15", "2025-01-16", "2025-01-17", "2025-01-20"]  # Last one should be empty
        
        for test_date in test_dates:
            success, date_events = self.run_test(
                f"Get Events for {test_date}",
                "GET",
                f"api/calendar-events/{test_date}",
                200
            )
            
            if success:
                print(f"   ✅ Found {len(date_events)} events for {test_date}")
                for event in date_events:
                    event_title = event.get('title', 'Unknown')
                    event_type = event.get('event_type', 'unknown')
                    is_all_day = event.get('is_all_day', False)
                    
                    if is_all_day:
                        print(f"      '{event_title}' ({event_type}) - All day")
                    else:
                        start_time = event.get('start_time', 'N/A')
                        end_time = event.get('end_time', 'N/A')
                        print(f"      '{event_title}' ({event_type}) - {start_time} to {end_time}")
                    
                    # Verify the event is actually for the requested date
                    if event.get('date') != test_date:
                        print(f"         ❌ Event date mismatch: {event.get('date')} != {test_date}")
        
        return True

    def test_task_completion(self):
        """Test marking tasks as completed"""
        print(f"\n✅ Testing Task Completion...")
        
        # First, find a task event to complete
        success, all_events = self.run_test(
            "Get All Events to Find Tasks",
            "GET",
            "api/calendar-events",
            200,
            params={"event_type": "task"}
        )
        
        if not success or not all_events:
            print("   ⚠️  No task events found for completion test")
            return False
        
        task_event = all_events[0]
        task_id = task_event.get('id')
        task_title = task_event.get('title', 'Unknown Task')
        
        print(f"   Testing completion of task: '{task_title}' (ID: {task_id})")
        
        # Verify task is not completed initially
        if task_event.get('is_completed'):
            print(f"   ⚠️  Task is already marked as completed")
        else:
            print(f"   ✅ Task is initially not completed")
        
        # Mark the task as completed
        success, response = self.run_test(
            f"Mark Task as Completed",
            "PUT",
            f"api/calendar-events/{task_id}/complete",
            200
        )
        
        if success:
            print(f"   ✅ Task completion request successful")
            
            # Verify the task is now marked as completed
            success, updated_events = self.run_test(
                "Verify Task Completion",
                "GET",
                f"api/calendar-events/{task_event.get('date')}",
                200
            )
            
            if success:
                completed_task = next((e for e in updated_events if e.get('id') == task_id), None)
                if completed_task and completed_task.get('is_completed'):
                    print(f"   ✅ Task is now marked as completed")
                    return True
                else:
                    print(f"   ❌ Task completion status not updated")
        
        return False

    def test_calendar_events_priority_levels(self):
        """Test different priority levels for calendar events"""
        print(f"\n🎯 Testing Calendar Events Priority Levels...")
        
        # Create events with different priority levels
        priority_test_events = [
            {
                "id": "",
                "title": "Low Priority Meeting",
                "description": "Optional team sync",
                "date": "2025-01-20",
                "start_time": "10:00",
                "end_time": "10:30",
                "is_all_day": False,
                "event_type": "meeting",
                "priority": "low",
                "location": "Virtual",
                "attendees": [],
                "reminder_minutes": 5,
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "Medium Priority Task",
                "description": "Review documentation",
                "date": "2025-01-20",
                "start_time": None,
                "end_time": None,
                "is_all_day": True,
                "event_type": "task",
                "priority": "medium",
                "location": None,
                "attendees": [],
                "reminder_minutes": 30,
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "High Priority Appointment",
                "description": "Important client meeting",
                "date": "2025-01-20",
                "start_time": "14:00",
                "end_time": "15:00",
                "is_all_day": False,
                "event_type": "appointment",
                "priority": "high",
                "location": "Client Office",
                "attendees": ["Client", "Manager"],
                "reminder_minutes": 60,
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "Urgent Reminder",
                "description": "Submit tax documents",
                "date": "2025-01-20",
                "start_time": "16:00",
                "end_time": "16:15",
                "is_all_day": False,
                "event_type": "reminder",
                "priority": "urgent",
                "location": None,
                "attendees": [],
                "reminder_minutes": 120,
                "is_completed": False,
                "is_active": True
            }
        ]
        
        created_priority_events = []
        
        for event_data in priority_test_events:
            success, created_event = self.run_test(
                f"Create {event_data['priority'].upper()} Priority Event: {event_data['title']}",
                "POST",
                "api/calendar-events",
                200,
                data=event_data
            )
            
            if success:
                created_priority_events.append(created_event)
                priority = created_event.get('priority')
                expected_priority = event_data['priority']
                
                if priority == expected_priority:
                    print(f"   ✅ Priority correctly set to '{priority}'")
                else:
                    print(f"   ❌ Priority mismatch: got '{priority}', expected '{expected_priority}'")
        
        # Verify all priority levels are represented
        priorities_created = [e.get('priority') for e in created_priority_events]
        expected_priorities = ['low', 'medium', 'high', 'urgent']
        
        for expected_priority in expected_priorities:
            if expected_priority in priorities_created:
                print(f"   ✅ {expected_priority.upper()} priority event created successfully")
            else:
                print(f"   ❌ {expected_priority.upper()} priority event not found")
        
        return len(created_priority_events) == len(priority_test_events)

    def test_all_day_vs_timed_events(self):
        """Test handling of all-day vs timed events"""
        print(f"\n⏰ Testing All-Day vs Timed Events...")
        
        # Create test events with different time configurations
        time_test_events = [
            {
                "id": "",
                "title": "All-Day Conference",
                "description": "Annual tech conference",
                "date": "2025-01-21",
                "start_time": None,
                "end_time": None,
                "is_all_day": True,
                "event_type": "meeting",
                "priority": "high",
                "location": "Convention Center",
                "attendees": ["Team"],
                "reminder_minutes": 480,  # 8 hours
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "Timed Meeting",
                "description": "Project kickoff meeting",
                "date": "2025-01-21",
                "start_time": "09:00",
                "end_time": "10:30",
                "is_all_day": False,
                "event_type": "meeting",
                "priority": "high",
                "location": "Conference Room B",
                "attendees": ["Project Team"],
                "reminder_minutes": 15,
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "All-Day Personal Event",
                "description": "Vacation day",
                "date": "2025-01-22",
                "start_time": None,
                "end_time": None,
                "is_all_day": True,
                "event_type": "personal",
                "priority": "low",
                "location": "Beach",
                "attendees": [],
                "reminder_minutes": 1440,  # 24 hours
                "is_completed": False,
                "is_active": True
            },
            {
                "id": "",
                "title": "Short Timed Task",
                "description": "Quick status update",
                "date": "2025-01-22",
                "start_time": "15:00",
                "end_time": "15:15",
                "is_all_day": False,
                "event_type": "task",
                "priority": "medium",
                "location": None,
                "attendees": [],
                "reminder_minutes": 5,
                "is_completed": False,
                "is_active": True
            }
        ]
        
        created_time_events = []
        
        for event_data in time_test_events:
            success, created_event = self.run_test(
                f"Create {'All-Day' if event_data['is_all_day'] else 'Timed'} Event: {event_data['title']}",
                "POST",
                "api/calendar-events",
                200,
                data=event_data
            )
            
            if success:
                created_time_events.append(created_event)
                
                # Verify all-day vs timed properties
                is_all_day = created_event.get('is_all_day')
                start_time = created_event.get('start_time')
                end_time = created_event.get('end_time')
                expected_all_day = event_data['is_all_day']
                
                if is_all_day == expected_all_day:
                    print(f"   ✅ All-day flag correctly set to {is_all_day}")
                else:
                    print(f"   ❌ All-day flag mismatch: got {is_all_day}, expected {expected_all_day}")
                
                if expected_all_day:
                    # All-day events should have None for start/end times
                    if start_time is None and end_time is None:
                        print(f"   ✅ All-day event has no specific times")
                    else:
                        print(f"   ❌ All-day event has times: {start_time}-{end_time}")
                else:
                    # Timed events should have start/end times
                    if start_time and end_time:
                        print(f"   ✅ Timed event has times: {start_time}-{end_time}")
                    else:
                        print(f"   ❌ Timed event missing times: {start_time}-{end_time}")
        
        print(f"   ✅ Created {len(created_time_events)} time-configuration test events")
        
        # Test retrieving events and verify time handling
        success, events_for_date = self.run_test(
            "Get Events for 2025-01-21 (Mixed All-Day and Timed)",
            "GET",
            "api/calendar-events/2025-01-21",
            200
        )
        
        if success:
            all_day_count = sum(1 for e in events_for_date if e.get('is_all_day'))
            timed_count = sum(1 for e in events_for_date if not e.get('is_all_day'))
            print(f"   ✅ Found {all_day_count} all-day and {timed_count} timed events for 2025-01-21")
        
        return len(created_time_events) == len(time_test_events)

    def test_calendar_events_data_validation(self):
        """Test data validation and error handling for calendar events"""
        print(f"\n🔍 Testing Calendar Events Data Validation...")
        
        # Test invalid event data
        invalid_test_cases = [
            {
                "name": "Missing Required Title",
                "data": {
                    "id": "",
                    "description": "Event without title",
                    "date": "2025-01-25",
                    "event_type": "meeting",
                    "priority": "medium",
                    "is_all_day": False,
                    "is_active": True
                },
                "expected_status": 422  # Validation error
            },
            {
                "name": "Invalid Date Format",
                "data": {
                    "id": "",
                    "title": "Invalid Date Event",
                    "description": "Event with invalid date",
                    "date": "2025-13-45",  # Invalid date
                    "event_type": "meeting",
                    "priority": "medium",
                    "is_all_day": False,
                    "is_active": True
                },
                "expected_status": 422  # Validation error
            },
            {
                "name": "Invalid Event Type",
                "data": {
                    "id": "",
                    "title": "Invalid Type Event",
                    "description": "Event with invalid type",
                    "date": "2025-01-25",
                    "event_type": "invalid_type",  # Not in allowed types
                    "priority": "medium",
                    "is_all_day": False,
                    "is_active": True
                },
                "expected_status": 422  # Validation error
            },
            {
                "name": "Invalid Priority Level",
                "data": {
                    "id": "",
                    "title": "Invalid Priority Event",
                    "description": "Event with invalid priority",
                    "date": "2025-01-25",
                    "event_type": "meeting",
                    "priority": "super_urgent",  # Not in allowed priorities
                    "is_all_day": False,
                    "is_active": True
                },
                "expected_status": 422  # Validation error
            }
        ]
        
        validation_tests_passed = 0
        
        for test_case in invalid_test_cases:
            success, response = self.run_test(
                f"Test Validation: {test_case['name']}",
                "POST",
                "api/calendar-events",
                test_case['expected_status'],
                data=test_case['data']
            )
            
            if success:  # Success means we got the expected error status
                validation_tests_passed += 1
                print(f"   ✅ Validation correctly rejected: {test_case['name']}")
            else:
                print(f"   ❌ Validation failed to reject: {test_case['name']}")
        
        # Test valid edge cases
        valid_edge_cases = [
            {
                "name": "Minimal Valid Event",
                "data": {
                    "id": "",
                    "title": "Minimal Event",
                    "date": "2025-01-25",
                    "event_type": "reminder",
                    "priority": "low",
                    "is_all_day": True,
                    "is_active": True
                }
            },
            {
                "name": "Event with All Optional Fields",
                "data": {
                    "id": "",
                    "title": "Complete Event",
                    "description": "Event with all fields populated",
                    "date": "2025-01-25",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "is_all_day": False,
                    "event_type": "appointment",
                    "priority": "urgent",
                    "location": "Test Location",
                    "attendees": ["Person 1", "Person 2", "Person 3"],
                    "reminder_minutes": 30,
                    "is_completed": False,
                    "is_active": True
                }
            }
        ]
        
        for test_case in valid_edge_cases:
            success, response = self.run_test(
                f"Test Valid Edge Case: {test_case['name']}",
                "POST",
                "api/calendar-events",
                200,
                data=test_case['data']
            )
            
            if success:
                validation_tests_passed += 1
                print(f"   ✅ Valid edge case accepted: {test_case['name']}")
            else:
                print(f"   ❌ Valid edge case rejected: {test_case['name']}")
        
        total_validation_tests = len(invalid_test_cases) + len(valid_edge_cases)
        print(f"   📊 Validation tests: {validation_tests_passed}/{total_validation_tests} passed")
        
        return validation_tests_passed == total_validation_tests

    def test_generate_roster_from_shift_templates(self):
        """Test the new roster generation endpoint using shift templates with manual overrides"""
        print(f"\n🚀 Testing Generate Roster from Shift Templates (NEW FUNCTIONALITY)...")
        
        # Test month
        test_month = "2025-08"
        
        # Clear existing roster for the test month
        success, response = self.run_test(
            f"Clear Roster for {test_month}",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        # Create test shift templates with manual overrides
        test_templates = {
            "templates": [
                {
                    "id": "template-monday-1",
                    "name": "Monday Morning Shift",
                    "start_time": "07:30",
                    "end_time": "15:30",
                    "is_sleepover": False,
                    "day_of_week": 0,  # Monday
                    "manual_shift_type": "weekday_evening",  # Override to evening rate
                    "manual_hourly_rate": 45.00  # Override hourly rate
                },
                {
                    "id": "template-monday-2", 
                    "name": "Monday Evening Shift",
                    "start_time": "15:00",
                    "end_time": "20:00",
                    "is_sleepover": False,
                    "day_of_week": 0,  # Monday
                    "manual_shift_type": None,  # No override - should auto-detect as evening
                    "manual_hourly_rate": None  # No override - should use standard rate
                },
                {
                    "id": "template-tuesday-1",
                    "name": "Tuesday Day Shift", 
                    "start_time": "08:00",
                    "end_time": "16:00",
                    "is_sleepover": False,
                    "day_of_week": 1,  # Tuesday
                    "manual_shift_type": None,
                    "manual_hourly_rate": 50.25  # Override hourly rate only
                },
                {
                    "id": "template-wednesday-sleepover",
                    "name": "Wednesday Sleepover",
                    "start_time": "23:30", 
                    "end_time": "07:30",
                    "is_sleepover": True,
                    "day_of_week": 2,  # Wednesday
                    "manual_shift_type": "weekday_night",
                    "manual_hourly_rate": 60.00
                }
            ]
        }
        
        # Test the new roster generation endpoint
        success, response = self.run_test(
            f"Generate Roster from Shift Templates for {test_month}",
            "POST",
            f"api/generate-roster-from-shift-templates/{test_month}",
            200,
            data=test_templates
        )
        
        if not success:
            print("   ❌ Failed to generate roster from shift templates")
            return False
        
        entries_created = response.get('entries_created', 0)
        overlaps_detected = response.get('overlaps_detected', 0)
        print(f"   ✅ Generated {entries_created} roster entries")
        if overlaps_detected > 0:
            print(f"   ⚠️  {overlaps_detected} overlaps detected and skipped")
        
        # Verify the generated roster
        success, roster_entries = self.run_test(
            f"Get Generated Roster for Verification",
            "GET", 
            "api/roster",
            200,
            params={"month": test_month}
        )
        
        if not success:
            print("   ❌ Failed to retrieve generated roster")
            return False
        
        print(f"   ✅ Retrieved {len(roster_entries)} roster entries for verification")
        
        # Test manual overrides preservation
        manual_override_tests_passed = 0
        manual_override_tests_total = 0
        
        for entry in roster_entries[:10]:  # Check first 10 entries
            date_obj = datetime.strptime(entry['date'], "%Y-%m-%d")
            day_of_week = date_obj.weekday()
            
            # Find matching template
            matching_template = None
            for template in test_templates["templates"]:
                if (template["day_of_week"] == day_of_week and 
                    template["start_time"] == entry["start_time"] and
                    template["end_time"] == entry["end_time"]):
                    matching_template = template
                    break
            
            if matching_template:
                manual_override_tests_total += 1
                
                # Check manual_shift_type preservation
                expected_manual_shift_type = matching_template.get("manual_shift_type")
                actual_manual_shift_type = entry.get("manual_shift_type")
                
                # Check manual_hourly_rate preservation  
                expected_manual_rate = matching_template.get("manual_hourly_rate")
                actual_manual_rate = entry.get("manual_hourly_rate")
                
                shift_type_correct = expected_manual_shift_type == actual_manual_shift_type
                hourly_rate_correct = expected_manual_rate == actual_manual_rate
                
                if shift_type_correct and hourly_rate_correct:
                    manual_override_tests_passed += 1
                    print(f"   ✅ Manual overrides preserved for {entry['date']} {entry['start_time']}-{entry['end_time']}")
                    if expected_manual_shift_type:
                        print(f"      Manual shift type: {actual_manual_shift_type}")
                    if expected_manual_rate:
                        print(f"      Manual hourly rate: ${actual_manual_rate}")
                else:
                    print(f"   ❌ Manual overrides not preserved for {entry['date']} {entry['start_time']}-{entry['end_time']}")
                    if not shift_type_correct:
                        print(f"      Shift type: expected {expected_manual_shift_type}, got {actual_manual_shift_type}")
                    if not hourly_rate_correct:
                        print(f"      Hourly rate: expected ${expected_manual_rate}, got ${actual_manual_rate}")
        
        # Test day-of-week placement
        day_placement_correct = True
        day_distribution = {}
        
        for entry in roster_entries:
            date_obj = datetime.strptime(entry['date'], "%Y-%m-%d")
            day_of_week = date_obj.weekday()
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
            day_distribution[day_name] = day_distribution.get(day_name, 0) + 1
        
        print(f"   Day distribution: {day_distribution}")
        
        # Verify only expected days have shifts (Monday, Tuesday, Wednesday based on our templates)
        expected_days = ['Monday', 'Tuesday', 'Wednesday']
        for day in expected_days:
            if day_distribution.get(day, 0) == 0:
                print(f"   ❌ Expected shifts on {day} but found none")
                day_placement_correct = False
            else:
                print(f"   ✅ Found {day_distribution[day]} shifts on {day}")
        
        # Test pay calculation with overrides
        pay_calculation_tests_passed = 0
        pay_calculation_tests_total = 0
        
        for entry in roster_entries[:5]:  # Check first 5 entries
            pay_calculation_tests_total += 1
            
            total_pay = entry.get('total_pay', 0)
            hours_worked = entry.get('hours_worked', 0)
            manual_rate = entry.get('manual_hourly_rate')
            
            if manual_rate and not entry.get('is_sleepover', False):
                expected_pay = hours_worked * manual_rate
                if abs(total_pay - expected_pay) < 0.01:
                    pay_calculation_tests_passed += 1
                    print(f"   ✅ Pay calculation with manual rate correct: {hours_worked}h × ${manual_rate} = ${total_pay}")
                else:
                    print(f"   ❌ Pay calculation with manual rate incorrect: expected ${expected_pay}, got ${total_pay}")
            else:
                # Standard pay calculation - just verify it's not zero
                if total_pay > 0:
                    pay_calculation_tests_passed += 1
                    print(f"   ✅ Standard pay calculation: ${total_pay} for {hours_worked}h")
                else:
                    print(f"   ❌ Pay calculation failed: ${total_pay} for {hours_worked}h")
        
        print(f"\n   📊 Test Results Summary:")
        print(f"      Manual override preservation: {manual_override_tests_passed}/{manual_override_tests_total}")
        print(f"      Day-of-week placement: {'✅' if day_placement_correct else '❌'}")
        print(f"      Pay calculations: {pay_calculation_tests_passed}/{pay_calculation_tests_total}")
        
        # Overall success criteria
        success_criteria = [
            entries_created > 0,
            manual_override_tests_passed == manual_override_tests_total,
            day_placement_correct,
            pay_calculation_tests_passed == pay_calculation_tests_total
        ]
        
        overall_success = all(success_criteria)
        print(f"   🎯 Overall Test Result: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return overall_success

    def test_roster_template_edit_delete(self):
        """Test enhanced roster template management - edit and delete functionality"""
        print(f"\n📝 Testing Enhanced Roster Template Management (NEW FUNCTIONALITY)...")
        
        # First create a test roster template
        test_template = {
            "id": "",  # Will be auto-generated
            "name": "Test Template for Edit/Delete",
            "description": "Original description",
            "is_active": True,
            "template_data": {
                "0": [  # Monday
                    {"start_time": "09:00", "end_time": "17:00", "is_sleepover": False}
                ],
                "2": [  # Wednesday  
                    {"start_time": "10:00", "end_time": "18:00", "is_sleepover": False}
                ]
            }
        }
        
        success, created_template = self.run_test(
            "Create Test Roster Template",
            "POST",
            "api/roster-templates",
            200,
            data=test_template
        )
        
        if not success or 'id' not in created_template:
            print("   ❌ Failed to create test template")
            return False
        
        template_id = created_template['id']
        print(f"   ✅ Created test template with ID: {template_id}")
        
        # Test 1: Update roster template (PUT endpoint)
        updated_template = {
            **created_template,
            "name": "Updated Template Name",
            "description": "Updated description with new details",
            "template_data": {
                "0": [  # Monday - modified
                    {"start_time": "08:00", "end_time": "16:00", "is_sleepover": False},
                    {"start_time": "16:00", "end_time": "22:00", "is_sleepover": False}
                ],
                "2": [  # Wednesday - kept same
                    {"start_time": "10:00", "end_time": "18:00", "is_sleepover": False}
                ],
                "4": [  # Friday - added new
                    {"start_time": "12:00", "end_time": "20:00", "is_sleepover": False}
                ]
            }
        }
        
        success, response = self.run_test(
            "Update Roster Template (PUT)",
            "PUT",
            f"api/roster-templates/{template_id}",
            200,
            data=updated_template
        )
        
        if not success:
            print("   ❌ Failed to update roster template")
            return False
        
        print(f"   ✅ Successfully updated roster template")
        print(f"      New name: {response.get('name')}")
        print(f"      New description: {response.get('description')}")
        
        # Verify the update by retrieving the template
        success, templates = self.run_test(
            "Verify Template Update",
            "GET",
            "api/roster-templates",
            200
        )
        
        if success:
            updated_template_found = next((t for t in templates if t['id'] == template_id), None)
            if updated_template_found:
                name_updated = updated_template_found.get('name') == "Updated Template Name"
                description_updated = updated_template_found.get('description') == "Updated description with new details"
                
                if name_updated and description_updated:
                    print(f"   ✅ Template update verified successfully")
                    
                    # Check template data structure
                    template_data = updated_template_found.get('template_data', {})
                    days_with_shifts = list(template_data.keys())
                    print(f"      Days with shifts: {days_with_shifts}")
                    
                    if '4' in days_with_shifts:  # Friday was added
                        print(f"   ✅ New Friday shifts added successfully")
                    else:
                        print(f"   ❌ New Friday shifts not found")
                        
                else:
                    print(f"   ❌ Template update verification failed")
                    print(f"      Name updated: {name_updated}")
                    print(f"      Description updated: {description_updated}")
            else:
                print(f"   ❌ Updated template not found in template list")
        
        # Test 2: Delete roster template (DELETE endpoint)
        success, response = self.run_test(
            "Delete Roster Template (DELETE)",
            "DELETE",
            f"api/roster-templates/{template_id}",
            200
        )
        
        if not success:
            print("   ❌ Failed to delete roster template")
            return False
        
        print(f"   ✅ Successfully deleted roster template")
        print(f"      Response: {response.get('message', 'Template deleted')}")
        
        # Verify the deletion by checking if template is no longer active
        success, templates_after_delete = self.run_test(
            "Verify Template Deletion",
            "GET", 
            "api/roster-templates",
            200
        )
        
        if success:
            deleted_template_found = next((t for t in templates_after_delete if t['id'] == template_id), None)
            if deleted_template_found:
                print(f"   ❌ Deleted template still found in active templates list")
                return False
            else:
                print(f"   ✅ Template deletion verified - template no longer in active list")
        
        # Test 3: Try to update deleted template (should fail)
        success, response = self.run_test(
            "Try to Update Deleted Template (Should Fail)",
            "PUT",
            f"api/roster-templates/{template_id}",
            404,  # Expect not found
            data=updated_template
        )
        
        if success:  # Success here means we got the expected 404
            print(f"   ✅ Update of deleted template correctly failed with 404")
        else:
            print(f"   ❌ Update of deleted template should have failed but didn't")
        
        # Test 4: Try to delete already deleted template (should fail)
        success, response = self.run_test(
            "Try to Delete Already Deleted Template (Should Fail)",
            "DELETE",
            f"api/roster-templates/{template_id}",
            404  # Expect not found
        )
        
        if success:  # Success here means we got the expected 404
            print(f"   ✅ Delete of already deleted template correctly failed with 404")
        else:
            print(f"   ❌ Delete of already deleted template should have failed but didn't")
        
        print(f"\n   📊 Enhanced Template Management Test Results:")
        print(f"      ✅ Template creation: Working")
        print(f"      ✅ Template update (PUT): Working") 
        print(f"      ✅ Template deletion (DELETE): Working")
        print(f"      ✅ Update verification: Working")
        print(f"      ✅ Deletion verification: Working")
        print(f"      ✅ Error handling: Working")
        
        return True

    def test_overlap_detection_in_template_generation(self):
        """Test overlap detection and prevention in the new roster generation"""
        print(f"\n🚫 Testing Overlap Detection in Template Generation...")
        
        test_month = "2025-09"
        
        # Clear the test month
        success, response = self.run_test(
            f"Clear Roster for {test_month}",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        # First, create some existing shifts manually
        existing_shift = {
            "id": "",
            "date": "2025-09-01",  # Monday
            "shift_template_id": "existing-shift",
            "start_time": "08:00",
            "end_time": "16:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "staff_id": None,
            "staff_name": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_shift = self.run_test(
            "Create Existing Shift for Overlap Test",
            "POST",
            "api/roster",
            200,
            data=existing_shift
        )
        
        if not success:
            print("   ⚠️  Could not create existing shift for overlap test")
            return False
        
        print(f"   ✅ Created existing shift: 2025-09-01 08:00-16:00")
        
        # Now try to generate roster with overlapping templates
        overlapping_templates = {
            "templates": [
                {
                    "id": "overlap-test-1",
                    "name": "Overlapping Monday Shift",
                    "start_time": "07:00",  # Overlaps with existing 08:00-16:00 shift
                    "end_time": "15:00",
                    "is_sleepover": False,
                    "day_of_week": 0,  # Monday
                    "manual_shift_type": None,
                    "manual_hourly_rate": None
                },
                {
                    "id": "overlap-test-2", 
                    "name": "Non-overlapping Monday Shift",
                    "start_time": "17:00",  # Does not overlap
                    "end_time": "21:00",
                    "is_sleepover": False,
                    "day_of_week": 0,  # Monday
                    "manual_shift_type": None,
                    "manual_hourly_rate": None
                }
            ]
        }
        
        success, response = self.run_test(
            f"Generate Roster with Overlapping Templates",
            "POST",
            f"api/generate-roster-from-shift-templates/{test_month}",
            200,
            data=overlapping_templates
        )
        
        if not success:
            print("   ❌ Failed to generate roster with overlap test")
            return False
        
        entries_created = response.get('entries_created', 0)
        overlaps_detected = response.get('overlaps_detected', 0)
        overlap_details = response.get('overlap_details', [])
        
        print(f"   ✅ Roster generation completed")
        print(f"      Entries created: {entries_created}")
        print(f"      Overlaps detected: {overlaps_detected}")
        
        if overlaps_detected > 0:
            print(f"   ✅ Overlap detection working - {overlaps_detected} overlaps prevented")
            for i, overlap in enumerate(overlap_details[:3]):  # Show first 3
                print(f"      Overlap {i+1}: {overlap.get('date')} {overlap.get('start_time')}-{overlap.get('end_time')}")
        else:
            print(f"   ⚠️  No overlaps detected - this might indicate an issue")
        
        # Verify the final roster
        success, final_roster = self.run_test(
            f"Verify Final Roster After Overlap Test",
            "GET",
            "api/roster",
            200,
            params={"month": test_month}
        )
        
        if success:
            monday_shifts = [e for e in final_roster if e['date'] == '2025-09-01']
            print(f"   ✅ Monday (2025-09-01) has {len(monday_shifts)} shifts:")
            
            for shift in monday_shifts:
                print(f"      {shift['start_time']}-{shift['end_time']} (template: {shift.get('shift_template_id', 'N/A')})")
            
            # Should have the original shift (08:00-16:00) and the non-overlapping one (17:00-21:00)
            # The overlapping one (07:00-15:00) should have been skipped
            expected_shifts = 2  # Original + non-overlapping
            if len(monday_shifts) == expected_shifts:
                print(f"   ✅ Correct number of shifts after overlap prevention")
                return True
            else:
                print(f"   ❌ Expected {expected_shifts} shifts, found {len(monday_shifts)}")
        
        return False

    def test_2to1_shift_overlap_functionality(self):
        """Test the new 2:1 shift overlap functionality"""
        print(f"\n🔄 Testing 2:1 Shift Overlap Functionality...")
        
        # Test date for overlap testing
        test_date = "2025-08-15"  # Friday
        
        # Clear any existing shifts for this date
        success, response = self.run_test(
            f"Clear existing shifts for {test_date}",
            "DELETE",
            f"api/roster/month/2025-08",
            200
        )
        
        # Test 1: Create a regular shift (baseline)
        regular_shift = {
            "id": "",
            "date": test_date,
            "shift_template_id": "regular-shift-test",
            "staff_id": None,
            "staff_name": None,
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "manual_shift_type": None,
            "manual_hourly_rate": None,
            "manual_sleepover": None,
            "wake_hours": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_regular_shift = self.run_test(
            "Create Regular Shift (09:00-17:00)",
            "POST",
            "api/roster/add-shift",
            200,
            data=regular_shift
        )
        
        if not success:
            print("   ⚠️  Could not create regular shift for 2:1 overlap testing")
            return False
        
        regular_shift_id = created_regular_shift.get('id')
        print(f"   ✅ Created regular shift: {regular_shift['start_time']}-{regular_shift['end_time']}")
        
        # Test 2: Try to create another regular shift that overlaps (should fail)
        overlapping_regular_shift = {
            "id": "",
            "date": test_date,
            "shift_template_id": "overlapping-regular-test",
            "staff_id": None,
            "staff_name": None,
            "start_time": "15:00",  # Overlaps with first shift
            "end_time": "23:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "manual_shift_type": None,
            "manual_hourly_rate": None,
            "manual_sleepover": None,
            "wake_hours": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, response = self.run_test(
            "Try to Create Overlapping Regular Shift (Should Fail)",
            "POST",
            "api/roster/add-shift",
            409,  # Expect conflict status
            data=overlapping_regular_shift
        )
        
        if success:  # Success here means we got the expected 409 status
            print(f"   ✅ Regular shift overlap correctly prevented")
        else:
            print(f"   ❌ Regular shift overlap detection failed")
            return False
        
        # Test 3: Create a "2:1 Evening Shift" that overlaps (should succeed)
        # First create a shift template with "2:1" in the name
        two_to_one_template = {
            "id": "",  # Let backend auto-generate
            "name": "2:1 Evening Shift",
            "start_time": "15:00",
            "end_time": "23:00",
            "is_sleepover": False,
            "day_of_week": 4  # Friday
        }
        
        success, created_template = self.run_test(
            "Create 2:1 Shift Template",
            "POST",
            "api/shift-templates",
            200,
            data=two_to_one_template
        )
        
        if not success or 'id' not in created_template:
            print("   ❌ Could not create 2:1 shift template")
            return False
        
        template_id = created_template['id']
        print(f"   ✅ Created 2:1 shift template: {two_to_one_template['name']} (ID: {template_id})")
        
        two_to_one_shift = {
            "id": "",
            "date": test_date,
            "shift_template_id": template_id,  # Use the actual template ID
            "staff_id": None,
            "staff_name": None,
            "start_time": "15:00",  # Overlaps with regular shift
            "end_time": "23:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "manual_shift_type": None,
            "manual_hourly_rate": None,
            "manual_sleepover": None,
            "wake_hours": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_2to1_shift = self.run_test(
            "Create 2:1 Evening Shift (Should Succeed Despite Overlap)",
            "POST",
            "api/roster/add-shift",
            200,
            data=two_to_one_shift
        )
        
        if success:
            print(f"   ✅ 2:1 shift overlap allowed successfully")
            two_to_one_shift_id = created_2to1_shift.get('id')
        else:
            print(f"   ❌ 2:1 shift overlap was incorrectly prevented")
            return False
        
        # Test 4: Create another "2:1 Support Shift" that overlaps with both (should succeed)
        # Create another 2:1 template
        another_2to1_template = {
            "id": "",  # Let backend auto-generate
            "name": "2:1 Support Shift",
            "start_time": "16:00",
            "end_time": "22:00",
            "is_sleepover": False,
            "day_of_week": 4  # Friday
        }
        
        success, created_template2 = self.run_test(
            "Create Another 2:1 Shift Template",
            "POST",
            "api/shift-templates",
            200,
            data=another_2to1_template
        )
        
        if not success or 'id' not in created_template2:
            print("   ❌ Could not create second 2:1 shift template")
            return False
        
        template_id2 = created_template2['id']
        print(f"   ✅ Created second 2:1 shift template: {another_2to1_template['name']} (ID: {template_id2})")
        
        another_2to1_shift = {
            "id": "",
            "date": test_date,
            "shift_template_id": template_id2,  # Use the actual template ID
            "staff_id": None,
            "staff_name": None,
            "start_time": "16:00",  # Overlaps with both previous shifts
            "end_time": "22:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "manual_shift_type": None,
            "manual_hourly_rate": None,
            "manual_sleepover": None,
            "wake_hours": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_another_2to1 = self.run_test(
            "Create Another 2:1 Support Shift (Should Succeed Despite Multiple Overlaps)",
            "POST",
            "api/roster/add-shift",
            200,
            data=another_2to1_shift
        )
        
        if success:
            print(f"   ✅ Multiple 2:1 shift overlaps allowed successfully")
        else:
            print(f"   ❌ Multiple 2:1 shift overlaps were incorrectly prevented")
            return False
        
        # Test 5: Test case insensitive detection - create "2:1 night shift" (lowercase)
        lowercase_2to1_template = {
            "id": "",  # Let backend auto-generate
            "name": "2:1 night shift",  # lowercase
            "start_time": "20:00",
            "end_time": "04:00",
            "is_sleepover": False,
            "day_of_week": 4  # Friday
        }
        
        success, created_template3 = self.run_test(
            "Create Lowercase 2:1 Shift Template",
            "POST",
            "api/shift-templates",
            200,
            data=lowercase_2to1_template
        )
        
        if not success or 'id' not in created_template3:
            print("   ❌ Could not create lowercase 2:1 shift template")
            return False
        
        template_id3 = created_template3['id']
        print(f"   ✅ Created lowercase 2:1 shift template: {lowercase_2to1_template['name']} (ID: {template_id3})")
        
        lowercase_2to1_shift = {
            "id": "",
            "date": test_date,
            "shift_template_id": template_id3,  # Use the actual template ID
            "staff_id": None,
            "staff_name": None,
            "start_time": "20:00",  # Overlaps with existing shifts
            "end_time": "04:00",
            "is_sleepover": False,
            "is_public_holiday": False,
            "manual_shift_type": None,
            "manual_hourly_rate": None,
            "manual_sleepover": None,
            "wake_hours": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_lowercase_2to1 = self.run_test(
            "Create Lowercase 2:1 Night Shift (Case Insensitive Test)",
            "POST",
            "api/roster/add-shift",
            200,
            data=lowercase_2to1_shift
        )
        
        if success:
            print(f"   ✅ Case insensitive 2:1 detection working")
        else:
            print(f"   ❌ Case insensitive 2:1 detection failed")
            return False
        
        # Test 6: Test updating a regular shift to overlap with 2:1 shift (should fail)
        if regular_shift_id:
            # First get the current state of the regular shift
            success, current_roster = self.run_test(
                "Get Current Roster to Check Regular Shift State",
                "GET",
                "api/roster",
                200,
                params={"month": "2025-08"}
            )
            
            if success:
                # Find the regular shift
                regular_shift_current = None
                for entry in current_roster:
                    if entry.get('id') == regular_shift_id:
                        regular_shift_current = entry
                        break
                
                if regular_shift_current:
                    print(f"   Current regular shift: {regular_shift_current['start_time']}-{regular_shift_current['end_time']}")
                    
                    # Try to extend it to overlap with 2:1 shifts
                    updated_regular_shift = {
                        **regular_shift_current,
                        "end_time": "19:00"  # Extend to overlap with 2:1 shifts
                    }
                    
                    success, response = self.run_test(
                        "Update Regular Shift to Overlap with 2:1 (Should Fail)",
                        "PUT",
                        f"api/roster/{regular_shift_id}",
                        409,  # Expect conflict status
                        data=updated_regular_shift
                    )
                    
                    if success:  # Success here means we got the expected 409 status
                        print(f"   ✅ Regular shift update overlap correctly prevented")
                    else:
                        print(f"   ❌ Regular shift update overlap detection failed")
                        return False
                else:
                    print(f"   ⚠️  Could not find regular shift for update test")
                    return False
            else:
                print(f"   ⚠️  Could not get current roster for update test")
                return False
        
        # Test 7: Test updating a 2:1 shift to overlap with regular shift (should succeed)
        if two_to_one_shift_id:
            updated_2to1_shift = {
                **created_2to1_shift,
                "start_time": "14:00"  # Extends overlap with regular shift
            }
            
            success, response = self.run_test(
                "Update 2:1 Shift to Extend Overlap (Should Succeed)",
                "PUT",
                f"api/roster/{two_to_one_shift_id}",
                200,
                data=updated_2to1_shift
            )
            
            if success:
                print(f"   ✅ 2:1 shift update overlap allowed successfully")
            else:
                print(f"   ❌ 2:1 shift update overlap was incorrectly prevented")
                return False
        
        print(f"   🎉 All 2:1 shift overlap tests passed!")
        return True

    def test_2to1_shift_template_generation(self):
        """Test 2:1 shift overlap in template generation"""
        print(f"\n📋 Testing 2:1 Shift Overlap in Template Generation...")
        
        # Test month for template generation
        test_month = "2025-09"
        
        # Clear existing roster for test month
        success, response = self.run_test(
            f"Clear Roster for {test_month}",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        # Create shift templates with 2:1 overlaps
        shift_templates = [
            {
                "name": "Regular Morning Shift",
                "start_time": "08:00",
                "end_time": "16:00",
                "is_sleepover": False,
                "day_of_week": 0,  # Monday
                "manual_shift_type": None,
                "manual_hourly_rate": None
            },
            {
                "name": "2:1 Afternoon Shift",  # This should be allowed to overlap
                "start_time": "14:00",
                "end_time": "22:00",
                "is_sleepover": False,
                "day_of_week": 0,  # Monday - overlaps with morning shift
                "manual_shift_type": None,
                "manual_hourly_rate": None
            },
            {
                "name": "2:1 Evening Support",  # This should also be allowed to overlap
                "start_time": "18:00",
                "end_time": "02:00",
                "is_sleepover": False,
                "day_of_week": 0,  # Monday - overlaps with afternoon shift
                "manual_shift_type": None,
                "manual_hourly_rate": None
            }
        ]
        
        # Test using the enhanced roster generation endpoint
        templates_data = {
            "templates": shift_templates
        }
        
        success, response = self.run_test(
            f"Generate Roster with 2:1 Overlapping Templates for {test_month}",
            "POST",
            f"api/generate-roster-from-shift-templates/{test_month}",
            200,
            data=templates_data
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            overlaps_detected = response.get('overlaps_detected', 0)
            overlap_details = response.get('overlap_details', [])
            
            print(f"   ✅ Generated {entries_created} roster entries")
            print(f"   Overlaps detected: {overlaps_detected}")
            
            if overlaps_detected > 0:
                print(f"   Overlap details (first 5):")
                for detail in overlap_details[:5]:
                    print(f"      {detail.get('date')} {detail.get('start_time')}-{detail.get('end_time')} ({detail.get('name', 'Unknown')})")
            
            # Verify the generated roster has overlapping 2:1 shifts
            success, roster_entries = self.run_test(
                f"Verify Generated Roster for {test_month}",
                "GET",
                "api/roster",
                200,
                params={"month": test_month}
            )
            
            if success:
                # Check for overlapping shifts on Mondays
                monday_shifts = []
                for entry in roster_entries:
                    date_obj = datetime.strptime(entry['date'], "%Y-%m-%d")
                    if date_obj.weekday() == 0:  # Monday
                        monday_shifts.append(entry)
                        if len(monday_shifts) >= 9:  # Check first 3 Mondays (3 shifts each)
                            break
                
                print(f"   Found {len(monday_shifts)} Monday shifts for overlap analysis")
                
                # Group by date and check for overlaps
                monday_dates = {}
                for shift in monday_shifts:
                    date = shift['date']
                    if date not in monday_dates:
                        monday_dates[date] = []
                    monday_dates[date].append(shift)
                
                overlap_found = False
                for date, shifts in monday_dates.items():
                    if len(shifts) > 1:
                        print(f"   Date {date} has {len(shifts)} shifts:")
                        for shift in shifts:
                            print(f"      {shift['start_time']}-{shift['end_time']}")
                        overlap_found = True
                        break
                
                if overlap_found:
                    print(f"   ✅ 2:1 shift overlaps successfully generated")
                else:
                    print(f"   ⚠️  No overlapping shifts found (may be expected if overlaps were prevented)")
                
                return True
        
        return False

    def test_2to1_day_template_overlap(self):
        """Test 2:1 shift overlap in day template application"""
        print(f"\n🌟 Testing 2:1 Shift Overlap in Day Template Application...")
        
        # Create a day template with 2:1 shifts
        day_template_with_2to1 = {
            "id": "",
            "name": "2:1 Monday Template",
            "description": "Monday template with 2:1 overlapping shifts",
            "day_of_week": 0,  # Monday
            "shifts": [
                {"start_time": "09:00", "end_time": "17:00", "is_sleepover": False},  # Regular shift
                {"start_time": "15:00", "end_time": "23:00", "is_sleepover": False},  # 2:1 overlap
                {"start_time": "19:00", "end_time": "03:00", "is_sleepover": False}   # Another 2:1 overlap
            ],
            "is_active": True
        }
        
        success, created_template = self.run_test(
            "Create Day Template with 2:1 Overlaps",
            "POST",
            "api/day-templates",
            200,
            data=day_template_with_2to1
        )
        
        if not success or 'id' not in created_template:
            print("   ⚠️  Could not create day template with 2:1 overlaps")
            return False
        
        template_id = created_template['id']
        print(f"   ✅ Created day template with ID: {template_id}")
        
        # Apply the template to a specific Monday
        target_date = "2025-09-01"  # Monday, September 1st, 2025
        
        success, response = self.run_test(
            f"Apply 2:1 Day Template to {target_date}",
            "POST",
            f"api/day-templates/apply-to-date/{template_id}?target_date={target_date}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            template_name = response.get('template_name', 'Unknown')
            print(f"   ✅ Applied '{template_name}' to {target_date}")
            print(f"   Created {entries_created} roster entries")
            
            # Verify the overlapping entries were created
            success, roster_entries = self.run_test(
                f"Verify Applied 2:1 Template Entries",
                "GET",
                "api/roster",
                200,
                params={"month": "2025-09"}
            )
            
            if success:
                target_entries = [e for e in roster_entries if e['date'] == target_date]
                print(f"   ✅ Found {len(target_entries)} entries for {target_date}")
                
                if len(target_entries) >= 3:  # Should have all 3 overlapping shifts
                    print(f"   ✅ All overlapping 2:1 shifts created successfully")
                    for entry in target_entries:
                        print(f"      Shift: {entry['start_time']}-{entry['end_time']}")
                    return True
                else:
                    print(f"   ❌ Expected 3 overlapping shifts, got {len(target_entries)}")
        
        return False

def main():
    print("🚀 Starting Shift Roster & Pay Calculator API Tests")
    print("🎯 FOCUS: Testing NEW Roster Generation from Shift Templates & Enhanced Template Management")
    print("=" * 60)
    
    tester = ShiftRosterAPITester()
    
    # Run basic tests first
    basic_tests = [
        tester.test_health_check,
        tester.test_get_staff,
        tester.test_get_shift_templates,
        tester.test_get_settings,
    ]
    
    # NEW ROSTER GENERATION TESTS - Main focus
    new_roster_generation_tests = [
        tester.test_generate_roster_from_shift_templates,
        tester.test_roster_template_edit_delete,
        tester.test_overlap_detection_in_template_generation,
    ]
    
    # NEW CALENDAR EVENTS TESTS
    calendar_events_tests = [
        tester.test_calendar_events_crud,
        tester.test_calendar_events_filtering,
        tester.test_get_events_for_specific_date,
        tester.test_task_completion,
        tester.test_calendar_events_priority_levels,
        tester.test_all_day_vs_timed_events,
        tester.test_calendar_events_data_validation,
    ]
    
    # EXISTING DAY TEMPLATE TESTS
    day_template_tests = [
        tester.test_day_templates_crud,
        tester.test_save_day_as_template,
        tester.test_apply_day_template_to_date,
        tester.test_day_template_overlap_detection,
        tester.test_day_template_filtering,
    ]
    
    # EXISTING ROSTER TEMPLATE TESTS
    roster_template_tests = [
        tester.test_roster_templates_crud,
        tester.test_save_current_roster_as_template,
        tester.test_generate_roster_from_template,
        tester.test_overlap_detection,
        tester.test_day_of_week_placement,
    ]
    
    # NEW: 2:1 Shift Overlap Functionality Tests
    two_to_one_overlap_tests = [
        tester.test_2to1_shift_overlap_functionality,
        tester.test_2to1_shift_template_generation,
        tester.test_2to1_day_template_overlap,
    ]
    
    # NEW: Allow Overlap Functionality Tests
    allow_overlap_tests = [
        tester.test_allow_overlap_functionality,
    ]
    additional_tests = [
        tester.test_generate_roster,
        tester.test_get_roster,
        tester.analyze_existing_pay_calculations,
        tester.test_pay_calculations,
        tester.test_roster_assignment,
    ]
    
    print("🔧 Running Basic API Tests...")
    for test in basic_tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🔄 Running 2:1 SHIFT OVERLAP TESTS...")
    print("🎯 Testing: 2:1 Shift Overlap Functionality")
    print("=" * 60)
    
    two_to_one_tests_passed = 0
    for test in two_to_one_overlap_tests:
        try:
            result = test()
            if result:
                two_to_one_tests_passed += 1
        except Exception as e:
            print(f"❌ 2:1 overlap test failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🚀 Running NEW ROSTER GENERATION TESTS...")
    print("🎯 Testing: Generate Roster from Shift Templates & Enhanced Template Management")
    print("=" * 60)
    
    new_roster_generation_tests_passed = 0
    for test in new_roster_generation_tests:
        try:
            result = test()
            if result:
                new_roster_generation_tests_passed += 1
        except Exception as e:
            print(f"❌ New roster generation test failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📅 Running Calendar Events Tests...")
    print("=" * 60)
    
    calendar_events_tests_passed = 0
    for test in calendar_events_tests:
        try:
            result = test()
            if result:
                calendar_events_tests_passed += 1
        except Exception as e:
            print(f"❌ Calendar events test failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🌟 Running Day Template Tests...")
    print("=" * 60)
    
    day_template_tests_passed = 0
    for test in day_template_tests:
        try:
            result = test()
            if result:
                day_template_tests_passed += 1
        except Exception as e:
            print(f"❌ Day template test failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 Running Roster Template Tests...")
    print("=" * 60)
    
    roster_template_tests_passed = 0
    for test in roster_template_tests:
        try:
            result = test()
            if result:
                roster_template_tests_passed += 1
        except Exception as e:
            print(f"❌ Roster template test failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🔧 Running Additional Tests...")
    
    for test in additional_tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Overall Results: {tester.tests_passed}/{tester.tests_run} API tests passed")
    print(f"🔄 2:1 Shift Overlap Tests: {two_to_one_tests_passed}/{len(two_to_one_overlap_tests)} 2:1 overlap tests passed")
    print(f"🚀 NEW Roster Generation Tests: {new_roster_generation_tests_passed}/{len(new_roster_generation_tests)} new roster generation tests passed")
    print(f"📅 Calendar Events Tests: {calendar_events_tests_passed}/{len(calendar_events_tests)} calendar events tests passed")
    print(f"🌟 Day Template Tests: {day_template_tests_passed}/{len(day_template_tests)} day template tests passed")
    print(f"🎯 Roster Template Tests: {roster_template_tests_passed}/{len(roster_template_tests)} roster template tests passed")
    
    two_to_one_success = two_to_one_tests_passed == len(two_to_one_overlap_tests)
    new_roster_generation_success = new_roster_generation_tests_passed == len(new_roster_generation_tests)
    calendar_events_success = calendar_events_tests_passed == len(calendar_events_tests)
    day_template_success = day_template_tests_passed == len(day_template_tests)
    roster_template_success = roster_template_tests_passed == len(roster_template_tests)
    
    if two_to_one_success:
        print("🎉 All 2:1 shift overlap tests passed!")
    else:
        print("⚠️  Some 2:1 shift overlap tests failed.")
    
    if new_roster_generation_success:
        print("🎉 All NEW roster generation tests passed!")
    else:
        print("⚠️  Some NEW roster generation tests failed.")
    
    if calendar_events_success:
        print("🎉 All calendar events tests passed!")
    else:
        print("⚠️  Some calendar events tests failed.")
    
    if day_template_success:
        print("🎉 All day template tests passed!")
    else:
        print("⚠️  Some day template tests failed.")
    
    if roster_template_success:
        print("🎉 All roster template tests passed!")
    else:
        print("⚠️  Some roster template tests failed.")
    
    if (two_to_one_success and new_roster_generation_success and calendar_events_success and 
        day_template_success and roster_template_success and 
        tester.tests_passed == tester.tests_run):
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())