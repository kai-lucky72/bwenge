# Bwenge OS

A comprehensive AI-powered educational platform with 3D avatars and personalized learning experiences.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Git
- Docker (optional, for Weaviate and easier setup)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bwenge-os
   ```

2. **Run the complete setup script**
   ```bash
   # Windows
   scripts\complete-setup.bat
   
   # Linux/Mac
   chmod +x scripts/complete-setup.sh
   ./scripts/complete-setup.sh
   ```

3. **Configure your API keys**
   ```bash
   # Edit .env file with your configuration
   nano .env  # Add your OPENAI_API_KEY and other keys
   ```

4. **Start services**
   ```bash
   # Option 1: Individual services (recommended for development)
   python scripts/run-service.py auth      # Start auth service
   python scripts/run-service.py api-gateway  # Start API gateway
   
   # Option 2: Docker Compose (if Docker available)
   make build && make up
   ```

5. **Test the setup**
   ```bash
   python scripts/test-api.py
   ```

The API Gateway will be available at `http://localhost:8000`

**Default Login:** admin@bwenge.com / admin123

## 🏗️ Architecture

Bwenge OS is built as a microservices architecture with the following components:

### Core Services

- **API Gateway** (Port 8000) - Central routing and authentication
- **Auth Service** (Port 8001) - User authentication and authorization
- **Ingest Service** (Port 8002) - Knowledge ingestion and processing
- **Persona Service** (Port 8003) - AI persona management and RAG
- **Chat Service** (Port 8004) - Real-time messaging and WebSocket
- **3D Service** (Port 8005) - 3D model management and serving
- **Analytics Service** (Port 8006) - Usage analytics and reporting
- **Payments Service** (Port 8007) - Subscription and billing

### Data Layer

- **PostgreSQL** - Primary database for structured data
- **Redis** - Caching and message broker
- **Weaviate** - Vector database for embeddings
- **Object Storage** - File storage for uploads and assets

## 📚 API Documentation

### Authentication

All API endpoints (except auth endpoints) require a JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Key Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `GET /users/me` - Get current user info

#### Knowledge Management
- `POST /knowledge/upload` - Upload knowledge files
- `GET /knowledge/{id}/status` - Check processing status
- `DELETE /knowledge/{id}` - Delete knowledge source

#### Personas
- `POST /personas` - Create new persona
- `GET /personas/{id}` - Get persona details
- `PUT /personas/{id}` - Update persona
- `POST /ai/respond` - Get AI response

#### Real-time Chat
- `WS /ws/chat?persona={id}&session={id}` - WebSocket chat endpoint

#### 3D Models
- `GET /3d/persona/{id}` - Get 3D model for persona
- `POST /3d/persona/{id}/upload` - Upload 3D model

#### Analytics
- `GET /orgs/{id}/reports/weekly` - Weekly analytics report
- `GET /orgs/{id}/students/{id}/progress` - Student progress

#### Payments
- `POST /payments/subscribe` - Create subscription
- `GET /subscriptions/current` - Get current subscription

## 🛠️ Development

### Running Individual Services

Each service can be run independently for development:

```bash
# Auth Service
cd services/auth-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Ingest Service
cd services/ingest-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

### Running Tests

```bash
make test
```

### Code Quality

```bash
make lint    # Run linting
make format  # Format code
```

### Database Operations

```bash
make migrate    # Run migrations
make reset-db   # Reset database
make backup     # Backup database
```

## 🔧 Configuration

### Environment Variables

Key environment variables to configure:

```bash
# Database
DATABASE_URL=postgresql://bwenge:bwenge_dev@localhost:5432/bwenge

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-jwt-secret-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Weaviate
WEAVIATE_URL=http://localhost:8080
```

### Subscription Plans

The system supports multiple subscription tiers:

- **Free**: 100 messages/month, 100MB storage, 5 users
- **Basic**: 1,000 messages/month, 1GB storage, 25 users ($29/month)
- **Pro**: 10,000 messages/month, 10GB storage, 100 users ($99/month)
- **Enterprise**: Unlimited usage ($299/month)

## 📁 Project Structure

```
bwenge-os/
├── services/                 # Microservices
│   ├── api-gateway/         # API Gateway service
│   ├── auth-service/        # Authentication service
│   ├── ingest-service/      # Knowledge ingestion
│   ├── persona-service/     # AI persona management
│   ├── chat-service/        # Real-time chat
│   ├── 3d-service/          # 3D model management
│   ├── analytics-service/   # Analytics and reporting
│   └── payments-service/    # Payment processing
├── libs/                    # Shared libraries
│   └── common/              # Common utilities
├── deploy/                  # Deployment configurations
│   └── kubernetes/          # K8s manifests
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
├── docker-compose.yml       # Development environment
├── Makefile                 # Development commands
└── README.md               # This file
```

## 🚀 Deployment

### Docker Compose (Development)

```bash
make up
```

### Kubernetes (Production)

```bash
kubectl apply -f deploy/kubernetes/
```

### Environment-specific Configurations

- **Development**: Use docker-compose.yml
- **Staging**: Use docker-compose.staging.yml
- **Production**: Use Kubernetes manifests

## 🔍 Monitoring and Observability

### Health Checks

All services expose `/health` endpoints for monitoring.

### Logging

Centralized logging is configured for all services. Logs are structured in JSON format.

### Metrics

Prometheus metrics are exposed by each service for monitoring and alerting.

## 🧪 Testing

### Unit Tests

```bash
pytest services/auth-service/tests/
```

### Integration Tests

```bash
pytest tests/integration/
```

### End-to-End Tests

```bash
pytest tests/e2e/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Write tests for new features
- Update documentation as needed
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the system architecture document

## 🗺️ Roadmap

### ✅ IMPLEMENTATION STATUS: COMPLETE

All planned features have been implemented and are ready for development/testing:

**Sprint 1-2: Foundation** ✅ COMPLETE
- ✅ Core authentication and user management
- ✅ API Gateway and service routing  
- ✅ Knowledge ingestion pipeline with Celery workers

**Sprint 3-4: AI Core** ✅ COMPLETE
- ✅ Persona management and RAG implementation
- ✅ Vector database integration (Weaviate)
- ✅ LLM orchestration (OpenAI integration)

**Sprint 5-6: Real-time Features** ✅ COMPLETE
- ✅ WebSocket chat implementation
- ✅ 3D model integration and management
- ✅ Animation system and signed URLs

**Sprint 7-8: Production Ready** ✅ COMPLETE
- ✅ Analytics and reporting dashboard
- ✅ Payment processing (Stripe integration)
- ✅ Security hardening and comprehensive testing
- ✅ Rate limiting and quota management

**Additional Features Implemented:**
- ✅ Complete database schema with migrations
- ✅ Comprehensive error handling and logging
- ✅ Prometheus metrics integration
- ✅ Session management with Redis
- ✅ File processing (PDF, DOCX, PPTX, audio, video)
- ✅ Multi-tenant organization support
- ✅ Development tools and setup scripts

### 🚀 Ready for Production Deployment

The system is now **feature-complete** and ready for:
- Development and testing
- Pilot deployment with real users
- Production scaling and optimization
