#!/usr/bin/env python3
"""
Smoke tests for Bwenge OS deployment validation.

This script runs basic health checks and functionality tests
to validate that a deployment is working correctly.
"""

import argparse
import requests

import json
import time
import sys
from typing import Dict, List, Optional

class SmokeTestRunner:
    """Runs smoke tests against Bwenge OS deployment."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # Test results
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def run_test(self, name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and record results."""
        print(f"Running test: {name}...")
        
        try:
            start_time = time.time()
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            if result:
                print(f"✅ {name} - PASSED ({duration:.2f}s)")
                self.passed += 1
                self.results.append({
                    "name": name,
                    "status": "PASSED",
                    "duration": duration,
                    "error": None
                })
                return True
            else:
                print(f"❌ {name} - FAILED ({duration:.2f}s)")
                self.failed += 1
                self.results.append({
                    "name": name,
                    "status": "FAILED", 
                    "duration": duration,
                    "error": "Test returned False"
                })
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {name} - ERROR ({duration:.2f}s): {str(e)}")
            self.failed += 1
            self.results.append({
                "name": name,
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            })
            return False
    
    def test_health_check(self) -> bool:
        """Test basic health check endpoint."""
        response = self.session.get(f"{self.base_url}/health")
        return response.status_code == 200 and response.json().get("status") == "healthy"
    
    def test_user_registration(self) -> bool:
        """Test user registration flow."""
        test_user = {
            "name": "Smoke Test User",
            "email": f"smoketest+{int(time.time())}@example.com",
            "password": "smoketest123",
            "org_name": "Smoke Test Org"
        }
        
        response = self.session.post(f"{self.base_url}/auth/register", json=test_user)
        if response.status_code != 200:
            return False
        
        data = response.json()
        return "access_token" in data and "refresh_token" in data
    
    def test_authentication_flow(self) -> bool:
        """Test complete authentication flow."""
        # Register user
        test_user = {
            "name": "Auth Test User",
            "email": f"authtest+{int(time.time())}@example.com", 
            "password": "authtest123"
        }
        
        register_response = self.session.post(f"{self.base_url}/auth/register", json=test_user)
        if register_response.status_code != 200:
            return False
        
        tokens = register_response.json()
        
        # Test login
        login_response = self.session.post(f"{self.base_url}/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        
        if login_response.status_code != 200:
            return False
        
        # Test protected endpoint
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        profile_response = self.session.get(f"{self.base_url}/users/me", headers=headers)
        
        return profile_response.status_code == 200
    
    def test_persona_creation(self) -> bool:
        """Test persona creation."""
        # First register and login
        test_user = {
            "name": "Persona Test User",
            "email": f"personatest+{int(time.time())}@example.com",
            "password": "personatest123"
        }
        
        register_response = self.session.post(f"{self.base_url}/auth/register", json=test_user)
        if register_response.status_code != 200:
            return False
        
        tokens = register_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Create persona
        persona_data = {
            "name": "Smoke Test Persona",
            "description": "A test persona for smoke testing",
            "tone": {"style": "friendly"},
            "rules": {"guidelines": ["Be helpful"]},
            "sample_prompts": ["Hello!"],
            "safety_rules": ["Keep it appropriate"]
        }
        
        response = self.session.post(f"{self.base_url}/personas", json=persona_data, headers=headers)
        return response.status_code == 200
    
    def test_ai_response(self) -> bool:
        """Test AI response generation."""
        # Setup user and persona
        test_user = {
            "name": "AI Test User",
            "email": f"aitest+{int(time.time())}@example.com",
            "password": "aitest123"
        }
        
        register_response = self.session.post(f"{self.base_url}/auth/register", json=test_user)
        if register_response.status_code != 200:
            return False
        
        tokens = register_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Create persona
        persona_data = {
            "name": "AI Test Persona",
            "description": "Test persona for AI responses",
            "tone": {},
            "rules": {},
            "sample_prompts": [],
            "safety_rules": []
        }
        
        persona_response = self.session.post(f"{self.base_url}/personas", json=persona_data, headers=headers)
        if persona_response.status_code != 200:
            return False
        
        persona_id = persona_response.json()["persona_id"]
        
        # Test AI response
        ai_request = {
            "persona_id": persona_id,
            "session_id": "smoke_test_session",
            "user_message": "Hello, this is a test message",
            "context": {}
        }
        
        ai_response = self.session.post(f"{self.base_url}/ai/respond", json=ai_request, headers=headers)
        if ai_response.status_code != 200:
            return False
        
        data = ai_response.json()
        return "response_text" in data and "citations" in data
    
    def test_3d_model_endpoint(self) -> bool:
        """Test 3D model endpoint."""
        # Setup user and persona
        test_user = {
            "name": "3D Test User",
            "email": f"3dtest+{int(time.time())}@example.com",
            "password": "3dtest123"
        }
        
        register_response = self.session.post(f"{self.base_url}/auth/register", json=test_user)
        if register_response.status_code != 200:
            return False
        
        tokens = register_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Create persona
        persona_data = {
            "name": "3D Test Persona",
            "description": "Test persona for 3D model",
            "tone": {},
            "rules": {},
            "sample_prompts": [],
            "safety_rules": []
        }
        
        persona_response = self.session.post(f"{self.base_url}/personas", json=persona_data, headers=headers)
        if persona_response.status_code != 200:
            return False
        
        persona_id = persona_response.json()["persona_id"]
        
        # Test 3D model endpoint
        model_response = self.session.get(f"{self.base_url}/3d/persona/{persona_id}", headers=headers)
        if model_response.status_code != 200:
            return False
        
        data = model_response.json()
        return "model_url" in data and "animations" in data
    
    def test_analytics_endpoint(self) -> bool:
        """Test analytics endpoint."""
        # Setup user
        test_user = {
            "name": "Analytics Test User",
            "email": f"analyticstest+{int(time.time())}@example.com",
            "password": "analyticstest123"
        }
        
        register_response = self.session.post(f"{self.base_url}/auth/register", json=test_user)
        if register_response.status_code != 200:
            return False
        
        tokens = register_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Get user profile to get org_id
        profile_response = self.session.get(f"{self.base_url}/users/me", headers=headers)
        if profile_response.status_code != 200:
            return False
        
        org_id = profile_response.json()["org_id"]
        
        # Test weekly report endpoint
        report_response = self.session.get(f"{self.base_url}/orgs/{org_id}/reports/weekly", headers=headers)
        if report_response.status_code != 200:
            return False
        
        data = report_response.json()
        return "total_messages" in data and "active_users" in data
    
    def test_subscription_endpoint(self) -> bool:
        """Test subscription endpoint."""
        # Setup user
        test_user = {
            "name": "Subscription Test User",
            "email": f"subtest+{int(time.time())}@example.com",
            "password": "subtest123"
        }
        
        register_response = self.session.post(f"{self.base_url}/auth/register", json=test_user)
        if register_response.status_code != 200:
            return False
        
        tokens = register_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Test current subscription endpoint
        sub_response = self.session.get(f"{self.base_url}/subscriptions/current", headers=headers)
        return sub_response.status_code == 200
    
    def test_rate_limiting(self) -> bool:
        """Test that rate limiting is working."""
        # Make multiple rapid requests to a rate-limited endpoint
        for i in range(15):  # Exceed typical rate limit
            response = self.session.post(f"{self.base_url}/auth/register", json={
                "name": "Rate Test",
                "email": f"ratetest{i}@example.com",
                "password": "ratetest123"
            })
            
            if response.status_code == 429:  # Rate limited
                return True
        
        # If we never hit rate limit, that might be a problem
        return False
    
    def run_basic_tests(self) -> bool:
        """Run basic smoke tests."""
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("Authentication Flow", self.test_authentication_flow),
            ("Rate Limiting", self.test_rate_limiting),
        ]
        
        all_passed = True
        for name, test_func in tests:
            if not self.run_test(name, test_func):
                all_passed = False
        
        return all_passed
    
    def run_comprehensive_tests(self) -> bool:
        """Run comprehensive smoke tests."""
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("Authentication Flow", self.test_authentication_flow),
            ("Persona Creation", self.test_persona_creation),
            ("AI Response", self.test_ai_response),
            ("3D Model Endpoint", self.test_3d_model_endpoint),
            ("Analytics Endpoint", self.test_analytics_endpoint),
            ("Subscription Endpoint", self.test_subscription_endpoint),
            ("Rate Limiting", self.test_rate_limiting),
        ]
        
        all_passed = True
        for name, test_func in tests:
            if not self.run_test(name, test_func):
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*50)
        print("SMOKE TEST SUMMARY")
        print("="*50)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if result["status"] != "PASSED":
                    print(f"  - {result['name']}: {result['error']}")
        
        print("="*50)
    
    def save_results(self, filename: str):
        """Save test results to JSON file."""
        summary = {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "total_tests": len(self.results),
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": (self.passed / len(self.results) * 100) if self.results else 0,
            "results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Run smoke tests for Bwenge OS")
    parser.add_argument("--url", required=True, help="Base URL of the deployment")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive tests")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    runner = SmokeTestRunner(args.url, args.timeout)
    
    print(f"Running smoke tests against: {args.url}")
    print("="*50)
    
    if args.comprehensive:
        success = runner.run_comprehensive_tests()
    else:
        success = runner.run_basic_tests()
    
    runner.print_summary()
    
    if args.output:
        runner.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()