from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

# Auth schemas
class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    org_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseSchema):
    user_id: uuid.UUID
    name: str
    email: str
    role: str
    is_active: bool
    org_id: uuid.UUID
    created_at: datetime

# Organization schemas
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    plan: str = "free"

class OrganizationResponse(BaseSchema):
    org_id: uuid.UUID
    name: str
    plan: str
    created_at: datetime

# Persona schemas
class PersonaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tone: Dict[str, Any] = {}
    rules: Dict[str, Any] = {}
    sample_prompts: List[str] = []
    safety_rules: List[str] = []

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tone: Optional[Dict[str, Any]] = None
    rules: Optional[Dict[str, Any]] = None
    sample_prompts: Optional[List[str]] = None
    safety_rules: Optional[List[str]] = None
    is_active: Optional[bool] = None

class PersonaResponse(BaseSchema):
    persona_id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: Optional[str]
    tone: Dict[str, Any]
    rules: Dict[str, Any]
    sample_prompts: List[str]
    safety_rules: List[str]
    is_active: bool
    created_at: datetime

# Knowledge schemas
class KnowledgeUploadResponse(BaseModel):
    upload_id: uuid.UUID
    status: str
    message: str

class KnowledgeStatusResponse(BaseModel):
    source_id: uuid.UUID
    title: str
    type: str
    status: str
    chunk_count: int
    error_message: Optional[str]
    created_at: datetime

# AI/Chat schemas
class AIRequest(BaseModel):
    persona_id: uuid.UUID
    session_id: str
    user_message: str
    context: Optional[Dict[str, Any]] = {}

class AIAction(BaseModel):
    type: str
    payload: Dict[str, Any]

class AICitation(BaseModel):
    source_id: uuid.UUID
    chunk_id: str
    text: str
    relevance_score: float

class AIResponse(BaseModel):
    response_text: str
    actions: List[AIAction] = []
    citations: List[AICitation] = []
    animation_hint: Optional[str] = None
    session_id: str

# 3D Model schemas
class Model3DResponse(BaseModel):
    model_url: str
    animations: List[str]
    scale: float
    bounding_box: Dict[str, Any]
    version: str
    mime_type: str

# Analytics schemas
class AnalyticsEventCreate(BaseModel):
    event_type: str
    payload: Dict[str, Any] = {}

class WeeklyReportResponse(BaseModel):
    org_id: uuid.UUID
    week_start: datetime
    week_end: datetime
    total_messages: int
    active_users: int
    top_personas: List[Dict[str, Any]]
    usage_stats: Dict[str, Any]

# Payment schemas
class SubscriptionCreate(BaseModel):
    plan_name: str
    success_url: str
    cancel_url: str

class SubscriptionResponse(BaseModel):
    checkout_url: str
    subscription_id: uuid.UUID

class WebhookEvent(BaseModel):
    type: str
    data: Dict[str, Any]

# Message schemas for chat
class ChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

class ChatSession(BaseModel):
    session_id: str
    persona_id: uuid.UUID
    user_id: uuid.UUID
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)