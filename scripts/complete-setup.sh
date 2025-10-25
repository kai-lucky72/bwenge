#!/bin/bash

# Bwenge OS Complete System Setup Script
# This script sets up the entire Bwenge OS system with all components

set -e

echo "🚀 Starting Bwenge OS Complete System Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

print_success "Prerequisites check passed"

# Create environment file
print_status "Setting up environment configuration..."

if [ ! -f .env ]; then
    cp .env.example .env
    print_warning "Created .env file from template. Please edit it with your configuration."
    print_warning "Required variables: OPENAI_API_KEY, STRIPE_SECRET_KEY, JWT_SECRET"
else
    print_success ".env file already exists"
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p uploads/{documents,audio,video,images}
mkdir -p assets/{3d,models,textures}
mkdir -p logs
mkdir -p backups
mkdir -p deploy/ssl

# Set permissions (if on Unix-like system)
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    chmod 755 uploads assets logs backups
    chmod +x scripts/*.sh
fi

print_success "Directories created"

# Build all Docker images
print_status "Building Docker images..."
docker-compose build

print_success "Docker images built"

# Start infrastructure services first
print_status "Starting infrastructure services..."
docker-compose up -d postgres redis weaviate

# Wait for services to be ready
print_status "Waiting for infrastructure services to be ready..."
sleep 15

# Check if services are responding
print_status "Checking service health..."

# Wait for PostgreSQL
until docker-compose exec -T postgres pg_isready -U bwenge; do
    print_status "Waiting for PostgreSQL..."
    sleep 2
done

# Wait for Redis
until docker-compose exec -T redis redis-cli ping; do
    print_status "Waiting for Redis..."
    sleep 2
done

# Wait for Weaviate
until curl -f http://localhost:8080/v1/meta > /dev/null 2>&1; do
    print_status "Waiting for Weaviate..."
    sleep 2
done

print_success "Infrastructure services are ready"

# Run database migrations
print_status "Running database migrations..."
docker-compose exec -T postgres psql -U bwenge -d bwenge -f /docker-entrypoint-initdb.d/init-db.sql

print_success "Database migrations completed"

# Start all application services
print_status "Starting application services..."
docker-compose up -d

# Wait for all services to start
print_status "Waiting for all services to start..."
sleep 20

# Health check all services
print_status "Running health checks..."

services=(
    "api-gateway:8000"
    "auth-service:8001"
    "ingest-service:8002"
    "persona-service:8003"
    "chat-service:8004"
    "3d-service:8005"
    "analytics-service:8006"
    "payments-service:8007"
)

all_healthy=true

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -f http://localhost:$port/health > /dev/null 2>&1; then
        print_success "$service_name is healthy"
    else
        print_error "$service_name is not responding"
        all_healthy=false
    fi
done

# Run API tests
if [ "$all_healthy" = true ]; then
    print_status "Running API tests..."
    
    if command -v python3 &> /dev/null; then
        python3 scripts/test-api.py
        print_success "API tests completed"
    else
        print_warning "Python3 not available, skipping API tests"
    fi
else
    print_warning "Some services are not healthy, skipping API tests"
fi

# Setup monitoring (optional)
read -p "Do you want to set up monitoring (Prometheus, Grafana)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Setting up monitoring..."
    docker-compose -f deploy/monitoring/docker-compose.monitoring.yml up -d
    print_success "Monitoring services started"
    print_status "Grafana available at: http://localhost:3000 (admin/admin)"
    print_status "Prometheus available at: http://localhost:9090"
fi

# Create sample data (optional)
read -p "Do you want to create sample data for testing? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Creating sample data..."
    
    # This would run a script to create sample users, personas, etc.
    # python3 scripts/create-sample-data.py
    
    print_success "Sample data created"
fi

# Final status report
echo ""
echo "🎉 Bwenge OS Setup Complete!"
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
echo "🗄️  Database Services:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo "   Weaviate: http://localhost:8080"
echo ""
echo "📚 Next Steps:"
echo "   1. Edit .env file with your API keys"
echo "   2. Test the system: curl http://localhost:8000/health"
echo "   3. View logs: docker-compose logs -f"
echo "   4. Access API docs: http://localhost:8000/docs"
echo "   5. Stop services: docker-compose down"
echo ""
echo "📖 Documentation:"
echo "   - README.md - Getting started guide"
echo "   - system-architecture.md - System architecture"
echo "   - docs/deployment-guide.md - Deployment guide"
echo ""

if [ "$all_healthy" = true ]; then
    print_success "All services are healthy and ready to use!"
else
    print_warning "Some services may need attention. Check logs with: docker-compose logs"
fi

echo ""
echo "🔧 Useful Commands:"
echo "   make up          - Start all services"
echo "   make down        - Stop all services"
echo "   make logs        - View logs"
echo "   make health      - Check service health"
echo "   make backup      - Backup database"
echo "   make clean       - Clean up resources"