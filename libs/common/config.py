import os
from typing import Optional, List
from pydantic import BaseSettings, Field

class DatabaseConfig(BaseSettings):
    """Database configuration"""
    url: str = Field(default="postgresql://bwenge:bwenge_dev@localhost:5432/bwenge", env="DATABASE_URL")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, env="DB_ECHO")

class RedisConfig(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")

class JWTConfig(BaseSettings):
    """JWT configuration"""
    secret: str = Field(env="JWT_SECRET")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

class OpenAIConfig(BaseSettings):
    """OpenAI configuration"""
    api_key: str = Field(env="OPENAI_API_KEY")
    default_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_DEFAULT_MODEL")
    embedding_model: str = Field(default="text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL")
    max_tokens: int = Field(default=500, env="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

class WeaviateConfig(BaseSettings):
    """Weaviate configuration"""
    url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")

class StripeConfig(BaseSettings):
    """Stripe configuration"""
    secret_key: str = Field(env="STRIPE_SECRET_KEY")
    webhook_secret: str = Field(env="STRIPE_WEBHOOK_SECRET")
    basic_price_id: Optional[str] = Field(default=None, env="STRIPE_BASIC_PRICE_ID")
    pro_price_id: Optional[str] = Field(default=None, env="STRIPE_PRO_PRICE_ID")
    enterprise_price_id: Optional[str] = Field(default=None, env="STRIPE_ENTERPRISE_PRICE_ID")

class StorageConfig(BaseSettings):
    """Storage configuration"""
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    assets_dir: str = Field(default="./assets", env="ASSETS_DIR")
    max_file_size: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    allowed_extensions: List[str] = Field(
        default=[".pdf", ".docx", ".pptx", ".txt", ".mp3", ".wav", ".mp4", ".avi"],
        env="ALLOWED_EXTENSIONS"
    )

class CeleryConfig(BaseSettings):
    """Celery configuration"""
    broker_url: str = Field(default="redis://localhost:6379", env="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379", env="CELERY_RESULT_BACKEND")
    task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    accept_content: List[str] = Field(default=["json"], env="CELERY_ACCEPT_CONTENT")
    timezone: str = Field(default="UTC", env="CELERY_TIMEZONE")
    enable_utc: bool = Field(default=True, env="CELERY_ENABLE_UTC")

class ServiceConfig(BaseSettings):
    """Service URLs configuration"""
    auth_service_url: str = Field(default="http://auth-service:8000", env="AUTH_SERVICE_URL")
    ingest_service_url: str = Field(default="http://ingest-service:8000", env="INGEST_SERVICE_URL")
    persona_service_url: str = Field(default="http://persona-service:8000", env="PERSONA_SERVICE_URL")
    chat_service_url: str = Field(default="http://chat-service:8000", env="CHAT_SERVICE_URL")
    threed_service_url: str = Field(default="http://3d-service:8000", env="3D_SERVICE_URL")
    analytics_service_url: str = Field(default="http://analytics-service:8000", env="ANALYTICS_SERVICE_URL")
    payments_service_url: str = Field(default="http://payments-service:8000", env="PAYMENTS_SERVICE_URL")

class AppConfig(BaseSettings):
    """Main application configuration"""
    service_name: str = Field(env="SERVICE_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    jwt: JWTConfig = JWTConfig()
    openai: OpenAIConfig = OpenAIConfig()
    weaviate: WeaviateConfig = WeaviateConfig()
    stripe: StripeConfig = StripeConfig()
    storage: StorageConfig = StorageConfig()
    celery: CeleryConfig = CeleryConfig()
    services: ServiceConfig = ServiceConfig()
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global config instance
config = AppConfig()

def get_config() -> AppConfig:
    """Get application configuration"""
    return config