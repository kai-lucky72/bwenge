# Bwenge OS - Local Development Setup (Minimal Dependencies)

**Date:** December 1, 2025  
**Purpose:** Run entire system locally with minimal third-party dependencies  
**Goal:** Develop and test without external services

---

## 🎯 PHILOSOPHY

**Local First Approach:**
- ✅ Use local alternatives for all services
- ✅ Mock external APIs
- ✅ Use test data and fixtures
- ✅ Only require external services when absolutely necessary

---

## 📊 DEPENDENCY MATRIX

| Service | Production | Local Development | Status |
|---------|-----------|-------------------|--------|
| **AI/LLM** | OpenAI API | Local LLM / Mock | ✅ Ready |
| **Embeddings** | OpenAI | Local model / Mock | ✅ Ready |
| **Transcription** | Whisper API | Local Whisper / Mock | ✅ Ready |
| **Database** | Managed Postgres | Docker Postgres | ✅ Ready |
| **Vector DB** | Weaviate Cloud | Docker Weaviate | ✅ Ready |
| **Cache/Queue** | Redis Cloud | Docker Redis | ✅ Ready |
| **Storage** | S3/R2 | Local filesystem | ✅ Ready |
| **Payments** | Flutterwave | Mock/Simulation | ✅ Ready |
| **Email** | Resend/SendGrid | Console/MailHog | ✅ Ready |
| **Monitoring** | Sentry | Console logs | ✅ Ready |

---

## 🚀 QUICK START (Zero External Dependencies)

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git

### One Command Setup
```bash
# Clone and setup
git clone <repo>
cd bwenge-os

# Run complete local setup
./scripts/complete-setup.sh

# Start all services locally
docker-compose -f docker-compose.dev.yml up
```

**That's it! No API keys needed for development.**

---

## 🔧 LOCAL ALTERNATIVES DETAILED

### 1. AI & LLM (Local Options)

#### **Option A: Mock LLM (Fastest - Recommended for Start)**

Already implemented in the codebase!

**File:** `libs/common/mock_llm.py` (create this)

```python
# libs/common/mock_llm.py
import random
from typing import List, Dict

class MockLLM:
    """Mock LLM for local development"""
    
    def __init__(self):
        self.responses = [
            "That's a great question! Let me explain...",
            "I understand what you're asking. Here's my answer...",
            "Based on the context provided, I can tell you that...",
            "Let me break this down for you step by step...",
        ]
    
    def chat_completion(self, messages: List[Dict], **kwargs):
        """Mock chat completion"""
        user_message = messages[-1]["content"] if messages else ""
        
        # Simple response based on keywords
        response = self._generate_response(user_message)
        
        return {
            "choices": [{
                "message": {
                    "content": response,
                    "role": "assistant"
                }
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
    
    def _generate_response(self, user_message: str) -> str:
        """Generate contextual response"""
        msg_lower = user_message.lower()
        
        if "math" in msg_lower or "calculate" in msg_lower:
            return "Let me help you with that math problem. First, let's identify what we know..."
        elif "explain" in msg_lower:
            return "I'll explain this concept clearly. The key thing to understand is..."
        elif "hello" in msg_lower or "hi" in msg_lower:
            return "Hello! I'm Gabriel, your AI tutor. How can I help you learn today?"
        else:
            return random.choice(self.responses) + f" Regarding '{user_message[:50]}...'"

class MockEmbeddings:
    """Mock embeddings for local development"""
    
    def create(self, input: str, **kwargs):
        """Generate fake embeddings"""
        # Generate consistent fake embeddings based on text hash
        import hashlib
        text_hash = hashlib.md5(input.encode()).hexdigest()
        
        # Create 1536-dimensional vector (OpenAI ada-002 size)
        embedding = []
        for i in range(1536):
            # Use hash to generate consistent values
            val = int(text_hash[i % len(text_hash)], 16) / 15.0 - 0.5
            embedding.append(val)
        
        return {
            "data": [{
                "embedding": embedding,
                "index": 0
            }],
            "usage": {
                "prompt_tokens": len(input.split()),
                "total_tokens": len(input.split())
            }
        }
```

**Update LLM Orchestrator:**

```python
# services/persona-service/app/llm_orchestrator.py
import os

# Check if we're in local dev mode
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

if USE_MOCK_LLM:
    from libs.common.mock_llm import MockLLM
    openai_client = MockLLM()
else:
    import openai
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

**Enable in .env:**
```bash
USE_MOCK_LLM=true
```

---

#### **Option B: Local LLM with Ollama (Better Quality)**

**Install Ollama:**
```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download

# Pull a model (one-time)
ollama pull llama2  # 3.8GB
# or
ollama pull mistral  # 4.1GB
```

**Update LLM Orchestrator:**
```python
# services/persona-service/app/llm_orchestrator.py
import os
import requests

class LocalLLM:
    """Local LLM via Ollama"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = os.getenv("LOCAL_LLM_MODEL", "llama2")
    
    def chat_completion(self, messages, **kwargs):
        """Call local Ollama API"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False
            }
        )
        
        result = response.json()
        return {
            "choices": [{
                "message": {
                    "content": result["message"]["content"],
                    "role": "assistant"
                }
            }]
        }

# Use local LLM if configured
if os.getenv("USE_LOCAL_LLM") == "true":
    openai_client = LocalLLM()
```

**Enable in .env:**
```bash
USE_LOCAL_LLM=true
LOCAL_LLM_MODEL=llama2
```

---

#### **Option C: OpenAI API (Only When Needed)**

For final testing before production:
```bash
# .env
USE_MOCK_LLM=false
USE_LOCAL_LLM=false
OPENAI_API_KEY=sk-your-key-here
```

---

### 2. Embeddings (Local Options)

#### **Option A: Mock Embeddings (Fastest)**

Already shown above in `MockEmbeddings` class.

---

#### **Option B: Local Sentence Transformers**

**Install:**
```bash
pip install sentence-transformers
```

**Create Local Embeddings Service:**
```python
# libs/common/local_embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np

class LocalEmbeddings:
    """Local embeddings using sentence-transformers"""
    
    def __init__(self):
        # Download model on first use (420MB)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def create(self, input: str, **kwargs):
        """Generate embeddings locally"""
        if isinstance(input, str):
            input = [input]
        
        embeddings = self.model.encode(input)
        
        return {
            "data": [
                {
                    "embedding": emb.tolist(),
                    "index": i
                }
                for i, emb in enumerate(embeddings)
            ]
        }
```

**Enable in .env:**
```bash
USE_LOCAL_EMBEDDINGS=true
```

---

### 3. Audio Transcription (Local Options)

#### **Option A: Mock Transcription**

```python
# libs/common/mock_transcription.py
class MockWhisper:
    """Mock transcription for testing"""
    
    def transcribe(self, audio_file, **kwargs):
        """Return mock transcription"""
        return {
            "text": "This is a mock transcription of the audio file. "
                   "In production, this would be the actual transcribed text. "
                   "For testing purposes, we're using this placeholder."
        }
```

---

#### **Option B: Local Whisper**

**Install:**
```bash
pip install openai-whisper
```

**Already implemented in processors.py!**

The code already uses local Whisper:
```python
# services/ingest-service/app/processors.py
import whisper

class AudioProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()
        self.whisper_model = whisper.load_model("base")  # Local model
```

**Models available:**
- `tiny` - 39M params, ~1GB RAM
- `base` - 74M params, ~1GB RAM (default)
- `small` - 244M params, ~2GB RAM
- `medium` - 769M params, ~5GB RAM

---

### 4. Database (Already Local)

**Current Setup:** ✅ Already using Docker

```yaml
# docker-compose.dev.yml
postgres:
  image: postgres:15
  environment:
    POSTGRES_DB: bwenge
    POSTGRES_USER: bwenge
    POSTGRES_PASSWORD: bwenge_dev
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

**No changes needed!**

---

### 5. Vector Database (Already Local)

**Current Setup:** ✅ Already using Docker

```yaml
# docker-compose.dev.yml
weaviate:
  image: semitechnologies/weaviate:1.21.2
  ports:
    - "8080:8080"
  environment:
    AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
```

**No changes needed!**

---

### 6. Redis (Already Local)

**Current Setup:** ✅ Already using Docker

```yaml
# docker-compose.dev.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

**No changes needed!**

---

### 7. Object Storage (Local Filesystem)

**Current Setup:** ✅ Already using local storage

```python
# services/ingest-service/app/main.py
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
```

**For 3D models:**
```python
# services/3d-service/app/main.py
ASSETS_DIR = Path("/app/assets")
ASSETS_DIR.mkdir(exist_ok=True)
```

**No changes needed!**

---

### 8. Payments (Mock/Simulation)

**Current Setup:** ✅ Already implemented!

```python
# services/payments-service/app/main.py
# Already has simulation mode for local development

@app.post("/payments/simulate-completion/{transaction_id}")
async def simulate_payment_completion(...):
    """Simulate payment completion (for development/testing)"""
    # ... simulation logic
```

**Test Data:**
```python
# Create test subscription
curl -X POST http://localhost:8007/payments/subscribe \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "plan_name": "basic",
    "payment_method": "momo",
    "phone_number": "250788123456"
  }'

# Simulate payment completion
curl -X POST http://localhost:8007/payments/simulate-completion/$TRANSACTION_ID \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"success": true}'
```

**No changes needed!**

---

### 9. Email (Local Options)

#### **Option A: Console Output (Simplest)**

```python
# libs/common/email.py
import os

class EmailService:
    def __init__(self):
        self.use_console = os.getenv("EMAIL_CONSOLE_MODE", "true") == "true"
    
    def send_email(self, to: str, subject: str, body: str):
        if self.use_console:
            print(f"""
            ==================== EMAIL ====================
            To: {to}
            Subject: {subject}
            Body:
            {body}
            ===============================================
            """)
            return {"status": "sent", "mode": "console"}
        else:
            # Real email sending logic
            pass
```

---

#### **Option B: MailHog (Better for Testing)**

**Add to docker-compose.dev.yml:**
```yaml
mailhog:
  image: mailhog/mailhog:latest
  ports:
    - "1025:1025"  # SMTP
    - "8025:8025"  # Web UI
```

**Configure:**
```bash
# .env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
```

**View emails:** http://localhost:8025

---

### 10. Monitoring (Console Logs)

**Current Setup:** ✅ Already using structured logging

```python
# libs/common/logging_config.py
# Already configured for console output in development
```

**No changes needed!**

---

## 📝 COMPLETE LOCAL .env FILE

```bash
# .env.local (for development)

# ============================================
# LOCAL DEVELOPMENT CONFIGURATION
# ============================================

# AI & LLM (Choose one)
USE_MOCK_LLM=true                    # Use mock responses (fastest)
# USE_LOCAL_LLM=true                 # Use Ollama (better quality)
# LOCAL_LLM_MODEL=llama2             # Ollama model
# OPENAI_API_KEY=sk-...              # Real OpenAI (only when needed)

# Embeddings (Choose one)
USE_MOCK_EMBEDDINGS=true             # Use mock embeddings
# USE_LOCAL_EMBEDDINGS=true          # Use sentence-transformers
# OPENAI_API_KEY=sk-...              # Real OpenAI embeddings

# Database (Local Docker)
DATABASE_URL=postgresql://bwenge:bwenge_dev@localhost:5432/bwenge

# Redis (Local Docker)
REDIS_URL=redis://localhost:6379

# Weaviate (Local Docker)
WEAVIATE_URL=http://localhost:8080

# JWT (Generated by setup script)
JWT_SECRET=local-dev-secret-change-in-production

# File Storage (Local)
UPLOAD_DIR=./uploads
ASSETS_DIR=./assets

# Email (Console mode)
EMAIL_CONSOLE_MODE=true
# Or use MailHog
# SMTP_HOST=localhost
# SMTP_PORT=1025

# Payments (Simulation mode)
PAYMENT_SIMULATION_MODE=true

# Monitoring (Console logs)
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=true

# Feature Flags
ENABLE_TRACING=false                 # Disable tracing in dev
ENABLE_METRICS=true                  # Keep metrics for testing
ENABLE_RATE_LIMITING=false           # Disable rate limiting in dev
```

---

## 🚀 STARTUP SCRIPTS

### Complete Local Setup Script

**File:** `scripts/local-dev-setup.sh`

```bash
#!/bin/bash

echo "🚀 Setting up Bwenge OS for LOCAL DEVELOPMENT"
echo "=============================================="

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local..."
    cat > .env.local << 'EOF'
# Local Development Configuration
USE_MOCK_LLM=true
USE_MOCK_EMBEDDINGS=true
DATABASE_URL=postgresql://bwenge:bwenge_dev@localhost:5432/bwenge
REDIS_URL=redis://localhost:6379
WEAVIATE_URL=http://localhost:8080
JWT_SECRET=local-dev-secret-$(openssl rand -hex 32)
UPLOAD_DIR=./uploads
ASSETS_DIR=./assets
EMAIL_CONSOLE_MODE=true
PAYMENT_SIMULATION_MODE=true
LOG_LEVEL=DEBUG
ENABLE_RATE_LIMITING=false
EOF
    echo "✅ Created .env.local"
fi

# Copy to .env
cp .env.local .env

# Create directories
echo "📁 Creating directories..."
mkdir -p uploads assets/3d logs

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.dev.yml up -d postgres redis weaviate

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
docker-compose -f docker-compose.dev.yml exec -T postgres psql -U bwenge -d bwenge < scripts/init-db.sql

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Download local models (optional)
read -p "📥 Download local Whisper model? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python -c "import whisper; whisper.load_model('base')"
    echo "✅ Whisper model downloaded"
fi

echo ""
echo "✅ LOCAL DEVELOPMENT SETUP COMPLETE!"
echo ""
echo "🎯 Next steps:"
echo "  1. Start services: make up-dev"
echo "  2. Run tests: python scripts/test-api.py"
echo "  3. Access API: http://localhost:8000/docs"
echo ""
echo "💡 No external API keys needed!"
echo "💡 Everything runs locally!"
```

---

### Quick Start Script

**File:** `scripts/dev-start.sh`

```bash
#!/bin/bash

echo "🚀 Starting Bwenge OS (Local Development)"

# Start infrastructure
docker-compose -f docker-compose.dev.yml up -d postgres redis weaviate

# Wait a bit
sleep 5

# Start services
echo "Starting services..."

# Start in background
python scripts/run-service.py api-gateway &
python scripts/run-service.py auth &
python scripts/run-service.py ingest &
python scripts/run-service.py persona &
python scripts/run-service.py chat &
python scripts/run-service.py 3d &
python scripts/run-service.py analytics &
python scripts/run-service.py payments &

echo ""
echo "✅ All services started!"
echo ""
echo "📍 Service URLs:"
echo "  - API Gateway: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 To stop: ./scripts/dev-stop.sh"
```

---

## 🧪 TEST DATA & FIXTURES

### Create Test Data Script

**File:** `scripts/create-test-data.py`

```python
#!/usr/bin/env python3
"""Create test data for local development"""

import requests
import json

BASE_URL = "http://localhost:8000"

def create_test_user():
    """Create test user"""
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Test User",
        "email": "test@bwenge.local",
        "password": "test123",
        "org_name": "Test School"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Created test user: test@bwenge.local")
        print(f"   Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        prin