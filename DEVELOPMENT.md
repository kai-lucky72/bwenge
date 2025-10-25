# 🛠️ Bwenge OS Development Guide

This guide covers everything you need to know to develop and run Bwenge OS locally.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ 
- PostgreSQL 12+
- Redis 6+
- Git

### Setup

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd bwenge-os
   
   # Windows
   scripts\complete-setup.bat
   
   # Linux/Mac
   chmod +x scripts/complete-setup.sh
   ./scripts/complete-setup.sh
   ```

2. **Configure environment:**
   ```bash
   # Edit .env file with your API keys
   nano .env  # or use your preferred editor
   ```

3. **Required API Keys:**
   - `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
   - `STRIPE_SECRET_KEY` - Optional, for payment testing
   - `JWT_SECRET` - Auto-generated during setup

## 🏗️ Architecture Overview

Bwenge OS is built as a microservices architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway    │    │   Auth Service  │
│   (Next.js)     │◄──►│   Port 8000      │◄──►│   Port 8001     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │ Ingest       │ │ Persona     │ │ Chat       │
        │ Service      │ │ Service     │ │ Service    │
        │ Port 8002    │ │ Port 8003   │ │ Port 8004  │
        └──────────────┘ └─────────────┘ └────────────┘
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │ 3D Service   │ │ Analytics   │ │ Payments   │
        │ Port 8005    │ │ Service     │ │ Service    │
        └──────────────┘ │ Port 8006   │ │ Port 8007  │
                         └─────────────┘ └────────────┘
```

### Data Layer

- **PostgreSQL** - Primary database for structured data
- **Redis** - Caching, sessions, and message broker
- **Weaviate** - Vector database for embeddings and RAG

## 🔧 Development Workflow

### Running Services

**Option 1: Individual Services (Recommended for Development)**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

# Run specific service
python scripts/run-service.py auth
python scripts/run-service.py api-gateway
python scripts/run-service.py persona

# List all services
python scripts/run-service.py --list
```

**Option 2: Docker Compose (If Docker is available)**
```bash
make build
make up
```

### Service Dependencies

Services should be started in this order for full functionality:

1. **Database services** (PostgreSQL, Redis, Weaviate)
2. **Auth Service** (8001) - Required by all other services
3. **API Gateway** (8000) - Routes requests to other services
4. **Core services** (Ingest, Persona, Chat, 3D, Analytics, Payments)

### Testing

```bash
# Test API endpoints
python scripts/test-api.py

# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health
# ... etc for other services

# Run unit tests (when available)
pytest
```

## 📁 Project Structure

```
bwenge-os/
├── services/                 # Microservices
│   ├── api-gateway/         # Central API gateway
│   ├── auth-service/        # Authentication
│   ├── ingest-service/      # Knowledge processing
│   ├── persona-service/     # AI personas and RAG
│   ├── chat-service/        # Real-time chat
│   ├── 3d-service/          # 3D model management
│   ├── analytics-service/   # Analytics and reporting
│   └── payments-service/    # Subscription management
├── libs/common/             # Shared libraries
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   ├── auth.py             # Authentication utilities
│   ├── database.py         # Database connection
│   └── ...                 # Other utilities
├── scripts/                 # Development scripts
├── uploads/                 # File uploads (created during setup)
├── assets/                  # Static assets
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
└── docker-compose.yml       # Docker configuration
```

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login  
- `POST /auth/refresh` - Refresh access token
- `GET /users/me` - Get current user info

### Knowledge Management
- `POST /knowledge/upload` - Upload knowledge files
- `GET /knowledge/{id}/status` - Check processing status
- `DELETE /knowledge/{id}` - Delete knowledge source

### AI & Personas
- `POST /personas` - Create new persona
- `GET /personas/{id}` - Get persona details
- `PUT /personas/{id}` - Update persona
- `POST /ai/respond` - Get AI response

### Real-time Chat
- `WS /ws/chat?persona={id}&session={id}` - WebSocket chat

### 3D Models
- `GET /3d/persona/{id}` - Get 3D model for persona
- `POST /3d/persona/{id}/upload` - Upload 3D model

## 🧪 Development Tips

### Adding New Features

1. **Database Changes:**
   ```bash
   # Modify models in libs/common/models.py
   # Update schemas in libs/common/schemas.py
   # Add migration to scripts/init-db.sql
   ```

2. **New API Endpoints:**
   ```bash
   # Add to appropriate service in services/{service}/app/main.py
   # Add route to API Gateway in services/api-gateway/app/main.py
   # Update API documentation
   ```

3. **Testing:**
   ```bash
   # Add tests to scripts/test-api.py
   # Test manually with curl or Postman
   ```

### Debugging

1. **Check Logs:**
   ```bash
   # Services log to stdout in JSON format
   # Check individual service terminals
   ```

2. **Database Issues:**
   ```bash
   # Connect to database
   psql -U bwenge -d bwenge
   
   # Check tables
   \dt
   
   # Check data
   SELECT * FROM users LIMIT 5;
   ```

3. **Redis Issues:**
   ```bash
   # Connect to Redis
   redis-cli
   
   # Check keys
   KEYS *
   
   # Check specific key
   GET session:some-session-id
   ```

### Common Issues

1. **Import Errors:**
   - Ensure `PYTHONPATH` includes project root
   - Check that `libs/common` is accessible

2. **Database Connection:**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env
   - Ensure database and user exist

3. **API Key Issues:**
   - Verify OPENAI_API_KEY is set
   - Check API key has sufficient credits
   - Test with simple OpenAI API call

4. **Port Conflicts:**
   - Check if ports 8000-8007 are available
   - Modify ports in service configurations if needed

## 🚀 Production Deployment

For production deployment, see the main README.md file. Key considerations:

- Use proper environment variables
- Set up SSL/TLS certificates
- Configure proper CORS origins
- Use production-grade databases
- Set up monitoring and logging
- Configure backup strategies

## 🤝 Contributing

1. Create feature branch from `main`
2. Make changes and test locally
3. Update documentation if needed
4. Submit pull request with description

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings to functions
- Keep functions focused and small
- Use meaningful variable names

### Commit Messages

Use conventional commit format:
- `feat: add new persona creation endpoint`
- `fix: resolve database connection issue`
- `docs: update API documentation`
- `refactor: improve error handling`

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Redis Documentation](https://redis.io/documentation)

## 🆘 Getting Help

1. Check this documentation first
2. Look at existing code examples
3. Check service logs for errors
4. Create an issue with detailed description
5. Include error messages and steps to reproduce