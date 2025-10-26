import pytest
import tempfile
import json
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
sys.path.append('/app')

from services.api_gateway.app.main import app as gateway_app
from libs.common.database import get_db

class TestEndToEndFlow:
    """End-to-end integration tests covering complete user workflows."""
    
    @pytest.fixture
    def gateway_client(self, override_get_db, mock_openai_client, mock_weaviate_client, test_redis_client):
        """Create test client for API gateway with all dependencies mocked."""
        gateway_app.dependency_overrides[get_db] = override_get_db
        return TestClient(gateway_app)
    
    def test_complete_user_journey(self, gateway_client):
        """Test complete user journey from registration to AI interaction."""
        
        # Step 1: User Registration
        registration_data = {
            "name": "E2E Test User",
            "email": "e2e@test.com",
            "password": "testpass123",
            "org_name": "E2E Test Organization"
        }
        
        register_response = gateway_client.post("/auth/register", json=registration_data)
        assert register_response.status_code == 200
        
        tokens = register_response.json()
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Step 2: Create a Persona
        persona_data = {
            "name": "E2E Math Tutor",
            "description": "An AI tutor for mathematics",
            "tone": {"style": "friendly", "formality": "casual"},
            "rules": {"guidelines": ["Be encouraging", "Use examples"]},
            "sample_prompts": ["Hello! Ready to learn math?"],
            "safety_rules": ["Keep content educational"]
        }
        
        persona_response = gateway_client.post(
            "/personas",
            json=persona_data,
            headers=auth_headers
        )
        assert persona_response.status_code == 200
        
        persona = persona_response.json()
        persona_id = persona["persona_id"]
        
        # Step 3: Upload Knowledge Content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write("Algebra is a branch of mathematics dealing with symbols and rules for manipulating those symbols.")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                files = {'file': ('algebra_basics.txt', f, 'text/plain')}
                data = {
                    'persona_id': persona_id,
                    'title': 'Algebra Basics'
                }
                
                upload_response = gateway_client.post(
                    "/knowledge/upload",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
            
            assert upload_response.status_code == 200
            upload_result = upload_response.json()
            upload_id = upload_result["upload_id"]
            
            # Step 4: Check Upload Status
            status_response = gateway_client.get(
                f"/knowledge/{upload_id}/status",
                headers=auth_headers
            )
            assert status_response.status_code == 200
            
            # Step 5: Get AI Response
            ai_request = {
                "persona_id": persona_id,
                "session_id": "e2e-test-session",
                "user_message": "Can you explain what algebra is?",
                "context": {}
            }
            
            ai_response = gateway_client.post(
                "/ai/respond",
                json=ai_request,
                headers=auth_headers
            )
            assert ai_response.status_code == 200
            
            ai_result = ai_response.json()
            assert "response_text" in ai_result
            assert "citations" in ai_result
            assert ai_result["session_id"] == "e2e-test-session"
            
            # Step 6: Get User Profile
            profile_response = gateway_client.get("/users/me", headers=auth_headers)
            assert profile_response.status_code == 200
            
            profile = profile_response.json()
            assert profile["email"] == registration_data["email"]
            assert profile["name"] == registration_data["name"]
            
        finally:
            import os
            os.unlink(tmp_file_path)
    
    def test_multi_user_organization_flow(self, gateway_client):
        """Test multi-user organization workflow."""
        
        # Step 1: Admin creates organization
        admin_data = {
            "name": "Admin User",
            "email": "admin@multiuser.com",
            "password": "adminpass123",
            "org_name": "Multi-User Test Org"
        }
        
        admin_register = gateway_client.post("/auth/register", json=admin_data)
        assert admin_register.status_code == 200
        
        admin_tokens = admin_register.json()
        admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
        
        # Get admin profile to get org_id
        admin_profile = gateway_client.get("/users/me", headers=admin_headers)
        org_id = admin_profile.json()["org_id"]
        
        # Step 2: Admin creates persona
        persona_data = {
            "name": "Shared Tutor",
            "description": "A shared AI tutor for the organization",
            "tone": {"style": "professional"},
            "rules": {"guidelines": ["Be helpful to all users"]},
            "sample_prompts": ["Welcome to our learning platform!"],
            "safety_rules": ["Maintain professional standards"]
        }
        
        persona_response = gateway_client.post(
            "/personas",
            json=persona_data,
            headers=admin_headers
        )
        assert persona_response.status_code == 200
        persona_id = persona_response.json()["persona_id"]
        
        # Step 3: Admin invites another user
        invite_data = {
            "name": "Invited User",
            "email": "invited@multiuser.com",
            "password": "invitedpass123"
        }
        
        invite_response = gateway_client.post(
            f"/orgs/{org_id}/invite",
            json=invite_data,
            headers=admin_headers
        )
        assert invite_response.status_code == 200
        
        # Step 4: Invited user logs in
        login_data = {
            "email": "invited@multiuser.com",
            "password": "invitedpass123"
        }
        
        login_response = gateway_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        user_tokens = login_response.json()
        user_headers = {"Authorization": f"Bearer {user_tokens['access_token']}"}
        
        # Step 5: Invited user can access shared persona
        persona_get_response = gateway_client.get(
            f"/personas/{persona_id}",
            headers=user_headers
        )
        assert persona_get_response.status_code == 200
        
        # Step 6: Both users can interact with the same persona
        for headers, session_suffix in [(admin_headers, "admin"), (user_headers, "user")]:
            ai_request = {
                "persona_id": persona_id,
                "session_id": f"multiuser-session-{session_suffix}",
                "user_message": "Hello, I'm ready to learn!",
                "context": {}
            }
            
            ai_response = gateway_client.post(
                "/ai/respond",
                json=ai_request,
                headers=headers
            )
            assert ai_response.status_code == 200
    
    def test_subscription_and_quota_flow(self, gateway_client):
        """Test subscription and usage quota workflow."""
        
        # Step 1: Register user
        user_data = {
            "name": "Quota Test User",
            "email": "quota@test.com",
            "password": "quotapass123",
            "org_name": "Quota Test Org"
        }
        
        register_response = gateway_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        tokens = register_response.json()
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Step 2: Check current subscription (should be free)
        subscription_response = gateway_client.get(
            "/subscriptions/current",
            headers=auth_headers
        )
        assert subscription_response.status_code == 200
        
        subscription = subscription_response.json()
        assert subscription["plan"] == "free" or subscription["plan"] == "none"
        
        # Step 3: Create free subscription
        free_subscription_data = {
            "plan_name": "free",
            "success_url": "http://localhost:3000/success",
            "cancel_url": "http://localhost:3000/cancel"
        }
        
        create_sub_response = gateway_client.post(
            "/payments/subscribe",
            json=free_subscription_data,
            headers=auth_headers
        )
        assert create_sub_response.status_code == 200
        
        # Step 4: Check available plans
        plans_response = gateway_client.get("/plans")
        assert plans_response.status_code == 200
        
        plans = plans_response.json()
        assert "plans" in plans
        assert len(plans["plans"]) > 0
    
    def test_analytics_and_reporting_flow(self, gateway_client):
        """Test analytics and reporting workflow."""
        
        # Step 1: Register user and create persona
        user_data = {
            "name": "Analytics User",
            "email": "analytics@test.com",
            "password": "analyticspass123",
            "org_name": "Analytics Test Org"
        }
        
        register_response = gateway_client.post("/auth/register", json=user_data)
        tokens = register_response.json()
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Get org_id
        profile_response = gateway_client.get("/users/me", headers=auth_headers)
        org_id = profile_response.json()["org_id"]
        
        # Step 2: Create persona for interactions
        persona_data = {
            "name": "Analytics Persona",
            "description": "For testing analytics",
            "tone": {},
            "rules": {},
            "sample_prompts": [],
            "safety_rules": []
        }
        
        persona_response = gateway_client.post(
            "/personas",
            json=persona_data,
            headers=auth_headers
        )
        persona_id = persona_response.json()["persona_id"]
        
        # Step 3: Generate some interactions
        for i in range(3):
            ai_request = {
                "persona_id": persona_id,
                "session_id": f"analytics-session-{i}",
                "user_message": f"Test message {i}",
                "context": {}
            }
            
            gateway_client.post(
                "/ai/respond",
                json=ai_request,
                headers=auth_headers
            )
        
        # Step 4: Get weekly report
        weekly_report_response = gateway_client.get(
            f"/orgs/{org_id}/reports/weekly",
            headers=auth_headers
        )
        assert weekly_report_response.status_code == 200
        
        report = weekly_report_response.json()
        assert "total_messages" in report
        assert "active_users" in report
        assert "top_personas" in report
        
        # Step 5: Get student progress (using same user as student)
        user_id = profile_response.json()["user_id"]
        progress_response = gateway_client.get(
            f"/orgs/{org_id}/students/{user_id}/progress",
            headers=auth_headers
        )
        assert progress_response.status_code == 200
        
        progress = progress_response.json()
        assert "learning_metrics" in progress
        assert "daily_activity" in progress
    
    def test_3d_model_integration_flow(self, gateway_client):
        """Test 3D model integration workflow."""
        
        # Step 1: Register and create persona
        user_data = {
            "name": "3D Test User",
            "email": "3d@test.com",
            "password": "3dpass123",
            "org_name": "3D Test Org"
        }
        
        register_response = gateway_client.post("/auth/register", json=user_data)
        tokens = register_response.json()
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        persona_data = {
            "name": "3D Avatar Persona",
            "description": "Persona with 3D avatar",
            "tone": {},
            "rules": {},
            "sample_prompts": [],
            "safety_rules": []
        }
        
        persona_response = gateway_client.post(
            "/personas",
            json=persona_data,
            headers=auth_headers
        )
        persona_id = persona_response.json()["persona_id"]
        
        # Step 2: Get 3D model (should return default)
        model_response = gateway_client.get(
            f"/3d/persona/{persona_id}",
            headers=auth_headers
        )
        assert model_response.status_code == 200
        
        model_data = model_response.json()
        assert "model_url" in model_data
        assert "animations" in model_data
        assert "scale" in model_data
        
        # Step 3: Get available animations
        animations_response = gateway_client.get("/3d/animations")
        assert animations_response.status_code == 200
        
        animations = animations_response.json()
        assert "animations" in animations
        assert isinstance(animations["animations"], list)
        assert len(animations["animations"]) > 0
    
    def test_error_handling_and_recovery(self, gateway_client):
        """Test error handling and recovery scenarios."""
        
        # Test 1: Invalid login
        invalid_login = {
            "email": "nonexistent@test.com",
            "password": "wrongpass"
        }
        
        login_response = gateway_client.post("/auth/login", json=invalid_login)
        assert login_response.status_code == 401
        
        # Test 2: Access without authentication
        unauth_response = gateway_client.get("/users/me")
        assert unauth_response.status_code == 403
        
        # Test 3: Access non-existent resource
        fake_token = "Bearer fake.token.here"
        headers = {"Authorization": fake_token}
        
        fake_persona_response = gateway_client.get(
            "/personas/00000000-0000-0000-0000-000000000000",
            headers=headers
        )
        assert fake_persona_response.status_code == 401  # Invalid token
        
        # Test 4: Invalid file upload
        user_data = {
            "name": "Error Test User",
            "email": "error@test.com",
            "password": "errorpass123"
        }
        
        register_response = gateway_client.post("/auth/register", json=user_data)
        tokens = register_response.json()
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Try to upload without persona_id
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp_file:
            tmp_file.write(b'test content')
            tmp_file.seek(0)
            
            files = {'file': ('test.txt', tmp_file, 'text/plain')}
            # Missing persona_id should cause error
            
            upload_response = gateway_client.post(
                "/knowledge/upload",
                files=files,
                headers=auth_headers
            )
            assert upload_response.status_code == 422  # Validation error