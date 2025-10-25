from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Track user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        if session_id not in self.user_sessions[user_id]:
            self.user_sessions[user_id].append(session_id)
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        # Clean up user sessions
        for user_id, sessions in self.user_sessions.items():
            if session_id in sessions:
                sessions.remove(session_id)
                if not sessions:
                    del self.user_sessions[user_id]
                break
    
    async def send_personal_message(self, message: str, session_id: str):
        """Send message to specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(message)
    
    async def send_to_user(self, message: str, user_id: str):
        """Send message to all sessions of a user"""
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                await self.send_personal_message(message, session_id)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connections"""
        for websocket in self.active_connections.values():
            await websocket.send_text(message)
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.active_connections.keys())
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get active sessions for a user"""
        return self.user_sessions.get(user_id, [])
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active"""
        return session_id in self.active_connections