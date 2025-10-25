# Bwenge OS Complete System Guide

This comprehensive guide covers the complete Bwenge OS system implementation, including all services, features, and operational procedures.

## 🏗️ System Architecture Overview

Bwenge OS is a microservices-based AI-powered educational platform with the following components:

### Core Services
- **API Gateway** (Port 8000) - Central routing, authentication, rate limiting
- **Auth Service** (Port 8001) - User authentication and authorization
- **Ingest Service** (Port 8002) - Knowledge ingestion and processing
- **Persona Service** (Port 8003) - AI persona management and RAG
- **Chat Service** (Port 8004) - Real-time messaging and WebSocket
- **3D Service** (Port 8005) - 3D model management and serving
- **Analytics Service** (Port 8006) - Usage analytics and reporting
- **Payments Service** (Port 8007) - Subscription and billing

### Infrastructure Components
- **PostgreSQL** - Primary database for structured data
- **Redis** - Caching, session storage, and message broker
- **Weaviate** - Vector database for embeddings and RAG
- **Celery** - Async task processing and scheduling
- **Nginx** - Reverse proxy and load balancer (production)

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Git
- 8GB+ RAM recommended
- 20GB+ disk space

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd bwenge-os
   chmod +x scripts/*.sh
   ./scripts/complete-setup.sh
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start System**
   ```bash
   make up
   ```

4. **Verify Installation**
   ```bash
   make health
   python3 scripts/system-status.py
   ```

## 📚 Complete Feature Set

### Authentication & Authorization
- ✅ JWT-based authentication with refresh tokens
- ✅ Multi-tenant organization support
- ✅ Role-based access control (admin, teacher, student)
- ✅ User registration and invitation system
- ✅ Password strength validation
- ✅ Session management

### Knowledge Management
- ✅ Multi-format file upload (PDF, DOCX, PPTX, TXT, audio, video)
- ✅ Automatic transcription (Whisper integration)
- ✅ Text extraction and processing
- ✅ Smart chunking with overlap
- ✅ Embedding generation (OpenAI)
- ✅ Vector storage (Weaviate)
- ✅ Async processing with Celery
- ✅ Processing status tracking

### AI & Personas
- ✅ Persona creation and management
- ✅ Customizable tone and behavior
- ✅ Safety rules and guidelines
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ LLM orchestration (OpenAI, Gemini support)
- ✅ Context-aware responses
- ✅ Citation generation
- ✅ Animation hints for 3D avatars

### Real-time Chat
- ✅ WebSocket-based real-time messaging
- ✅ Session management
- ✅ Message persistence
- ✅ Streaming responses
- ✅ Typing indicators
- ✅ Connection management

### 3D Avatar System
- ✅ 3D model upload and management
- ✅ GLTF/GLB format support
- ✅ Animation mapping
- ✅ Signed URL generation
- ✅ Asset serving with CDN support
- ✅ Model metadata management

### Analytics & Reporting
- ✅ Event tracking
- ✅ Usage analytics
- ✅ Weekly reports
- ✅ Student progress tracking
- ✅ Engagement metrics
- ✅ Dashboard data aggregation

### Payment & Subscriptions
- ✅ Stripe integration
- ✅ Multiple subscription tiers
- ✅ Webhook handling
- ✅ Usage quota enforcement
- ✅ Billing management
- ✅ Plan upgrades/downgrades

### Monitoring & Observability
- ✅ Prometheus metrics
- ✅ Structured logging
- ✅ Health checks
- ✅ Performance monitoring
- ✅ Error tracking
- ✅ System status dashboard

### Security Features
- ✅ Rate limiting
- ✅ Input validation
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ CORS configuration
- ✅ Tenant isolation
- ✅ Signed URLs for assets
- ✅ Audit logging

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://bwenge:password@localhost:5432/bwenge

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-secure-jwt-secret-key

# AI Services
OPENAI_API_KEY=sk-your-openai-api-key

# Payment Processing
STRIPE_SECRET_KEY=sk_live_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Vector Database
WEAVIATE_URL=http://localhost:8080

# File Storage
UPLOAD_DIR=./uploads
ASSETS_DIR=./assets
MAX_FILE_SIZE=104857600  # 100MB

# Security
URL_SECRET=your-url-signing-secret
BASE_URL=https://your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Environment
ENVIRONMENT=production
```

### Subscription Plans

```json
{
  "free": {
    "price": 0,
    "messages": 100,
    "storage": "100MB",
    "users": 5
  },
  "basic": {
    "price": 29,
    "messages": 1000,
    "storage": "1GB",
    "users": 25
  },
  "pro": {
    "price": 99,
    "messages": 10000,
    "storage": "10GB",
    "users": 100
  },
  "enterprise": {
    "price": 299,
    "messages": "unlimited",
    "storage": "unlimited",
    "users": "unlimited"
  }
}
```

## 🛠️ Development

### Local Development Setup

```bash
# Setup development environment
./scripts/setup-dev.sh

# Run individual services
cd services/auth-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Run tests
make test

# Code quality
make lint
make format
```

### Adding New Features

1. **Create new service**
   ```bash
   mkdir services/new-service
   cp -r services/auth-service/* services/new-service/
   # Modify as needed
   ```

2. **Update docker-compose.yml**
   ```yaml
   new-service:
     build: ./services/new-service
     ports:
       - "8008:8000"
     environment:
       - DATABASE_URL=${DATABASE_URL}
   ```

3. **Add to API Gateway**
   ```python
   SERVICES["new"] = "http://new-service:8000"
   ```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🚀 Deployment

### Development
```bash
make up
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production (Kubernetes)
```bash
./scripts/deploy-production.sh production your-domain.com
```

### Production (Docker Compose)
```bash
docker-compose -f docker-compose.production.yml up -d
```

## 📊 Monitoring

### System Status
```bash
# Quick status check
make health

# Comprehensive status
python3 scripts/system-status.py

# Watch mode
python3 scripts/system-status.py --watch 30

# JSON output
python3 scripts/system-status.py --json
```

### Metrics & Dashboards
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Service metrics: http://localhost:8000/metrics

### Log Analysis
```bash
# View all logs
make logs

# Service-specific logs
docker-compose logs -f auth-service

# Error logs only
docker-compose logs | grep ERROR
```

## 🔄 Backup & Restore

### Full System Backup
```bash
./scripts/backup-restore.sh backup
```

### Restore from Backup
```bash
./scripts/backup-restore.sh restore --backup-name full_backup_20231201_120000
```

### Database Only
```bash
# Backup
./scripts/backup-restore.sh db-backup

# Restore
./scripts/backup-restore.sh db-restore backups/db_backup_20231201_120000.sql.gz
```

### Automated Backups
```bash
# Add to crontab
0 2 * * * /path/to/bwenge-os/scripts/backup-restore.sh backup
0 3 * * 0 /path/to/bwenge-os/scripts/backup-restore.sh cleanup --keep-days 30
```

## 🧪 Testing

### API Testing
```bash
# Run comprehensive API tests
python3 scripts/test-api.py

# Create sample data
python3 scripts/create-sample-data.py
```

### Unit Tests
```bash
# Run all tests
pytest

# Service-specific tests
pytest services/auth-service/tests/

# Coverage report
pytest --cov=. --cov-report=html
```

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Run load test
artillery run tests/load-test.yml
```

## 🔒 Security

### Security Checklist
- [ ] Change default passwords
- [ ] Configure JWT secrets
- [ ] Enable HTTPS
- [ ] Set up rate limiting
- [ ] Configure CORS properly
- [ ] Enable audit logging
- [ ] Set up monitoring alerts
- [ ] Regular security updates

### Security Scanning
```bash
# Dependency scanning
pip-audit

# Container scanning
docker scan bwenge-os/auth-service

# SAST scanning
bandit -r services/
```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check logs
   docker-compose logs service-name
   
   # Check environment variables
   docker-compose config
   
   # Restart service
   docker-compose restart service-name
   ```

2. **Database connection errors**
   ```bash
   # Check database status
   docker-compose exec postgres pg_isready -U bwenge
   
   # Reset database
   make reset-db
   ```

3. **High memory usage**
   ```bash
   # Check resource usage
   docker stats
   
   # Scale down services
   docker-compose up -d --scale celery-worker=1
   ```

4. **Vector search not working**
   ```bash
   # Check Weaviate status
   curl http://localhost:8080/v1/meta
   
   # Rebuild vector index
   python3 scripts/rebuild-vectors.py
   ```

### Performance Optimization

1. **Database optimization**
   ```sql
   -- Add indexes
   CREATE INDEX CONCURRENTLY idx_users_org_id ON users(org_id);
   
   -- Analyze tables
   ANALYZE;
   ```

2. **Redis optimization**
   ```bash
   # Configure memory policy
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

3. **Application optimization**
   - Enable caching
   - Optimize database queries
   - Use connection pooling
   - Implement pagination

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale services
docker-compose up -d --scale auth-service=3 --scale persona-service=2

# Kubernetes scaling
kubectl scale deployment auth-service --replicas=3
```

### Database Scaling
- Read replicas for read-heavy workloads
- Connection pooling with PgBouncer
- Database partitioning for large datasets

### Caching Strategy
- Redis for session storage
- Application-level caching
- CDN for static assets

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit pull request

### Code Standards
- Follow PEP 8 for Python
- Use type hints
- Write comprehensive tests
- Document all functions
- Use conventional commits

## 📄 API Documentation

### Authentication Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `GET /users/me` - Get current user info

### Knowledge Management
- `POST /knowledge/upload` - Upload knowledge file
- `GET /knowledge/{id}/status` - Check processing status
- `DELETE /knowledge/{id}` - Delete knowledge source

### Persona Management
- `POST /personas` - Create persona
- `GET /personas/{id}` - Get persona details
- `PUT /personas/{id}` - Update persona
- `POST /ai/respond` - Get AI response

### Real-time Chat
- `WS /ws/chat?persona={id}&session={id}` - WebSocket chat

### 3D Models
- `GET /3d/persona/{id}` - Get 3D model for persona
- `POST /3d/persona/{id}/upload` - Upload 3D model

### Analytics
- `GET /orgs/{id}/reports/weekly` - Weekly report
- `GET /orgs/{id}/students/{id}/progress` - Student progress

### Payments
- `POST /payments/subscribe` - Create subscription
- `GET /subscriptions/current` - Get current subscription

## 📞 Support

### Getting Help
- Check documentation in `/docs`
- Review troubleshooting guide
- Check system status
- Review logs for errors
- Create GitHub issue

### Community
- GitHub Discussions
- Discord Server
- Stack Overflow (tag: bwenge-os)

---

## 🎯 System Completeness Checklist

### ✅ Core Services Implemented
- [x] API Gateway with routing and rate limiting
- [x] Authentication service with JWT
- [x] Knowledge ingestion with async processing
- [x] Persona management with RAG
- [x] Real-time chat with WebSocket
- [x] 3D model service with signed URLs
- [x] Analytics and reporting
- [x] Payment processing with Stripe

### ✅ Infrastructure Components
- [x] PostgreSQL database with migrations
- [x] Redis for caching and queues
- [x] Weaviate vector database
- [x] Celery for async tasks
- [x] Docker containerization
- [x] Kubernetes deployment configs

### ✅ Monitoring & Operations
- [x] Prometheus metrics
- [x] Structured logging
- [x] Health checks
- [x] System status monitoring
- [x] Backup and restore system
- [x] Deployment automation

### ✅ Security & Quality
- [x] Input validation
- [x] Rate limiting
- [x] Tenant isolation
- [x] Error handling
- [x] Test coverage
- [x] Code quality tools

### ✅ Documentation & Tools
- [x] Complete API documentation
- [x] Deployment guides
- [x] Troubleshooting guides
- [x] Development setup
- [x] Operational procedures

**🎉 SYSTEM IS COMPLETE AND PRODUCTION-READY! 🎉**