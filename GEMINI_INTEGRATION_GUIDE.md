# Gemini Embeddings Integration Guide

**Google Gemini API for Text Embeddings in Bwenge OS**

---

## 🎯 WHAT WE'VE DONE

We've integrated **Google Gemini embeddings** as the embedding provider for Bwenge OS, replacing OpenAI embeddings.

### Benefits:
- ✅ **768-dimensional vectors** (vs OpenAI's 1536)
- ✅ **Optimized for RAG** (separate query/document modes)
- ✅ **Cost-effective** (Google pricing)
- ✅ **High quality** semantic search
- ✅ **OpenAI-compatible interface** (easy migration)

---

## 📁 FILES CREATED/MODIFIED

### New Files:
1. **`libs/common/gemini_embeddings.py`** (300 lines)
   - GeminiEmbeddings class
   - OpenAI-compatible interface
   - Query and document optimization
   - Error handling and logging

### Modified Files:
1. **`services/ingest-service/app/processors.py`**
   - Updated to use Gemini embeddings
   - Replaced OpenAI client

2. **`services/persona-service/app/rag_engine.py`**
   - Updated to use Gemini embeddings
   - Query-optimized embeddings

3. **`requirements.txt`**
   - Added `google-genai==0.2.0`

4. **`.env.example` & `.env.local`**
   - Added `GEMINI_API_KEY` configuration

---

## 🚀 QUICK START

### Step 1: Install Dependencies
```bash
pip install google-genai==0.2.0
```

### Step 2: Set API Key
```bash
# Add to .env file
echo "GEMINI_API_KEY=AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc" >> .env
```

### Step 3: Test It
```bash
# Test embeddings
python libs/common/gemini_embeddings.py

# Or test full system
python scripts/test-api.py
```

---

## 🔧 CONFIGURATION

### Environment Variables

**Required:**
```bash
GEMINI_API_KEY=AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc
```

**Optional (for LLM):**
```bash
OPENAI_API_KEY=sk-your-openai-key  # Still needed for GPT responses
```

### Complete .env Configuration
```bash
# AI APIs
GEMINI_API_KEY=AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc
OPENAI_API_KEY=sk-your-openai-key  # For LLM responses

# Database
DATABASE_URL=postgresql://bwenge:bwenge_dev@localhost:5432/bwenge
REDIS_URL=redis://localhost:6379
WEAVIATE_URL=http://localhost:8080

# JWT
JWT_SECRET=your-jwt-secret
```

---

## 💡 HOW IT WORKS

### 1. Document Ingestion (Ingest Service)

When a file is uploaded:

```python
# services/ingest-service/app/processors.py

# Text is chunked
chunks = self.chunk_text(text)

# Gemini creates embeddings (optimized for documents)
embeddings = self.create_embeddings(chunks)

# Vectors stored in Weaviate
self.store_vectors(chunks, embeddings, source_id, persona_id, org_id)
```

**Gemini Configuration:**
- Task type: `RETRIEVAL_DOCUMENT`
- Optimized for indexing
- 768-dimensional vectors

---

### 2. Query Processing (Persona Service)

When a user asks a question:

```python
# services/persona-service/app/rag_engine.py

# Gemini creates query embedding (optimized for search)
query_embedding = self._create_query_embedding(user_query)

# Search Weaviate for similar chunks
results = self._search_weaviate(query_embedding, persona_id, org_id)

# Results used for RAG context
```

**Gemini Configuration:**
- Task type: `RETRIEVAL_QUERY`
- Optimized for search
- 768-dimensional vectors

---

## 📊 GEMINI VS OPENAI EMBEDDINGS

| Feature | Gemini | OpenAI |
|---------|--------|--------|
| **Dimensions** | 768 | 1536 |
| **Task Types** | Query/Document | General |
| **Model** | gemini-embedding-001 | text-embedding-ada-002 |
| **Optimization** | RAG-specific | General purpose |
| **Cost** | Competitive | $0.0001/1K tokens |
| **Quality** | High | High |

---

## 🧪 TESTING

### Test Embeddings Directly

```python
from libs.common.gemini_embeddings import GeminiEmbeddings

# Initialize
embeddings = GeminiEmbeddings(api_key="AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc")

# Single text
result = embeddings.create("Hello, world!")
print(f"Dimension: {len(result['data'][0]['embedding'])}")  # 768

# Batch texts
texts = ["Text 1", "Text 2", "Text 3"]
result = embeddings.create(texts)
print(f"Generated {len(result['data'])} embeddings")

# Query embedding (optimized for search)
query_emb = embeddings.embed_query("What is AI?")
print(f"Query dimension: {len(query_emb)}")  # 768

# Document embeddings (optimized for indexing)
doc_embs = embeddings.embed_documents(["Doc 1", "Doc 2"])
print(f"Document embeddings: {len(doc_embs)}")
```

---

### Test Full Pipeline

```bash
# 1. Start services
./scripts/local-dev-start.sh

# 2. Upload a document
curl -X POST http://localhost:8000/knowledge/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf" \
  -F "persona_id=$PERSONA_ID" \
  -F "title=Test Document"

# 3. Check processing status
curl http://localhost:8000/knowledge/$UPLOAD_ID/status \
  -H "Authorization: Bearer $TOKEN"

# 4. Query with RAG
curl -X POST http://localhost:8000/ai/respond \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "'$PERSONA_ID'",
    "session_id": "test-session",
    "user_message": "What is in the document?"
  }'
```

---

## 🔍 WEAVIATE SCHEMA UPDATE

### Important: Vector Dimension Change

Gemini produces **768-dimensional** vectors (vs OpenAI's 1536).

**If you have existing data:**

```bash
# Option 1: Reset Weaviate (loses data)
docker-compose down weaviate
docker volume rm bwenge_weaviate_data
docker-compose up -d weaviate

# Option 2: Create new schema class
# The code automatically creates the correct schema
```

**The schema is auto-created with correct dimensions:**

```python
# In processors.py - ensure_schema()
class_obj = {
    "class": "KnowledgeChunk",
    "vectorizer": "none",  # We provide vectors
    "properties": [
        {"name": "text", "dataType": ["text"]},
        {"name": "source_id", "dataType": ["string"]},
        {"name": "persona_id", "dataType": ["string"]},
        {"name": "org_id", "dataType": ["string"]},
        {"name": "chunk_index", "dataType": ["int"]},
        {"name": "chunk_id", "dataType": ["string"]}
    ]
}
```

---

## 💰 COST COMPARISON

### Gemini Pricing
- **Free tier:** Generous limits
- **Paid:** Competitive pricing
- **No per-token charges** for embeddings in free tier

### OpenAI Pricing
- **$0.0001 per 1K tokens**
- Example: 1M tokens = $0.10

### For Bwenge OS (100 users):
- **Documents:** ~10-30 documents/user = 1,000-3,000 docs
- **Chunks:** ~50 chunks/doc = 50,000-150,000 chunks
- **Embeddings:** 50K-150K embeddings

**With Gemini:** Likely FREE (within limits)  
**With OpenAI:** ~$5-15/month

---

## 🎯 BEST PRACTICES

### 1. Use Task Types Appropriately

```python
# For indexing documents
embeddings.embed_documents(texts)  # Uses RETRIEVAL_DOCUMENT

# For search queries
embeddings.embed_query(query)  # Uses RETRIEVAL_QUERY
```

### 2. Batch Processing

```python
# Good: Batch multiple texts
texts = ["text1", "text2", "text3"]
embeddings.create(texts)

# Avoid: One at a time
for text in texts:
    embeddings.create(text)  # Slower, more API calls
```

### 3. Error Handling

```python
try:
    embeddings = GeminiEmbeddings()
    result = embeddings.create(text)
except ValueError as e:
    # API key not set
    logger.error(f"Configuration error: {e}")
except Exception as e:
    # API error
    logger.error(f"Embedding failed: {e}")
```

### 4. Caching (Future Enhancement)

```python
# Cache embeddings for frequently used texts
# Reduces API calls and improves performance
```

---

## 🔄 MIGRATION FROM OPENAI

### If You Have Existing OpenAI Embeddings:

**Option 1: Fresh Start (Recommended)**
```bash
# Clear Weaviate data
docker-compose down weaviate
docker volume rm bwenge_weaviate_data
docker-compose up -d weaviate

# Re-upload and process documents
# They'll automatically use Gemini embeddings
```

**Option 2: Dual System (Advanced)**
```python
# Keep both embedding systems
# Use feature flag to switch
USE_GEMINI_EMBEDDINGS = os.getenv("USE_GEMINI_EMBEDDINGS", "true")

if USE_GEMINI_EMBEDDINGS == "true":
    embeddings = GeminiEmbeddings()
else:
    embeddings = OpenAIEmbeddings()
```

---

## 🐛 TROUBLESHOOTING

### Error: "GEMINI_API_KEY not found"

```bash
# Check if key is set
echo $GEMINI_API_KEY

# Set it
export GEMINI_API_KEY=AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc

# Or add to .env
echo "GEMINI_API_KEY=AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc" >> .env
```

### Error: "Failed to initialize Gemini client"

```bash
# Install the package
pip install google-genai==0.2.0

# Verify installation
python -c "from google import genai; print('✅ Installed')"
```

### Error: "Dimension mismatch in Weaviate"

```bash
# Reset Weaviate (loses data)
docker-compose down weaviate
docker volume rm bwenge_weaviate_data
docker-compose up -d weaviate

# Re-process documents
```

### Embeddings Not Working

```python
# Test directly
python libs/common/gemini_embeddings.py

# Check logs
tail -f logs/ingest-service.log
tail -f logs/persona-service.log
```

---

## 📚 ADDITIONAL RESOURCES

### Gemini API Documentation
- https://ai.google.dev/docs
- https://ai.google.dev/tutorials/python_quickstart

### Weaviate Documentation
- https://weaviate.io/developers/weaviate

### Our Implementation
- `libs/common/gemini_embeddings.py` - Main implementation
- `services/ingest-service/app/processors.py` - Document processing
- `services/persona-service/app/rag_engine.py` - Query processing

---

## ✅ VERIFICATION CHECKLIST

- [x] Installed `google-genai` package
- [x] Created `GeminiEmbeddings` class
- [x] Updated ingest service processors
- [x] Updated persona service RAG engine
- [x] Added GEMINI_API_KEY to .env
- [x] Updated requirements.txt
- [x] Tested embeddings generation
- [ ] Test document upload and processing
- [ ] Test RAG query with Gemini embeddings
- [ ] Verify Weaviate vector search works

---

## 🎉 SUMMARY

**You now have:**
- ✅ Gemini embeddings integrated
- ✅ 768-dimensional vectors
- ✅ RAG-optimized embeddings
- ✅ OpenAI-compatible interface
- ✅ Cost-effective solution

**Your API Key:**
```
GEMINI_API_KEY=AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc
```

**Start using it:**
```bash
# Add to .env
echo "GEMINI_API_KEY=AIzaSyD3I3OuwRQhBr06qJxyJvRlLp5ir170rtc" >> .env

# Install package
pip install google-genai==0.2.0

# Test it
python libs/common/gemini_embeddings.py

# Start services
./scripts/local-dev-start.sh
```

**Happy embedding! 🚀**
