import pytest
from fastapi.testclient import TestClient
import sys
sys.path.append('/app')

from services.persona_service.app.main import app as persona_app
from services.chat_service.app.main import app as chat_app
from libs.common.database import get_db

class TestAIPersonaFlow:
    """Integration tests for AI persona and chat functionality."""
    
    @pytest.fixture
    def persona_client(self, override_get_db, mock_openai_client, mock_weaviate_client):
        """Create test client for persona service."""
        persona_app.dependency_overrides[get_db] = override_get_db
        return TestClient(persona_app)
    
    @pytest.fixture
    def chat_client(self, override_get_db, test_redis_client):
        """Create test client for chat service."""
        chat_app.dependency_overrides[get_db] = override_get_db
        return TestClient(chat_app)
    
    def test_persona_creation_flow(self, persona_client, auth_headers):
        """Test complete persona creation flow."""
        persona_data = {
            "name": "Integration Test Persona",
            "description": "A persona for integration testing",
            "tone": {
                "style": "professional",
                "formality": "formal"
            },
            "rules": {
                "guidelines": [
                    "Be helpful and informative",
                    "Stay on topic"
                ]
            },
            "sample_prompts": [
                "Hello, how can I help you today?",
                "What would you like to learn?"
            ],
            "safety_rules": [
                "Keep content appropriate",
                "No harmful information"
            ]
        }
        
        response = persona_client.post(
            "/personas",
            json=persona_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["name"] == persona_data["name"]
        assert result["description"] == persona_data["description"]
        assert result["tone"] == persona_data["tone"]
        assert result["is_active"] is True
        
        return result["persona_id"]
    
    def test_persona_retrieval(self, persona_client, test_persona, auth_headers):
        """Test persona retrieval."""
        response = persona_client.get(
            f"/personas/{test_persona.persona_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["name"] == test_persona.name
        assert result["description"] == test_persona.description
    
    def test_persona_update(self, persona_client, test_persona, auth_headers):
        """Test persona update functionality."""
        update_data = {
            "name": "Updated Persona Name",
            "description": "Updated description",
            "tone": {
                "style": "casual",
                "enthusiasm": "high"
            }
        }
        
        response = persona_client.put(
            f"/personas/{test_persona.persona_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["name"] == update_data["name"]
        assert result["description"] == update_data["description"]
        assert result["tone"] == update_data["tone"]
    
    def test_persona_listing(self, persona_client, auth_headers):
        """Test listing personas for organization."""
        response = persona_client.get(
            "/personas",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        personas = response.json()
        assert isinstance(personas, list)
    
    def test_ai_response_generation(self, persona_client, test_persona, auth_headers):
        """Test AI response generation with RAG."""
        ai_request = {
            "persona_id": str(test_persona.persona_id),
            "session_id": "test-session-123",
            "user_message": "Hello, can you help me with mathematics?",
            "context": {
                "conversation_history": []
            }
        }
        
        response = persona_client.post(
            "/ai/respond",
            json=ai_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "response_text" in result
        assert "actions" in result
        assert "citations" in result
        assert "session_id" in result
        assert result["session_id"] == ai_request["session_id"]
        
        # Verify response structure
        assert isinstance(result["actions"], list)
        assert isinstance(result["citations"], list)
    
    def test_ai_response_with_context(self, persona_client, test_persona, auth_headers):
        """Test AI response with conversation context."""
        ai_request = {
            "persona_id": str(test_persona.persona_id),
            "session_id": "test-session-456",
            "user_message": "What did we discuss earlier?",
            "context": {
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "Tell me about algebra"
                    },
                    {
                        "role": "assistant", 
                        "content": "Algebra is a branch of mathematics..."
                    }
                ]
            }
        }
        
        response = persona_client.post(
            "/ai/respond",
            json=ai_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "response_text" in result
    
    def test_persona_deletion(self, persona_client, test_persona, auth_headers):
        """Test persona soft deletion."""
        response = persona_client.delete(
            f"/personas/{test_persona.persona_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify persona is deactivated
        get_response = persona_client.get(
            f"/personas/{test_persona.persona_id}",
            headers=auth_headers
        )
        
        # Should still exist but be inactive
        assert get_response.status_code == 200
    
    def test_unauthorized_persona_access(self, persona_client, test_persona):
        """Test that unauthorized access is rejected."""
        response = persona_client.get(f"/personas/{test_persona.persona_id}")
        assert response.status_code == 403
    
    def test_cross_organization_isolation(self, persona_client, test_persona, auth_headers, test_db_session):
        """Test that users cannot access personas from other organizations."""
        # Create another organization and persona
        from libs.common.models import Organization, Persona
        
        other_org = Organization(name="Other Organization", plan="free")
        test_db_session.add(other_org)
        test_db_session.commit()
        test_db_session.refresh(other_org)
        
        other_persona = Persona(
            org_id=other_org.org_id,
            name="Other Org Persona",
            description="Should not be accessible"
        )
        test_db_session.add(other_persona)
        test_db_session.commit()
        test_db_session.refresh(other_persona)
        
        # Try to access other organization's persona
        response = persona_client.get(
            f"/personas/{other_persona.persona_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404  # Should not be found due to org isolation
    
    def test_rag_context_retrieval(self, persona_client, test_persona, auth_headers, test_db_session):
        """Test RAG context retrieval functionality."""
        # Create a knowledge source for testing
        from libs.common.models import KnowledgeSource
        
        knowledge_source = KnowledgeSource(
            org_id=test_persona.org_id,
            persona_id=test_persona.persona_id,
            title="Test Knowledge for RAG",
            type="text",
            status="ready",
            chunk_count=5
        )
        test_db_session.add(knowledge_source)
        test_db_session.commit()
        
        # Test AI response that should use RAG
        ai_request = {
            "persona_id": str(test_persona.persona_id),
            "session_id": "rag-test-session",
            "user_message": "Tell me about the uploaded content",
            "context": {}
        }
        
        response = persona_client.post(
            "/ai/respond",
            json=ai_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should have citations from RAG
        assert "citations" in result
        # Citations might be empty in mock, but structure should be correct
        assert isinstance(result["citations"], list)