import pytest
from fastapi.testclient import TestClient

def test_user_registration(test_client, test_user_data):
    """Test user registration"""
    response = test_client.post("/auth/register", json=test_user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_user_login(test_client, test_user_data):
    """Test user login"""
    # First register
    test_client.post("/auth/register", json=test_user_data)
    
    # Then login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = test_client.post("/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_get_current_user(test_client, auth_headers):
    """Test getting current user info"""
    response = test_client.get("/users/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "name" in data

def test_invalid_login(test_client):
    """Test login with invalid credentials"""
    login_data = {
        "email": "invalid@example.com",
        "password": "wrongpassword"
    }
    response = test_client.post("/auth/login", json=login_data)
    
    assert response.status_code == 401

def test_unauthorized_access(test_client):
    """Test accessing protected endpoint without token"""
    response = test_client.get("/users/me")
    
    assert response.status_code == 401