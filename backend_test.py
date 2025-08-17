import requests
import sys
import json
from datetime import datetime, timedelta

class ShiftRosterAPITester:
    def __init__(self, base_url="https://rostersync.preview.emergentagent.com"):
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
            "created_at": None,  # Will be set by backend
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
        
        # Test date for overlap testing
        test_date = "2025-08-15"
        
        # First, add a shift
        shift1 = {
            "date": test_date,
            "shift_template_id": "test-overlap-1",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "is_public_holiday": False
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
            "date": test_date,
            "shift_template_id": "test-overlap-2",
            "start_time": "15:00",  # Overlaps with first shift
            "end_time": "20:00",
            "is_sleepover": False,
            "is_public_holiday": False
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
            "date": test_date,
            "shift_template_id": "test-overlap-3",
            "start_time": "18:00",  # After first shift ends
            "end_time": "22:00",
            "is_sleepover": False,
            "is_public_holiday": False
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

def main():
    print("🚀 Starting Shift Roster & Pay Calculator API Tests")
    print("🎯 FOCUS: Testing NEW Roster Template Functionality")
    print("=" * 60)
    
    tester = ShiftRosterAPITester()
    
    # Run basic tests first
    basic_tests = [
        tester.test_health_check,
        tester.test_get_staff,
        tester.test_get_shift_templates,
        tester.test_get_settings,
    ]
    
    # NEW ROSTER TEMPLATE TESTS - Main focus
    template_tests = [
        tester.test_roster_templates_crud,
        tester.test_save_current_roster_as_template,
        tester.test_generate_roster_from_template,
        tester.test_overlap_detection,
        tester.test_day_of_week_placement,
    ]
    
    # Additional tests
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
    print("🎯 Running NEW ROSTER TEMPLATE TESTS...")
    print("=" * 60)
    
    template_tests_passed = 0
    for test in template_tests:
        try:
            result = test()
            if result:
                template_tests_passed += 1
        except Exception as e:
            print(f"❌ Template test failed with exception: {str(e)}")
    
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
    print(f"🎯 Template Tests: {template_tests_passed}/{len(template_tests)} template tests passed")
    
    if template_tests_passed == len(template_tests):
        print("🎉 All NEW roster template tests passed!")
        template_success = True
    else:
        print("⚠️  Some roster template tests failed.")
        template_success = False
    
    if tester.tests_passed == tester.tests_run and template_success:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())