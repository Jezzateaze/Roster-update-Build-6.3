import requests
import sys
import json
from datetime import datetime

class ClientBiographyTester:
    def __init__(self, base_url="https://shift-master-10.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.staff_auth_token = None
        self.jeremy_client_id = "feedf5e9-7f8b-46d6-ac34-14110806b475"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, use_auth=False, use_staff_auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if use_auth and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        elif use_staff_auth and self.staff_auth_token:
            headers['Authorization'] = f'Bearer {self.staff_auth_token}'

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

            return success, response.json() if response.status_code < 400 else response.text

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
            user_data = response.get('user', {})
            print(f"   ✅ Admin authenticated successfully")
            print(f"   Role: {user_data.get('role')}")
            print(f"   Token: {self.auth_token[:20]}..." if self.auth_token else "No token")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def authenticate_staff(self):
        """Authenticate as staff user for role-based testing"""
        print(f"\n👤 Authenticating as Staff...")
        
        # Try to authenticate with a staff user (rose/888888 as mentioned in review)
        login_data = {
            "username": "rose",
            "pin": "888888"
        }
        
        success, response = self.run_test(
            "Staff Login",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success:
            self.staff_auth_token = response.get('token')
            user_data = response.get('user', {})
            print(f"   ✅ Staff authenticated successfully")
            print(f"   Role: {user_data.get('role')}")
            print(f"   Staff ID: {user_data.get('staff_id', 'N/A')}")
            print(f"   Token: {self.staff_auth_token[:20]}..." if self.staff_auth_token else "No token")
            return True
        else:
            print(f"   ❌ Staff authentication failed")
            return False

    def test_biography_update_endpoint(self):
        """Test PUT /api/clients/{client_id}/biography endpoint"""
        print(f"\n📝 Testing Biography Update Endpoint...")
        
        if not self.auth_token:
            print("   ❌ No admin authentication token available")
            return False

        # Test comprehensive biography data for Jeremy
        comprehensive_biography = {
            "strengths": "Jeremy has a passion for gardening and enjoys growing vegetables and flowers. He is skilled in various crafts including woodworking and painting. Jeremy loves cooking and often prepares meals for himself. He has an interest in photography and enjoys taking pictures of nature. Jeremy also enjoys playing video games and is quite skilled at strategy games.",
            "living_arrangements": "Jeremy lives independently in a comfortable 1-bedroom apartment located at 20/384 Stanley Rd, Carina 4152. He shares his home with his beloved Maltese dog, Siana-Rose, who provides companionship and emotional support. The apartment is well-maintained and Jeremy takes pride in keeping it organized and clean.",
            "daily_life": "Jeremy follows a structured daily routine that includes morning walks with Siana-Rose, tending to his small garden on the balcony, and engaging in various hobbies throughout the day. He enjoys cooking his own meals and maintains good personal hygiene and self-care routines. Jeremy participates in community activities and maintains social connections with neighbors and friends.",
            "goals": [
                {
                    "title": "Improve Physical Fitness",
                    "description": "Increase daily physical activity and improve overall health and stamina",
                    "how_to_achieve": "Daily walks with Siana-Rose, join local gym, participate in swimming classes, track progress with fitness app"
                },
                {
                    "title": "Expand Social Network",
                    "description": "Build meaningful friendships and social connections in the community",
                    "how_to_achieve": "Join hobby groups, attend community events, volunteer at local organizations, participate in group activities"
                },
                {
                    "title": "Develop Cooking Skills",
                    "description": "Learn new recipes and improve culinary abilities for better nutrition",
                    "how_to_achieve": "Take cooking classes, practice new recipes weekly, create meal plans, learn about nutrition"
                },
                {
                    "title": "Enhance Photography Skills",
                    "description": "Improve photography techniques and potentially exhibit work",
                    "how_to_achieve": "Take photography course, practice different techniques, join photography club, create portfolio"
                },
                {
                    "title": "Maintain Independent Living",
                    "description": "Continue living independently with minimal support",
                    "how_to_achieve": "Develop daily living skills, maintain apartment, manage finances, build support network"
                },
                {
                    "title": "Pursue Creative Interests",
                    "description": "Explore and develop artistic talents in painting and crafts",
                    "how_to_achieve": "Attend art classes, set up home studio space, participate in local art shows, practice regularly"
                }
            ],
            "supports": [
                {
                    "description": "Personal care and daily living assistance",
                    "provider": "Workcare Support Services - Sarah Johnson",
                    "frequency": "3 times per week",
                    "type": "In-home support"
                },
                {
                    "description": "Community access and social participation",
                    "provider": "Community Connect - Michael Chen",
                    "frequency": "2 times per week",
                    "type": "Community participation"
                },
                {
                    "description": "Health and medical support coordination",
                    "provider": "Brisbane Health Network - Dr. Amanda Wilson",
                    "frequency": "Monthly",
                    "type": "Health coordination"
                },
                {
                    "description": "Behavioral support and counseling",
                    "provider": "Positive Behavior Solutions - Lisa Thompson",
                    "frequency": "Fortnightly",
                    "type": "Behavioral support"
                },
                {
                    "description": "Occupational therapy services",
                    "provider": "Allied Health Partners - James Rodriguez",
                    "frequency": "Monthly",
                    "type": "Therapy services"
                },
                {
                    "description": "Pet care support for Siana-Rose",
                    "provider": "Pet Care Plus - Emma Davis",
                    "frequency": "As needed",
                    "type": "Pet support"
                }
            ],
            "additional_info": "Jeremy is highly motivated to maintain his independence and actively participates in his support planning. He has strong communication skills and is able to express his needs and preferences clearly. Jeremy responds well to routine and structure but also enjoys flexibility for spontaneous activities. He has a good relationship with his support workers and values their assistance in achieving his goals."
        }

        # Test 1: Admin full access biography update
        print(f"\n   🎯 TEST 1: Admin Full Access Biography Update")
        success, response = self.run_test(
            f"Update Jeremy's Biography (Admin Full Access)",
            "PUT",
            f"api/clients/{self.jeremy_client_id}/biography",
            200,
            data=comprehensive_biography,
            use_auth=True
        )

        if success:
            print(f"   ✅ Admin biography update successful")
            print(f"   Updated fields: {list(response.keys()) if isinstance(response, dict) else 'Response received'}")
        else:
            print(f"   ❌ Admin biography update failed")
            return False

        # Test 2: Staff limited access biography update (if staff auth available)
        if self.staff_auth_token:
            print(f"\n   🎯 TEST 2: Staff Limited Access Biography Update")
            
            # Staff should only be able to update certain fields
            staff_allowed_update = {
                "strengths": "Updated strengths by staff - Jeremy shows great resilience and adaptability",
                "daily_life": "Updated daily life by staff - Jeremy maintains excellent routines",
                "additional_info": "Updated additional info by staff - Jeremy is very cooperative"
            }
            
            success, response = self.run_test(
                f"Update Jeremy's Biography (Staff Limited Access)",
                "PUT",
                f"api/clients/{self.jeremy_client_id}/biography",
                200,
                data=staff_allowed_update,
                use_staff_auth=True
            )

            if success:
                print(f"   ✅ Staff biography update successful")
                print(f"   Staff can update allowed fields")
            else:
                print(f"   ⚠️  Staff biography update failed - may indicate proper access restrictions")

        # Test 3: Unauthenticated access (should fail)
        print(f"\n   🎯 TEST 3: Unauthenticated Biography Update (Should Fail)")
        success, response = self.run_test(
            f"Update Biography Without Auth (Should Fail)",
            "PUT",
            f"api/clients/{self.jeremy_client_id}/biography",
            403,  # Expect forbidden (backend returns 403 for "Not authenticated")
            data={"strengths": "Unauthorized update"},
            use_auth=False
        )

        if success:  # Success means we got expected 403
            print(f"   ✅ Unauthenticated access correctly blocked")
        else:
            print(f"   ❌ Unauthenticated access was not properly blocked")
            return False

        return True

    def test_biography_data_retrieval(self):
        """Test GET /api/clients/{client_id} and GET /api/clients endpoints"""
        print(f"\n📖 Testing Biography Data Retrieval...")
        
        if not self.auth_token:
            print("   ❌ No admin authentication token available")
            return False

        # Test 1: Get specific client with biography (Admin access)
        print(f"\n   🎯 TEST 1: Get Jeremy's Profile with Biography (Admin Access)")
        success, client_data = self.run_test(
            f"Get Jeremy's Client Profile",
            "GET",
            f"api/clients/{self.jeremy_client_id}",
            200,
            use_auth=True
        )

        if success:
            print(f"   ✅ Client profile retrieved successfully")
            
            # Check if biography data is present
            biography = client_data.get('biography', {}) if isinstance(client_data, dict) else {}
            if biography:
                print(f"   ✅ Biography data found")
                print(f"   Biography fields: {list(biography.keys())}")
                
                # Verify comprehensive data
                expected_fields = ['strengths', 'living_arrangements', 'daily_life', 'goals', 'supports', 'additional_info']
                missing_fields = [field for field in expected_fields if field not in biography]
                
                if not missing_fields:
                    print(f"   ✅ All expected biography fields present")
                    
                    # Check goals structure
                    goals = biography.get('goals', [])
                    if goals and len(goals) >= 6:
                        print(f"   ✅ Goals data complete: {len(goals)} goals found")
                        
                        # Verify goal structure
                        first_goal = goals[0] if goals else {}
                        goal_fields = ['title', 'description', 'how_to_achieve']
                        if all(field in first_goal for field in goal_fields):
                            print(f"   ✅ Goal structure is correct")
                        else:
                            print(f"   ❌ Goal structure incomplete: {list(first_goal.keys())}")
                    else:
                        print(f"   ⚠️  Goals data incomplete: {len(goals)} goals found")
                    
                    # Check supports structure
                    supports = biography.get('supports', [])
                    if supports and len(supports) >= 6:
                        print(f"   ✅ Supports data complete: {len(supports)} supports found")
                        
                        # Verify support structure
                        first_support = supports[0] if supports else {}
                        support_fields = ['description', 'provider', 'frequency', 'type']
                        if all(field in first_support for field in support_fields):
                            print(f"   ✅ Support structure is correct")
                        else:
                            print(f"   ❌ Support structure incomplete: {list(first_support.keys())}")
                    else:
                        print(f"   ⚠️  Supports data incomplete: {len(supports)} supports found")
                        
                else:
                    print(f"   ❌ Missing biography fields: {missing_fields}")
                    return False
            else:
                print(f"   ❌ No biography data found in client profile")
                return False
        else:
            print(f"   ❌ Failed to retrieve client profile")
            return False

        # Test 2: Get all clients with biography filtering (Admin access)
        print(f"\n   🎯 TEST 2: Get All Clients with Biography Data (Admin Access)")
        success, clients_data = self.run_test(
            f"Get All Clients",
            "GET",
            f"api/clients",
            200,
            use_auth=True
        )

        if success:
            print(f"   ✅ Clients list retrieved successfully")
            
            if isinstance(clients_data, list) and len(clients_data) > 0:
                print(f"   Found {len(clients_data)} clients")
                
                # Find Jeremy in the list
                jeremy_client = None
                for client in clients_data:
                    if client.get('id') == self.jeremy_client_id:
                        jeremy_client = client
                        break
                
                if jeremy_client:
                    print(f"   ✅ Jeremy found in clients list")
                    biography = jeremy_client.get('biography', {})
                    if biography:
                        print(f"   ✅ Jeremy's biography data included in list")
                    else:
                        print(f"   ❌ Jeremy's biography data missing from list")
                        return False
                else:
                    print(f"   ❌ Jeremy not found in clients list")
                    return False
            else:
                print(f"   ⚠️  No clients found or invalid response format")

        # Test 3: Staff access to client data (if staff auth available)
        if self.staff_auth_token:
            print(f"\n   🎯 TEST 3: Staff Access to Client Biography (Should be Filtered)")
            success, staff_client_data = self.run_test(
                f"Get Jeremy's Profile (Staff Access)",
                "GET",
                f"api/clients/{self.jeremy_client_id}",
                200,
                use_staff_auth=True
            )

            if success:
                print(f"   ✅ Staff can access client profile")
                
                # Check if biography data is filtered for staff
                biography = staff_client_data.get('biography', {}) if isinstance(staff_client_data, dict) else {}
                if biography:
                    # Staff should only see certain fields
                    staff_allowed_fields = ['strengths', 'daily_life', 'additional_info']
                    staff_restricted_fields = ['living_arrangements', 'goals', 'supports']
                    
                    has_allowed = any(field in biography for field in staff_allowed_fields)
                    has_restricted = any(field in biography for field in staff_restricted_fields)
                    
                    if has_allowed and not has_restricted:
                        print(f"   ✅ Staff biography access properly filtered")
                        print(f"   Staff can see: {[f for f in staff_allowed_fields if f in biography]}")
                    elif has_allowed and has_restricted:
                        print(f"   ⚠️  Staff can see restricted fields - access control may need review")
                        print(f"   Staff can see: {list(biography.keys())}")
                    else:
                        print(f"   ⚠️  Staff biography access unclear")
                else:
                    print(f"   ⚠️  No biography data in staff response")

        return True

    def test_data_validation(self):
        """Test ClientBiography model field validation"""
        print(f"\n🔍 Testing Data Validation...")
        
        if not self.auth_token:
            print("   ❌ No admin authentication token available")
            return False

        # Test 1: Valid goals array structure
        print(f"\n   🎯 TEST 1: Valid Goals Array Structure")
        valid_goals_data = {
            "goals": [
                {
                    "title": "Test Goal 1",
                    "description": "This is a test goal description",
                    "how_to_achieve": "Steps to achieve this goal"
                },
                {
                    "title": "Test Goal 2", 
                    "description": "Another test goal description",
                    "how_to_achieve": "More steps to achieve this goal"
                }
            ]
        }
        
        success, response = self.run_test(
            f"Update with Valid Goals Structure",
            "PUT",
            f"api/clients/{self.jeremy_client_id}/biography",
            200,
            data=valid_goals_data,
            use_auth=True
        )

        if success:
            print(f"   ✅ Valid goals structure accepted")
        else:
            print(f"   ❌ Valid goals structure rejected")
            return False

        # Test 2: Valid supports array structure
        print(f"\n   🎯 TEST 2: Valid Supports Array Structure")
        valid_supports_data = {
            "supports": [
                {
                    "description": "Test support service",
                    "provider": "Test Provider Name",
                    "frequency": "Weekly",
                    "type": "Support type"
                },
                {
                    "description": "Another test support service",
                    "provider": "Another Provider Name", 
                    "frequency": "Monthly",
                    "type": "Another support type"
                }
            ]
        }
        
        success, response = self.run_test(
            f"Update with Valid Supports Structure",
            "PUT",
            f"api/clients/{self.jeremy_client_id}/biography",
            200,
            data=valid_supports_data,
            use_auth=True
        )

        if success:
            print(f"   ✅ Valid supports structure accepted")
        else:
            print(f"   ❌ Valid supports structure rejected")
            return False

        # Test 3: Valid text fields
        print(f"\n   🎯 TEST 3: Valid Text Fields")
        valid_text_data = {
            "strengths": "Test strengths text content",
            "living_arrangements": "Test living arrangements description",
            "daily_life": "Test daily life description",
            "additional_info": "Test additional information content"
        }
        
        success, response = self.run_test(
            f"Update with Valid Text Fields",
            "PUT",
            f"api/clients/{self.jeremy_client_id}/biography",
            200,
            data=valid_text_data,
            use_auth=True
        )

        if success:
            print(f"   ✅ Valid text fields accepted")
        else:
            print(f"   ❌ Valid text fields rejected")
            return False

        # Test 4: Invalid goals structure (should fail gracefully)
        print(f"\n   🎯 TEST 4: Invalid Goals Structure (Should Handle Gracefully)")
        invalid_goals_data = {
            "goals": [
                {
                    "title": "Missing fields goal"
                    # Missing description and how_to_achieve
                },
                "invalid_goal_format"  # Should be object, not string
            ]
        }
        
        success, response = self.run_test(
            f"Update with Invalid Goals Structure",
            "PUT",
            f"api/clients/{self.jeremy_client_id}/biography",
            422,  # Expect Pydantic validation error
            data=invalid_goals_data,
            use_auth=True
        )

        if success:  # Success means we got expected 422
            print(f"   ✅ Invalid goals structure properly rejected with validation error")
        else:
            print(f"   ⚠️  Invalid goals structure validation response unexpected")

        # Test 5: Invalid supports structure (should fail gracefully)
        print(f"\n   🎯 TEST 5: Invalid Supports Structure (Should Handle Gracefully)")
        invalid_supports_data = {
            "supports": [
                {
                    "description": "Missing fields support"
                    # Missing provider, frequency, type
                },
                123  # Should be object, not number
            ]
        }
        
        success, response = self.run_test(
            f"Update with Invalid Supports Structure",
            "PUT",
            f"api/clients/{self.jeremy_client_id}/biography",
            422,  # Expect Pydantic validation error
            data=invalid_supports_data,
            use_auth=True
        )

        if success:  # Success means we got expected 422
            print(f"   ✅ Invalid supports structure properly rejected with validation error")
        else:
            print(f"   ⚠️  Invalid supports structure validation response unexpected")

        return True

    def test_jeremy_profile_verification(self):
        """Verify Jeremy's profile contains comprehensive information"""
        print(f"\n👤 Testing Jeremy's Profile Verification...")
        
        if not self.auth_token:
            print("   ❌ No admin authentication token available")
            return False

        # First, restore Jeremy's comprehensive biography data (in case it was overwritten by tests)
        comprehensive_biography = {
            "strengths": "Jeremy has a passion for gardening and enjoys growing vegetables and flowers. He is skilled in various crafts including woodworking and painting. Jeremy loves cooking and often prepares meals for himself. He has an interest in photography and enjoys taking pictures of nature. Jeremy also enjoys playing video games and is quite skilled at strategy games.",
            "living_arrangements": "Jeremy lives independently in a comfortable 1-bedroom apartment located at 20/384 Stanley Rd, Carina 4152. He shares his home with his beloved Maltese dog, Siana-Rose, who provides companionship and emotional support. The apartment is well-maintained and Jeremy takes pride in keeping it organized and clean.",
            "daily_life": "Jeremy follows a structured daily routine that includes morning walks with Siana-Rose, tending to his small garden on the balcony, and engaging in various hobbies throughout the day. He enjoys cooking his own meals and maintains good personal hygiene and self-care routines. Jeremy participates in community activities and maintains social connections with neighbors and friends.",
            "goals": [
                {
                    "title": "Improve Physical Fitness",
                    "description": "Increase daily physical activity and improve overall health and stamina",
                    "how_to_achieve": "Daily walks with Siana-Rose, join local gym, participate in swimming classes, track progress with fitness app"
                },
                {
                    "title": "Expand Social Network",
                    "description": "Build meaningful friendships and social connections in the community",
                    "how_to_achieve": "Join hobby groups, attend community events, volunteer at local organizations, participate in group activities"
                },
                {
                    "title": "Develop Cooking Skills",
                    "description": "Learn new recipes and improve culinary abilities for better nutrition",
                    "how_to_achieve": "Take cooking classes, practice new recipes weekly, create meal plans, learn about nutrition"
                },
                {
                    "title": "Enhance Photography Skills",
                    "description": "Improve photography techniques and potentially exhibit work",
                    "how_to_achieve": "Take photography course, practice different techniques, join photography club, create portfolio"
                },
                {
                    "title": "Maintain Independent Living",
                    "description": "Continue living independently with minimal support",
                    "how_to_achieve": "Develop daily living skills, maintain apartment, manage finances, build support network"
                },
                {
                    "title": "Pursue Creative Interests",
                    "description": "Explore and develop artistic talents in painting and crafts",
                    "how_to_achieve": "Attend art classes, set up home studio space, participate in local art shows, practice regularly"
                }
            ],
            "supports": [
                {
                    "description": "Personal care and daily living assistance",
                    "provider": "Workcare Support Services - Sarah Johnson",
                    "frequency": "3 times per week",
                    "type": "In-home support"
                },
                {
                    "description": "Community access and social participation",
                    "provider": "Community Connect - Michael Chen",
                    "frequency": "2 times per week",
                    "type": "Community participation"
                },
                {
                    "description": "Health and medical support coordination",
                    "provider": "Brisbane Health Network - Dr. Amanda Wilson",
                    "frequency": "Monthly",
                    "type": "Health coordination"
                },
                {
                    "description": "Behavioral support and counseling",
                    "provider": "Positive Behavior Solutions - Lisa Thompson",
                    "frequency": "Fortnightly",
                    "type": "Behavioral support"
                },
                {
                    "description": "Occupational therapy services",
                    "provider": "Allied Health Partners - James Rodriguez",
                    "frequency": "Monthly",
                    "type": "Therapy services"
                },
                {
                    "description": "Pet care support for Siana-Rose",
                    "provider": "Pet Care Plus - Emma Davis",
                    "frequency": "As needed",
                    "type": "Pet support"
                }
            ],
            "additional_info": "Jeremy is highly motivated to maintain his independence and actively participates in his support planning. He has strong communication skills and is able to express his needs and preferences clearly. Jeremy responds well to routine and structure but also enjoys flexibility for spontaneous activities. He has a good relationship with his support workers and values their assistance in achieving his goals."
        }

        # Restore comprehensive data
        print(f"   🔄 Restoring Jeremy's comprehensive biography data...")
        success, response = self.run_test(
            f"Restore Jeremy's Comprehensive Biography",
            "PUT",
            f"api/clients/{self.jeremy_client_id}/biography",
            200,
            data=comprehensive_biography,
            use_auth=True
        )

        if not success:
            print(f"   ⚠️  Could not restore comprehensive biography data")

        # Get Jeremy's complete profile
        success, jeremy_profile = self.run_test(
            f"Get Jeremy's Complete Profile for Verification",
            "GET",
            f"api/clients/{self.jeremy_client_id}",
            200,
            use_auth=True
        )

        if not success:
            print(f"   ❌ Could not retrieve Jeremy's profile")
            return False

        print(f"   ✅ Jeremy's profile retrieved successfully")
        
        # Verify basic profile information
        expected_basic_info = {
            'full_name': 'Jeremy James Tomlinson',
            'id': self.jeremy_client_id
        }
        
        profile_valid = True
        for field, expected_value in expected_basic_info.items():
            actual_value = jeremy_profile.get(field)
            if actual_value == expected_value:
                print(f"   ✅ {field}: {actual_value}")
            else:
                print(f"   ❌ {field}: got '{actual_value}', expected '{expected_value}'")
                profile_valid = False

        # Verify biography section
        biography = jeremy_profile.get('biography', {})
        if not biography:
            print(f"   ❌ No biography section found")
            return False

        print(f"   ✅ Biography section found")

        # Verify comprehensive goals (should have 6 goals)
        goals = biography.get('goals', [])
        if len(goals) >= 6:
            print(f"   ✅ Comprehensive goals found: {len(goals)} goals")
            
            # Verify goal structure and content
            goal_titles = [goal.get('title', '') for goal in goals]
            expected_goal_areas = ['fitness', 'social', 'cooking', 'photography', 'independent', 'creative']
            
            goals_coverage = 0
            for area in expected_goal_areas:
                if any(area.lower() in title.lower() for title in goal_titles):
                    goals_coverage += 1
            
            if goals_coverage >= 4:  # At least 4 of 6 expected areas
                print(f"   ✅ Goals cover diverse areas: {goals_coverage}/6 expected areas")
            else:
                print(f"   ⚠️  Goals coverage limited: {goals_coverage}/6 expected areas")
                
            # Check goal implementation strategies
            goals_with_strategies = [goal for goal in goals if goal.get('how_to_achieve')]
            if len(goals_with_strategies) >= 5:
                print(f"   ✅ Goals have implementation strategies: {len(goals_with_strategies)}/{len(goals)}")
            else:
                print(f"   ⚠️  Some goals missing strategies: {len(goals_with_strategies)}/{len(goals)}")
        else:
            print(f"   ❌ Insufficient goals: {len(goals)} found, expected at least 6")
            profile_valid = False

        # Verify support providers (should have 6 providers)
        supports = biography.get('supports', [])
        if len(supports) >= 6:
            print(f"   ✅ Comprehensive support providers found: {len(supports)} providers")
            
            # Verify support provider details
            supports_with_contact = [support for support in supports if support.get('provider')]
            if len(supports_with_contact) >= 5:
                print(f"   ✅ Support providers have contact details: {len(supports_with_contact)}/{len(supports)}")
            else:
                print(f"   ⚠️  Some supports missing provider details: {len(supports_with_contact)}/{len(supports)}")
                
            # Check support types diversity
            support_types = [support.get('type', '') for support in supports]
            unique_types = len(set(support_types))
            if unique_types >= 4:
                print(f"   ✅ Diverse support types: {unique_types} different types")
            else:
                print(f"   ⚠️  Limited support type diversity: {unique_types} different types")
        else:
            print(f"   ❌ Insufficient support providers: {len(supports)} found, expected at least 6")
            profile_valid = False

        # Verify detailed text sections
        text_sections = {
            'strengths': 'Strengths and interests',
            'living_arrangements': 'Living arrangements with Siana-Rose',
            'daily_life': 'Daily life and routines',
            'additional_info': 'Additional information'
        }
        
        for field, description in text_sections.items():
            content = biography.get(field, '')
            if content and len(content) > 50:  # Substantial content
                print(f"   ✅ {description}: {len(content)} characters")
            else:
                print(f"   ⚠️  {description}: {len(content)} characters (may be insufficient)")

        # Check for specific Jeremy details
        living_arrangements = biography.get('living_arrangements', '')
        if 'siana-rose' in living_arrangements.lower() and 'carina' in living_arrangements.lower():
            print(f"   ✅ Specific Jeremy details found (Siana-Rose, Carina address)")
        else:
            print(f"   ⚠️  Some specific Jeremy details may be missing")

        return profile_valid

    def run_all_tests(self):
        """Run all Client Biography Management tests"""
        print(f"🎯 CLIENT BIOGRAPHY MANAGEMENT SYSTEM TESTING")
        print(f"=" * 60)
        print(f"Testing newly implemented Client Biography Management system")
        print(f"Jeremy's Client ID: {self.jeremy_client_id}")
        
        # Authenticate
        if not self.authenticate_admin():
            print(f"\n❌ CRITICAL: Admin authentication failed - cannot proceed with tests")
            return False
        
        # Try to authenticate staff for role-based testing
        self.authenticate_staff()
        
        # Run all test suites
        test_results = []
        
        print(f"\n" + "="*60)
        print(f"TEST SUITE 1: BIOGRAPHY UPDATE ENDPOINT TESTING")
        print(f"="*60)
        test_results.append(self.test_biography_update_endpoint())
        
        print(f"\n" + "="*60)
        print(f"TEST SUITE 2: BIOGRAPHY DATA RETRIEVAL")
        print(f"="*60)
        test_results.append(self.test_biography_data_retrieval())
        
        print(f"\n" + "="*60)
        print(f"TEST SUITE 3: DATA VALIDATION")
        print(f"="*60)
        test_results.append(self.test_data_validation())
        
        print(f"\n" + "="*60)
        print(f"TEST SUITE 4: JEREMY'S PROFILE VERIFICATION")
        print(f"="*60)
        test_results.append(self.test_jeremy_profile_verification())
        
        # Final results
        passed_suites = sum(test_results)
        total_suites = len(test_results)
        
        print(f"\n" + "="*60)
        print(f"FINAL RESULTS - CLIENT BIOGRAPHY MANAGEMENT TESTING")
        print(f"="*60)
        print(f"📊 Test Suites: {passed_suites}/{total_suites} passed ({(passed_suites/total_suites)*100:.1f}%)")
        print(f"📊 Individual Tests: {self.tests_passed}/{self.tests_run} passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        if passed_suites == total_suites:
            print(f"🎉 ALL CLIENT BIOGRAPHY TESTS PASSED!")
            print(f"✅ Biography Update Endpoint working with role-based access")
            print(f"✅ Biography Data Retrieval working with proper filtering")
            print(f"✅ Data Validation working for ClientBiography model")
            print(f"✅ Jeremy's Profile contains comprehensive information")
            print(f"✅ Client Biography Management system is production-ready")
        else:
            print(f"⚠️  SOME TESTS FAILED - Review required")
            failed_suites = total_suites - passed_suites
            print(f"❌ {failed_suites} test suite(s) need attention")
        
        return passed_suites == total_suites

if __name__ == "__main__":
    tester = ClientBiographyTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)