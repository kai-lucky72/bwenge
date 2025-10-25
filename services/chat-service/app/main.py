from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List
import redis
import httpx

# Add libs to path
sys.path.append('/app')
from libs.common.database import get_db, init_db
from libs.common.models import Conversation, Persona, User
from libs.common.schemas import ChatMessage, ChatSession

from .connection_manager import ConnectionManager
from .session_manager import SessionManager

app = FastAPI(
    title="Bwenge OS Chat Service",
    description="Real-time chat and messaging service",
    version="1.0.0"
)

# Initialize services
connection_manager = ConnectionManager()
session_manager = SessionManager()

# Redis client for session storage
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Persona service URL
PERSONA_SERVICE_URL = os.getenv("PERSONA_SERVICE_URL", "http://persona-service:8000")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chat-service"}

@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    persona_id: str = Query(...),
    session_id: str = Query(None),
    token: str = Query(...)
):
    """WebSocket endpoint for real-time chat"""
    
    # Verify token and get user info
    user_info = await verify_token(token)
    if not user_info:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Accept connection
    await connection_manager.connect(websocket, session_id, user_info["user_id"])
    
    try:
        # Load or create session
        session = await session_manager.get_or_create_session(
            session_id=session_id,
            persona_id=persona_id,
            user_id=user_info["user_id"]
        )
        
        # Send session info
        await websocket.send_text(json.dumps({
            "type": "session_info",
            "session_id": session_id,
            "persona_id": persona_id,
            "message_count": len(session.messages)
        }))
        
        # Send recent messages
        if session.messages:
            for message in session.messages[-10:]:  # Last 10 messages
                await websocket.send_text(json.dumps({
                    "type": "message",
                    "message": message.dict()
                }))
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "user_message":
                await handle_user_message(
                    websocket=websocket,
                    session_id=session_id,
                    persona_id=persona_id,
                    user_message=message_data["content"],
                    user_info=user_info
                )
            
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")

async def handle_user_message(
    websocket: WebSocket,
    session_id: str,
    persona_id: str,
    user_message: str,
    user_info: Dict
):
    """Handle incoming user message"""
    
    try:
        # Create user message
        user_msg = ChatMessage(
            sender="user",
            content=user_message,
            timestamp=datetime.utcnow()
        )
        
        # Add to session
        await session_manager.add_message(session_id, user_msg)
        
        # Send user message back (confirmation)
        await websocket.send_text(json.dumps({
            "type": "message",
            "message": user_msg.dict()
        }))
        
        # Send typing indicator
        await websocket.send_text(json.dumps({
            "type": "typing",
            "is_typing": True
        }))
        
        # Get AI response
        ai_response = await get_ai_response(
            persona_id=persona_id,
            user_message=user_message,
            session_id=session_id,
            user_info=user_info
        )
        
        # Stop typing indicator
        await websocket.send_text(json.dumps({
            "type": "typing",
            "is_typing": False
        }))
        
        # Create AI message
        ai_msg = ChatMessage(
            sender="assistant",
            content=ai_response["response_text"],
            timestamp=datetime.utcnow(),
            metadata={
                "citations": ai_response.get("citations", []),
                "animation_hint": ai_response.get("animation_hint"),
                "actions": ai_response.get("actions", [])
            }
        )
        
        # Add to session
        await session_manager.add_message(session_id, ai_msg)
        
        # Send AI response
        await websocket.send_text(json.dumps({
            "type": "message",
            "message": ai_msg.dict()
        }))
        
        # Send animation hint if present
        if ai_response.get("animation_hint"):
            await websocket.send_text(json.dumps({
                "type": "animation",
                "animation": ai_response["animation_hint"]
            }))
        
    except Exception as e:
        print(f"Error handling user message: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Sorry, I encountered an error processing your message."
        }))

async def get_ai_response(
    persona_id: str,
    user_message: str,
    session_id: str,
    user_info: Dict
) -> Dict:
    """Get AI response from persona service"""
    
    try:
        # Get conversation history for context
        session = await session_manager.get_session(session_id)
        conversation_history = []
        
        if session and session.messages:
            # Convert last few messages to conversation format
            for msg in session.messages[-5:]:  # Last 5 messages
                conversation_history.append({
                    "role": "user" if msg.sender == "user" else "assistant",
                    "content": msg.content
                })
        
        # Prepare request to persona service
        request_data = {
            "persona_id": persona_id,
            "session_id": session_id,
            "user_message": user_message,
            "context": {
                "conversation_history": conversation_history
            }
        }
        
        # Call persona service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PERSONA_SERVICE_URL}/ai/respond",
                json=request_data,
                headers={"Authorization": f"Bearer {user_info.get('token', '')}"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Persona service error: {response.status_code}")
                
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return {
            "response_text": "I apologize, but I'm having trouble processing your request right now. Please try again.",
            "citations": [],
            "animation_hint": "neutral",
            "actions": []
        }

async def verify_token(token: str) -> Dict:
    """Verify JWT token (simplified)"""
    # In production, this should properly verify the JWT
    # For now, return mock user info
    return {
        "user_id": "mock-user-id",
        "org_id": "mock-org-id",
        "token": token
    }

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0
):
    """Get messages for a session"""
    
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = session.messages[offset:offset + limit]
    return {
        "session_id": session_id,
        "messages": [msg.dict() for msg in messages],
        "total": len(session.messages)
    }

@app.post("/sessions/{session_id}/persist")
async def persist_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Persist session to database"""
    
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Check if conversation exists
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if conversation:
            # Update existing conversation
            conversation.messages = [msg.dict() for msg in session.messages]
            conversation.updated_at = datetime.utcnow()
        else:
            # Create new conversation
            conversation = Conversation(
                persona_id=session.persona_id,
                user_id=session.user_id,
                session_id=session_id,
                messages=[msg.dict() for msg in session.messages]
            )
            db.add(conversation)
        
        db.commit()
        return {"message": "Session persisted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist session: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)