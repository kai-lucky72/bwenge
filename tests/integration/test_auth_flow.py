import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
sys.path.append('/app')

from services.auth_service.app.main import app as auth_app
from services.api_gateway.app.main import app as gateway_app
from libs.common.database import get_db

class TestAuthenticationFlow:
    """Integration tests for authentication flow."""
    
    @pytest.fixture
    def auth_client(self, override_get_db):
        """Create test client for auth service."""
        auth_app.dependency_overrides[get_db] = override_get_db
        return TestClient(auth_app)
    
    @pytest.fixture
    def gateway_client(self, override_get_db):
        """Create test client for API gateway."""
        gateway_app.dependency_overrides[get_db] = override_get_db
        return TestClient(gateway_app)
    
    def test_user_registration_flow(self, auth_client):
        """Test complete user registration flow."""
        # Test user registration
        registration_data = {
            "name": "Integration Test User",
            "email": "integration@test.com",
            "password": "testpass123",
            "org_name": "Integration Test Org"
        }
        
        response = auth_client.post("/auth/register", json=registration_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_user_login_flow(self, auth_client, test_user):
        """Test user login flow."""
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        
        response = auth_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_token_refresh_flow(self, auth_client, test_user):
        """Test token refresh flow."""
        # First login to get tokens
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        
        login_response = auth_client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Test token refresh
        refresh_response = auth_client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
    
    def test_protected_endpoint_access(self, auth_client, test_user):
        """Test accessing protected endpoints with valid token."""
        # Login to get token
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        
        login_response = auth_client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Access protected endpoint
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = auth_client.get("/users/me", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == test_user.email
        assert user_data["name"] == test_user.name
    
    def test_invalid_token_rejection(self, auth_client):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = auth_client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_organization_invitation_flow(self, auth_client, test_user, test_organization):
        """Test organization invitation flow."""
        # Login as admin
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        
        login_response = auth_client.post("/auth/login", json=login_data)
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Invite new user
        invite_data = {
            "name": "Invited User",
            "email": "invited@test.com",
            "password": "invitedpass123"
        }
        
        response = auth_client.post(
            f"/orgs/{test_organization.org_id}/invite",
            json=invite_data,
            headers=headers
        )
        
        assert response.status_code == 200
        assert "user_id" in response.json()
    
    def test_gateway_auth_integration(self, gateway_client, test_user):
        """Test authentication through API gateway."""
        # Test login through gateway
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        
        response = gateway_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        
        # Test protected endpoint through gateway
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = gateway_client.get("/users/me", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == test_user.email