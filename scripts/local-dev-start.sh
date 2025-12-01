#!/bin/bash

# Bwenge OS - Local Development Quick Start
# No external API keys needed!

set -e

echo "🚀 Starting Bwenge OS - Local Development Mode"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env exists, if not copy from .env.local
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env from .env.local...${NC}"
    cp .env.local .env
    echo -e "${GREEN}✅ Created .env file${NC}"
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p uploads assets/3d assets/models logs
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Start Docker services
echo -e "${BLUE}🐳 Starting Docker services (Postgres, Redis, Weaviate)...${NC}"
docker-compose -f docker-compose.dev.yml up -d postgres redis weaviate

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start (15 seconds)...${NC}"
sleep 15

# Check if database is initialized
echo -e "${BLUE}🗄️  Checking database...${NC}"
if docker-compose -f docker-compose.dev.yml exec -T postgres psql -U bwenge -d bwenge -c "\dt" | grep -q "organizations"; then
    echo -e "${GREEN}✅ Database already initialized${NC}"
else
    echo -e "${YELLOW}📊 Initializing database...${NC}"
    docker-compose -f docker-compose.dev.yml exec -T postgres psql -U bwenge -d bwenge < scripts/init-db.sql
    echo -e "${GREEN}✅ Database initialized${NC}"
fi
echo ""

# Check Python dependencies
echo -e "${BLUE}📦 Checking Python dependencies...${NC}"
if python -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}📥 Installing dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi
echo ""

# Start services
echo -e "${BLUE}🚀 Starting Bwenge OS services...${NC}"
echo ""

# Start Celery worker in background
echo -e "${BLUE}   Starting Celery worker...${NC}"
cd services/ingest-service
celery -A app.celery_app worker --loglevel=info > ../../logs/celery.log 2>&1 &
CELERY_PID=$!
cd ../..
echo -e "${GREEN}   ✅ Celery worker started (PID: $CELERY_PID)${NC}"

# Start all services in background
services=("api-gateway" "auth" "ingest" "persona" "chat" "3d" "analytics" "payments")
pids=()

for service in "${services[@]}"; do
    echo -e "${BLUE}   Starting $service service...${NC}"
    python scripts/run-service.py $service > logs/$service.log 2>&1 &
    pid=$!
    pids+=($pid)
    echo -e "${GREEN}   ✅ $service started (PID: $pid)${NC}"
    sleep 2
done

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Bwenge OS is running locally!${NC}"
echo "=============================================="
echo ""
echo "📍 Service URLs:"
echo "   • API Gateway:  http://localhost:8000"
echo "   • API Docs:     http://localhost:8000/docs"
echo "   • Auth Service: http://localhost:8001"
echo "   • Weaviate:     http://localhost:8080"
echo ""
echo "📊 Infrastructure:"
echo "   • PostgreSQL:   localhost:5432"
echo "   • Redis:        localhost:6379"
echo "   • Weaviate:     localhost:8080"
echo ""
echo "📝 Logs:"
echo "   • View logs:    tail -f logs/*.log"
echo "   • Celery:       tail -f logs/celery.log"
echo ""
echo "🧪 Test the API:"
echo "   python scripts/test-api.py"
echo ""
echo "🛑 To stop all services:"
echo "   ./scripts/local-dev-stop.sh"
echo ""
echo "💡 Using MOCK services (no external APIs needed):"
echo "   • Mock LLM (no OpenAI API key)"
echo "   • Mock Embeddings"
echo "   • Mock Whisper"
echo "   • Mock Payments"
echo "   • Console Email"
echo ""
echo "=============================================="

# Save PIDs for stopping later
echo "${pids[@]} $CELERY_PID" > .dev-pids

# Keep script running and show logs
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Trap Ctrl+C
trap './scripts/local-dev-stop.sh' INT

# Wait
wait
