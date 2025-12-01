# Bwenge OS - Local Development Guide

**Zero External Dependencies Required!** 🎉

---

## 🎯 QUICK START (5 Minutes)

### Step 1: Prerequisites
```bash
# Install these first:
- Python 3.11+
- Docker & Docker Compose
- Git
```

### Step 2: Clone & Setup
```bash
git clone <repo>
cd bwenge-os

# Make scripts executable
chmod +x scripts/*.sh

# Start everything
./scripts/local-dev-start.sh
```

### Step 3: Test
```bash
# In another terminal
python scripts/test-api.py
```

**That's it! No API keys needed!** ✅

---

## 💡 WHAT'S RUNNING LOCALLY

### Mock Services (No External APIs)
- ✅ **Mock LLM** - Simulates OpenAI GPT
- ✅ **Mock Embeddings** - Simulates OpenAI embeddings
- ✅ **Mock Whisper** - Simulates audio transcription
- ✅ **Mock Payments** - Simulates Flutterwave
- ✅ **Console Email** - Prints emails to console

### Real Services (Docker)
- ✅ **PostgreSQL** - Real database
- ✅ **Redis** - Real cache/queue
- ✅ **Weaviate** - Real vector database

### Your Services
- ✅ All 8 microservices running locally
- ✅ Celery worker for async tasks

---

## 📁 FILES CREATED

```
bwenge-os/
├── .env.local                      # Local config (no API keys)
├── libs/common/mock_services.py    # Mock implementations
├── scripts/
│   ├── local-dev-start.sh         # Start everything
│   └── local-dev-stop.sh          # Stop everything
└── LOCAL_DEVELOPMENT_SETUP.md      # Full documentation
```

---

## 🔧 CONFIGURATION

### Current Setup (.env.local)
```bash
# Mock services (no external APIs)
USE_MOCK_LLM=true
USE_MOCK_EMBEDDINGS=true
USE_MOCK_WHISPER=true
EMAIL_CONSOLE_MODE=true
PAYMENT_SIMULATION_MODE=true

# Local infrastructure
DATABASE_URL=postgresql://bwenge:bwenge_dev@localhost:5432/bwenge
REDIS_URL=redis://localhost:6379
WEAVIATE_URL=http://localhost:8080
```

### To Use Real Services (Optional)
```bash
# Edit .env and change:
USE_MOCK_LLM=false
OPENAI_API_KEY=sk-your-key-here
```

---

## 🧪 TESTING

### Test Everything
```bash
python scripts/test-api.py
```

### Test Individual Services
```bash
# Test auth
curl http://localhost:8001/health

# Test API gateway
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

### Create Test Data
```bash
# Register test user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@bwenge.local",
    "password": "test123",
    "org_name": "Test School"
  }'
```

---

## 📊 MONITORING

### View Logs
```bash
# All services
tail -f logs/*.log

# Specific service
tail -f logs/api-gateway.log

# Celery worker
tail -f logs/celery.log
```

### Check Service Status
```bash
# Check if services are running
ps aux | grep python

# Check Docker services
docker-compose -f docker-compose.dev.yml ps
```

---

## 🐛 TROUBLESHOOTING

### Services Won't Start
```bash
# Check if ports are in use
lsof -i :8000
lsof -i :5432

# Kill processes
kill -9 <PID>

# Restart Docker
docker-compose -f docker-compose.dev.yml restart
```

### Database Issues
```bash
# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d postgres
sleep 10
docker-compose -f docker-compose.dev.yml exec -T postgres psql -U bwenge -d bwenge < scripts/init-db.sql
```

### Mock Services Not Working
```bash
# Check .env file
cat .env | grep USE_MOCK

# Should show:
# USE_MOCK_LLM=true
# USE_MOCK_EMBEDDINGS=true
# USE_MOCK_WHISPER=true
```

---

## 🚀 DEVELOPMENT WORKFLOW

### 1. Start Development
```bash
./scripts/local-dev-start.sh
```

### 2. Make Changes
```bash
# Edit code in your IDE
# Services auto-reload on changes
```

### 3. Test Changes
```bash
# Run tests
python scripts/test-api.py

# Or test manually
curl http://localhost:8000/...
```

### 4. Stop Development
```bash
./scripts/local-dev-stop.sh
```

---

## 💰 COST COMPARISON

### Local Development (This Setup)
- **Cost:** $0/month
- **External APIs:** None
- **Perfect for:** Development, testing, learning

### With Real APIs
- **Cost:** $50-100/month
- **External APIs:** OpenAI
- **Perfect for:** Final testing, production prep

---

## 🎓 WHAT YOU CAN DO

### Without Any API Keys:
- ✅ Develop all features
- ✅ Test all endpoints
- ✅ Run integration tests
- ✅ Debug issues
- ✅ Learn the system
- ✅ Demo to stakeholders

### What You Need Real APIs For:
- ❌ Production deployment
- ❌ Real AI responses
- ❌ Real audio transcription
- ❌ Real payments

---

## 📚 NEXT STEPS

### Phase 1: Local Development (Current)
- Use mock services
- Develop features
- Write tests
- Debug issues

### Phase 2: Integration Testing
- Add OpenAI API key
- Test real AI responses
- Test real transcription
- Keep other mocks

### Phase 3: Production Prep
- Add all real services
- Deploy to staging
- Full integration testing
- Performance testing

---

## 🔑 WHEN TO ADD REAL API KEYS

### Add OpenAI API Key When:
- You need to test real AI quality
- You're preparing for production
- You want to demo real responses

### Add Payment API When:
- You're testing payment flows
- You're preparing for launch
- You need real transaction testing

### Add Email Service When:
- You're testing email flows
- You're preparing for production
- You need real email delivery

---

## ✅ CHECKLIST

### Initial Setup
- [ ] Clone repository
- [ ] Install Docker
- [ ] Install Python 3.11+
- [ ] Run `./scripts/local-dev-start.sh`
- [ ] Test with `python scripts/test-api.py`

### Daily Development
- [ ] Start services: `./scripts/local-dev-start.sh`
- [ ] Make changes
- [ ] Test changes
- [ ] Stop services: `./scripts/local-dev-stop.sh`

### Before Committing
- [ ] Run tests
- [ ] Check logs for errors
- [ ] Test affected endpoints
- [ ] Update documentation

---

## 🎉 BENEFITS OF THIS SETUP

### For Development:
- ✅ **Fast** - No API latency
- ✅ **Free** - No API costs
- ✅ **Reliable** - No API downtime
- ✅ **Offline** - Works without internet
- ✅ **Consistent** - Same responses every time

### For Testing:
- ✅ **Predictable** - Mock responses are consistent
- ✅ **Fast** - No network delays
- ✅ **Isolated** - No external dependencies
- ✅ **Debuggable** - Full control over responses

### For Learning:
- ✅ **No barriers** - Start immediately
- ✅ **No costs** - Learn for free
- ✅ **Full system** - All features available
- ✅ **Safe** - Can't break production

---

## 📞 SUPPORT

### Common Questions:

**Q: Do I need any API keys?**  
A: No! Everything runs locally with mocks.

**Q: Will this work offline?**  
A: Yes! After initial Docker image downloads.

**Q: How do I add real OpenAI?**  
A: Set `USE_MOCK_LLM=false` and add `OPENAI_API_KEY` in .env

**Q: Can I deploy this to production?**  
A: No, you need real APIs for production. This is for development only.

**Q: How much does this cost?**  
A: $0! Everything is free and local.

---

## 🚀 YOU'RE READY!

Start developing with:
```bash
./scripts/local-dev-start.sh
```

Happy coding! 🎉
