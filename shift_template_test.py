import requests
import sys
import json
from datetime import datetime

class ShiftTemplateEditTester:
    def __init__(self, base_url="https://workforce-wizard.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.shift_templates = []
        self.created_template_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

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

    def test_get_shift_templates(self):
        """Get all shift templates for editing tests"""
        success, response = self.run_test(
            "Get Shift Templates for Editing",
            "GET",
            "api/shift-templates",
            200
        )
        if success:
            self.shift_templates = response
            print(f"   Found {len(response)} shift templates")
            
            # Find Monday Shift 1 for testing
            monday_shift_1 = next((t for t in response if t['name'] == 'Monday Shift 1'), None)
            if monday_shift_1:
                print(f"   Monday Shift 1 current time: {monday_shift_1['start_time']}-{monday_shift_1['end_time']}")
                print(f"   Sleepover: {monday_shift_1['is_sleepover']}")
            else:
                print("   ⚠️  Monday Shift 1 not found")
        return success

    def test_update_shift_template(self):
        """Test updating a shift template (Monday Shift 1 from 07:30-15:30 to 08:00-16:00)"""
        monday_shift_1 = next((t for t in self.shift_templates if t['name'] == 'Monday Shift 1'), None)
        if not monday_shift_1:
            print("❌ Cannot test template update - Monday Shift 1 not found")
            return False

        # Store original times for restoration
        original_start = monday_shift_1['start_time']
        original_end = monday_shift_1['end_time']
        
        print(f"   Original times: {original_start}-{original_end}")
        print(f"   Updating to: 08:00-16:00")

        # Update the template
        updated_template = {
            **monday_shift_1,
            "start_time": "08:00",
            "end_time": "16:00"
        }

        success, response = self.run_test(
            "Update Monday Shift 1 Template (08:00-16:00)",
            "PUT",
            f"api/shift-templates/{monday_shift_1['id']}",
            200,
            data=updated_template
        )

        if success:
            print(f"   Updated template: {response['start_time']}-{response['end_time']}")
            
            # Verify the change persisted
            verify_success, verify_response = self.run_test(
                "Verify Template Update Persisted",
                "GET",
                "api/shift-templates",
                200
            )
            
            if verify_success:
                updated_monday_shift = next((t for t in verify_response if t['name'] == 'Monday Shift 1'), None)
                if updated_monday_shift:
                    if updated_monday_shift['start_time'] == "08:00" and updated_monday_shift['end_time'] == "16:00":
                        print(f"   ✅ Template update verified: {updated_monday_shift['start_time']}-{updated_monday_shift['end_time']}")
                    else:
                        print(f"   ❌ Template update not persisted correctly")
                        success = False

            # Restore original times
            restore_template = {
                **monday_shift_1,
                "start_time": original_start,
                "end_time": original_end
            }
            
            restore_success, _ = self.run_test(
                "Restore Original Template Times",
                "PUT",
                f"api/shift-templates/{monday_shift_1['id']}",
                200,
                data=restore_template
            )
            
            if restore_success:
                print(f"   ✅ Original times restored: {original_start}-{original_end}")

        return success

    def test_sleepover_toggle(self):
        """Test toggling sleepover status on a template"""
        # Find a non-sleepover shift to test with
        test_shift = next((t for t in self.shift_templates 
                          if not t['is_sleepover'] and 'Shift 2' in t['name']), None)
        
        if not test_shift:
            print("❌ Cannot test sleepover toggle - suitable shift not found")
            return False

        original_sleepover = test_shift['is_sleepover']
        print(f"   Testing with {test_shift['name']}")
        print(f"   Original sleepover status: {original_sleepover}")

        # Toggle sleepover status
        updated_template = {
            **test_shift,
            "is_sleepover": not original_sleepover
        }

        success, response = self.run_test(
            f"Toggle Sleepover Status for {test_shift['name']}",
            "PUT",
            f"api/shift-templates/{test_shift['id']}",
            200,
            data=updated_template
        )

        if success:
            print(f"   Updated sleepover status: {response['is_sleepover']}")
            
            # Restore original status
            restore_template = {
                **test_shift,
                "is_sleepover": original_sleepover
            }
            
            restore_success, _ = self.run_test(
                "Restore Original Sleepover Status",
                "PUT",
                f"api/shift-templates/{test_shift['id']}",
                200,
                data=restore_template
            )
            
            if restore_success:
                print(f"   ✅ Original sleepover status restored: {original_sleepover}")

        return success

    def test_individual_shift_time_editing(self):
        """Test editing individual shift times in roster entries"""
        # Get current month roster
        current_month = datetime.now().strftime("%Y-%m")
        success, roster_response = self.run_test(
            f"Get Roster for Individual Shift Editing",
            "GET",
            f"api/roster?month={current_month}",
            200
        )
        
        if not success or not roster_response:
            print("❌ Cannot test individual shift editing - no roster data")
            return False

        # Find a Friday shift to test (15:00-20:00 to 14:00-19:00)
        friday_shift = None
        for entry in roster_response:
            entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
            if (entry_date.weekday() == 4 and  # Friday
                entry['start_time'] == '15:00' and 
                entry['end_time'] == '20:00'):
                friday_shift = entry
                break

        if not friday_shift:
            print("❌ Cannot test individual shift editing - suitable Friday shift not found")
            return False

        print(f"   Testing with Friday shift: {friday_shift['date']} {friday_shift['start_time']}-{friday_shift['end_time']}")
        print(f"   Original pay: ${friday_shift['total_pay']}")

        # Update shift times (15:00-20:00 to 14:00-19:00)
        updated_shift = {
            **friday_shift,
            "start_time": "14:00",
            "end_time": "19:00"
        }

        success, response = self.run_test(
            "Update Individual Friday Shift Times (14:00-19:00)",
            "PUT",
            f"api/roster/{friday_shift['id']}",
            200,
            data=updated_shift
        )

        if success:
            print(f"   Updated shift times: {response['start_time']}-{response['end_time']}")
            print(f"   Updated hours: {response['hours_worked']}")
            print(f"   Updated pay: ${response['total_pay']}")
            
            # Verify evening rate applies (should be $44.50/hr for 5 hours = $222.50)
            expected_pay = 5.0 * 44.50  # 5 hours at evening rate
            actual_pay = response['total_pay']
            
            if abs(actual_pay - expected_pay) < 0.01:
                print(f"   ✅ Evening rate applied correctly: ${actual_pay}")
            else:
                print(f"   ❌ Evening rate not applied correctly: got ${actual_pay}, expected ${expected_pay}")

            # Restore original times
            restore_shift = {
                **friday_shift,
                "start_time": "15:00",
                "end_time": "20:00"
            }
            
            restore_success, _ = self.run_test(
                "Restore Original Friday Shift Times",
                "PUT",
                f"api/roster/{friday_shift['id']}",
                200,
                data=restore_shift
            )
            
            if restore_success:
                print(f"   ✅ Original shift times restored")

        return success

    def test_get_shift_templates_with_enhanced_fields(self):
        """Test GET /api/shift-templates - Verify templates include new fields"""
        print(f"\n📋 Testing GET Shift Templates with Enhanced Fields...")
        
        success, templates = self.run_test(
            "Get All Shift Templates with Enhanced Fields",
            "GET",
            "api/shift-templates",
            200
        )
        
        if not success or not templates:
            print("   ❌ Failed to retrieve shift templates")
            return False
        
        print(f"   ✅ Retrieved {len(templates)} shift templates")
        
        # Check if templates include the new fields
        enhanced_fields_found = 0
        templates_with_manual_overrides = 0
        
        for i, template in enumerate(templates[:5]):  # Check first 5 templates
            template_name = template.get('name', f'Template {i+1}')
            print(f"\n   Analyzing template: {template_name}")
            
            # Check for new fields presence
            has_manual_shift_type = 'manual_shift_type' in template
            has_manual_hourly_rate = 'manual_hourly_rate' in template
            
            if has_manual_shift_type and has_manual_hourly_rate:
                enhanced_fields_found += 1
                print(f"      ✅ Has enhanced fields: manual_shift_type, manual_hourly_rate")
                
                # Check field values
                manual_shift_type = template.get('manual_shift_type')
                manual_hourly_rate = template.get('manual_hourly_rate')
                
                print(f"      manual_shift_type: {manual_shift_type}")
                print(f"      manual_hourly_rate: {manual_hourly_rate}")
                
                if manual_shift_type is not None or manual_hourly_rate is not None:
                    templates_with_manual_overrides += 1
                    print(f"      ✅ Template has manual overrides set")
            else:
                print(f"      ❌ Missing enhanced fields")
                if not has_manual_shift_type:
                    print(f"         Missing: manual_shift_type")
                if not has_manual_hourly_rate:
                    print(f"         Missing: manual_hourly_rate")
        
        print(f"\n   📊 Summary:")
        print(f"      Templates with enhanced fields: {enhanced_fields_found}/{min(5, len(templates))}")
        print(f"      Templates with manual overrides: {templates_with_manual_overrides}")
        
        return enhanced_fields_found > 0

    def test_update_template_name(self):
        """Test updating template name"""
        print(f"\n✏️ Testing Update Template Name...")
        
        if not self.shift_templates:
            print("   ❌ No templates available for name update test")
            return False
        
        template_to_update = self.shift_templates[0]
        template_id = template_to_update['id']
        original_name = template_to_update['name']
        
        # Update the template name
        updated_template = {
            **template_to_update,
            "name": f"Updated {original_name} - Enhanced Edition"
        }
        
        success, response = self.run_test(
            "Update Template Name",
            "PUT",
            f"api/shift-templates/{template_id}",
            200,
            data=updated_template
        )
        
        if success:
            new_name = response.get('name')
            expected_name = updated_template['name']
            
            if new_name == expected_name:
                print(f"   ✅ Template name updated successfully")
                print(f"   New name: {new_name}")
                
                # Restore original name
                restore_template = {
                    **template_to_update,
                    "name": original_name
                }
                
                restore_success, _ = self.run_test(
                    "Restore Original Template Name",
                    "PUT",
                    f"api/shift-templates/{template_id}",
                    200,
                    data=restore_template
                )
                
                if restore_success:
                    print(f"   ✅ Original name restored: {original_name}")
                
                return True
            else:
                print(f"   ❌ Name update failed - got '{new_name}', expected '{expected_name}'")
        
        return False

    def test_set_manual_shift_type_override(self):
        """Test setting manual shift type override"""
        print(f"\n🕐 Testing Manual Shift Type Override...")
        
        if not self.shift_templates:
            print("   ❌ No templates available for shift type override test")
            return False
        
        template_to_update = self.shift_templates[0]
        template_id = template_to_update['id']
        original_manual_shift_type = template_to_update.get('manual_shift_type')
        
        # Test different manual shift type overrides
        shift_type_tests = [
            "weekday_evening",
            "weekday_night", 
            "saturday",
            "sunday",
            "public_holiday"
        ]
        
        test_results = []
        
        for shift_type in shift_type_tests:
            print(f"\n   Testing manual shift type: {shift_type}")
            
            # Update with manual shift type
            updated_template = {
                **template_to_update,
                "manual_shift_type": shift_type
            }
            
            success, response = self.run_test(
                f"Set Manual Shift Type to {shift_type}",
                "PUT",
                f"api/shift-templates/{template_id}",
                200,
                data=updated_template
            )
            
            if success:
                returned_shift_type = response.get('manual_shift_type')
                if returned_shift_type == shift_type:
                    print(f"      ✅ Manual shift type set to: {returned_shift_type}")
                    test_results.append(True)
                else:
                    print(f"      ❌ Shift type mismatch - got '{returned_shift_type}', expected '{shift_type}'")
                    test_results.append(False)
            else:
                test_results.append(False)
        
        # Test setting to null/None to remove override
        print(f"\n   Testing removal of manual shift type override (set to null)")
        
        updated_template = {
            **template_to_update,
            "manual_shift_type": None
        }
        
        success, response = self.run_test(
            "Remove Manual Shift Type Override",
            "PUT",
            f"api/shift-templates/{template_id}",
            200,
            data=updated_template
        )
        
        if success:
            returned_shift_type = response.get('manual_shift_type')
            if returned_shift_type is None:
                print(f"      ✅ Manual shift type override removed (null)")
                test_results.append(True)
            else:
                print(f"      ❌ Failed to remove override - still has: {returned_shift_type}")
                test_results.append(False)
        
        # Restore original value
        restore_template = {
            **template_to_update,
            "manual_shift_type": original_manual_shift_type
        }
        
        restore_success, _ = self.run_test(
            "Restore Original Manual Shift Type",
            "PUT",
            f"api/shift-templates/{template_id}",
            200,
            data=restore_template
        )
        
        if restore_success:
            print(f"   ✅ Original manual shift type restored: {original_manual_shift_type}")
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        print(f"\n   📊 Manual shift type tests: {passed_tests}/{total_tests} passed")
        
        return passed_tests == total_tests

    def test_set_manual_hourly_rate_override(self):
        """Test setting manual hourly rate override"""
        print(f"\n💰 Testing Manual Hourly Rate Override...")
        
        if not self.shift_templates:
            print("   ❌ No templates available for hourly rate override test")
            return False
        
        template_to_update = self.shift_templates[0]
        template_id = template_to_update['id']
        original_manual_hourly_rate = template_to_update.get('manual_hourly_rate')
        
        # Test different manual hourly rate overrides
        hourly_rate_tests = [
            45.00,
            50.25,
            35.75,
            60.00,
            42.50
        ]
        
        test_results = []
        
        for hourly_rate in hourly_rate_tests:
            print(f"\n   Testing manual hourly rate: ${hourly_rate}")
            
            # Update with manual hourly rate
            updated_template = {
                **template_to_update,
                "manual_hourly_rate": hourly_rate
            }
            
            success, response = self.run_test(
                f"Set Manual Hourly Rate to ${hourly_rate}",
                "PUT",
                f"api/shift-templates/{template_id}",
                200,
                data=updated_template
            )
            
            if success:
                returned_rate = response.get('manual_hourly_rate')
                if returned_rate is not None and abs(returned_rate - hourly_rate) < 0.01:  # Allow for floating point precision
                    print(f"      ✅ Manual hourly rate set to: ${returned_rate}")
                    test_results.append(True)
                else:
                    print(f"      ❌ Rate mismatch - got ${returned_rate}, expected ${hourly_rate}")
                    test_results.append(False)
            else:
                test_results.append(False)
        
        # Test setting to null/None to remove override
        print(f"\n   Testing removal of manual hourly rate override (set to null)")
        
        updated_template = {
            **template_to_update,
            "manual_hourly_rate": None
        }
        
        success, response = self.run_test(
            "Remove Manual Hourly Rate Override",
            "PUT",
            f"api/shift-templates/{template_id}",
            200,
            data=updated_template
        )
        
        if success:
            returned_rate = response.get('manual_hourly_rate')
            if returned_rate is None:
                print(f"      ✅ Manual hourly rate override removed (null)")
                test_results.append(True)
            else:
                print(f"      ❌ Failed to remove override - still has: ${returned_rate}")
                test_results.append(False)
        
        # Restore original value
        restore_template = {
            **template_to_update,
            "manual_hourly_rate": original_manual_hourly_rate
        }
        
        restore_success, _ = self.run_test(
            "Restore Original Manual Hourly Rate",
            "PUT",
            f"api/shift-templates/{template_id}",
            200,
            data=restore_template
        )
        
        if restore_success:
            print(f"   ✅ Original manual hourly rate restored: {original_manual_hourly_rate}")
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        print(f"\n   📊 Manual hourly rate tests: {passed_tests}/{total_tests} passed")
        
        return passed_tests == total_tests

    def test_update_both_manual_fields_simultaneously(self):
        """Test updating both manual fields simultaneously"""
        print(f"\n🔄 Testing Simultaneous Update of Both Manual Fields...")
        
        if not self.shift_templates:
            print("   ❌ No templates available for simultaneous update test")
            return False
        
        template_to_update = self.shift_templates[0]
        template_id = template_to_update['id']
        original_manual_shift_type = template_to_update.get('manual_shift_type')
        original_manual_hourly_rate = template_to_update.get('manual_hourly_rate')
        
        # Update both fields simultaneously
        updated_template = {
            **template_to_update,
            "manual_shift_type": "saturday",
            "manual_hourly_rate": 55.75
        }
        
        success, response = self.run_test(
            "Update Both Manual Fields Simultaneously",
            "PUT",
            f"api/shift-templates/{template_id}",
            200,
            data=updated_template
        )
        
        if success:
            returned_shift_type = response.get('manual_shift_type')
            returned_rate = response.get('manual_hourly_rate')
            
            shift_type_correct = returned_shift_type == "saturday"
            rate_correct = returned_rate is not None and abs(returned_rate - 55.75) < 0.01
            
            if shift_type_correct and rate_correct:
                print(f"   ✅ Both fields updated successfully")
                print(f"      Manual shift type: {returned_shift_type}")
                print(f"      Manual hourly rate: ${returned_rate}")
                
                # Restore original values
                restore_template = {
                    **template_to_update,
                    "manual_shift_type": original_manual_shift_type,
                    "manual_hourly_rate": original_manual_hourly_rate
                }
                
                restore_success, _ = self.run_test(
                    "Restore Original Manual Fields",
                    "PUT",
                    f"api/shift-templates/{template_id}",
                    200,
                    data=restore_template
                )
                
                if restore_success:
                    print(f"   ✅ Original values restored")
                
                return True
            else:
                print(f"   ❌ Simultaneous update failed")
                if not shift_type_correct:
                    print(f"      Shift type mismatch: got '{returned_shift_type}', expected 'saturday'")
                if not rate_correct:
                    print(f"      Rate mismatch: got ${returned_rate}, expected $55.75")
        
        return False

    def test_backward_compatibility(self):
        """Test backward compatibility with existing templates"""
        print(f"\n🔄 Testing Backward Compatibility...")
        
        if not self.shift_templates:
            print("   ⚠️  No existing templates available for backward compatibility test")
            return True  # Not a failure, just no data to test
        
        # Test updating an existing template without the new fields
        existing_template = self.shift_templates[0]
        template_id = existing_template['id']
        original_name = existing_template.get('name')
        
        print(f"   Testing existing template: {original_name}")
        
        # Update only traditional fields
        updated_template = {
            **existing_template,
            "name": f"Compatibility Test - {original_name}"
        }
        
        success, response = self.run_test(
            "Update Existing Template (Backward Compatibility)",
            "PUT",
            f"api/shift-templates/{template_id}",
            200,
            data=updated_template
        )
        
        if success:
            # Verify the update worked and new fields are present (even if null)
            has_manual_shift_type = 'manual_shift_type' in response
            has_manual_hourly_rate = 'manual_hourly_rate' in response
            
            if has_manual_shift_type and has_manual_hourly_rate:
                print(f"   ✅ Backward compatibility maintained")
                print(f"      Template updated successfully")
                print(f"      Enhanced fields present: manual_shift_type={response.get('manual_shift_type')}, manual_hourly_rate={response.get('manual_hourly_rate')}")
                
                # Restore original name
                restore_template = {
                    **existing_template,
                    "name": original_name
                }
                
                restore_success, _ = self.run_test(
                    "Restore Original Template Name",
                    "PUT",
                    f"api/shift-templates/{template_id}",
                    200,
                    data=restore_template
                )
                
                if restore_success:
                    print(f"   ✅ Original name restored: {original_name}")
                
                return True
            else:
                print(f"   ❌ Enhanced fields missing from updated template")
                return False
        
        return False

def main():
    print("🚀 Starting Enhanced Shift Template Editing Tests")
    print("=" * 60)
    
    tester = ShiftTemplateEditTester()
    
    # Run enhanced template editing tests
    tests = [
        tester.test_get_shift_templates,
        tester.test_get_shift_templates_with_enhanced_fields,
        tester.test_update_template_name,
        tester.test_set_manual_shift_type_override,
        tester.test_set_manual_hourly_rate_override,
        tester.test_update_both_manual_fields_simultaneously,
        tester.test_backward_compatibility,
        tester.test_update_shift_template,
        tester.test_sleepover_toggle,
        tester.test_individual_shift_time_editing,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Enhanced Shift Template Tests: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All enhanced shift template tests passed!")
        return 0
    else:
        print("⚠️  Some enhanced shift template tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())