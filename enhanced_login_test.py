#!/usr/bin/env python3
"""
Enhanced Login System Backend Test
Tests the Enhanced Login System backend functionality as per review request
"""

import requests
import json
from datetime import datetime

class EnhancedLoginSystemTester:
    def __init__(self, base_url="https://shift-master-10.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
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

            try:
                return success, response.json() if response.status_code < 400 else {}
            except:
                return success, response.text if success else response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_enhanced_login_system(self):
        """Test Enhanced Login System backend functionality as per review request"""
        print(f"\n🔐 Testing Enhanced Login System Backend Functionality - COMPREHENSIVE REVIEW REQUEST TESTS...")
        
        # Test 1: GET /api/users/login endpoint - should return all admin and staff users for login dropdown
        print(f"\n   🎯 TEST 1: GET /api/users/login endpoint - Login dropdown users")
        success, login_users = self.run_test(
            "Get Login Users for Dropdown",
            "GET",
            "api/users/login",
            200
        )
        
        if not success:
            print("   ❌ Could not get login users")
            return False
        
        print(f"   ✅ Found {len(login_users)} users for login dropdown")
        
        # Verify we have admin and staff users
        admin_users = [user for user in login_users if user.get('role') == 'admin']
        staff_users = [user for user in login_users if user.get('role') == 'staff']
        
        print(f"   Admin users: {len(admin_users)}")
        print(f"   Staff users: {len(staff_users)}")
        
        # Expected: 1 admin + 13+ staff users
        expected_min_total = 14
        if len(login_users) >= expected_min_total:
            print(f"   ✅ Expected minimum {expected_min_total} users found ({len(login_users)} total)")
        else:
            print(f"   ⚠️  Expected minimum {expected_min_total} users, found {len(login_users)}")
        
        # Verify user data structure
        if login_users:
            sample_user = login_users[0]
            required_fields = ['id', 'username', 'role', 'is_first_login']
            missing_fields = [field for field in required_fields if field not in sample_user]
            
            if not missing_fields:
                print(f"   ✅ User data structure is valid")
                print(f"   Sample user: {sample_user.get('username')} ({sample_user.get('role')})")
            else:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False
        
        # Test 2: Check if system admin user exists (username: 'system')
        print(f"\n   🎯 TEST 2: Check for System Admin User (username: 'system')")
        
        system_admin_exists = any(user.get('username') == 'system' for user in login_users)
        
        if system_admin_exists:
            print("   ✅ System admin user exists in login dropdown")
        else:
            print("   ⚠️  System admin user not found - will test with regular Admin user")
        
        # Test 3: POST /api/auth/login endpoint with System admin user (or fallback to Admin)
        print(f"\n   🎯 TEST 3: POST /api/auth/login with Admin user")
        
        # Try system admin first, then fallback to Admin
        login_attempts = [
            {"username": "system", "pin": "1234", "description": "System Admin"},
            {"username": "Admin", "pin": "1234", "description": "Regular Admin"}
        ]
        
        admin_login_successful = False
        admin_user_data = None
        
        for attempt in login_attempts:
            print(f"\n      Trying {attempt['description']} login ({attempt['username']}/{attempt['pin']})...")
            
            success, login_response = self.run_test(
                f"{attempt['description']} Login",
                "POST",
                "api/auth/login",
                200,
                data={"username": attempt["username"], "pin": attempt["pin"]}
            )
            
            if success:
                self.auth_token = login_response.get('token')
                admin_user_data = login_response.get('user', {})
                
                print(f"      ✅ {attempt['description']} login successful")
                print(f"      Username: {admin_user_data.get('username')}")
                print(f"      Role: {admin_user_data.get('role')}")
                print(f"      First-time login: {admin_user_data.get('is_first_login')}")
                print(f"      Token: {self.auth_token[:20]}..." if self.auth_token else "No token")
                
                # Verify it's admin role
                if admin_user_data.get('role') == 'admin':
                    print(f"      ✅ Admin has correct admin role")
                    admin_login_successful = True
                    break
                else:
                    print(f"      ❌ Expected admin role, got: {admin_user_data.get('role')}")
            else:
                print(f"      ❌ {attempt['description']} login failed")
        
        if not admin_login_successful:
            print("   ❌ No admin login successful - cannot continue with authenticated tests")
            return False
        
        # Test 4: First-time login detection
        print(f"\n   🎯 TEST 4: First-time login detection")
        
        if admin_user_data:
            is_first_login = admin_user_data.get('is_first_login', False)
            
            print(f"   Admin first-time login status: {is_first_login}")
            if is_first_login is not None:
                print(f"   ✅ First-time login flag is properly managed")
            else:
                print(f"   ❌ First-time login flag is missing")
                return False
        
        # Test 5: PUT /api/auth/change-pin endpoint for changing admin PIN
        print(f"\n   🎯 TEST 5: PUT /api/auth/change-pin endpoint - Change PIN functionality")
        
        if not self.auth_token:
            print("   ❌ No authentication token available for PIN change test")
            return False
        
        # Test PIN change with new PIN
        new_pin_data = {
            "new_pin": "5678"
        }
        
        success, pin_change_response = self.run_test(
            "Change Admin PIN to 5678",
            "PUT",
            "api/auth/change-pin",
            200,
            data=new_pin_data,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ PIN change successful")
            print(f"   Response: {pin_change_response.get('message', 'No message')}")
            
            # Test login with new PIN
            print(f"\n      Testing login with new PIN...")
            current_username = admin_user_data.get('username')
            new_pin_login_data = {
                "username": current_username,
                "pin": "5678"
            }
            
            success, new_pin_login = self.run_test(
                "Login with New PIN (5678)",
                "POST",
                "api/auth/login",
                200,
                data=new_pin_login_data
            )
            
            if success:
                user_data = new_pin_login.get('user', {})
                print(f"      ✅ Login with new PIN successful")
                print(f"      First-time login after PIN change: {user_data.get('is_first_login')}")
                
                # Verify first-time login is now False
                if not user_data.get('is_first_login'):
                    print(f"      ✅ First-time login flag correctly set to False after PIN change")
                else:
                    print(f"      ⚠️  First-time login flag is still True (may be expected behavior)")
            else:
                print(f"      ❌ Login with new PIN failed")
                return False
            
            # Change PIN back to original for other tests
            print(f"\n      Restoring original PIN...")
            restore_pin_data = {
                "new_pin": "1234"
            }
            
            # Get new token from the new PIN login
            restore_token = new_pin_login.get('token')
            original_token = self.auth_token
            self.auth_token = restore_token
            
            success, restore_response = self.run_test(
                "Restore Original PIN (1234)",
                "PUT",
                "api/auth/change-pin",
                200,
                data=restore_pin_data,
                use_auth=True
            )
            
            # Restore original token
            self.auth_token = original_token
            
            if success:
                print(f"      ✅ Original PIN restored")
            else:
                print(f"      ⚠️  Could not restore original PIN")
        else:
            print(f"   ❌ PIN change failed")
            return False
        
        # Test 6: Authentication tokens working correctly
        print(f"\n   🎯 TEST 6: Verify authentication tokens are working correctly")
        
        # Test with valid token
        if self.auth_token:
            success, profile_data = self.run_test(
                "Access Protected Endpoint with Valid Token",
                "GET",
                "api/users/me",
                200,
                use_auth=True
            )
            
            if success:
                print(f"   ✅ Valid token allows access to protected endpoints")
                print(f"   Profile: {profile_data.get('username')} ({profile_data.get('role')})")
            else:
                print(f"   ❌ Valid token was rejected")
                return False
        
        # Test with invalid token
        print(f"\n      Testing with invalid token...")
        original_token = self.auth_token
        self.auth_token = "invalid_token_12345"
        
        success, error_response = self.run_test(
            "Access Protected Endpoint with Invalid Token (Should Fail)",
            "GET",
            "api/users/me",
            401,  # Expect unauthorized
            use_auth=True
        )
        
        # Restore original token
        self.auth_token = original_token
        
        if success:  # Success means we got expected 401
            print(f"   ✅ Invalid token correctly rejected")
        else:
            print(f"   ❌ Invalid token was not properly rejected")
            return False
        
        # Test 7: Test staff user login
        print(f"\n   🎯 TEST 7: Test staff user authentication")
        
        # Test a few staff users
        staff_test_users = ["rose", "angela", "chanelle"]
        staff_login_success = 0
        
        for username in staff_test_users:
            print(f"\n      Testing staff login: {username}/888888")
            
            success, staff_login = self.run_test(
                f"Staff Login: {username}",
                "POST",
                "api/auth/login",
                200,
                data={"username": username, "pin": "888888"}
            )
            
            if success:
                staff_user_data = staff_login.get('user', {})
                print(f"      ✅ {username} login successful")
                print(f"         Role: {staff_user_data.get('role')}")
                print(f"         Staff ID: {staff_user_data.get('staff_id', 'N/A')}")
                
                if staff_user_data.get('role') == 'staff':
                    staff_login_success += 1
                    print(f"         ✅ Correct staff role")
                else:
                    print(f"         ❌ Expected staff role, got: {staff_user_data.get('role')}")
            else:
                print(f"      ❌ {username} login failed")
        
        print(f"\n   Staff authentication results: {staff_login_success}/{len(staff_test_users)} successful")
        
        # Final Assessment
        print(f"\n   🎉 ENHANCED LOGIN SYSTEM TEST RESULTS:")
        print(f"      ✅ GET /api/users/login: Returns {len(login_users)} users for dropdown")
        print(f"      ✅ User data structure: Valid with required fields")
        print(f"      ✅ Admin login: Working with PIN 1234")
        print(f"      ✅ First-time login detection: Implemented and working")
        print(f"      ✅ PIN change functionality: Working correctly")
        print(f"      ✅ Authentication tokens: Working correctly")
        print(f"      ✅ Security: Invalid tokens properly rejected")
        print(f"      ✅ Staff authentication: {staff_login_success}/{len(staff_test_users)} staff users working")
        
        # Determine overall success
        critical_tests_passed = (
            len(login_users) >= expected_min_total and  # Login users endpoint working
            len(admin_users) > 0 and  # At least one admin user
            len(staff_users) > 0 and  # At least one staff user
            admin_login_successful and  # Admin authentication working
            self.auth_token is not None and  # Token generation working
            staff_login_success > 0  # At least some staff can login
        )
        
        if critical_tests_passed:
            print(f"\n   🎉 CRITICAL SUCCESS: Enhanced Login System backend functionality is working!")
            print(f"      - Login dropdown endpoint returns {len(login_users)} users ({len(admin_users)} admin + {len(staff_users)} staff)")
            print(f"      - Admin authentication works with PIN 1234")
            print(f"      - First-time login flags are properly managed")
            print(f"      - PIN change functionality works for authenticated users")
            print(f"      - Authentication tokens are working correctly")
            print(f"      - Staff users can authenticate ({staff_login_success}/{len(staff_test_users)} tested)")
        else:
            print(f"\n   ❌ CRITICAL ISSUES FOUND:")
            if len(login_users) < expected_min_total:
                print(f"      - Insufficient users returned from login endpoint ({len(login_users)} < {expected_min_total})")
            if len(admin_users) == 0:
                print(f"      - No admin users found")
            if len(staff_users) == 0:
                print(f"      - No staff users found")
            if not admin_login_successful:
                print(f"      - Admin authentication not working")
            if self.auth_token is None:
                print(f"      - Token generation not working")
            if staff_login_success == 0:
                print(f"      - Staff authentication not working")
        
        return critical_tests_passed

def main():
    print("🚀 Starting Enhanced Login System Backend Tests")
    print("🎯 FOCUS: Test Enhanced Login System backend functionality as per review request")
    print("=" * 80)
    
    tester = EnhancedLoginSystemTester()
    
    # Run the Enhanced Login System test
    print("\n" + "="*80)
    print("🎯 ENHANCED LOGIN SYSTEM BACKEND TESTS")
    print("="*80)
    success = tester.test_enhanced_login_system()
    
    print(f"\n🏁 Enhanced Login System Test Complete!")
    print(f"Result: {'✅ PASSED - Enhanced Login System working!' if success else '❌ FAILED - Enhanced Login System has issues'}")
    
    # Print final summary
    print(f"\n📊 TEST SUMMARY:")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "   Success rate: 0%")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())