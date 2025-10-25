#!/bin/bash

# Bwenge OS Development Setup Script

set -e

echo "🚀 Setting up Bwenge OS development environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing"
    echo "   Required: OPENAI_API_KEY, STRIPE_SECRET_KEY (for payments)"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads
mkdir -p assets/3d
mkdir -p assets/models
mkdir -p logs

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d postgres redis weaviate

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T postgres psql -U bwenge -d bwenge -f /docker-entrypoint-initdb.d/init-db.sql || true

# Start all services
echo "🌟 Starting all services..."
docker-compose up -d

# Wait for services to start
sleep 15

# Health check
echo "🏥 Running health checks..."
make health

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📍 Services are running at:"
echo "   API Gateway: http://localhost:8000"
echo "   Auth Service: http://localhost:8001"
echo "   Ingest Service: http://localhost:8002"
echo "   Persona Service: http://localhost:8003"
echo "   Chat Service: http://localhost:8004"
echo "   3D Service: http://localhost:8005"
echo "   Analytics Service: http://localhost:8006"
echo "   Payments Service: http://localhost:8007"
echo ""
echo "📚 Next steps:"
echo "   1. Edit .env file with your API keys"
echo "   2. Test the API: curl http://localhost:8000/health"
echo "   3. View logs: make logs"
echo "   4. Stop services: make down"
echo ""
echo "📖 Documentation: README.md"