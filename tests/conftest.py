import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import redis
import weaviate
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

# Import your app modules
import sys
sys.path.append('/app')
from libs.common.database import Base, get_db
from libs.common.models import *

# Test database URL
TEST_DATABASE_URL = "postgresql://test:test@localhost:5433/test_bwenge"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for testing."""
    with PostgresContainer("postgres:15", 
                          username="test", 
                          password="test", 
                          dbname="test_bwenge",
                          port=5433) as postgres:
        yield postgres

@pytest.fixture(scope="session")
def redis_container():
    """Start Redis container for testing."""
    with RedisContainer("redis:7-alpine", port=6380) as redis_c:
        yield redis_c

@pytest.fixture(scope="session")
def test_db_engine(postgres_container):
    """Create test database engine."""
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db_session(test_db_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_redis_client(redis_container):
    """Create test Redis client."""
    client = redis.Redis.from_url(redis_container.get_connection_url())
    yield client
    client.flushall()

@pytest.fixture
def override_get_db(test_db_session):
    """Override database dependency for testing."""
    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    return _override_get_db

@pytest.fixture
def test_organization(test_db_session):
    """Create test organization."""
    from libs.common.models import Organization
    org = Organization(name="Test Organization", plan="free")
    test_db_session.add(org)
    test_db_session.commit()
    test_db_session.refresh(org)
    return org

@pytest.fixture
def test_user(test_db_session, test_organization):
    """Create test user."""
    from libs.common.models import User
    from libs.common.auth import hash_password
    
    user = User(
        org_id=test_organization.org_id,
        name="Test User",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        role="admin"
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user

@pytest.fixture
def test_persona(test_db_session, test_organization):
    """Create test persona."""
    from libs.common.models import Persona
    
    persona = Persona(
        org_id=test_organization.org_id,
        name="Test Persona",
        description="A test AI persona",
        tone={"style": "friendly"},
        rules={"guidelines": ["Be helpful"]},
        sample_prompts=["Hello!", "How can I help?"],
        safety_rules=["Keep it appropriate"]
    )
    test_db_session.add(persona)
    test_db_session.commit()
    test_db_session.refresh(persona)
    return persona

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    from libs.common.auth import create_access_token
    
    token_data = {
        "sub": str(test_user.user_id),
        "email": test_user.email,
        "org_id": str(test_user.org_id),
        "role": test_user.role
    }
    
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock OpenAI client for testing."""
    class MockOpenAIResponse:
        def __init__(self, text="Test AI response"):
            self.choices = [type('obj', (object,), {
                'message': type('obj', (object,), {'content': text})()
            })()]
    
    class MockEmbeddingResponse:
        def __init__(self):
            self.data = [type('obj', (object,), {
                'embedding': [0.1] * 1536  # Mock embedding vector
            })()]
    
    class MockOpenAIClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return MockOpenAIResponse()
        
        class embeddings:
            @staticmethod
            def create(**kwargs):
                return MockEmbeddingResponse()
    
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: MockOpenAIClient())
    return MockOpenAIClient()

@pytest.fixture
def mock_weaviate_client(monkeypatch):
    """Mock Weaviate client for testing."""
    class MockWeaviateClient:
        def __init__(self):
            self.schema = type('obj', (object,), {
                'get': lambda: {"classes": []},
                'create_class': lambda x: None
            })()
            self.data_object = type('obj', (object,), {
                'create': lambda **kwargs: None
            })()
            self.query = type('obj', (object,), {
                'get': lambda *args: type('obj', (object,), {
                    'with_near_vector': lambda x: type('obj', (object,), {
                        'with_where': lambda x: type('obj', (object,), {
                            'with_limit': lambda x: type('obj', (object,), {
                                'with_additional': lambda x: type('obj', (object,), {
                                    'do': lambda: {
                                        "data": {
                                            "Get": {
                                                "KnowledgeChunk": [
                                                    {
                                                        "text": "Test chunk",
                                                        "source_id": "test-source",
                                                        "chunk_id": "test-chunk",
                                                        "chunk_index": 0,
                                                        "_additional": {"distance": 0.1}
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                })()
                            })()
                        })()
                    })()
                })()
            })()
    
    monkeypatch.setattr("weaviate.Client", lambda **kwargs: MockWeaviateClient())
    return MockWeaviateClient()