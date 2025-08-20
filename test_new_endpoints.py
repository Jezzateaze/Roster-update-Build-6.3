#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class NewEndpointsTester:
    def __init__(self, base_url="https://workforce-wizard.preview.emergentagent.com"):
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

    def test_authentication_system(self):
        """Test authentication with Admin/0000 credentials"""
        print(f"\n🔐 Testing Authentication System...")
        
        # Test login with Admin/0000 credentials
        login_data = {
            "username": "Admin",
            "pin": "0000"
        }
        
        success, response = self.run_test(
            "Admin Login with PIN 0000",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success:
            self.auth_token = response.get('token')
            user_data = response.get('user', {})
            expires_at = response.get('expires_at')
            
            print(f"   ✅ Login successful")
            print(f"   User: {user_data.get('username')} ({user_data.get('role')})")
            print(f"   Token received: {self.auth_token[:20]}..." if self.auth_token else "No token")
            print(f"   Session expires: {expires_at}")
            
            # Verify user role is admin
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role confirmed")
            else:
                print(f"   ❌ Expected admin role, got: {user_data.get('role')}")
                
            return True
        else:
            print(f"   ❌ Authentication failed")
            return False

    def test_user_profile_update(self):
        """Test PUT /api/users/me endpoint for updating current user profile"""
        print(f"\n👤 Testing User Profile Update (PUT /api/users/me)...")
        
        if not self.auth_token:
            print("   ⚠️  No authentication token available - skipping profile update tests")
            return False
        
        # Test 1: Get current user profile first
        success, current_profile = self.run_test(
            "Get Current User Profile",
            "GET",
            "api/users/me",
            200,
            use_auth=True
        )
        
        if not success:
            print("   ❌ Could not get current user profile")
            return False
        
        print(f"   Current user: {current_profile.get('username')} ({current_profile.get('role')})")
        print(f"   Current email: {current_profile.get('email', 'Not set')}")
        
        # Test 2: Update profile with valid data
        profile_updates = {
            "first_name": "John",
            "last_name": "Administrator", 
            "email": "john.admin@rostersync.com",
            "phone": "+61 400 123 456",
            "address": "123 Collins Street, Melbourne VIC 3000, Australia"
        }
        
        success, updated_profile = self.run_test(
            "Update User Profile with Valid Data",
            "PUT",
            "api/users/me",
            200,
            data=profile_updates,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ Profile updated successfully")
            print(f"   Updated name: {updated_profile.get('first_name')} {updated_profile.get('last_name')}")
            print(f"   Updated email: {updated_profile.get('email')}")
            print(f"   Updated phone: {updated_profile.get('phone')}")
            print(f"   Updated address: {updated_profile.get('address')}")
            
            # Verify the updates were applied correctly
            updates_correct = True
            for field, expected_value in profile_updates.items():
                actual_value = updated_profile.get(field)
                if actual_value != expected_value:
                    print(f"   ❌ Field '{field}' mismatch: got '{actual_value}', expected '{expected_value}'")
                    updates_correct = False
                else:
                    print(f"   ✅ Field '{field}' updated correctly: {actual_value}")
            
            if not updates_correct:
                return False
        else:
            print("   ❌ Profile update failed")
            return False
        
        # Test 3: Update profile with missing auth token (should fail with 401)
        print(f"\n   Testing profile update without authentication...")
        success, response = self.run_test(
            "Update Profile Without Auth Token (Should Fail)",
            "PUT", 
            "api/users/me",
            401,  # Expect unauthorized
            data={"first_name": "Unauthorized"},
            use_auth=False  # Don't use auth token
        )
        
        if success:  # Success here means we got the expected 401 status
            print(f"   ✅ Unauthorized access correctly blocked")
        else:
            print(f"   ❌ Unauthorized access was not blocked properly")
            return False
        
        # Test 4: Update with partial data (should work)
        partial_updates = {
            "phone": "+61 400 999 888"
        }
        
        success, partial_updated = self.run_test(
            "Update Profile with Partial Data",
            "PUT",
            "api/users/me", 
            200,
            data=partial_updates,
            use_auth=True
        )
        
        if success:
            if partial_updated.get('phone') == partial_updates['phone']:
                print(f"   ✅ Partial update successful: phone = {partial_updated.get('phone')}")
            else:
                print(f"   ❌ Partial update failed: expected {partial_updates['phone']}, got {partial_updated.get('phone')}")
                return False
        
        # Test 5: Update with empty data (should fail with 400)
        success, response = self.run_test(
            "Update Profile with Empty Data (Should Fail)",
            "PUT",
            "api/users/me",
            400,  # Expect bad request
            data={},
            use_auth=True
        )
        
        if success:  # Success here means we got the expected 400 status
            print(f"   ✅ Empty update correctly rejected")
        else:
            print(f"   ❌ Empty update was not rejected properly")
            return False
        
        print(f"   ✅ All user profile update tests passed")
        return True

    def test_address_search_autocomplete(self):
        """Test GET /api/address/search endpoint for address autocomplete"""
        print(f"\n🏠 Testing Address Search Autocomplete (GET /api/address/search)...")
        
        # Test 1: Valid address search with good query
        test_queries = [
            {
                "query": "123 Collins Street Melbourne",
                "description": "Melbourne CBD address",
                "min_results": 1
            },
            {
                "query": "Sydney Opera House",
                "description": "Famous landmark",
                "min_results": 1
            },
            {
                "query": "10 Downing Street London",
                "description": "International address",
                "min_results": 1
            },
            {
                "query": "Brisbane City Hall",
                "description": "Brisbane landmark",
                "min_results": 1
            }
        ]
        
        for test_case in test_queries:
            success, results = self.run_test(
                f"Search Address: {test_case['description']}",
                "GET",
                "api/address/search",
                200,
                params={"q": test_case["query"], "limit": 5}
            )
            
            if success:
                print(f"   ✅ Found {len(results)} results for '{test_case['query']}'")
                
                if len(results) >= test_case["min_results"]:
                    print(f"   ✅ Minimum results requirement met ({len(results)} >= {test_case['min_results']})")
                    
                    # Verify result structure
                    if results:
                        first_result = results[0]
                        required_fields = ["display_name", "street_number", "route", "locality", 
                                         "administrative_area_level_1", "country", "postal_code", 
                                         "latitude", "longitude"]
                        
                        structure_valid = True
                        for field in required_fields:
                            if field not in first_result:
                                print(f"   ❌ Missing required field: {field}")
                                structure_valid = False
                        
                        if structure_valid:
                            print(f"   ✅ Result structure is valid")
                            print(f"      Display name: {first_result.get('display_name', 'N/A')[:80]}...")
                            print(f"      Country: {first_result.get('country', 'N/A')}")
                            print(f"      Coordinates: {first_result.get('latitude', 0)}, {first_result.get('longitude', 0)}")
                        else:
                            print(f"   ❌ Result structure is invalid")
                            return False
                else:
                    print(f"   ⚠️  Fewer results than expected ({len(results)} < {test_case['min_results']})")
            else:
                print(f"   ❌ Address search failed for '{test_case['query']}'")
                return False
        
        # Test 2: Short query (less than 3 characters) - should return empty or handle gracefully
        success, short_results = self.run_test(
            "Search with Short Query (Should Return Empty)",
            "GET",
            "api/address/search",
            200,
            params={"q": "ab", "limit": 5}
        )
        
        if success:
            print(f"   ✅ Short query handled gracefully: {len(short_results)} results")
            if len(short_results) == 0:
                print(f"   ✅ Short query correctly returned empty results")
            else:
                print(f"   ⚠️  Short query returned {len(short_results)} results (may be valid)")
        
        # Test 3: Invalid/nonsense query - should handle gracefully
        success, invalid_results = self.run_test(
            "Search with Invalid Query (Should Handle Gracefully)",
            "GET",
            "api/address/search",
            200,
            params={"q": "xyzabc123nonexistentplace999", "limit": 5}
        )
        
        if success:
            print(f"   ✅ Invalid query handled gracefully: {len(invalid_results)} results")
        else:
            print(f"   ❌ Invalid query caused server error")
            return False
        
        # Test 4: Empty query - should handle gracefully
        success, empty_results = self.run_test(
            "Search with Empty Query (Should Handle Gracefully)",
            "GET",
            "api/address/search",
            200,
            params={"q": "", "limit": 5}
        )
        
        if success:
            print(f"   ✅ Empty query handled gracefully: {len(empty_results)} results")
        else:
            print(f"   ❌ Empty query caused server error")
            return False
        
        # Test 5: Test with different limit values
        success, limited_results = self.run_test(
            "Search with Custom Limit (limit=2)",
            "GET",
            "api/address/search",
            200,
            params={"q": "Melbourne", "limit": 2}
        )
        
        if success:
            if len(limited_results) <= 2:
                print(f"   ✅ Limit parameter respected: {len(limited_results)} results (max 2)")
            else:
                print(f"   ❌ Limit parameter not respected: {len(limited_results)} results (expected max 2)")
                return False
        
        # Test 6: Test without limit parameter (should use default)
        success, default_results = self.run_test(
            "Search without Limit Parameter (Should Use Default)",
            "GET",
            "api/address/search",
            200,
            params={"q": "Sydney"}
        )
        
        if success:
            print(f"   ✅ Default limit working: {len(default_results)} results")
        
        print(f"   ✅ All address search autocomplete tests passed")
        return True

    def run_new_endpoint_tests(self):
        """Run tests for the new endpoints specified in the review request"""
        print("🚀 Starting New Endpoints Testing...")
        print(f"   Base URL: {self.base_url}")
        print("🎯 FOCUS: Testing PUT /api/users/me and GET /api/address/search endpoints")
        
        # Authentication test (required for protected endpoints)
        if not self.test_authentication_system():
            print("❌ Authentication failed - cannot proceed with protected endpoint tests")
            return False
        
        # Test the new endpoints
        tests = [
            self.test_user_profile_update,
            self.test_address_search_autocomplete,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with error: {str(e)}")
        
        # Print summary
        print(f"\n📊 New Endpoints Test Summary:")
        print(f"   Tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = NewEndpointsTester()
    success = tester.run_new_endpoint_tests()
    sys.exit(0 if success else 1)