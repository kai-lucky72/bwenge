# Bwenge OS - Local Development Setup Guide

## ✅ Complete Implementation Status

All services, endpoints, and Docker configurations are now **fully implemented** and ready for local development.

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose installed
- OpenAI API Key (for embeddings and LLM)
- Git

### 2. Environment Setup

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://bwenge:bwenge_dev@postgres:5432/bwenge

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET=your-jwt-secret-key-change-in-production

# OpenAI (Required)
OPENAI_API_KEY=your-openai-api-key

# Weaviate
WEAVIATE_URL=http://weaviate:8080

# 3D Service
URL_SECRET=dev-url-secret-key
BASE_URL=http://localhost:8005
```

### 3. Start All Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
curl http://localhost:8000/health
```

### 4. Verify Services

All services should be running on:
- **API Gateway:** http://localhost:8000
- **Auth Service:** http://localhost:8001
- **Ingest Service:** http://localhost:8002
- **Persona Service:** http://localhost:8003
- **Chat Service:** http://localhost:8004
- **3D Service:** http://localhost:8005
- **Analytics Service:** http://localhost:8006
- **Payments Service:** http://localhost:8007

---

## 📋 Complete API Endpoints

### Authentication (`/auth/*`)
- ✅ `POST /auth/register` - Register new user
- ✅ `POST /auth/login` - User login
- ✅ `POST /auth/refresh` - Refresh access token
- ✅ `GET /users/me` - Get current user
- ✅ `POST /orgs/{org_id}/invite` - Invite user to organization
- ✅ `GET /orgs/{org_id}/members` - List organization members

### Knowledge Management (`/knowledge/*`)
- ✅ `POST /knowledge/upload` - Upload knowledge file
- ✅ `GET /knowledge/{upload_id}/status` - Get processing status
- ✅ `GET /knowledge/sources` - List knowledge sources
- ✅ `DELETE /knowledge/{source_id}` - Delete knowledge source

### Personas (`/personas/*`)
- ✅ `POST /personas` - Create persona
- ✅ `GET /personas` - List personas
- ✅ `GET /personas/{persona_id}` - Get persona details
- ✅ `PUT /personas/{persona_id}` - Update persona
- ✅ `POST /personas/{persona_id}/settings` - Update persona settings
- ✅ `DELETE /personas/{persona_id}` - Delete persona
- ✅ `POST /ai/respond` - Get AI response

### Chat (`/ws/*`, `/sessions/*`)
- ✅ `WS /ws/chat?persona={id}&session={s}&token={token}` - WebSocket chat
- ✅ `GET /sessions/{session_id}/messages` - Get session messages
- ✅ `POST /sessions/{session_id}/persist` - Persist session

### 3D Models (`/3d/*`)
- ✅ `GET /3d/persona/{persona_id}` - Get 3D model
- ✅ `POST /3d/persona/{persona_id}/upload` - Upload 3D model
- ✅ `DELETE /3d/persona/{persona_id}` - Delete 3D model
- ✅ `GET /3d/animations` - List available animations

### Analytics (`/orgs/{org_id}/*`, `/events`)
- ✅ `GET /orgs/{org_id}/reports/weekly` - Weekly report
- ✅ `GET /orgs/{org_id}/students/{student_id}/progress` - Student progress
- ✅ `GET /orgs/{org_id}/dashboard` - Organization dashboard
- ✅ `POST /events` - Track analytics event

### Payments (`/payments/*`, `/subscriptions/*`, `/plans`)
- ✅ `POST /payments/subscribe` - Create subscription
- ✅ `GET /subscriptions/current` - Get current subscription
- ✅ `GET /plans` - List subscription plans
- ✅ `GET /payments/transactions` - List transactions
- ✅ `GET /payments/methods` - List payment methods
- ✅ `POST /payments/simulate-completion/{transaction_id}` - Simulate payment (dev)
- ✅ `POST /payments/cancel-subscription` - Cancel subscription
- ✅ `POST /webhooks/payment` - Payment webhook (placeholder)

---

## 🗄️ Database-Only Payments

The payments service is configured for **local development** with:
- ✅ Database-only payment transactions
- ✅ No Stripe/Paystack dependencies
- ✅ Payment simulation endpoint for testing
- ✅ Rwanda payment methods (MTN, Airtel, Bank, Cash, Tigo)
- ✅ Subscription plans with quotas

### Testing Payments

1. **Create Subscription:**
   ```bash
   POST /payments/subscribe
   {
     "plan_name": "basic",
     "payment_method": "momo",
     "phone_number": "+250788123456"
   }
   ```

2. **Simulate Payment Completion:**
   ```bash
   POST /payments/simulate-completion/{transaction_id}
   {
     "success": true
   }
   ```

3. **Check Subscription:**
   ```bash
   GET /subscriptions/current
   ```

---

## 🐳 Docker Services

### Core Services
- ✅ **postgres** - PostgreSQL 15 database
- ✅ **redis** - Redis 7 for caching and Celery broker
- ✅ **weaviate** - Vector database for embeddings

### Application Services
- ✅ **api-gateway** - Central API gateway (port 8000)
- ✅ **auth-service** - Authentication service (port 8001)
- ✅ **ingest-service** - Knowledge ingestion (port 8002)
- ✅ **celery-worker** - Background task processor
- ✅ **persona-service** - AI persona management (port 8003)
- ✅ **chat-service** - WebSocket chat (port 8004)
- ✅ **3d-service** - 3D model management (port 8005)
- ✅ **analytics-service** - Analytics and reporting (port 8006)
- ✅ **payments-service** - Payment processing (port 8007)

---

## 🔧 Development Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
docker-compose logs -f celery-worker
```

### Rebuild Services
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U bwenge -d bwenge

# Run migrations (automatic on startup)
# Tables are created via init_db() on service startup
```

### Redis Access
```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli
```

---

## 📝 Testing the API

### 1. Register a User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpassword123",
    "org_name": "Test Organization"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 3. Create a Persona
```bash
curl -X POST http://localhost:8000/personas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Math Tutor",
    "description": "A friendly math tutor",
    "tone": {"style": "friendly"},
    "rules": {"guidelines": ["Be encouraging"]},
    "sample_prompts": [],
    "safety_rules": []
  }'
```

### 4. Upload Knowledge
```bash
curl -X POST http://localhost:8000/knowledge/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@document.pdf" \
  -F "persona_id=YOUR_PERSONA_ID" \
  -F "title=Math Textbook"
```

### 5. Chat via WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat?persona=YOUR_PERSONA_ID&session=test-session&token=YOUR_ACCESS_TOKEN');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "user_message",
    content: "Hello!"
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

---

## 🔍 API Documentation

Once services are running, access interactive API docs:

- **API Gateway Swagger:** http://localhost:8000/docs
- **API Gateway ReDoc:** http://localhost:8000/redoc

All endpoints are documented with:
- Request/response schemas
- Authentication requirements
- Rate limits
- Example payloads

---

## ⚙️ Configuration

### Service URLs (Auto-configured in Docker)
All services communicate via internal Docker network:
- `http://auth-service:8000`
- `http://ingest-service:8000`
- `http://persona-service:8000`
- `http://chat-service:8000`
- `http://3d-service:8000`
- `http://analytics-service:8000`
- `http://payments-service:8000`

### Rate Limits
- Authentication: 5-20 requests/minute
- File uploads: 10 requests/minute
- AI responses: 60 requests/minute
- General API: 100 requests/minute

---

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check service status
docker-compose ps

# Check logs for errors
docker-compose logs service-name

# Restart specific service
docker-compose restart service-name
```

### Database Connection Issues
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U bwenge -d bwenge -c "SELECT 1;"
```

### Celery Worker Not Processing
```bash
# Check worker logs
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker
```

### Weaviate Connection Issues
```bash
# Check Weaviate status
curl http://localhost:8080/v1/.well-known/ready

# Check logs
docker-compose logs weaviate
```

---

## ✅ Implementation Checklist

### Backend Services
- ✅ All 8 microservices implemented
- ✅ All API endpoints exposed via gateway
- ✅ WebSocket support for chat
- ✅ Database-only payments (no Stripe)
- ✅ Celery workers for async processing
- ✅ Vector database integration

### Docker Configuration
- ✅ All services containerized
- ✅ docker-compose.yml configured
- ✅ docker-compose.dev.yml for development
- ✅ docker-compose.staging.yml for staging
- ✅ Volume mounts for hot-reload
- ✅ Health checks configured

### Features
- ✅ Authentication & authorization
- ✅ Multi-tenant support
- ✅ Knowledge ingestion pipeline
- ✅ RAG implementation
- ✅ Real-time chat
- ✅ 3D model management
- ✅ Analytics & reporting
- ✅ Subscription management

---

## 🎯 Next Steps

1. **Start Services:**
   ```bash
   docker-compose up -d
   ```

2. **Test API:**
   - Register a user
   - Create a persona
   - Upload knowledge
   - Start a chat session

3. **Monitor Logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Access API Docs:**
   - Visit http://localhost:8000/docs

---

## 📚 Additional Resources

- **System Architecture:** See `system-architecture.md`
- **Backend Analysis:** See `BACKEND_ANALYSIS.md`
- **API Documentation:** http://localhost:8000/docs
- **Service Health:** http://localhost:8000/health

---

**Status:** ✅ **Ready for Local Development**

All services, endpoints, and configurations are complete and functional!

