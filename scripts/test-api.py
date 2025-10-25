#!/usr/bin/env python3
"""
Bwenge OS API Testing Script

This script tests the basic functionality of all Bwenge OS services.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Service URLs
SERVICES = {
    "api-gateway": "http://localhost:8000",
    "auth-service": "http://localhost:8001", 
    "ingest-service": "http://localhost:8002",
    "persona-service": "http://localhost:8003",
    "chat-service": "http://localhost:8004",
    "3d-service": "http://localhost:8005",
    "analytics-service": "http://localhost:8006",
    "payments-service": "http://localhost:8007"
}

def test_health_checks():
    """Test health endpoints for all services"""
    print("🏥 Testing health checks...")
    
    for service_name, base_url in SERVICES.items():
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: OK")
            else:
                print(f"❌ {service_name}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {service_name}: Connection failed - {e}")

def test_auth_flow():
    """Test authentication flow"""
    print("\n🔐 Testing authentication flow...")
    
    base_url = SERVICES["api-gateway"]
    
    # Test registration
    register_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123",
        "org_name": "Test Organization"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/register", json=register_data)
        if response.status_code == 200:
            print("✅ User registration: OK")
            tokens = response.json()
            access_token = tokens["access_token"]
            
            # Test getting user info
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{base_url}/users/me", headers=headers)
            if response.status_code == 200:
                print("✅ Get user info: OK")
                return access_token
            else:
                print(f"❌ Get user info: HTTP {response.status_code}")
        else:
            print(f"❌ User registration: HTTP {response.status_code}")
            # Try login instead
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            response = requests.post(f"{base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                print("✅ User login: OK")
                tokens = response.json()
                return tokens["access_token"]
            else:
                print(f"❌ User login: HTTP {response.status_code}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Auth flow failed: {e}")
    
    return None

def test_persona_creation(access_token: str):
    """Test persona creation"""
    print("\n🤖 Testing persona creation...")
    
    base_url = SERVICES["api-gateway"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    persona_data = {
        "name": "Test Teacher",
        "description": "A helpful AI teacher for testing",
        "tone": {"style": "friendly", "formality": "casual"},
        "rules": {"guidelines": ["Be helpful", "Stay on topic"]},
        "sample_prompts": ["Hello!", "How can I help you?"],
        "safety_rules": ["No inappropriate content"]
    }
    
    try:
        response = requests.post(f"{base_url}/personas", json=persona_data, headers=headers)
        if response.status_code == 200:
            print("✅ Persona creation: OK")
            persona = response.json()
            return persona["persona_id"]
        else:
            print(f"❌ Persona creation: HTTP {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Persona creation failed: {e}")
    
    return None

def test_ai_response(access_token: str, persona_id: str):
    """Test AI response generation"""
    print("\n🧠 Testing AI response...")
    
    base_url = SERVICES["api-gateway"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    ai_request = {
        "persona_id": persona_id,
        "session_id": "test-session-123",
        "user_message": "Hello, can you help me learn about Python programming?",
        "context": {}
    }
    
    try:
        response = requests.post(f"{base_url}/ai/respond", json=ai_request, headers=headers)
        if response.status_code == 200:
            print("✅ AI response: OK")
            ai_response = response.json()
            print(f"   Response: {ai_response['response_text'][:100]}...")
            return True
        else:
            print(f"❌ AI response: HTTP {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ AI response failed: {e}")
    
    return False

def test_3d_model(access_token: str, persona_id: str):
    """Test 3D model endpoint"""
    print("\n🎭 Testing 3D model endpoint...")
    
    base_url = SERVICES["api-gateway"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{base_url}/3d/persona/{persona_id}", headers=headers)
        if response.status_code == 200:
            print("✅ 3D model endpoint: OK")
            model_data = response.json()
            print(f"   Model URL: {model_data['model_url']}")
            return True
        else:
            print(f"❌ 3D model endpoint: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 3D model test failed: {e}")
    
    return False

def test_subscription_plans():
    """Test subscription plans endpoint"""
    print("\n💳 Testing subscription plans...")
    
    base_url = SERVICES["api-gateway"]
    
    try:
        response = requests.get(f"{base_url}/plans")
        if response.status_code == 200:
            print("✅ Subscription plans: OK")
            plans = response.json()
            print(f"   Available plans: {len(plans['plans'])}")
            return True
        else:
            print(f"❌ Subscription plans: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Subscription plans test failed: {e}")
    
    return False

def main():
    """Run all tests"""
    print("🧪 Bwenge OS API Test Suite")
    print("=" * 40)
    
    # Test health checks
    test_health_checks()
    
    # Test authentication
    access_token = test_auth_flow()
    if not access_token:
        print("\n❌ Cannot continue without valid access token")
        sys.exit(1)
    
    # Test persona creation
    persona_id = test_persona_creation(access_token)
    if not persona_id:
        print("\n❌ Cannot continue without valid persona")
        sys.exit(1)
    
    # Test AI response
    test_ai_response(access_token, persona_id)
    
    # Test 3D model
    test_3d_model(access_token, persona_id)
    
    # Test subscription plans
    test_subscription_plans()
    
    print("\n🎉 Test suite completed!")
    print("\n📝 Note: Some tests may fail if external services (OpenAI, Stripe) are not configured.")

if __name__ == "__main__":
    main()