#!/usr/bin/env python3
"""
Backend API Testing for Lily's Score MVP
Tests all required endpoints and functionality
"""

import requests
import sys
import json
from datetime import datetime

class LilyScoreAPITester:
    def __init__(self, base_url="https://creditscan-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            'test': name,
            'success': success,
            'details': details
        })

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy' and 'timestamp' in data:
                    self.log_test("Health Endpoint", True, f"Status: {data['status']}")
                    return True
                else:
                    self.log_test("Health Endpoint", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_test("Health Endpoint", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_synthetic_demo_endpoint(self):
        """Test /api/synthetic-demo endpoint"""
        try:
            response = requests.get(f"{self.api_url}/synthetic-demo", 
                                  params={'weekly_rent': 900}, 
                                  timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['success', 'final_score', 'tier', 'breakdown']
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test("Synthetic Demo Endpoint", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Validate score range
                score = data.get('final_score', 0)
                if not (0 <= score <= 100):
                    self.log_test("Synthetic Demo Endpoint", False, f"Invalid score: {score}")
                    return False
                
                # Validate tier
                valid_tiers = ['Premium', 'Standard', 'Watchlist', 'Reject']
                if data.get('tier') not in valid_tiers:
                    self.log_test("Synthetic Demo Endpoint", False, f"Invalid tier: {data.get('tier')}")
                    return False
                
                # Validate breakdown (should have 5 metrics)
                breakdown = data.get('breakdown', [])
                if len(breakdown) != 5:
                    self.log_test("Synthetic Demo Endpoint", False, f"Expected 5 metrics, got {len(breakdown)}")
                    return False
                
                self.log_test("Synthetic Demo Endpoint", True, 
                            f"Score: {score}, Tier: {data.get('tier')}, Metrics: {len(breakdown)}")
                return True
            else:
                self.log_test("Synthetic Demo Endpoint", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Synthetic Demo Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_test_cases_endpoint(self):
        """Test /api/test-cases endpoint"""
        try:
            response = requests.get(f"{self.api_url}/test-cases", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_test("Test Cases Endpoint", False, "Response should be a list")
                    return False
                
                if len(data) != 3:
                    self.log_test("Test Cases Endpoint", False, f"Expected 3 test cases, got {len(data)}")
                    return False
                
                # Validate each test case
                for i, test_case in enumerate(data):
                    required_fields = ['case', 'score', 'tier', 'expected_tier']
                    missing_fields = [field for field in required_fields if field not in test_case]
                    if missing_fields:
                        self.log_test("Test Cases Endpoint", False, 
                                    f"Test case {i+1} missing fields: {missing_fields}")
                        return False
                    
                    # Validate score range
                    score = test_case.get('score', 0)
                    if not (0 <= score <= 100):
                        self.log_test("Test Cases Endpoint", False, 
                                    f"Test case {i+1} invalid score: {score}")
                        return False
                
                self.log_test("Test Cases Endpoint", True, f"All 3 test cases valid")
                return True
            else:
                self.log_test("Test Cases Endpoint", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Test Cases Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_root_endpoint(self):
        """Test /api/ root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'Lily\'s Score' in data['message']:
                    self.log_test("Root API Endpoint", True, f"Message: {data['message']}")
                    return True
                else:
                    self.log_test("Root API Endpoint", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Root API Endpoint", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Root API Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_analyze_endpoint_validation(self):
        """Test /api/analyze endpoint validation (without file)"""
        try:
            # Test with missing file
            response = requests.post(f"{self.api_url}/analyze", 
                                   data={'weekly_rent': 900}, 
                                   timeout=10)
            
            if response.status_code == 422:  # Validation error expected
                self.log_test("Analyze Endpoint Validation", True, "Correctly rejects missing file")
                return True
            else:
                self.log_test("Analyze Endpoint Validation", False, 
                            f"Expected 422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Analyze Endpoint Validation", False, f"Request failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n🔍 Testing Lily's Score Backend API")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("=" * 60)
        
        # Test all endpoints
        self.test_health_endpoint()
        self.test_root_endpoint()
        self.test_synthetic_demo_endpoint()
        self.test_test_cases_endpoint()
        self.test_analyze_endpoint_validation()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} test(s) failed")
            return False

def main():
    """Main test runner"""
    tester = LilyScoreAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': tester.tests_run,
        'passed_tests': tester.tests_passed,
        'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        'test_details': tester.test_results
    }
    
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())