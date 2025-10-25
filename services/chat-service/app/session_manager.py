import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os

import sys
sys.path.append('/app')
from libs.common.schemas import ChatSession, ChatMessage

class SessionManager:
    """Manages chat sessions in Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True
        )
        self.session_ttl = 24 * 60 * 60  # 24 hours
    
    async def get_or_create_session(
        self,
        session_id: str,
        persona_id: str,
        user_id: str
    ) -> ChatSession:
        """Get existing session or create new one"""
        
        session = await self.get_session(session_id)
        if session:
            return session
        
        # Create new session
        session = ChatSession(
            session_id=session_id,
            persona_id=uuid.UUID(persona_id),
            user_id=uuid.UUID(user_id),
            messages=[],
            created_at=datetime.utcnow()
        )
        
        await self.save_session(session)
        return session
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session from Redis"""
        try:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                
                # Convert message data back to ChatMessage objects
                messages = []
                for msg_data in data.get("messages", []):
                    messages.append(ChatMessage(**msg_data))
                
                return ChatSession(
                    session_id=data["session_id"],
                    persona_id=uuid.UUID(data["persona_id"]),
                    user_id=uuid.UUID(data["user_id"]),
                    messages=messages,
                    created_at=datetime.fromisoformat(data["created_at"])
                )
            return None
        except Exception as e:
            print(f"Error getting session {session_id}: {e}")
            return None
    
    async def save_session(self, session: ChatSession):
        """Save session to Redis"""
        try:
            # Convert to serializable format
            session_data = {
                "session_id": session.session_id,
                "persona_id": str(session.persona_id),
                "user_id": str(session.user_id),
                "messages": [msg.dict() for msg in session.messages],
                "created_at": session.created_at.isoformat()
            }
            
            self.redis_client.setex(
                f"session:{session.session_id}",
                self.session_ttl,
                json.dumps(session_data, default=str)
            )
        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
    
    async def add_message(self, session_id: str, message: ChatMessage):
        """Add message to session"""
        session = await self.get_session(session_id)
        if session:
            session.messages.append(message)
            await self.save_session(session)
    
    async def delete_session(self, session_id: str):
        """Delete session from Redis"""
        try:
            self.redis_client.delete(f"session:{session_id}")
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
    
    async def get_user_sessions(self, user_id: str) -> list:
        """Get all sessions for a user"""
        try:
            # This is a simple implementation - in production you might want
            # to maintain a separate index of user sessions
            pattern = "session:*"
            sessions = []
            
            for key in self.redis_client.scan_iter(match=pattern):
                session_data = self.redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    if data.get("user_id") == user_id:
                        sessions.append({
                            "session_id": data["session_id"],
                            "persona_id": data["persona_id"],
                            "created_at": data["created_at"],
                            "message_count": len(data.get("messages", []))
                        })
            
            return sessions
        except Exception as e:
            print(f"Error getting user sessions for {user_id}: {e}")
            return []
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (called by background task)"""
        try:
            # Redis TTL handles expiration automatically, but we can add
            # additional cleanup logic here if needed
            pass
        except Exception as e:
            print(f"Error during session cleanup: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            pattern = "session:*"
            total_sessions = 0
            total_messages = 0
            
            for key in self.redis_client.scan_iter(match=pattern):
                total_sessions += 1
                session_data = self.redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    total_messages += len(data.get("messages", []))
            
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "average_messages_per_session": total_messages / max(total_sessions, 1)
            }
        except Exception as e:
            print(f"Error getting session stats: {e}")
            return {"error": str(e)}