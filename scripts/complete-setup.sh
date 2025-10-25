#!/bin/bash

# Bwenge OS Complete Setup Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Starting Bwenge OS Complete Setup..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is available (optional)
check_docker() {
    if command -v docker &> /dev/null; then
        print_status "Docker is available"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not available - will set up for local development"
        DOCKER_AVAILABLE=false
    fi
}

# Create .env file from template
setup_environment() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        print_status "Created .env file from template"
        print_warning "Please edit .env file with your API keys and configuration"
        print_info "Required API keys:"
        print_info "  - OPENAI_API_KEY (for AI functionality)"
        print_info "  - STRIPE_SECRET_KEY (for payments - optional for development)"
        print_info "  - JWT_SECRET (generate a secure random string)"
    else
        print_status ".env file already exists"
    fi
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements.txt
    
    print_status "Python dependencies installed"
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    
    mkdir -p uploads
    mkdir -p assets/3d
    mkdir -p assets/models
    mkdir -p logs
    
    print_status "Directories created"
}

# Setup database (if PostgreSQL is available locally)
setup_database() {
    print_info "Setting up database..."
    
    if command -v psql &> /dev/null; then
        print_info "PostgreSQL found - setting up local database"
        
        # Check if database exists
        if psql -lqt | cut -d \| -f 1 | grep -qw bwenge; then
            print_status "Database 'bwenge' already exists"
        else
            # Create database and user
            sudo -u postgres createdb bwenge
            sudo -u postgres createuser bwenge
            sudo -u postgres psql -c "ALTER USER bwenge PASSWORD 'bwenge_dev';"
            sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE bwenge TO bwenge;"
            
            print_status "Database and user created"
        fi
        
        # Run initialization script
        psql -U bwenge -d bwenge -f scripts/init-db.sql
        print_status "Database schema initialized"
        
    else
        print_warning "PostgreSQL not found locally"
        print_info "You can either:"
        print_info "  1. Install PostgreSQL locally"
        print_info "  2. Use Docker: docker run -d -p 5432:5432 -e POSTGRES_DB=bwenge -e POSTGRES_USER=bwenge -e POSTGRES_PASSWORD=bwenge_dev postgres:15"
        print_info "  3. Use a cloud database service"
    fi
}

# Setup Redis (if available locally)
setup_redis() {
    print_info "Setting up Redis..."
    
    if command -v redis-server &> /dev/null; then
        print_status "Redis found locally"
        
        # Check if Redis is running
        if redis-cli ping &> /dev/null; then
            print_status "Redis is already running"
        else
            print_info "Starting Redis server..."
            redis-server --daemonize yes
            print_status "Redis server started"
        fi
    else
        print_warning "Redis not found locally"
        print_info "You can either:"
        print_info "  1. Install Redis locally"
        print_info "  2. Use Docker: docker run -d -p 6379:6379 redis:7-alpine"
        print_info "  3. Use a cloud Redis service"
    fi
}

# Setup Weaviate (Docker recommended)
setup_weaviate() {
    print_info "Setting up Weaviate vector database..."
    
    if [ "$DOCKER_AVAILABLE" = true ]; then
        # Check if Weaviate is already running
        if curl -s http://localhost:8080/v1/meta &> /dev/null; then
            print_status "Weaviate is already running"
        else
            print_info "Starting Weaviate with Docker..."
            docker run -d \
                -p 8080:8080 \
                -e QUERY_DEFAULTS_LIMIT=25 \
                -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED='true' \
                -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
                -e DEFAULT_VECTORIZER_MODULE='none' \
                -e ENABLE_MODULES='text2vec-openai,generative-openai' \
                -e CLUSTER_HOSTNAME='node1' \
                --name weaviate \
                semitechnologies/weaviate:1.21.2
            
            # Wait for Weaviate to start
            print_info "Waiting for Weaviate to start..."
            sleep 10
            
            if curl -s http://localhost:8080/v1/meta &> /dev/null; then
                print_status "Weaviate started successfully"
            else
                print_error "Failed to start Weaviate"
            fi
        fi
    else
        print_warning "Docker not available - Weaviate setup skipped"
        print_info "Please install Docker and run: docker run -d -p 8080:8080 semitechnologies/weaviate:1.21.2"
    fi
}

# Create sample data
create_sample_data() {
    print_info "Creating sample data..."
    
    if [ -f "scripts/create-sample-data.py" ]; then
        source venv/bin/activate
        python scripts/create-sample-data.py
        print_status "Sample data created"
    else
        print_warning "Sample data script not found - skipping"
    fi
}

# Test the setup
test_setup() {
    print_info "Testing the setup..."
    
    if [ -f "scripts/test-api.py" ]; then
        source venv/bin/activate
        
        # Start services in background for testing
        print_info "Starting services for testing..."
        
        # Start auth service
        cd services/auth-service
        uvicorn app.main:app --port 8001 &
        AUTH_PID=$!
        cd ../..
        
        # Start API gateway
        cd services/api-gateway
        uvicorn app.main:app --port 8000 &
        GATEWAY_PID=$!
        cd ../..
        
        # Wait for services to start
        sleep 5
        
        # Run tests
        python scripts/test-api.py
        
        # Stop services
        kill $AUTH_PID $GATEWAY_PID 2>/dev/null || true
        
        print_status "Setup test completed"
    else
        print_warning "Test script not found - skipping tests"
    fi
}

# Generate JWT secret if not set
generate_jwt_secret() {
    if grep -q "your-jwt-secret-key" .env; then
        print_info "Generating JWT secret..."
        JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i "s/your-jwt-secret-key/$JWT_SECRET/g" .env
        print_status "JWT secret generated"
    fi
}

# Main setup flow
main() {
    print_info "Starting Bwenge OS setup..."
    
    check_docker
    setup_environment
    generate_jwt_secret
    install_dependencies
    create_directories
    setup_database
    setup_redis
    setup_weaviate
    create_sample_data
    
    echo ""
    echo "🎉 Bwenge OS Setup Complete!"
    echo "==============================="
    print_status "Backend services are ready to run"
    print_info "Next steps:"
    print_info "  1. Edit .env file with your API keys"
    print_info "  2. Start services: make up (with Docker) or run individual services"
    print_info "  3. Test API: python scripts/test-api.py"
    print_info "  4. Check health: make health"
    echo ""
    print_info "Service URLs (when running):"
    print_info "  - API Gateway: http://localhost:8000"
    print_info "  - Auth Service: http://localhost:8001"
    print_info "  - Ingest Service: http://localhost:8002"
    print_info "  - Persona Service: http://localhost:8003"
    print_info "  - Chat Service: http://localhost:8004"
    print_info "  - 3D Service: http://localhost:8005"
    print_info "  - Analytics Service: http://localhost:8006"
    print_info "  - Payments Service: http://localhost:8007"
    echo ""
    print_info "Default admin login: admin@bwenge.com / admin123"
}

# Run main function
main "$@"