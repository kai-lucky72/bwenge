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
# libs/common/local_llm.py
import requests

class OllamaLLM:
    """Local LLM using Ollama"""
    
    def __init__(self, model="llama2"):
        self.base_url = "http://localhost:11434"
        self.model = model
    
    def chat_completion(self, messages, **kwargs):
        """Chat completion with Ollama"""
        # Convert messages to prompt
        prompt = "\n".join([
            f"{m['role']}: {m['content']}" 
            for m in messages
        ])
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        result = response.json()
        return {
            "choices": [{
                "message": {
                    "content": result["response"],
                    "role": "assistant"
                }
            }]
        }
```

**Pros:**
- ✅ Free, unlimited usage
- ✅ No API keys needed
- ✅ Good quality responses
- ✅ Privacy (all local)

**Cons:**
- ⚠️ Requires 8GB+ RAM
- ⚠️ Slower than OpenAI
- ⚠️ Needs initial download

---

#### **Option C: OpenAI with Free Tier**

If you want real OpenAI for testing:
```bash
# Get free $5 credit (new accounts)
# https://platform.openai.com/signup

# Set in .env
OPENAI_API_KEY=sk-...
USE_MOCK_LLM=false
```

---

### 2. Embeddings (Local Options)

#### **Option A: Mock Embeddings (Fastest)**

```python
# libs/common/mock_embeddings.py
import numpy as np
import hashlib

class MockEmbeddings:
    """Deterministic mock embeddings for testing"""
    
    def create(self, text: str):
        """Create deterministic embedding from text"""
        # Use hash for deterministic results
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        
        # Return 1536-dimensional vector
        embedding = np.random.rand(1536).tolist()
        
        return {
            "data": [{
                "embedding": embedding
            }]
        }
```

---

#### **Option B: Sentence Transformers (Local, Good Quality)**

```bash
# Install
pip install sentence-transformers

# First run downloads model (~400MB)
```

```python
# libs/common/local_embeddings.py
from sentence_transformers import SentenceTransformer

class LocalEmbeddings:
    """Local embeddings using sentence-transformers"""
    
    def __init__(self):
        # Load model (cached after first run)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def create(self, text: str):
        """Create embedding locally"""
        embedding = self.model.encode(text).tolist()
        
        return {
            "data": [{
                "embedding": embedding
            }]
        }
```

**Pros:**
- ✅ Free, unlimited
- ✅ Good quality
- ✅ Fast after initial load

**Cons:**
- ⚠️ Different dimensions (384 vs 1536)
- ⚠️ Initial model download

---

### 3. Audio Transcription (Local Options)

#### **Option A: Mock Transcription**

```python
# libs/common/mock_transcription.py
class MockTranscription:
    """Mock audio transcription"""
    
    def transcribe(self, audio_file):
        """Return mock transcription"""
        return {
            "text": f"[Mock transcription of {audio_file}] This is sample transcribed text for testing purposes."
        }
```

---

#### **Option B: Local Whisper**

```bash
# Install
pip install openai-whisper

# First run downloads model
```

```python
# Already implemented in processors.py!
import whisper

model = whisper.load_model("base")  # ~140MB
result = model.transcribe("audio.mp3")
text = result["text"]
```

**Models:**
- `tiny` - 39MB, fastest
- `base` - 74MB, good balance ✅ Recommended
- `small` - 244MB, better quality
- `medium` - 769MB, high quality
- `large` - 1550MB, best quality

---

### 4. Database (Local - Already Configured)

#### **PostgreSQL via Docker** ✅ Already Setup

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

**No external service needed!**

---

### 5. Vector Database (Local - Already Configured)

#### **Weaviate via Docker** ✅ Already Setup

```yaml
# docker-compose.dev.yml
weaviate:
  image: semitechnologies/weaviate:1.21.2
  po