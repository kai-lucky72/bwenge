import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import tempfile
import shutil

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    from libs.common.database import Base
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file uploads"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123",
        "org_name": "Test Organization"
    }

@pytest.fixture
def test_persona_data():
    """Test persona data"""
    return {
        "name": "Test Teacher",
        "description": "A helpful AI teacher for testing",
        "tone": {"style": "friendly", "formality": "casual"},
        "rules": {"guidelines": ["Be helpful", "Stay on topic"]},
        "sample_prompts": ["Hello!", "How can I help you?"],
        "safety_rules": ["No inappropriate content"]
    }

@pytest.fixture
def auth_headers(test_client, test_user_data):
    """Get authentication headers for testing"""
    # Register user
    response = test_client.post("/auth/register", json=test_user_data)
    if response.status_code == 200:
        tokens = response.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Try login if registration fails
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = test_client.post("/auth/login", json=login_data)
    if response.status_code == 200:
        tokens = response.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}
    
    raise Exception("Failed to authenticate test user")