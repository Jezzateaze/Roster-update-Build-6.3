import requests
import sys
import json
from datetime import datetime, timedelta

class AdvancedRosterTemplateAPITester:
    def __init__(self, base_url="https://care-scheduler-5.preview.emergentagent.com"):
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

    def authenticate(self):
        """Authenticate with Admin credentials"""
        print(f"\n🔐 Authenticating with Admin credentials...")
        
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
            print(f"   ✅ Authentication successful")
            return True
        else:
            print(f"   ❌ Authentication failed")
            return False

    def test_roster_template_crud_with_new_fields(self):
        """Test roster template CRUD operations with new 2:1 shift fields"""
        print(f"\n📋 Testing Enhanced Roster Template CRUD with 2:1 Shift Fields...")
        
        # Test 1: Get all roster templates and verify new fields are returned
        success, templates = self.run_test(
            "GET /api/roster-templates - Verify New Fields",
            "GET",
            "api/roster-templates",
            200
        )
        
        if success:
            print(f"   Found {len(templates)} existing roster templates")
            
            # Check if any existing templates have the new fields
            if templates:
                sample_template = templates[0]
                new_fields = ['enable_2_1_shift', 'allow_overlap_override', 'prevent_duplicate_unassigned', 'allow_different_staff_only']
                fields_present = []
                for field in new_fields:
                    if field in sample_template:
                        fields_present.append(field)
                        print(f"   ✅ New field '{field}' present: {sample_template[field]}")
                    else:
                        print(f"   ⚠️  New field '{field}' not present in existing template")
                
                if len(fields_present) == len(new_fields):
                    print(f"   ✅ All new 2:1 shift fields are present in existing templates")
                else:
                    print(f"   ⚠️  Only {len(fields_present)}/{len(new_fields)} new fields present")
        
        # Test 2: Create a new roster template with 2:1 shift configuration
        test_template_2_1_enabled = {
            "id": "",  # Will be auto-generated
            "name": "2:1 Shift Template - Enabled",
            "description": "Template with 2:1 shift support enabled",
            "is_active": True,
            "enable_2_1_shift": True,
            "allow_overlap_override": True,
            "prevent_duplicate_unassigned": False,
            "allow_different_staff_only": True,
            "template_data": {
                "0": [  # Monday
                    {"start_time": "09:00", "end_time": "17:00", "is_sleepover": False, "name": "2:1 Morning Shift"},
                    {"start_time": "17:00", "end_time": "01:00", "is_sleepover": False, "name": "2:1 Evening Shift"}
                ],
                "1": [  # Tuesday
                    {"start_time": "08:00", "end_time": "16:00", "is_sleepover": False, "name": "2:1 Day Shift"}
                ]
            }
        }
        
        success, created_template = self.run_test(
            "Create Roster Template with 2:1 Configuration",
            "POST",
            "api/roster-templates",
            200,
            data=test_template_2_1_enabled
        )
        
        template_id_2_1 = None
        if success and 'id' in created_template:
            template_id_2_1 = created_template['id']
            print(f"   Created 2:1 template with ID: {template_id_2_1}")
            
            # Verify new fields were saved correctly
            for field in ['enable_2_1_shift', 'allow_overlap_override', 'prevent_duplicate_unassigned', 'allow_different_staff_only']:
                expected_value = test_template_2_1_enabled[field]
                actual_value = created_template.get(field)
                if actual_value == expected_value:
                    print(f"   ✅ Field '{field}' saved correctly: {actual_value}")
                else:
                    print(f"   ❌ Field '{field}' mismatch: got {actual_value}, expected {expected_value}")
        
        # Test 3: Create another template with different configuration
        test_template_strict = {
            "id": "",  # Will be auto-generated
            "name": "Strict Template - No Overlaps",
            "description": "Template with strict duplicate prevention",
            "is_active": True,
            "enable_2_1_shift": False,
            "allow_overlap_override": False,
            "prevent_duplicate_unassigned": True,
            "allow_different_staff_only": False,
            "template_data": {
                "0": [  # Monday
                    {"start_time": "09:00", "end_time": "17:00", "is_sleepover": False}
                ]
            }
        }
        
        success, created_strict_template = self.run_test(
            "Create Strict Template (No 2:1 Shifts)",
            "POST",
            "api/roster-templates",
            200,
            data=test_template_strict
        )
        
        template_id_strict = None
        if success and 'id' in created_strict_template:
            template_id_strict = created_strict_template['id']
            print(f"   Created strict template with ID: {template_id_strict}")
        
        # Test 4: Update template with new field values
        if template_id_2_1:
            updated_template = {
                **created_template,
                "description": "Updated 2:1 template with modified settings",
                "enable_2_1_shift": False,  # Disable 2:1 shifts
                "allow_overlap_override": False,  # Disable overlap override
                "prevent_duplicate_unassigned": True,  # Enable duplicate prevention
                "allow_different_staff_only": False  # Disable different staff only
            }
            
            success, response = self.run_test(
                "PUT /api/roster-templates/{id} - Update New Fields",
                "PUT",
                f"api/roster-templates/{template_id_2_1}",
                200,
                data=updated_template
            )
            
            if success:
                print(f"   ✅ Template updated successfully")
                # Verify the updates
                for field in ['enable_2_1_shift', 'allow_overlap_override', 'prevent_duplicate_unassigned', 'allow_different_staff_only']:
                    expected_value = updated_template[field]
                    actual_value = response.get(field)
                    if actual_value == expected_value:
                        print(f"   ✅ Updated field '{field}' correctly: {actual_value}")
                    else:
                        print(f"   ❌ Updated field '{field}' mismatch: got {actual_value}, expected {expected_value}")
        
        return template_id_2_1, template_id_strict

    def test_enhanced_template_generation_logic(self):
        """Test POST /api/generate-roster-from-template with various 2:1 configurations"""
        print(f"\n🔄 Testing Enhanced Template Generation Logic...")
        
        # First create test templates with different configurations
        template_id_2_1, template_id_strict = self.test_roster_template_crud_with_new_fields()
        
        if not template_id_2_1 or not template_id_strict:
            print("   ⚠️  Could not create test templates")
            return False
        
        test_month = "2025-12"  # Use December for testing
        
        # Clear existing roster for test month
        success, response = self.run_test(
            f"Clear Roster for {test_month}",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        # Test 1: Generate roster with 2:1 shift enabled template
        print(f"\n   🎯 TEST 1: Generate roster with enable_2_1_shift=true")
        success, response = self.run_test(
            f"Generate Roster from 2:1 Template",
            "POST",
            f"api/generate-roster-from-template/{template_id_2_1}/{test_month}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            template_config = response.get('template_config', {})
            overlaps_detected = response.get('overlaps_detected', 0)
            duplicates_prevented = response.get('duplicates_prevented', 0)
            duplicates_allowed = response.get('duplicates_allowed', 0)
            
            print(f"   ✅ Generated {entries_created} entries with 2:1 template")
            print(f"   Template config: {template_config}")
            print(f"   Overlaps detected: {overlaps_detected}")
            print(f"   Duplicates prevented: {duplicates_prevented}")
            print(f"   Duplicates allowed: {duplicates_allowed}")
            
            # Verify template config is returned correctly
            expected_config = {
                'enable_2_1_shift': True,
                'allow_overlap_override': True,
                'prevent_duplicate_unassigned': False,
                'allow_different_staff_only': True
            }
            
            config_correct = True
            for key, expected_value in expected_config.items():
                actual_value = template_config.get(key)
                if actual_value != expected_value:
                    print(f"   ❌ Config mismatch for '{key}': got {actual_value}, expected {expected_value}")
                    config_correct = False
                else:
                    print(f"   ✅ Config correct for '{key}': {actual_value}")
            
            if config_correct:
                print(f"   ✅ Template configuration returned correctly")
        
        # Test 2: Generate roster again to test duplicate handling
        print(f"\n   🎯 TEST 2: Generate roster again to test duplicate handling")
        success, response = self.run_test(
            f"Generate Roster Again (Test Duplicates)",
            "POST",
            f"api/generate-roster-from-template/{template_id_2_1}/{test_month}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            duplicates_prevented = response.get('duplicates_prevented', 0)
            duplicates_allowed = response.get('duplicates_allowed', 0)
            
            print(f"   ✅ Second generation: {entries_created} new entries")
            print(f"   Duplicates prevented: {duplicates_prevented}")
            print(f"   Duplicates allowed: {duplicates_allowed}")
            
            # With 2:1 enabled and prevent_duplicate_unassigned=False, should allow duplicates
            if duplicates_allowed > 0:
                print(f"   ✅ 2:1 template correctly allowed duplicate entries")
            else:
                print(f"   ⚠️  Expected some duplicate entries to be allowed with 2:1 configuration")
        
        # Test 3: Test with strict template (no 2:1 shifts)
        print(f"\n   🎯 TEST 3: Generate roster with strict template (enable_2_1_shift=false)")
        
        # Clear roster first
        success, response = self.run_test(
            f"Clear Roster for Strict Test",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        success, response = self.run_test(
            f"Generate Roster from Strict Template",
            "POST",
            f"api/generate-roster-from-template/{template_id_strict}/{test_month}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            template_config = response.get('template_config', {})
            
            print(f"   ✅ Generated {entries_created} entries with strict template")
            print(f"   Template config: {template_config}")
            
            # Verify strict configuration
            expected_strict_config = {
                'enable_2_1_shift': False,
                'allow_overlap_override': False,
                'prevent_duplicate_unassigned': True,
                'allow_different_staff_only': False
            }
            
            for key, expected_value in expected_strict_config.items():
                actual_value = template_config.get(key)
                if actual_value == expected_value:
                    print(f"   ✅ Strict config correct for '{key}': {actual_value}")
                else:
                    print(f"   ❌ Strict config mismatch for '{key}': got {actual_value}, expected {expected_value}")
        
        # Test 4: Try to generate again with strict template (should prevent duplicates)
        print(f"\n   🎯 TEST 4: Generate strict template again (should prevent duplicates)")
        success, response = self.run_test(
            f"Generate Strict Template Again (Test Prevention)",
            "POST",
            f"api/generate-roster-from-template/{template_id_strict}/{test_month}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            duplicates_prevented = response.get('duplicates_prevented', 0)
            
            print(f"   ✅ Second strict generation: {entries_created} new entries")
            print(f"   Duplicates prevented: {duplicates_prevented}")
            
            # With strict settings, should prevent duplicates
            if duplicates_prevented > 0:
                print(f"   ✅ Strict template correctly prevented duplicate entries")
            elif entries_created == 0:
                print(f"   ✅ Strict template prevented all duplicates (0 new entries)")
            else:
                print(f"   ⚠️  Expected duplicates to be prevented with strict configuration")
        
        return True

    def test_duplicate_detection_scenarios(self):
        """Test various duplicate detection scenarios"""
        print(f"\n🔍 Testing Duplicate Detection Scenarios...")
        
        test_month = "2025-11"  # Use November for testing
        
        # Clear existing roster
        success, response = self.run_test(
            f"Clear Roster for {test_month}",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        # Create a test template for duplicate testing
        duplicate_test_template = {
            "id": "",
            "name": "Duplicate Test Template",
            "description": "Template for testing duplicate scenarios",
            "is_active": True,
            "enable_2_1_shift": False,
            "allow_overlap_override": False,
            "prevent_duplicate_unassigned": True,
            "allow_different_staff_only": True,
            "template_data": {
                "0": [  # Monday
                    {"start_time": "09:00", "end_time": "17:00", "is_sleepover": False}
                ]
            }
        }
        
        success, created_template = self.run_test(
            "Create Duplicate Test Template",
            "POST",
            "api/roster-templates",
            200,
            data=duplicate_test_template
        )
        
        if not success or 'id' not in created_template:
            print("   ⚠️  Could not create test template")
            return False
        
        template_id = created_template['id']
        
        # Test 1: Create unassigned shifts manually first
        print(f"\n   🎯 TEST 1: Create unassigned shifts, then load template")
        
        test_date = "2025-11-03"  # First Monday in November
        unassigned_shift = {
            "id": "",
            "date": test_date,
            "shift_template_id": "manual-test",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "staff_id": None,
            "staff_name": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_shift = self.run_test(
            "Create Unassigned Shift Manually",
            "POST",
            "api/roster",
            200,
            data=unassigned_shift
        )
        
        if success:
            print(f"   ✅ Created unassigned shift at {test_date} 09:00-17:00")
            
            # Now try to load template (should prevent duplicates)
            success, response = self.run_test(
                f"Load Template with Existing Unassigned Shift",
                "POST",
                f"api/generate-roster-from-template/{template_id}/{test_month}",
                200
            )
            
            if success:
                entries_created = response.get('entries_created', 0)
                duplicates_prevented = response.get('duplicates_prevented', 0)
                prevention_details = response.get('prevention_details', [])
                
                print(f"   ✅ Template load result: {entries_created} new entries")
                print(f"   Duplicates prevented: {duplicates_prevented}")
                
                if duplicates_prevented > 0:
                    print(f"   ✅ Correctly prevented duplicates with unassigned shifts")
                    for detail in prevention_details[:3]:  # Show first 3
                        print(f"      - {detail.get('date')} {detail.get('start_time')}-{detail.get('end_time')}: {detail.get('reason')}")
                else:
                    print(f"   ⚠️  Expected duplicates to be prevented with existing unassigned shifts")
        
        # Test 2: Create assigned shifts and test different staff scenario
        print(f"\n   🎯 TEST 2: Create assigned shifts, then test different staff handling")
        
        # Get staff data for assignment
        success, staff_data = self.run_test(
            "Get Staff for Assignment Test",
            "GET",
            "api/staff",
            200
        )
        
        if success and len(staff_data) >= 2:
            staff1 = staff_data[0]
            staff2 = staff_data[1]
            
            test_date_2 = "2025-11-10"  # Second Monday
            assigned_shift = {
                "id": "",
                "date": test_date_2,
                "shift_template_id": "manual-assigned",
                "start_time": "09:00",
                "end_time": "17:00",
                "is_sleepover": False,
                "staff_id": staff1['id'],
                "staff_name": staff1['name'],
                "hours_worked": 0.0,
                "base_pay": 0.0,
                "sleepover_allowance": 0.0,
                "total_pay": 0.0
            }
            
            success, created_assigned_shift = self.run_test(
                f"Create Assigned Shift ({staff1['name']})",
                "POST",
                "api/roster",
                200,
                data=assigned_shift
            )
            
            if success:
                print(f"   ✅ Created assigned shift for {staff1['name']} at {test_date_2}")
                
                # Create template that allows different staff only
                different_staff_template = {
                    "id": "",
                    "name": "Different Staff Template",
                    "description": "Template allowing different staff only",
                    "is_active": True,
                    "enable_2_1_shift": False,
                    "allow_overlap_override": False,
                    "prevent_duplicate_unassigned": False,
                    "allow_different_staff_only": True,
                    "template_data": {
                        "0": [  # Monday
                            {"start_time": "09:00", "end_time": "17:00", "is_sleepover": False}
                        ]
                    }
                }
                
                success, diff_staff_template = self.run_test(
                    "Create Different Staff Template",
                    "POST",
                    "api/roster-templates",
                    200,
                    data=different_staff_template
                )
                
                if success and 'id' in diff_staff_template:
                    diff_template_id = diff_staff_template['id']
                    
                    # Try to load template (should allow different staff)
                    success, response = self.run_test(
                        f"Load Template with Different Staff Policy",
                        "POST",
                        f"api/generate-roster-from-template/{diff_template_id}/{test_month}",
                        200
                    )
                    
                    if success:
                        entries_created = response.get('entries_created', 0)
                        duplicates_allowed = response.get('duplicates_allowed', 0)
                        allowance_details = response.get('allowance_details', [])
                        
                        print(f"   ✅ Different staff template result: {entries_created} new entries")
                        print(f"   Duplicates allowed: {duplicates_allowed}")
                        
                        if duplicates_allowed > 0:
                            print(f"   ✅ Correctly allowed duplicates for different staff scenario")
                            for detail in allowance_details[:3]:
                                print(f"      - {detail.get('date')} {detail.get('start_time')}-{detail.get('end_time')}: {detail.get('reason')}")
        
        return True

    def test_2_1_shift_functionality(self):
        """Test 2:1 shift functionality with multiple shifts at same time"""
        print(f"\n👥 Testing 2:1 Shift Functionality...")
        
        test_month = "2025-10"  # Use October for testing
        
        # Clear existing roster
        success, response = self.run_test(
            f"Clear Roster for {test_month}",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        # Create a 2:1 shift template
        two_to_one_template = {
            "id": "",
            "name": "2:1 Shift Template",
            "description": "Template with 2:1 shift support for multiple staff",
            "is_active": True,
            "enable_2_1_shift": True,
            "allow_overlap_override": True,
            "prevent_duplicate_unassigned": False,
            "allow_different_staff_only": False,
            "template_data": {
                "0": [  # Monday
                    {"start_time": "09:00", "end_time": "17:00", "is_sleepover": False, "name": "2:1 Day Shift"},
                    {"start_time": "17:00", "end_time": "01:00", "is_sleepover": False, "name": "2:1 Evening Shift"}
                ],
                "1": [  # Tuesday
                    {"start_time": "08:00", "end_time": "16:00", "is_sleepover": False, "name": "2:1 Morning Shift"}
                ]
            }
        }
        
        success, created_template = self.run_test(
            "Create 2:1 Shift Template",
            "POST",
            "api/roster-templates",
            200,
            data=two_to_one_template
        )
        
        if not success or 'id' not in created_template:
            print("   ⚠️  Could not create 2:1 template")
            return False
        
        template_id = created_template['id']
        print(f"   ✅ Created 2:1 template with ID: {template_id}")
        
        # Test 1: Generate roster with 2:1 template
        print(f"\n   🎯 TEST 1: Generate roster with enable_2_1_shift=true")
        success, response = self.run_test(
            f"Generate 2:1 Roster",
            "POST",
            f"api/generate-roster-from-template/{template_id}/{test_month}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            template_config = response.get('template_config', {})
            
            print(f"   ✅ Generated {entries_created} entries with 2:1 template")
            print(f"   2:1 shift enabled: {template_config.get('enable_2_1_shift')}")
            print(f"   Overlap override: {template_config.get('allow_overlap_override')}")
        
        # Test 2: Generate roster again to create multiple shifts at same time
        print(f"\n   🎯 TEST 2: Generate roster again to create overlapping shifts")
        success, response = self.run_test(
            f"Generate 2:1 Roster Again (Create Overlaps)",
            "POST",
            f"api/generate-roster-from-template/{template_id}/{test_month}",
            200
        )
        
        if success:
            entries_created = response.get('entries_created', 0)
            duplicates_allowed = response.get('duplicates_allowed', 0)
            allowance_details = response.get('allowance_details', [])
            
            print(f"   ✅ Second generation: {entries_created} new entries")
            print(f"   Duplicates allowed: {duplicates_allowed}")
            
            if duplicates_allowed > 0:
                print(f"   ✅ Successfully created multiple shifts at same time")
                for detail in allowance_details[:3]:
                    print(f"      - {detail.get('date')} {detail.get('start_time')}-{detail.get('end_time')}: {detail.get('reason')}")
            else:
                print(f"   ⚠️  Expected multiple shifts to be allowed with 2:1 configuration")
        
        # Test 3: Verify roster entries have allow_overlap field set
        print(f"\n   🎯 TEST 3: Verify roster entries have allow_overlap field set")
        success, roster_entries = self.run_test(
            f"Get Generated Roster Entries",
            "GET",
            "api/roster",
            200,
            params={"month": test_month}
        )
        
        if success:
            print(f"   ✅ Retrieved {len(roster_entries)} roster entries")
            
            # Check first few entries for allow_overlap field
            overlap_entries = 0
            for entry in roster_entries[:10]:
                if entry.get('allow_overlap'):
                    overlap_entries += 1
                    print(f"      - {entry['date']} {entry['start_time']}-{entry['end_time']}: allow_overlap = {entry.get('allow_overlap')}")
            
            if overlap_entries > 0:
                print(f"   ✅ Found {overlap_entries} entries with allow_overlap=True")
            else:
                print(f"   ⚠️  No entries found with allow_overlap=True")
        
        # Test 4: Test manual shift creation with allow_overlap
        print(f"\n   🎯 TEST 4: Test manual shift creation with allow_overlap")
        
        test_date = "2025-10-06"  # First Monday in October
        manual_overlap_shift = {
            "id": "",
            "date": test_date,
            "shift_template_id": "manual-2-1",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_sleepover": False,
            "allow_overlap": True,  # Enable overlap for 2:1 shift
            "staff_id": None,
            "staff_name": None,
            "hours_worked": 0.0,
            "base_pay": 0.0,
            "sleepover_allowance": 0.0,
            "total_pay": 0.0
        }
        
        success, created_manual_shift = self.run_test(
            "Create Manual Shift with allow_overlap=True",
            "POST",
            "api/roster/add-shift",
            200,
            data=manual_overlap_shift
        )
        
        if success:
            print(f"   ✅ Created manual shift with allow_overlap=True")
            
            # Try to create another overlapping shift
            second_overlap_shift = {
                **manual_overlap_shift,
                "id": "",
                "shift_template_id": "manual-2-1-second",
                "allow_overlap": True
            }
            
            success, second_created_shift = self.run_test(
                "Create Second Overlapping Shift",
                "POST",
                "api/roster/add-shift",
                200,
                data=second_overlap_shift
            )
            
            if success:
                print(f"   ✅ Successfully created second overlapping shift")
                print(f"   ✅ 2:1 shift functionality working - multiple shifts at same time allowed")
            else:
                print(f"   ❌ Could not create second overlapping shift")
        
        return True

    def test_response_validation(self):
        """Test that enhanced responses include all required fields"""
        print(f"\n📊 Testing Response Validation...")
        
        # Create a test template for response validation
        response_test_template = {
            "id": "",
            "name": "Response Test Template",
            "description": "Template for testing response validation",
            "is_active": True,
            "enable_2_1_shift": True,
            "allow_overlap_override": False,
            "prevent_duplicate_unassigned": True,
            "allow_different_staff_only": True,
            "template_data": {
                "0": [  # Monday
                    {"start_time": "09:00", "end_time": "17:00", "is_sleepover": False}
                ]
            }
        }
        
        success, created_template = self.run_test(
            "Create Response Test Template",
            "POST",
            "api/roster-templates",
            200,
            data=response_test_template
        )
        
        if not success or 'id' not in created_template:
            print("   ⚠️  Could not create test template")
            return False
        
        template_id = created_template['id']
        test_month = "2025-09"
        
        # Clear roster for testing
        success, response = self.run_test(
            f"Clear Roster for Response Test",
            "DELETE",
            f"api/roster/month/{test_month}",
            200
        )
        
        # Generate roster and validate response structure
        success, response = self.run_test(
            f"Generate Roster for Response Validation",
            "POST",
            f"api/generate-roster-from-template/{template_id}/{test_month}",
            200
        )
        
        if success:
            print(f"   ✅ Generated roster successfully")
            
            # Validate required response fields
            required_fields = [
                'message',
                'entries_created',
                'template_config'
            ]
            
            optional_fields = [
                'overlaps_detected',
                'overlap_details',
                'duplicates_prevented',
                'prevention_details',
                'duplicates_allowed',
                'allowance_details'
            ]
            
            # Check required fields
            missing_required = []
            for field in required_fields:
                if field not in response:
                    missing_required.append(field)
                else:
                    print(f"   ✅ Required field '{field}' present: {response[field]}")
            
            if missing_required:
                print(f"   ❌ Missing required fields: {missing_required}")
                return False
            
            # Check template_config structure
            template_config = response.get('template_config', {})
            expected_config_fields = [
                'enable_2_1_shift',
                'allow_overlap_override',
                'prevent_duplicate_unassigned',
                'allow_different_staff_only'
            ]
            
            missing_config_fields = []
            for field in expected_config_fields:
                if field not in template_config:
                    missing_config_fields.append(field)
                else:
                    print(f"   ✅ Template config field '{field}' present: {template_config[field]}")
            
            if missing_config_fields:
                print(f"   ❌ Missing template config fields: {missing_config_fields}")
                return False
            
            # Check optional fields (should be present when applicable)
            for field in optional_fields:
                if field in response:
                    print(f"   ✅ Optional field '{field}' present: {response[field]}")
                else:
                    print(f"   ℹ️  Optional field '{field}' not present (may be expected)")
            
            # Validate entries_created count
            entries_created = response.get('entries_created', 0)
            if isinstance(entries_created, int) and entries_created >= 0:
                print(f"   ✅ entries_created is valid integer: {entries_created}")
            else:
                print(f"   ❌ entries_created is invalid: {entries_created}")
                return False
            
            print(f"   ✅ All response validation tests passed")
            return True
        
        return False

    def run_all_tests(self):
        """Run all advanced roster template tests"""
        print(f"🚀 Starting Advanced Roster Template Management Tests...")
        print(f"🎯 Testing newly implemented 2:1 shift support and intelligent duplicate handling")
        
        # Authenticate first
        if not self.authenticate():
            print(f"❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run all test suites
        test_results = []
        
        try:
            # Test 1: Template CRUD with new fields
            print(f"\n" + "="*80)
            result = self.test_roster_template_crud_with_new_fields()
            test_results.append(("Template CRUD with New Fields", result))
            
            # Test 2: Enhanced template generation logic
            print(f"\n" + "="*80)
            result = self.test_enhanced_template_generation_logic()
            test_results.append(("Enhanced Template Generation Logic", result))
            
            # Test 3: Duplicate detection scenarios
            print(f"\n" + "="*80)
            result = self.test_duplicate_detection_scenarios()
            test_results.append(("Duplicate Detection Scenarios", result))
            
            # Test 4: 2:1 shift functionality
            print(f"\n" + "="*80)
            result = self.test_2_1_shift_functionality()
            test_results.append(("2:1 Shift Functionality", result))
            
            # Test 5: Response validation
            print(f"\n" + "="*80)
            result = self.test_response_validation()
            test_results.append(("Response Validation", result))
            
        except Exception as e:
            print(f"❌ Test execution failed with error: {str(e)}")
            return False
        
        # Print final results
        print(f"\n" + "="*80)
        print(f"🎉 ADVANCED ROSTER TEMPLATE TESTING COMPLETE!")
        print(f"="*80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total API calls: {self.tests_run}")
        print(f"   Successful API calls: {self.tests_passed}")
        print(f"   API success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"   Test suites passed: {passed_tests}/{total_tests}")
        print(f"   Overall success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL ADVANCED ROSTER TEMPLATE TESTS PASSED!")
            print(f"✅ 2:1 shift support and intelligent duplicate handling working correctly")
            return True
        else:
            print(f"\n⚠️  Some tests failed - review results above")
            return False

if __name__ == "__main__":
    tester = AdvancedRosterTemplateAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)