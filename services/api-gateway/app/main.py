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

# Setup logging
setup_logging("api-gateway")
logger = get_logger(__name__)

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
    description="Central API Gateway for Bwenge OS microservices",
    version="1.0.0"
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
            
            return {
                "status_code": response.status_code,
                "content": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "headers": dict(response.headers)
            }
        except httpx.RequestError as e:
            logger.error(f"Request to {service_name} failed: {e}")
            raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(get_metrics(), media_type=get_metrics_content_type())

# Auth routes
@app.post("/auth/register")
@limiter.limit("5/minute")
async def register(request: Request):
    """Register new user"""
    result = await proxy_request("auth", "/auth/register", request, "POST")
    return result["content"]

@app.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request):
    """User login"""
    result = await proxy_request("auth", "/auth/login", request, "POST")
    return result["content"]

@app.post("/auth/refresh")
@limiter.limit("20/minute")
async def refresh_token(request: Request):
    """Refresh access token"""
    result = await proxy_request("auth", "/auth/refresh", request, "POST")
    return result["content"]

@app.get("/users/me")
@limiter.limit("100/minute")
async def get_current_user(request: Request):
    """Get current user info"""
    result = await proxy_request("auth", "/users/me", request, "GET")
    return result["content"]

# Knowledge routes
@app.post("/knowledge/upload")
@limiter.limit("10/minute")
async def upload_knowledge(request: Request):
    """Upload knowledge file"""
    result = await proxy_request("ingest", "/knowledge/upload", request, "POST")
    return result["content"]

@app.get("/knowledge/{upload_id}/status")
@limiter.limit("100/minute")
async def get_knowledge_status(upload_id: str, request: Request):
    """Get knowledge processing status"""
    result = await proxy_request("ingest", f"/knowledge/{upload_id}/status", request, "GET")
    return result["content"]

@app.delete("/knowledge/{source_id}")
@limiter.limit("20/minute")
async def delete_knowledge(source_id: str, request: Request):
    """Delete knowledge source"""
    result = await proxy_request("ingest", f"/knowledge/{source_id}", request, "DELETE")
    return result["content"]

# Persona routes
@app.post("/personas")
@limiter.limit("20/minute")
async def create_persona(request: Request):
    """Create new persona"""
    result = await proxy_request("persona", "/personas", request, "POST")
    return result["content"]

@app.get("/personas/{persona_id}")
@limiter.limit("100/minute")
async def get_persona(persona_id: str, request: Request):
    """Get persona details"""
    result = await proxy_request("persona", f"/personas/{persona_id}", request, "GET")
    return result["content"]

@app.put("/personas/{persona_id}")
@limiter.limit("20/minute")
async def update_persona(persona_id: str, request: Request):
    """Update persona"""
    result = await proxy_request("persona", f"/personas/{persona_id}", request, "PUT")
    return result["content"]

@app.post("/ai/respond")
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