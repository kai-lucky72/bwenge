from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Float, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .database import Base

class Organization(Base):
    __tablename__ = "organizations"
    
    org_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    plan = Column(String(50), default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization")
    personas = relationship("Persona", back_populates="organization")
    knowledge_sources = relationship("KnowledgeSource", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), default="user")
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    conversations = relationship("Conversation", back_populates="user")

class Persona(Base):
    __tablename__ = "personas"
    
    persona_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    tone = Column(JSONB, default={})
    rules = Column(JSONB, default={})
    sample_prompts = Column(JSONB, default=[])
    safety_rules = Column(JSONB, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="personas")
    knowledge_sources = relationship("KnowledgeSource", back_populates="persona")
    conversations = relationship("Conversation", back_populates="persona")
    model_3d = relationship("Model3D", back_populates="persona", uselist=False)

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    
    source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.persona_id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'pdf', 'audio', 'video', 'text'
    status = Column(String(50), default="pending")  # 'pending', 'processing', 'ready', 'failed'
    storage_path = Column(String(500))
    file_size = Column(BigInteger)
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="knowledge_sources")
    persona = relationship("Persona", back_populates="knowledge_sources")

class Conversation(Base):
    __tablename__ = "conversations"
    
    conv_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.persona_id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    session_id = Column(String(255))
    messages = Column(JSONB, default=[])
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    persona = relationship("Persona", back_populates="conversations")
    user = relationship("User", back_populates="conversations")

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.persona_id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Model3D(Base):
    __tablename__ = "models_3d"
    
    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.persona_id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    model_url = Column(String(500), nullable=False)
    animations = Column(JSONB, default=[])
    scale = Column(Float, default=1.0)
    bounding_box = Column(JSONB, default={})
    version = Column(String(50), default="1.0")
    mime_type = Column(String(100), default="model/gltf+json")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    persona = relationship("Persona", back_populates="model_3d")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    stripe_subscription_id = Column(String(255), unique=True)
    status = Column(String(50), nullable=False)
    plan_name = Column(String(100), nullable=False)
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UsageQuota(Base):
    __tablename__ = "usage_quotas"
    
    quota_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    quota_type = Column(String(50), nullable=False)  # 'messages', 'storage', 'users'
    limit_value = Column(Integer, nullable=False)
    used_value = Column(Integer, default=0)
    reset_period = Column(String(20), default="monthly")  # 'daily', 'weekly', 'monthly'
    last_reset = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())