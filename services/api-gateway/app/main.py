from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import os
import sys
from typing import Dict, Any

# Add libs to path
sys.path.append('/app')
from libs.common.logging_config import setup_logging, get_logger
from libs.common.metrics import get_metrics, get_metrics_content_type, track_request_metrics
from libs.common.exceptions import handle_exceptions
# from libs.common.tracing import setup_tracing, TracingMiddleware, trace_function, add_span_attributes

# Setup logging and tracing
setup_logging("api-gateway")
logger = get_logger(__name__)

# Setup distributed tracing
# tracer = setup_tracing("api-gateway", "1.0.0")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Service URLs
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "ingest": os.getenv("INGEST_SERVICE_URL", "http://ingest-service:8000"),
    "persona": os.getenv("PERSONA_SERVICE_URL", "http://persona-service:8000"),
    "chat": os.getenv("CHAT_SERVICE_URL", "http://chat-service:8000"),
    "3d": os.getenv("3D_SERVICE_URL", "http://3d-service:8000"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000"),
    "payments": os.getenv("PAYMENTS_SERVICE_URL", "http://payments-service:8000"),
}

app = FastAPI(
    title="Bwenge OS API Gateway",
    description="""
    # Bwenge OS API Gateway
    
    Central API Gateway for Bwenge OS - An AI-powered educational platform with 3D avatars.
    
    ## Features
    
    * **Authentication & Authorization** - JWT-based auth with multi-tenant support
    * **Knowledge Management** - Upload and process educational content (PDF, DOCX, audio, video)
    * **AI Personas** - Create and manage AI tutors with custom personalities
    * **Real-time Chat** - WebSocket-based chat with AI personas
    * **3D Avatars** - Manage 3D models and animations for personas
    * **Analytics** - Track usage and learning progress
    * **Payments** - Subscription management with Stripe integration
    
    ## Authentication
    
    Most endpoints require authentication. Include the JWT token in the Authorization header:
    
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    Get your token by calling the `/auth/login` endpoint.
    
    ## Rate Limiting
    
    API endpoints are rate-limited to prevent abuse. Limits vary by endpoint type:
    
    * Authentication: 5-20 requests/minute
    * File uploads: 10 requests/minute  
    * AI responses: 60 requests/minute
    * General API: 100 requests/minute
    
    ## Multi-tenancy
    
    The system supports multiple organizations. Users can only access resources 
    within their organization. Organization isolation is enforced at the API level.
    
    ## Error Handling
    
    The API uses standard HTTP status codes:
    
    * `200` - Success
    * `400` - Bad Request (validation error)
    * `401` - Unauthorized (invalid/missing token)
    * `403` - Forbidden (insufficient permissions)
    * `404` - Not Found
    * `422` - Unprocessable Entity (validation error)
    * `429` - Too Many Requests (rate limited)
    * `500` - Internal Server Error
    
    Error responses include a `detail` field with more information.
    """,
    version="1.0.0",
    contact={
        "name": "Bwenge OS Support",
        "email": "support@bwenge.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.bwenge.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Knowledge Management", 
            "description": "Upload and manage educational content"
        },
        {
            "name": "AI Personas",
            "description": "Create and manage AI tutors with custom personalities"
        },
        {
            "name": "3D Models",
            "description": "Manage 3D avatars and animations"
        },
        {
            "name": "Analytics",
            "description": "Usage analytics and learning progress tracking"
        },
        {
            "name": "Payments",
            "description": "Subscription and billing management"
        },
        {
            "name": "System",
            "description": "Health checks and system information"
        }
    ]
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Add tracing middleware
# app.add_middleware(TracingMiddleware)

# @trace_function("proxy_request")
async def proxy_request(
    service_name: str,
    path: str,
    request: Request,
    method: str = "GET"
) -> Dict[str, Any]:
    """Proxy request to microservice"""
    service_url = SERVICES.get(service_name)
    if not service_url:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    url = f"{service_url}{path}"
    
    # Add tracing attributes
    # add_span_attributes(
    #     service_name=service_name,
    #     target_url=url,
    #     http_method=method
    # )
    
    # Prepare headers (forward auth headers)
    headers = {}
    if "authorization" in request.headers:
        headers["authorization"] = request.headers["authorization"]
    if "x-tenant-id" in request.headers:
        headers["x-tenant-id"] = request.headers["x-tenant-id"]
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=request.query_params)
            elif method.upper() == "POST":
                body = await request.body()
                response = await client.post(url, headers=headers, content=body)
            elif method.upper() == "PUT":
                body = await request.body()
                response = await client.put(url, headers=headers, content=body)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            # Add response attributes to trace
            # add_span_attributes(
            #     http_status_code=response.status_code,
            #     response_size=len(response.content) if response.content else 0
            # )
            
            return {
                "status_code": response.status_code,
                "content": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "headers": dict(response.headers)
            }
        except httpx.RequestError as e:
            logger.error(f"Request to {service_name} failed: {e}")
            # add_span_attributes(error_type="request_error", error_message=str(e))
            raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

# Health check
@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="Check if the API Gateway is running and healthy",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "service": "api-gateway"}
                }
            }
        }
    }
)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(get_metrics(), media_type=get_metrics_content_type())

# Auth routes
@app.post(
    "/auth/register",
    tags=["Authentication"],
    summary="Register New User",
    description="""
    Register a new user account. If `org_name` is provided, a new organization 
    will be created and the user will be set as admin. Otherwise, the user 
    will be added to a default organization.
    
    **Rate limit:** 5 requests per minute
    """,
    responses={
        200: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        400: {"description": "Email already registered or validation error"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("5/minute")
async def register(request: Request):
    """Register new user"""
    result = await proxy_request("auth", "/auth/register", request, "POST")
    return result["content"]

@app.post(
    "/auth/login",
    tags=["Authentication"],
    summary="User Login",
    description="""
    Authenticate user with email and password. Returns JWT access and refresh tokens.
    
    **Rate limit:** 10 requests per minute
    """,
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {"description": "Invalid credentials"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("10/minute")
async def login(request: Request):
    """User login"""
    result = await proxy_request("auth", "/auth/login", request, "POST")
    return result["content"]

@app.post(
    "/auth/refresh",
    tags=["Authentication"],
    summary="Refresh Access Token",
    description="""
    Refresh an expired access token using a valid refresh token.
    
    **Rate limit:** 20 requests per minute
    """,
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {"description": "Invalid or expired refresh token"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("20/minute")
async def refresh_token(request: Request):
    """Refresh access token"""
    result = await proxy_request("auth", "/auth/refresh", request, "POST")
    return result["content"]

@app.get(
    "/users/me",
    tags=["Authentication"],
    summary="Get Current User",
    description="""
    Get information about the currently authenticated user.
    
    **Requires authentication**
    
    **Rate limit:** 100 requests per minute
    """,
    responses={
        200: {
            "description": "User information",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "role": "admin",
                        "is_active": True,
                        "org_id": "123e4567-e89b-12d3-a456-426614174001",
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Invalid or missing authentication token"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("100/minute")
async def get_current_user(request: Request):
    """Get current user info"""
    result = await proxy_request("auth", "/users/me", request, "GET")
    return result["content"]

# Knowledge routes
@app.post(
    "/knowledge/upload",
    tags=["Knowledge Management"],
    summary="Upload Knowledge File",
    description="""
    Upload educational content for processing. Supported formats:
    
    * **Documents:** PDF, DOCX, PPTX, TXT
    * **Audio:** MP3, WAV, MP4 (audio)
    * **Video:** MP4, AVI (audio will be extracted)
    
    Files are processed asynchronously:
    1. File is uploaded and stored
    2. Content is extracted (text/transcription)
    3. Text is chunked and embedded
    4. Vectors are stored for RAG retrieval
    
    **Requires authentication**
    
    **Rate limit:** 10 requests per minute
    """,
    responses={
        200: {
            "description": "File uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "upload_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "pending",
                        "message": "File uploaded successfully and queued for processing"
                    }
                }
            }
        },
        400: {"description": "Unsupported file type or validation error"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("10/minute")
async def upload_knowledge(request: Request):
    """Upload knowledge file"""
    result = await proxy_request("ingest", "/knowledge/upload", request, "POST")
    return result["content"]

@app.get(
    "/knowledge/{upload_id}/status",
    tags=["Knowledge Management"],
    summary="Get Processing Status",
    description="""
    Check the processing status of an uploaded file.
    
    **Status values:**
    * `pending` - File uploaded, waiting for processing
    * `processing` - Currently being processed
    * `ready` - Processing complete, available for RAG
    * `failed` - Processing failed (check error_message)
    
    **Requires authentication**
    
    **Rate limit:** 100 requests per minute
    """,
    responses={
        200: {
            "description": "Processing status",
            "content": {
                "application/json": {
                    "example": {
                        "source_id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Mathematics Textbook Chapter 1",
                        "type": "pdf",
                        "status": "ready",
                        "chunk_count": 25,
                        "error_message": None,
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                }
            }
        },
        404: {"description": "Upload not found"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("100/minute")
async def get_knowledge_status(upload_id: str, request: Request):
    """Get knowledge processing status"""
    result = await proxy_request("ingest", f"/knowledge/{upload_id}/status", request, "GET")
    return result["content"]

@app.delete(
    "/knowledge/{source_id}",
    tags=["Knowledge Management"],
    summary="Delete Knowledge Source",
    description="""
    Delete a knowledge source and all associated data.
    This will remove:
    * The original uploaded file
    * All processed chunks
    * Vector embeddings
    * Database records
    
    **This action cannot be undone.**
    
    **Requires authentication**
    
    **Rate limit:** 20 requests per minute
    """,
    responses={
        200: {
            "description": "Knowledge source deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Knowledge source deleted successfully"}
                }
            }
        },
        404: {"description": "Knowledge source not found"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("20/minute")
async def delete_knowledge(source_id: str, request: Request):
    """Delete knowledge source"""
    result = await proxy_request("ingest", f"/knowledge/{source_id}", request, "DELETE")
    return result["content"]

# Persona routes
@app.post(
    "/personas",
    tags=["AI Personas"],
    summary="Create AI Persona",
    description="""
    Create a new AI persona with custom personality, rules, and behavior.
    
    **Persona Configuration:**
    * **Name & Description** - Basic identification
    * **Tone** - Communication style (formal/casual, enthusiastic/calm, etc.)
    * **Rules** - Behavioral guidelines and constraints
    * **Sample Prompts** - Example interactions to guide behavior
    * **Safety Rules** - Content and behavior restrictions
    
    **Requires authentication**
    
    **Rate limit:** 20 requests per minute
    """,
    responses={
        200: {
            "description": "Persona created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Gabriel - Math Tutor",
                        "description": "A friendly AI tutor specialized in mathematics",
                        "tone": {"style": "friendly", "formality": "casual"},
                        "rules": {"guidelines": ["Be encouraging", "Use examples"]},
                        "is_active": True,
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Validation error"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("20/minute")
async def create_persona(request: Request):
    """Create new persona"""
    result = await proxy_request("persona", "/personas", request, "POST")
    return result["content"]

@app.get(
    "/personas/{persona_id}",
    tags=["AI Personas"],
    summary="Get Persona Details",
    description="""
    Retrieve detailed information about a specific AI persona.
    
    **Requires authentication**
    
    **Rate limit:** 100 requests per minute
    """,
    responses={
        200: {
            "description": "Persona details",
            "content": {
                "application/json": {
                    "example": {
                        "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Gabriel - Math Tutor",
                        "description": "A friendly AI tutor specialized in mathematics",
                        "tone": {"style": "friendly", "formality": "casual"},
                        "rules": {"guidelines": ["Be encouraging", "Use examples"]},
                        "sample_prompts": ["Hello! Ready to learn math?"],
                        "safety_rules": ["Keep content educational"],
                        "is_active": True,
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                }
            }
        },
        404: {"description": "Persona not found"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("100/minute")
async def get_persona(persona_id: str, request: Request):
    """Get persona details"""
    result = await proxy_request("persona", f"/personas/{persona_id}", request, "GET")
    return result["content"]

@app.put(
    "/personas/{persona_id}",
    tags=["AI Personas"],
    summary="Update Persona",
    description="""
    Update an existing AI persona's configuration.
    
    **Requires authentication**
    
    **Rate limit:** 20 requests per minute
    """,
    responses={
        200: {"description": "Persona updated successfully"},
        404: {"description": "Persona not found"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("20/minute")
async def update_persona(persona_id: str, request: Request):
    """Update persona"""
    result = await proxy_request("persona", f"/personas/{persona_id}", request, "PUT")
    return result["content"]

@app.post(
    "/ai/respond",
    tags=["AI Personas"],
    summary="Get AI Response",
    description="""
    Generate an AI response using RAG (Retrieval-Augmented Generation).
    
    **Process:**
    1. Query vector database for relevant knowledge chunks
    2. Combine persona configuration + retrieved context + conversation history
    3. Generate response using LLM (OpenAI GPT)
    4. Return structured response with citations and metadata
    
    **Response includes:**
    * Generated text response
    * Source citations from knowledge base
    * Animation hints for 3D avatar
    * Suggested actions (future feature)
    
    **Requires authentication**
    
    **Rate limit:** 60 requests per minute
    """,
    responses={
        200: {
            "description": "AI response generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "response_text": "Great question! Algebra is a branch of mathematics that uses symbols and letters to represent numbers and quantities in formulas and equations.",
                        "actions": [],
                        "citations": [
                            {
                                "source_id": "123e4567-e89b-12d3-a456-426614174000",
                                "chunk_id": "chunk_001",
                                "text": "Algebra is a branch of mathematics dealing with symbols...",
                                "relevance_score": 0.95
                            }
                        ],
                        "animation_hint": "explaining",
                        "session_id": "session_123"
                    }
                }
            }
        },
        404: {"description": "Persona not found"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "AI service error"}
    }
)
@limiter.limit("60/minute")
async def ai_respond(request: Request):
    """Get AI response"""
    result = await proxy_request("persona", "/ai/respond", request, "POST")
    return result["content"]

# 3D Model routes
@app.get("/3d/persona/{persona_id}")
@limiter.limit("100/minute")
async def get_3d_model(persona_id: str, request: Request):
    """Get 3D model for persona"""
    result = await proxy_request("3d", f"/3d/persona/{persona_id}", request, "GET")
    return result["content"]

# Analytics routes
@app.get("/orgs/{org_id}/reports/weekly")
@limiter.limit("20/minute")
async def get_weekly_report(org_id: str, request: Request):
    """Get weekly analytics report"""
    result = await proxy_request("analytics", f"/orgs/{org_id}/reports/weekly", request, "GET")
    return result["content"]

@app.get("/orgs/{org_id}/students/{student_id}/progress")
@limiter.limit("50/minute")
async def get_student_progress(org_id: str, student_id: str, request: Request):
    """Get student progress"""
    result = await proxy_request("analytics", f"/orgs/{org_id}/students/{student_id}/progress", request, "GET")
    return result["content"]

# Payment routes
@app.post("/payments/subscribe")
@limiter.limit("5/minute")
async def create_subscription(request: Request):
    """Create subscription"""
    result = await proxy_request("payments", "/payments/subscribe", request, "POST")
    return result["content"]

@app.post("/webhooks/payment")
async def payment_webhook(request: Request):
    """Handle payment webhooks"""
    result = await proxy_request("payments", "/webhooks/payment", request, "POST")
    return result["content"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)