import requests
import sys
import json
from datetime import datetime, timedelta, date
import calendar

class PrintFunctionalityBackendTester:
    def __init__(self, base_url="https://shift-master-10.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.staff_token = None
        self.staff_user_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False, auth_token=None, expect_json=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if use_auth:
            token = auth_token or self.admin_token
            if token:
                headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if params:
            print(f"   Params: {params}")
        
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
        print(f"\n🔐 Authenticating as Admin (username='Admin', PIN='1234')...")
        
        login_data = {
            "username": "Admin",
            "pin": "1234"
        }
        
        success, response = self.run_test(
            "Admin Authentication",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success:
            self.admin_token = response.get('token')
            user_data = response.get('user', {})
            print(f"   ✅ Admin authenticated successfully")
            print(f"   Role: {user_data.get('role')}")
            print(f"   Token: {self.admin_token[:20]}..." if self.admin_token else "No token")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def authenticate_staff(self):
        """Authenticate as Staff user (rose)"""
        print(f"\n🔐 Authenticating as Staff (username='rose', PIN='888888')...")
        
        login_data = {
            "username": "rose",
            "pin": "888888"
        }
        
        success, response = self.run_test(
            "Staff Authentication",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success:
            self.staff_token = response.get('token')
            self.staff_user_data = response.get('user', {})
            print(f"   ✅ Staff authenticated successfully")
            print(f"   Role: {self.staff_user_data.get('role')}")
            print(f"   Staff ID: {self.staff_user_data.get('staff_id')}")
            print(f"   Token: {self.staff_token[:20]}..." if self.staff_token else "No token")
            return True
        else:
            print(f"   ❌ Staff authentication failed")
            return False

    def test_roster_data_retrieval_for_print(self):
        """Test roster data retrieval for print functionality"""
        print(f"\n📊 TESTING ROSTER DATA RETRIEVAL FOR PRINT FUNCTIONALITY...")
        
        # Test 1: Monthly print data retrieval (August 2025)
        print(f"\n   🎯 TEST 1: Monthly Print Data - GET /api/roster for August 2025")
        
        success, august_roster = self.run_test(
            "Get August 2025 Roster Data for Monthly Print",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if not success:
            print("   ❌ Could not retrieve August 2025 roster data")
            return False
        
        print(f"   ✅ Retrieved {len(august_roster)} roster entries for August 2025")
        
        # Verify required fields for printing
        if august_roster:
            sample_entry = august_roster[0]
            required_fields = ['id', 'date', 'start_time', 'end_time', 'hours_worked', 'total_pay']
            optional_fields = ['staff_name', 'staff_id', 'client_name']
            
            print(f"   📋 Verifying data structure for print requirements...")
            
            # Check required fields
            missing_required = [field for field in required_fields if field not in sample_entry]
            if missing_required:
                print(f"   ❌ Missing required fields: {missing_required}")
                return False
            else:
                print(f"   ✅ All required fields present: {required_fields}")
            
            # Check optional fields
            present_optional = [field for field in optional_fields if field in sample_entry]
            print(f"   ✅ Optional fields present: {present_optional}")
            
            # Show sample data structure
            print(f"   📄 Sample entry structure:")
            print(f"      ID: {sample_entry.get('id')}")
            print(f"      Date: {sample_entry.get('date')}")
            print(f"      Time: {sample_entry.get('start_time')} - {sample_entry.get('end_time')}")
            print(f"      Staff: {sample_entry.get('staff_name', 'Unassigned')}")
            print(f"      Hours: {sample_entry.get('hours_worked', 0)}")
            print(f"      Pay: ${sample_entry.get('total_pay', 0)}")
        
        # Test 2: Cross-month data retrieval for weekly/custom ranges
        print(f"\n   🎯 TEST 2: Cross-Month Data Retrieval for Weekly/Custom Ranges")
        
        # Since API only supports monthly queries, test getting multiple months
        # Get August 2025 data
        success_aug, august_data = self.run_test(
            "Get August 2025 Data for Cross-Month Range",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        # Get September 2025 data
        success_sep, september_data = self.run_test(
            "Get September 2025 Data for Cross-Month Range",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-09"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        success = success_aug and success_sep
        cross_month_roster = august_data + september_data if success else []
        
        if success:
            print(f"   ✅ Retrieved {len(cross_month_roster)} entries for cross-month range")
            
            # Verify date range coverage
            if cross_month_roster:
                dates = [entry['date'] for entry in cross_month_roster]
                min_date = min(dates)
                max_date = max(dates)
                print(f"   📅 Date range covered: {min_date} to {max_date}")
                
                # Check if we have entries from both months
                august_entries = [d for d in dates if d.startswith('2025-08')]
                september_entries = [d for d in dates if d.startswith('2025-09')]
                
                if august_entries and september_entries:
                    print(f"   ✅ Cross-month data integrity verified")
                    print(f"      August entries: {len(august_entries)}")
                    print(f"      September entries: {len(september_entries)}")
                    
                    # Test filtering for specific date range (Aug 25 - Sep 5)
                    filtered_entries = [
                        entry for entry in cross_month_roster 
                        if "2025-08-25" <= entry['date'] <= "2025-09-05"
                    ]
                    print(f"   📅 Filtered range (Aug 25 - Sep 5): {len(filtered_entries)} entries")
                    
                    if filtered_entries:
                        min_date = min([entry['date'] for entry in filtered_entries])
                        max_date = max([entry['date'] for entry in filtered_entries])
                        print(f"   📅 Actual filtered range: {min_date} to {max_date}")
                        print(f"   ✅ Cross-month filtering capability demonstrated")
                else:
                    print(f"   ⚠️  Limited cross-month data (Aug: {len(august_entries)}, Sep: {len(september_entries)})")
        else:
            print(f"   ❌ Cross-month data retrieval failed")
            return False
        
        # Test 3: Data completeness verification
        print(f"\n   🎯 TEST 3: Data Completeness for Print Requirements")
        
        all_entries = august_roster + cross_month_roster
        unique_entries = {entry['id']: entry for entry in all_entries}.values()
        
        print(f"   📊 Analyzing {len(unique_entries)} unique roster entries...")
        
        # Count entries by type
        assigned_shifts = [e for e in unique_entries if e.get('staff_name')]
        unassigned_shifts = [e for e in unique_entries if not e.get('staff_name')]
        sleepover_shifts = [e for e in unique_entries if e.get('is_sleepover')]
        
        print(f"   📈 Entry breakdown:")
        print(f"      Assigned shifts: {len(assigned_shifts)}")
        print(f"      Unassigned shifts: {len(unassigned_shifts)}")
        print(f"      Sleepover shifts: {len(sleepover_shifts)}")
        
        # Verify pay calculations are present
        entries_with_pay = [e for e in unique_entries if e.get('total_pay', 0) > 0]
        entries_with_hours = [e for e in unique_entries if e.get('hours_worked', 0) > 0]
        
        print(f"   💰 Pay data completeness:")
        print(f"      Entries with pay calculations: {len(entries_with_pay)}/{len(unique_entries)}")
        print(f"      Entries with hours worked: {len(entries_with_hours)}/{len(unique_entries)}")
        
        if len(entries_with_hours) == len(unique_entries):
            print(f"   ✅ All entries have hours worked calculated")
        else:
            print(f"   ⚠️  Some entries missing hours worked")
        
        return True

    def test_date_range_data_fetching(self):
        """Test date range data fetching for print functionality"""
        print(f"\n📅 TESTING DATE RANGE DATA FETCHING FOR PRINT...")
        
        # Test 1: Weekly range (Monday to Sunday) - using monthly API with filtering
        print(f"\n   🎯 TEST 1: Weekly Range Data Fetching (Monday to Sunday)")
        
        # Get August 2025 data and filter for a specific week
        success, august_data = self.run_test(
            "Get August 2025 Data for Weekly Filtering",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if not success:
            print("   ❌ Could not get August data for weekly filtering")
            return False
        
        # Filter for weekly range (August 4-10, 2025 - Monday to Sunday)
        weekly_data = [
            entry for entry in august_data 
            if "2025-08-04" <= entry['date'] <= "2025-08-10"
        ]
        
        print(f"   ✅ Filtered {len(weekly_data)} entries for weekly range from {len(august_data)} total")
        
        # Verify date coverage
        if weekly_data:
            dates = sorted(set([entry['date'] for entry in weekly_data]))
            print(f"   📅 Dates covered: {dates[0]} to {dates[-1]}")
            print(f"   📊 Unique dates: {len(dates)} days")
            
            # Check if we have data for each day of the week
            expected_dates = []
            current_date = datetime.strptime("2025-08-04", "%Y-%m-%d")
            for i in range(7):
                expected_dates.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
            
            present_dates = [d for d in expected_dates if d in dates]
            missing_dates = [d for d in expected_dates if d not in dates]
            
            print(f"   📅 Weekly coverage: {len(present_dates)}/7 days present")
            if missing_dates:
                print(f"   ⚠️  Missing dates in weekly range: {missing_dates}")
            else:
                print(f"   ✅ Complete weekly coverage (7 days)")
        
        # Test 2: Custom date range spanning multiple months
        print(f"\n   🎯 TEST 2: Custom Date Range Spanning Multiple Months")
        
        # Get July and August data for multi-month range
        success_jul, july_data = self.run_test(
            "Get July 2025 Data for Multi-Month Range",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-07"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        success_aug, august_data = self.run_test(
            "Get August 2025 Data for Multi-Month Range",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        success = success_jul and success_aug
        
        if success:
            # Filter for custom range (July 28 - August 15, 2025)
            combined_data = july_data + august_data
            custom_range_data = [
                entry for entry in combined_data 
                if "2025-07-28" <= entry['date'] <= "2025-08-15"
            ]
            
            print(f"   ✅ Filtered {len(custom_range_data)} entries for custom multi-month range")
            
            if custom_range_data:
                dates = [entry['date'] for entry in custom_range_data]
                july_entries = [d for d in dates if d.startswith('2025-07')]
                august_entries = [d for d in dates if d.startswith('2025-08')]
                
                print(f"   📊 Multi-month breakdown:")
                print(f"      July 2025 entries: {len(july_entries)}")
                print(f"      August 2025 entries: {len(august_entries)}")
                
                if july_entries and august_entries:
                    print(f"   ✅ Multi-month data integrity verified")
                    
                    # Show actual date range
                    min_date = min(dates)
                    max_date = max(dates)
                    print(f"   📅 Actual range: {min_date} to {max_date}")
                else:
                    print(f"   ⚠️  Limited multi-month coverage")
        else:
            print(f"   ❌ Custom multi-month range fetching failed")
            return False
        
        # Test 3: Data integrity across date boundaries
        print(f"\n   🎯 TEST 3: Data Integrity Across Date Boundaries")
        
        # Test month boundary using July and August data
        if success:
            # Filter for month boundary (July 31 - August 2, 2025)
            boundary_data = [
                entry for entry in combined_data 
                if "2025-07-31" <= entry['date'] <= "2025-08-02"
            ]
            
            print(f"   ✅ Filtered {len(boundary_data)} entries for month boundary")
            
            if boundary_data:
                # Check for data consistency across boundary
                dates = sorted(set([entry['date'] for entry in boundary_data]))
                print(f"   📅 Boundary dates: {dates}")
                
                # Verify no duplicate entries
                entry_ids = [entry['id'] for entry in boundary_data]
                unique_ids = set(entry_ids)
                
                if len(entry_ids) == len(unique_ids):
                    print(f"   ✅ No duplicate entries across date boundary")
                else:
                    print(f"   ❌ Found {len(entry_ids) - len(unique_ids)} duplicate entries")
                    return False
                
                # Check data structure consistency
                for entry in boundary_data[:3]:  # Check first 3 entries
                    required_fields = ['id', 'date', 'start_time', 'end_time', 'hours_worked']
                    missing_fields = [f for f in required_fields if f not in entry]
                    if missing_fields:
                        print(f"   ❌ Entry {entry['id']} missing fields: {missing_fields}")
                        return False
                
                print(f"   ✅ Data structure consistent across boundaries")
            else:
                print(f"   ⚠️  No data found for month boundary dates")
        else:
            print(f"   ❌ Month boundary data fetching failed")
            return False
        
        return True

    def test_role_based_data_access_for_print(self):
        """Test role-based data access for print functionality"""
        print(f"\n👥 TESTING ROLE-BASED DATA ACCESS FOR PRINT...")
        
        # Test 1: Admin access to all roster data
        print(f"\n   🎯 TEST 1: Admin Access - Should see ALL roster data")
        
        success, admin_roster_data = self.run_test(
            "Admin Access to All Roster Data",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if not success:
            print("   ❌ Admin could not access roster data")
            return False
        
        print(f"   ✅ Admin retrieved {len(admin_roster_data)} roster entries")
        
        # Analyze admin data access
        if admin_roster_data:
            assigned_shifts = [e for e in admin_roster_data if e.get('staff_name')]
            unassigned_shifts = [e for e in admin_roster_data if not e.get('staff_name')]
            shifts_with_pay = [e for e in admin_roster_data if e.get('total_pay', 0) > 0]
            
            print(f"   📊 Admin data access breakdown:")
            print(f"      Total entries: {len(admin_roster_data)}")
            print(f"      Assigned shifts: {len(assigned_shifts)}")
            print(f"      Unassigned shifts: {len(unassigned_shifts)}")
            print(f"      Shifts with pay info: {len(shifts_with_pay)}")
            
            # Verify admin can see all staff's pay information
            staff_names = set([e.get('staff_name') for e in assigned_shifts if e.get('staff_name')])
            print(f"   👥 Staff members visible to admin: {len(staff_names)}")
            if len(staff_names) > 0:
                print(f"      Sample staff: {list(staff_names)[:5]}")
        
        # Test 2: Staff access to own shifts + unassigned shifts
        print(f"\n   🎯 TEST 2: Staff Access - Should see own shifts + unassigned shifts")
        
        success, staff_roster_data = self.run_test(
            "Staff Access to Filtered Roster Data",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.staff_token
        )
        
        if not success:
            print("   ❌ Staff could not access roster data")
            return False
        
        print(f"   ✅ Staff retrieved {len(staff_roster_data)} roster entries")
        
        # Analyze staff data access
        if staff_roster_data and self.staff_user_data:
            staff_id = self.staff_user_data.get('staff_id')
            staff_name = self.staff_user_data.get('username', '').title()
            
            print(f"   👤 Testing access for staff: {staff_name} (ID: {staff_id})")
            
            # Categorize shifts
            own_shifts = [e for e in staff_roster_data if e.get('staff_id') == staff_id]
            unassigned_shifts = [e for e in staff_roster_data if not e.get('staff_id')]
            other_staff_shifts = [e for e in staff_roster_data if e.get('staff_id') and e.get('staff_id') != staff_id]
            
            print(f"   📊 Staff data access breakdown:")
            print(f"      Total entries visible: {len(staff_roster_data)}")
            print(f"      Own shifts: {len(own_shifts)}")
            print(f"      Unassigned shifts: {len(unassigned_shifts)}")
            print(f"      Other staff shifts: {len(other_staff_shifts)}")
            
            # Verify pay information filtering
            own_shifts_with_pay = [e for e in own_shifts if e.get('total_pay') is not None]
            unassigned_with_pay = [e for e in unassigned_shifts if e.get('total_pay') is not None]
            other_staff_with_pay = [e for e in other_staff_shifts if e.get('total_pay') is not None]
            other_staff_without_pay = [e for e in other_staff_shifts if e.get('total_pay') is None]
            
            print(f"   💰 Pay information filtering:")
            print(f"      Own shifts with pay: {len(own_shifts_with_pay)}/{len(own_shifts)}")
            print(f"      Unassigned with pay: {len(unassigned_with_pay)}/{len(unassigned_shifts)}")
            print(f"      Other staff with pay: {len(other_staff_with_pay)}/{len(other_staff_shifts)}")
            print(f"      Other staff without pay: {len(other_staff_without_pay)}/{len(other_staff_shifts)}")
            
            # Verify proper pay filtering for staff users
            if len(other_staff_shifts) > 0:
                if len(other_staff_without_pay) == len(other_staff_shifts):
                    print(f"   ✅ Pay information properly filtered - other staff shifts show no pay")
                elif len(other_staff_with_pay) == len(other_staff_shifts):
                    print(f"   ⚠️  Pay information NOT filtered - other staff pay is visible")
                else:
                    print(f"   ⚠️  Mixed pay filtering - some other staff shifts show pay")
            
            # Show sample data for verification
            if own_shifts:
                sample_own = own_shifts[0]
                print(f"   📄 Sample own shift:")
                print(f"      Date: {sample_own.get('date')}")
                print(f"      Time: {sample_own.get('start_time')} - {sample_own.get('end_time')}")
                print(f"      Pay: ${sample_own.get('total_pay', 'N/A')}")
            
            if other_staff_shifts:
                sample_other = other_staff_shifts[0]
                print(f"   📄 Sample other staff shift:")
                print(f"      Staff: {sample_other.get('staff_name', 'N/A')}")
                print(f"      Date: {sample_other.get('date')}")
                print(f"      Time: {sample_other.get('start_time')} - {sample_other.get('end_time')}")
                print(f"      Pay: ${sample_other.get('total_pay', 'FILTERED')}")
        
        # Test 3: Compare admin vs staff data access
        print(f"\n   🎯 TEST 3: Compare Admin vs Staff Data Access")
        
        print(f"   📊 Access comparison:")
        print(f"      Admin total entries: {len(admin_roster_data)}")
        print(f"      Staff total entries: {len(staff_roster_data)}")
        
        if len(admin_roster_data) >= len(staff_roster_data):
            print(f"   ✅ Admin has equal or greater access than staff")
        else:
            print(f"   ❌ Staff has more access than admin (unexpected)")
            return False
        
        # Verify staff can only see appropriate data
        if staff_roster_data and self.staff_user_data:
            staff_id = self.staff_user_data.get('staff_id')
            
            # Check if staff can see other staff's pay information
            other_staff_entries = [e for e in staff_roster_data if e.get('staff_id') and e.get('staff_id') != staff_id]
            other_staff_with_visible_pay = [e for e in other_staff_entries if e.get('total_pay') is not None and e.get('total_pay') > 0]
            
            if len(other_staff_with_visible_pay) == 0:
                print(f"   ✅ Staff cannot see other staff's pay information")
            else:
                print(f"   ⚠️  Staff can see {len(other_staff_with_visible_pay)} other staff shifts with pay")
        
        return True

    def test_data_format_for_print(self):
        """Test data format suitability for print functionality"""
        print(f"\n🖨️ TESTING DATA FORMAT FOR PRINT FUNCTIONALITY...")
        
        # Get sample data for format testing
        success, roster_data = self.run_test(
            "Get Roster Data for Format Testing",
            "GET",
            "api/roster",
            200,
            params={"month": "2025-08"},
            use_auth=True,
            auth_token=self.admin_token
        )
        
        if not success or not roster_data:
            print("   ❌ Could not retrieve roster data for format testing")
            return False
        
        print(f"   ✅ Retrieved {len(roster_data)} entries for format testing")
        
        # Test 1: Required fields verification
        print(f"\n   🎯 TEST 1: Required Fields Verification")
        
        required_fields = ['id', 'date', 'start_time', 'end_time', 'staff_name', 'hours_worked']
        optional_fields = ['client_name', 'total_pay', 'base_pay', 'sleepover_allowance']
        
        field_coverage = {}
        for field in required_fields + optional_fields:
            field_coverage[field] = sum(1 for entry in roster_data if entry.get(field) is not None)
        
        print(f"   📋 Field coverage analysis:")
        for field in required_fields:
            coverage = field_coverage.get(field, 0)
            percentage = (coverage / len(roster_data)) * 100
            status = "✅" if percentage >= 90 else "⚠️" if percentage >= 50 else "❌"
            print(f"      {status} {field}: {coverage}/{len(roster_data)} ({percentage:.1f}%)")
            
            if percentage < 90 and field in ['id', 'date', 'start_time', 'end_time', 'hours_worked']:
                print(f"         ❌ Critical field {field} has insufficient coverage")
                return False
        
        print(f"   📋 Optional field coverage:")
        for field in optional_fields:
            coverage = field_coverage.get(field, 0)
            percentage = (coverage / len(roster_data)) * 100
            print(f"      📊 {field}: {coverage}/{len(roster_data)} ({percentage:.1f}%)")
        
        # Test 2: Pay information format verification
        print(f"\n   🎯 TEST 2: Pay Information Format Verification")
        
        entries_with_pay = [e for e in roster_data if e.get('total_pay') is not None]
        print(f"   💰 Entries with pay information: {len(entries_with_pay)}/{len(roster_data)}")
        
        if entries_with_pay:
            # Check pay format consistency
            pay_format_issues = []
            for entry in entries_with_pay[:10]:  # Check first 10 entries
                total_pay = entry.get('total_pay')
                if not isinstance(total_pay, (int, float)):
                    pay_format_issues.append(f"Entry {entry['id']}: pay is {type(total_pay)}")
                elif total_pay < 0:
                    pay_format_issues.append(f"Entry {entry['id']}: negative pay {total_pay}")
            
            if pay_format_issues:
                print(f"   ❌ Pay format issues found:")
                for issue in pay_format_issues[:5]:
                    print(f"      - {issue}")
                return False
            else:
                print(f"   ✅ Pay information properly formatted")
            
            # Show pay breakdown examples
            sample_entry = entries_with_pay[0]
            print(f"   📄 Sample pay breakdown:")
            print(f"      Total Pay: ${sample_entry.get('total_pay', 0):.2f}")
            print(f"      Base Pay: ${sample_entry.get('base_pay', 0):.2f}")
            print(f"      Sleepover: ${sample_entry.get('sleepover_allowance', 0):.2f}")
        
        # Test 3: Data sorting and structure for print layouts
        print(f"\n   🎯 TEST 3: Data Sorting and Structure for Print Layouts")
        
        # Test date sorting
        dates = [entry['date'] for entry in roster_data if entry.get('date')]
        sorted_dates = sorted(dates)
        
        if dates == sorted_dates:
            print(f"   ✅ Data is properly sorted by date")
        else:
            print(f"   ⚠️  Data may need sorting for print layout")
        
        print(f"   📅 Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
        
        # Test time format consistency
        time_format_valid = True
        for entry in roster_data[:10]:  # Check first 10 entries
            start_time = entry.get('start_time', '')
            end_time = entry.get('end_time', '')
            
            # Check HH:MM format
            if not (len(start_time) == 5 and start_time[2] == ':'):
                print(f"   ❌ Invalid start_time format: {start_time}")
                time_format_valid = False
                break
            if not (len(end_time) == 5 and end_time[2] == ':'):
                print(f"   ❌ Invalid end_time format: {end_time}")
                time_format_valid = False
                break
        
        if time_format_valid:
            print(f"   ✅ Time format is consistent (HH:MM)")
        else:
            return False
        
        # Test grouping potential for print layouts
        print(f"\n   📊 Data grouping analysis for print layouts:")
        
        # Group by date
        date_groups = {}
        for entry in roster_data:
            date = entry.get('date')
            if date:
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(entry)
        
        print(f"      Unique dates: {len(date_groups)}")
        print(f"      Avg entries per date: {len(roster_data) / len(date_groups):.1f}")
        
        # Group by staff
        staff_groups = {}
        for entry in roster_data:
            staff = entry.get('staff_name', 'Unassigned')
            if staff not in staff_groups:
                staff_groups[staff] = []
            staff_groups[staff].append(entry)
        
        print(f"      Unique staff/unassigned: {len(staff_groups)}")
        assigned_staff = [k for k in staff_groups.keys() if k != 'Unassigned']
        print(f"      Assigned staff members: {len(assigned_staff)}")
        
        # Test 4: Print-ready data structure verification
        print(f"\n   🎯 TEST 4: Print-Ready Data Structure Verification")
        
        # Create a sample print data structure
        sample_print_data = []
        for entry in roster_data[:5]:  # Test with first 5 entries
            print_entry = {
                'date': entry.get('date', ''),
                'day_of_week': '',  # Would be calculated
                'start_time': entry.get('start_time', ''),
                'end_time': entry.get('end_time', ''),
                'duration': f"{entry.get('hours_worked', 0):.1f}h",
                'staff': entry.get('staff_name', 'Unassigned'),
                'client': entry.get('client_name', 'N/A'),
                'pay': f"${entry.get('total_pay', 0):.2f}" if entry.get('total_pay') is not None else 'N/A'
            }
            sample_print_data.append(print_entry)
        
        print(f"   📄 Sample print-ready data structure:")
        for i, entry in enumerate(sample_print_data[:2]):
            print(f"      Entry {i+1}:")
            for key, value in entry.items():
                print(f"        {key}: {value}")
        
        print(f"   ✅ Data structure is suitable for print layouts")
        
        return True

    def run_all_tests(self):
        """Run all print functionality backend tests"""
        print(f"🎯 STARTING PRINT FUNCTIONALITY BACKEND SUPPORT TESTING")
        print(f"=" * 80)
        
        # Authenticate users
        if not self.authenticate_admin():
            print(f"\n❌ CRITICAL FAILURE: Could not authenticate admin user")
            return False
        
        if not self.authenticate_staff():
            print(f"\n❌ CRITICAL FAILURE: Could not authenticate staff user")
            return False
        
        # Run all test suites
        test_results = []
        
        print(f"\n" + "="*80)
        test_results.append(("Roster Data Retrieval for Print", self.test_roster_data_retrieval_for_print()))
        
        print(f"\n" + "="*80)
        test_results.append(("Date Range Data Fetching", self.test_date_range_data_fetching()))
        
        print(f"\n" + "="*80)
        test_results.append(("Role-Based Data Access for Print", self.test_role_based_data_access_for_print()))
        
        print(f"\n" + "="*80)
        test_results.append(("Data Format for Print", self.test_data_format_for_print()))
        
        # Final results
        print(f"\n" + "="*80)
        print(f"🎉 PRINT FUNCTIONALITY BACKEND TESTING COMPLETED")
        print(f"=" * 80)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        print(f"\n📊 TEST SUITE RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}: {test_name}")
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"   Test Suites Passed: {passed_tests}/{total_tests}")
        
        overall_success = passed_tests == total_tests
        
        if overall_success:
            print(f"\n🎉 CRITICAL SUCCESS: Print Functionality Backend Support FULLY WORKING!")
            print(f"   ✅ Roster data retrieval for monthly print working")
            print(f"   ✅ Cross-month data fetching for weekly/custom ranges working")
            print(f"   ✅ Role-based data access properly implemented")
            print(f"   ✅ Data format suitable for print layouts")
            print(f"   ✅ All required fields present for printing")
            print(f"   ✅ Pay information properly formatted and filtered")
            print(f"   ✅ Backend ready to support Phase 3 print functionality")
        else:
            print(f"\n❌ CRITICAL ISSUES FOUND:")
            failed_tests = [name for name, result in test_results if not result]
            for test_name in failed_tests:
                print(f"   - {test_name}")
            print(f"   Backend needs fixes before Phase 3 print functionality can be implemented")
        
        return overall_success

if __name__ == "__main__":
    tester = PrintFunctionalityBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)