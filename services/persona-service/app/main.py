from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import sys
import os

# Add libs to path
sys.path.append('/app')
from libs.common.database import get_db, init_db
from libs.common.models import Persona
from libs.common.schemas import PersonaCreate, PersonaUpdate, PersonaResponse, AIRequest, AIResponse
from libs.common.auth import get_current_user

from .llm_orchestrator import LLMOrchestrator
from .rag_engine import RAGEngine

app = FastAPI(
    title="Bwenge OS Persona Service",
    description="Persona management and AI response service",
    version="1.0.0"
)

# Initialize services
llm_orchestrator = LLMOrchestrator()
rag_engine = RAGEngine()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "persona-service"}

@app.post("/personas", response_model=PersonaResponse)
async def create_persona(
    persona_data: PersonaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new persona"""
    
    persona = Persona(
        org_id=current_user["org_id"],
        name=persona_data.name,
        description=persona_data.description,
        tone=persona_data.tone,
        rules=persona_data.rules,
        sample_prompts=persona_data.sample_prompts,
        safety_rules=persona_data.safety_rules
    )
    
    db.add(persona)
    db.commit()
    db.refresh(persona)
    
    return PersonaResponse(
        persona_id=persona.persona_id,
        org_id=persona.org_id,
        name=persona.name,
        description=persona.description,
        tone=persona.tone,
        rules=persona.rules,
        sample_prompts=persona.sample_prompts,
        safety_rules=persona.safety_rules,
        is_active=persona.is_active,
        created_at=persona.created_at
    )

@app.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get persona details"""
    
    persona = db.query(Persona).filter(
        Persona.persona_id == persona_id,
        Persona.org_id == current_user["org_id"]
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    return PersonaResponse(
        persona_id=persona.persona_id,
        org_id=persona.org_id,
        name=persona.name,
        description=persona.description,
        tone=persona.tone,
        rules=persona.rules,
        sample_prompts=persona.sample_prompts,
        safety_rules=persona.safety_rules,
        is_active=persona.is_active,
        created_at=persona.created_at
    )

@app.put("/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: str,
    persona_data: PersonaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update persona"""
    
    persona = db.query(Persona).filter(
        Persona.persona_id == persona_id,
        Persona.org_id == current_user["org_id"]
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Update fields
    update_data = persona_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(persona, field, value)
    
    db.commit()
    db.refresh(persona)
    
    return PersonaResponse(
        persona_id=persona.persona_id,
        org_id=persona.org_id,
        name=persona.name,
        description=persona.description,
        tone=persona.tone,
        rules=persona.rules,
        sample_prompts=persona.sample_prompts,
        safety_rules=persona.safety_rules,
        is_active=persona.is_active,
        created_at=persona.created_at
    )

@app.get("/personas")
async def list_personas(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List personas for organization"""
    
    personas = db.query(Persona).filter(
        Persona.org_id == current_user["org_id"],
        Persona.is_active == True
    ).all()
    
    return [
        PersonaResponse(
            persona_id=persona.persona_id,
            org_id=persona.org_id,
            name=persona.name,
            description=persona.description,
            tone=persona.tone,
            rules=persona.rules,
            sample_prompts=persona.sample_prompts,
            safety_rules=persona.safety_rules,
            is_active=persona.is_active,
            created_at=persona.created_at
        )
        for persona in personas
    ]

@app.post("/ai/respond", response_model=AIResponse)
async def ai_respond(
    request: AIRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI response using RAG"""
    
    # Get persona
    persona = db.query(Persona).filter(
        Persona.persona_id == request.persona_id,
        Persona.org_id == current_user["org_id"]
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    try:
        # Retrieve relevant context using RAG
        context = rag_engine.retrieve_context(
            query=request.user_message,
            persona_id=str(request.persona_id),
            org_id=current_user["org_id"],
            top_k=5
        )
        
        # Generate response using LLM
        response = await llm_orchestrator.generate_response(
            persona=persona,
            user_message=request.user_message,
            context=context,
            session_context=request.context
        )
        
        return AIResponse(
            response_text=response["text"],
            actions=response.get("actions", []),
            citations=response.get("citations", []),
            animation_hint=response.get("animation_hint"),
            session_id=request.session_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )

@app.delete("/personas/{persona_id}")
async def delete_persona(
    persona_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete persona (soft delete)"""
    
    persona = db.query(Persona).filter(
        Persona.persona_id == persona_id,
        Persona.org_id == current_user["org_id"]
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    persona.is_active = False
    db.commit()
    
    return {"message": "Persona deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)