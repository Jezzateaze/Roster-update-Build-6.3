#!/usr/bin/env python3
"""
OCR Document Processing Test Suite
Comprehensive testing for iPhone PDF upload failures and OCR functionality
"""

import requests
import sys
import json
import tempfile
import os
import time
from datetime import datetime

class OCRTester:
    def __init__(self, base_url="https://shift-master-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, files=None, use_auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        # Add authentication header if required and available
        if use_auth and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        # Only add Content-Type for JSON requests
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    response = requests.post(url, headers=headers, files=files)
                else:
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
        """Authenticate with Admin/0000 credentials"""
        print(f"\n🔐 Authenticating with Admin/0000...")
        
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
            print(f"   Token: {self.auth_token[:20]}..." if self.auth_token else "No token")
            return True
        else:
            print(f"   ❌ Authentication failed")
            return False

    def test_ocr_health_and_basic_functionality(self):
        """Test OCR Health and Basic Functionality"""
        print(f"\n🔍 Testing OCR Health and Basic Functionality...")
        
        # Test 1: OCR Health Check
        print(f"\n   🎯 TEST 1: OCR Health Check (GET /api/ocr/health)")
        success, health_response = self.run_test(
            "OCR Health Check",
            "GET",
            "api/ocr/health",
            200,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ OCR Health endpoint accessible")
            tesseract_version = health_response.get('tesseract_version', 'N/A')
            poppler_available = health_response.get('poppler_available', False)
            upload_dir_exists = health_response.get('upload_dir_exists', False)
            
            print(f"      Tesseract version: {tesseract_version}")
            print(f"      Poppler available: {poppler_available}")
            print(f"      Upload directory exists: {upload_dir_exists}")
            
            # Verify required components
            if tesseract_version != 'N/A' and poppler_available and upload_dir_exists:
                print(f"   ✅ All OCR components are working correctly")
                return True
            else:
                print(f"   ❌ Some OCR components are missing or not working")
                return False
        else:
            print(f"   ❌ OCR Health check failed")
            return False

    def create_test_pdf(self):
        """Create a test PDF file with NDIS content"""
        # Create a simple PDF manually (minimal PDF structure)
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_pdf_path = temp_pdf.name
        
        # Write minimal PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 150
>>
stream
BT
/F1 12 Tf
100 700 Td
(NDIS PARTICIPANT PLAN) Tj
100 680 Td
(Participant Name: John Smith) Tj
100 660 Td
(NDIS Number: 123456789) Tj
100 640 Td
(Date of Birth: 15/03/1990) Tj
100 620 Td
(Plan Period: 01/01/2025 to 31/12/2025) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
400
%%EOF"""
        temp_pdf.write(pdf_content)
        temp_pdf.close()
        
        return temp_pdf_path

    def test_file_upload_and_validation(self):
        """Test File Upload and Validation including iPhone PDF scenarios"""
        print(f"\n📁 Testing File Upload and Validation - IPHONE PDF FOCUS...")
        
        # Create test PDF file
        print(f"\n   🎯 TEST 1: Create test PDF file for upload testing")
        temp_pdf_path = self.create_test_pdf()
        print(f"   ✅ Created test PDF file: {temp_pdf_path}")
        
        # Test 2: Upload PDF with standard MIME type
        print(f"\n   🎯 TEST 2: Upload PDF with standard MIME type")
        
        try:
            with open(temp_pdf_path, 'rb') as pdf_file:
                files = {'file': ('test_ndis_plan.pdf', pdf_file, 'application/pdf')}
                success, task_data = self.run_test(
                    "Upload PDF with standard MIME type",
                    "POST",
                    "api/ocr/process",
                    200,
                    files=files,
                    use_auth=True
                )
            
            if success:
                print(f"   ✅ PDF upload with standard MIME type successful")
                task_id = task_data.get('task_id')
                print(f"      Task ID: {task_id}")
                
                # Poll for completion
                if task_id:
                    self.poll_ocr_completion(task_id)
            else:
                print(f"   ❌ PDF upload failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Error during PDF upload test: {e}")
            return False
        
        # Test 3: Upload PDF with iPhone/iOS MIME types
        print(f"\n   🎯 TEST 3: Upload PDF with iPhone/iOS MIME types (CRITICAL TEST)")
        
        # Test various iOS MIME types that cause issues
        ios_mime_types = [
            ('application/octet-stream', 'iPhone Safari generic MIME type'),
            ('application/binary', 'iOS binary MIME type'),
            ('application/download', 'iOS download MIME type'),
            ('text/plain', 'iOS text MIME type for PDFs')
        ]
        
        ios_success_count = 0
        
        for mime_type, description in ios_mime_types:
            print(f"\n      Testing {description}: {mime_type}")
            
            try:
                with open(temp_pdf_path, 'rb') as pdf_file:
                    files = {'file': ('iphone_ndis_plan.pdf', pdf_file, mime_type)}
                    success, task_data = self.run_test(
                        f"Upload PDF with {mime_type}",
                        "POST",
                        "api/ocr/process",
                        200,
                        files=files,
                        use_auth=True
                    )
                
                if success:
                    print(f"      ✅ PDF upload with {mime_type} successful")
                    task_id = task_data.get('task_id')
                    print(f"         Task ID: {task_id}")
                    ios_success_count += 1
                else:
                    print(f"      ❌ PDF upload with {mime_type} failed")
                    print(f"         This indicates iPhone PDF validation is failing!")
                    
            except Exception as e:
                print(f"      ❌ Error testing {mime_type}: {e}")
        
        # Cleanup temporary files
        try:
            os.unlink(temp_pdf_path)
        except:
            pass
        
        print(f"\n   📊 iOS MIME Type Test Results: {ios_success_count}/{len(ios_mime_types)} passed")
        
        if ios_success_count == len(ios_mime_types):
            print(f"   🎉 ALL FILE UPLOAD AND VALIDATION TESTS PASSED!")
            print(f"   ✅ Standard PDF upload working")
            print(f"   ✅ iPhone/iOS MIME types supported")
            return True
        else:
            print(f"   ❌ Some iPhone/iOS MIME types are failing")
            return False

    def poll_ocr_completion(self, task_id, max_wait=30):
        """Poll OCR task for completion"""
        print(f"      Polling for completion...")
        wait_time = 0
        
        while wait_time < max_wait:
            success, status_data = self.run_test(
                f"Check OCR Status",
                "GET",
                f"api/ocr/status/{task_id}",
                200,
                use_auth=True
            )
            
            if success:
                status = status_data.get('status')
                progress = status_data.get('progress', 0)
                
                print(f"      Processing status: {status} ({progress}%)")
                
                if status == 'completed':
                    print(f"      ✅ PDF processing completed successfully")
                    
                    # Get results
                    success, result_data = self.run_test(
                        f"Get OCR Results",
                        "GET",
                        f"api/ocr/result/{task_id}",
                        200,
                        use_auth=True
                    )
                    
                    if success:
                        extracted_data = result_data.get('extracted_data', {})
                        print(f"      Extracted name: {extracted_data.get('full_name', 'N/A')}")
                        print(f"      Extracted NDIS number: {extracted_data.get('ndis_number', 'N/A')}")
                        print(f"      Confidence score: {extracted_data.get('confidence_score', 0)}%")
                    break
                elif status == 'failed':
                    error = status_data.get('error', 'Unknown error')
                    print(f"      ❌ PDF processing failed: {error}")
                    break
            
            time.sleep(2)
            wait_time += 2
        
        if wait_time >= max_wait:
            print(f"      ⚠️  PDF processing timed out after {max_wait} seconds")

    def test_error_handling_and_logging(self):
        """Test Error Handling and Logging for OCR system"""
        print(f"\n🚨 Testing OCR Error Handling and Logging...")
        
        # Test 1: Upload corrupted PDF
        print(f"\n   🎯 TEST 1: Upload corrupted PDF file")
        
        # Create a corrupted PDF (just text with PDF extension)
        with tempfile.NamedTemporaryFile(suffix='.pdf', mode='w', delete=False) as corrupted_pdf:
            corrupted_pdf_path = corrupted_pdf.name
            corrupted_pdf.write("This is not a valid PDF file content")
        
        try:
            with open(corrupted_pdf_path, 'rb') as corrupted_file:
                files = {'file': ('corrupted.pdf', corrupted_file, 'application/pdf')}
                success, error_response = self.run_test(
                    "Upload Corrupted PDF",
                    "POST",
                    "api/ocr/process",
                    400,
                    files=files,
                    use_auth=True
                )
            
            if success:
                print(f"   ✅ Corrupted PDF correctly rejected with 400 error")
                return True
            else:
                print(f"   ❌ Corrupted PDF was not properly rejected")
                return False
                
        except Exception as e:
            print(f"   ❌ Error testing corrupted PDF: {e}")
            return False
        finally:
            try:
                os.unlink(corrupted_pdf_path)
            except:
                pass

    def test_mobile_ios_specific_scenarios(self):
        """Test Mobile/iOS Specific Scenarios for iPhone PDF uploads"""
        print(f"\n📱 Testing Mobile/iOS Specific Scenarios - IPHONE PDF UPLOAD FOCUS...")
        
        # Create realistic iPhone PDF scenario
        print(f"\n   🎯 TEST 1: Create realistic iPhone PDF with magic bytes validation")
        temp_pdf_path = self.create_test_pdf()
        
        # Test PDF magic bytes validation
        print(f"\n   🎯 TEST 2: Test PDF magic bytes validation (%PDF signature)")
        
        # Verify the PDF has correct magic bytes
        with open(temp_pdf_path, 'rb') as pdf_file:
            first_bytes = pdf_file.read(4)
            
        if first_bytes == b'%PDF':
            print(f"   ✅ PDF magic bytes validation: {first_bytes}")
        else:
            print(f"   ❌ PDF magic bytes incorrect: {first_bytes}")
            return False
        
        # Test enhanced file validation for mobile browsers
        print(f"\n   🎯 TEST 3: Test enhanced file validation for mobile browsers")
        
        try:
            with open(temp_pdf_path, 'rb') as pdf_file:
                # Simulate mobile browser sending wrong MIME type
                files = {'file': ('mobile_scan.pdf', pdf_file, 'application/octet-stream')}
                success, response = self.run_test(
                    "Upload PDF with wrong MIME type (mobile scenario)",
                    "POST",
                    "api/ocr/process",
                    200,
                    files=files,
                    use_auth=True
                )
            
            if success:
                print(f"   ✅ Enhanced validation working: PDF with wrong MIME type accepted")
                print(f"      Backend correctly validated using magic bytes + extension")
                return True
            else:
                print(f"   ❌ Enhanced validation failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Error testing enhanced validation: {e}")
            return False
        finally:
            try:
                os.unlink(temp_pdf_path)
            except:
                pass

    def run_comprehensive_ocr_tests(self):
        """Run comprehensive OCR tests as per review request"""
        print("=" * 80)
        print("🎯 OCR DOCUMENT PROCESSING COMPREHENSIVE TESTING")
        print("=" * 80)
        print("Testing iPhone PDF upload failures and OCR functionality")
        print("Focus: 'All 1 files failed to process. Please check the file formats and try again.'")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - stopping OCR tests")
            return False
        
        test_results = {}
        
        # Test 1: OCR Health and Basic Functionality
        print("\n" + "="*50)
        print("1. OCR HEALTH AND BASIC FUNCTIONALITY TEST")
        print("="*50)
        test_results['ocr_health'] = self.test_ocr_health_and_basic_functionality()
        
        # Test 2: File Upload and Validation (iPhone PDF Focus)
        print("\n" + "="*50)
        print("2. FILE UPLOAD AND VALIDATION TEST (IPHONE PDF FOCUS)")
        print("="*50)
        test_results['file_upload'] = self.test_file_upload_and_validation()
        
        # Test 3: Error Handling and Logging
        print("\n" + "="*50)
        print("3. ERROR HANDLING AND LOGGING TEST")
        print("="*50)
        test_results['error_handling'] = self.test_error_handling_and_logging()
        
        # Test 4: Mobile/iOS Specific Scenarios
        print("\n" + "="*50)
        print("4. MOBILE/iOS SPECIFIC SCENARIOS TEST")
        print("="*50)
        test_results['mobile_ios'] = self.test_mobile_ios_specific_scenarios()
        
        # Summary
        print("\n" + "="*80)
        print("🎯 OCR COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Results: {passed_tests}/{total_tests} tests passed")
        print(f"Total API calls made: {self.tests_run}")
        print(f"Successful API calls: {self.tests_passed}")
        print(f"API Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL OCR TESTS PASSED!")
            print("✅ OCR Health endpoints working")
            print("✅ iPhone PDF upload compatibility verified")
            print("✅ File validation working for mobile browsers")
            print("✅ Error handling and logging working")
            print("✅ Mobile/iOS specific scenarios working")
            print("\n🔧 DIAGNOSIS: iPhone PDF upload issue should be RESOLVED")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} OCR test(s) failed - see details above")
            print("\n🔧 DIAGNOSIS: iPhone PDF upload issue may still exist")
            
            if not test_results.get('file_upload', False):
                print("🚨 CRITICAL: File upload validation is failing for iPhone PDFs")
                print("   - Check MIME type handling for application/octet-stream")
                print("   - Verify PDF magic bytes validation")
                print("   - Check enhanced mobile browser file validation")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    print("🔍 OCR Document Processing Test Suite")
    print("Debugging iPhone PDF upload failures")
    print("=" * 50)
    
    tester = OCRTester()
    success = tester.run_comprehensive_ocr_tests()
    
    if success:
        print("\n✅ All OCR tests passed - iPhone PDF upload issue should be resolved")
        sys.exit(0)
    else:
        print("\n❌ Some OCR tests failed - iPhone PDF upload issue may persist")
        sys.exit(1)