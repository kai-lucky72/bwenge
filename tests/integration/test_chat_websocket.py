import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import WebSocket
import sys
sys.path.append('/app')

from services.chat_service.app.main import app as chat_app
from libs.common.database import get_db

class TestChatWebSocket:
    """Integration tests for WebSocket chat functionality."""
    
    @pytest.fixture
    def chat_client(self, override_get_db, test_redis_client):
        """Create test client for chat service."""
        chat_app.dependency_overrides[get_db] = override_get_db
        return TestClient(chat_app)
    
    def test_websocket_connection(self, chat_client, test_persona, test_user):
        """Test WebSocket connection establishment."""
        from libs.common.auth import create_access_token
        
        # Create token for WebSocket auth
        token_data = {
            "sub": str(test_user.user_id),
            "email": test_user.email,
            "org_id": str(test_user.org_id),
            "role": test_user.role
        }
        access_token = create_access_token(token_data)
        
        # Test WebSocket connection
        with chat_client.websocket_connect(
            f"/ws/chat?persona_id={test_persona.persona_id}&session_id=test-session&token={access_token}"
        ) as websocket:
            # Should receive session info
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "session_info"
            assert message["persona_id"] == str(test_persona.persona_id)
            assert "session_id" in message
    
    def test_websocket_message_flow(self, chat_client, test_persona, test_user):
        """Test complete WebSocket message flow."""
        from libs.common.auth import create_access_token
        from unittest.mock import patch
        
        token_data = {
            "sub": str(test_user.user_id),
            "email": test_user.email,
            "org_id": str(test_user.org_id),
            "role": test_user.role
        }
        access_token = create_access_token(token_data)
        
        # Mock the AI response
        mock_ai_response = {
            "response_text": "Hello! I'm here to help you with mathematics.",
            "citations": [],
            "animation_hint": "greeting",
            "actions": []
        }
        
        with patch('services.chat_service.app.main.get_ai_response') as mock_get_ai:
            mock_get_ai.return_value = mock_ai_response
            
            with chat_client.websocket_connect(
                f"/ws/chat?persona_id={test_persona.persona_id}&session_id=test-ws-session&token={access_token}"
            ) as websocket:
                # Receive session info
                session_info = json.loads(websocket.receive_text())
                assert session_info["type"] == "session_info"
                
                # Send user message
                user_message = {
                    "type": "user_message",
                    "content": "Hello, can you help me with algebra?"
                }
                websocket.send_text(json.dumps(user_message))
                
                # Should receive user message confirmation
                user_msg_response = json.loads(websocket.receive_text())
                assert user_msg_response["type"] == "message"
                assert user_msg_response["message"]["sender"] == "user"
                assert user_msg_response["message"]["content"] == user_message["content"]
                
                # Should receive typing indicator
                typing_msg = json.loads(websocket.receive_text())
                assert typing_msg["type"] == "typing"
                assert typing_msg["is_typing"] is True
                
                # Should receive stop typing
                stop_typing_msg = json.loads(websocket.receive_text())
                assert stop_typing_msg["type"] == "typing"
                assert stop_typing_msg["is_typing"] is False
                
                # Should receive AI response
                ai_msg_response = json.loads(websocket.receive_text())
                assert ai_msg_response["type"] == "message"
                assert ai_msg_response["message"]["sender"] == "assistant"
                assert ai_msg_response["message"]["content"] == mock_ai_response["response_text"]
                
                # Should receive animation hint
                animation_msg = json.loads(websocket.receive_text())
                assert animation_msg["type"] == "animation"
                assert animation_msg["animation"] == "greeting"
    
    def test_websocket_invalid_token(self, chat_client, test_persona):
        """Test WebSocket connection with invalid token."""
        with pytest.raises(Exception):  # Should fail to connect
            with chat_client.websocket_connect(
                f"/ws/chat?persona_id={test_persona.persona_id}&session_id=test-session&token=invalid_token"
            ):
                pass
    
    def test_session_persistence(self, chat_client, test_persona, test_user):
        """Test that chat sessions are properly persisted."""
        from libs.common.auth import create_access_token
        
        token_data = {
            "sub": str(test_user.user_id),
            "email": test_user.email,
            "org_id": str(test_user.org_id),
            "role": test_user.role
        }
        access_token = create_access_token(token_data)
        
        session_id = "persistent-test-session"
        
        # First connection - send a message
        with chat_client.websocket_connect(
            f"/ws/chat?persona_id={test_persona.persona_id}&session_id={session_id}&token={access_token}"
        ) as websocket:
            # Skip session info
            websocket.receive_text()
            
            # Send message
            user_message = {
                "type": "user_message",
                "content": "Remember this message"
            }
            websocket.send_text(json.dumps(user_message))
            
            # Receive confirmations (skip for this test)
            websocket.receive_text()  # User message confirmation
            websocket.receive_text()  # Typing indicator
            websocket.receive_text()  # Stop typing
            websocket.receive_text()  # AI response
        
        # Second connection - should have message history
        with chat_client.websocket_connect(
            f"/ws/chat?persona_id={test_persona.persona_id}&session_id={session_id}&token={access_token}"
        ) as websocket:
            # Receive session info
            session_info = json.loads(websocket.receive_text())
            assert session_info["type"] == "session_info"
            assert session_info["message_count"] > 0  # Should have previous messages
    
    def test_session_messages_api(self, chat_client, test_persona, test_user, test_db_session):
        """Test session messages REST API."""
        from libs.common.models import Conversation
        from datetime import datetime
        
        # Create a conversation with messages
        conversation = Conversation(
            persona_id=test_persona.persona_id,
            user_id=test_user.user_id,
            session_id="api-test-session",
            messages=[
                {
                    "sender": "user",
                    "content": "Hello",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "sender": "assistant",
                    "content": "Hi there!",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        )
        test_db_session.add(conversation)
        test_db_session.commit()
        
        # Test getting messages
        response = chat_client.get(f"/sessions/api-test-session/messages")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "api-test-session"
        assert len(data["messages"]) == 2
        assert data["total"] == 2
    
    def test_session_persistence_api(self, chat_client, test_persona, test_user):
        """Test session persistence API endpoint."""
        from libs.common.auth import create_access_token
        
        token_data = {
            "sub": str(test_user.user_id),
            "email": test_user.email,
            "org_id": str(test_user.org_id),
            "role": test_user.role
        }
        access_token = create_access_token(token_data)
        
        session_id = "persist-api-test"
        
        # Create a session with messages via WebSocket
        with chat_client.websocket_connect(
            f"/ws/chat?persona_id={test_persona.persona_id}&session_id={session_id}&token={access_token}"
        ) as websocket:
            # Skip session info
            websocket.receive_text()
            
            # Send message
            user_message = {
                "type": "user_message",
                "content": "Test persistence"
            }
            websocket.send_text(json.dumps(user_message))
            
            # Skip responses
            for _ in range(4):  # User msg, typing, stop typing, AI response
                websocket.receive_text()
        
        # Test persistence API
        response = chat_client.post(f"/sessions/{session_id}/persist")
        assert response.status_code == 200
        assert "persisted successfully" in response.json()["message"]
    
    def test_websocket_error_handling(self, chat_client, test_persona, test_user):
        """Test WebSocket error handling."""
        from libs.common.auth import create_access_token
        from unittest.mock import patch
        
        token_data = {
            "sub": str(test_user.user_id),
            "email": test_user.email,
            "org_id": str(test_user.org_id),
            "role": test_user.role
        }
        access_token = create_access_token(token_data)
        
        # Mock AI service to raise an error
        with patch('services.chat_service.app.main.get_ai_response') as mock_get_ai:
            mock_get_ai.side_effect = Exception("AI service error")
            
            with chat_client.websocket_connect(
                f"/ws/chat?persona_id={test_persona.persona_id}&session_id=error-test&token={access_token}"
            ) as websocket:
                # Skip session info
                websocket.receive_text()
                
                # Send message that will cause error
                user_message = {
                    "type": "user_message",
                    "content": "This will cause an error"
                }
                websocket.send_text(json.dumps(user_message))
                
                # Should receive user message confirmation
                websocket.receive_text()
                
                # Should receive typing indicator
                websocket.receive_text()
                
                # Should receive error message
                error_response = json.loads(websocket.receive_text())
                assert error_response["type"] == "error"
                assert "error" in error_response["message"].lower()