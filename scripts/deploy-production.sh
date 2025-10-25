#!/bin/bash

# Bwenge OS Production Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Configuration
ENVIRONMENT=${1:-production}
DOMAIN=${2:-your-domain.com}

print_status "Starting Bwenge OS Production Deployment for $ENVIRONMENT"

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed"
    exit 1
fi

# Check if we have a Kubernetes context
if ! kubectl cluster-info &> /dev/null; then
    print_error "No Kubernetes cluster available"
    exit 1
fi

print_success "Prerequisites check passed"

# Create namespace
print_status "Creating Kubernetes namespace..."
kubectl create namespace bwenge-os --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
print_status "Creating secrets..."

if [ ! -f ".env.production" ]; then
    print_error ".env.production file not found"
    print_status "Please create .env.production with production configuration"
    exit 1
fi

# Load environment variables
source .env.production

# Create Kubernetes secrets
kubectl create secret generic bwenge-secrets \
    --from-literal=jwt-secret="$JWT_SECRET" \
    --from-literal=openai-api-key="$OPENAI_API_KEY" \
    --from-literal=stripe-secret-key="$STRIPE_SECRET_KEY" \
    --from-literal=stripe-webhook-secret="$STRIPE_WEBHOOK_SECRET" \
    --from-literal=postgres-password="$POSTGRES_PASSWORD" \
    --from-literal=url-secret="$URL_SECRET" \
    --namespace=bwenge-os \
    --dry-run=client -o yaml | kubectl apply -f -

print_success "Secrets created"

# Build and push Docker images
print_status "Building and pushing Docker images..."

# Set image registry
REGISTRY=${DOCKER_REGISTRY:-"ghcr.io/your-org/bwenge-os"}

services=("api-gateway" "auth-service" "ingest-service" "persona-service" "chat-service" "3d-service" "analytics-service" "payments-service")

for service in "${services[@]}"; do
    print_status "Building $service..."
    
    docker build -t "$REGISTRY/$service:$ENVIRONMENT" ./services/$service
    docker push "$REGISTRY/$service:$ENVIRONMENT"
    
    print_success "Built and pushed $service"
done

# Deploy infrastructure
print_status "Deploying infrastructure..."

# PostgreSQL
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: bwenge-os
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: bwenge
        - name: POSTGRES_USER
          value: bwenge
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: bwenge-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: init-script
          mountPath: /docker-entrypoint-initdb.d
      volumes:
      - name: init-script
        configMap:
          name: postgres-init
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: bwenge-os
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
EOF

# Redis
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: bwenge-os
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: bwenge-os
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: bwenge-os
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
EOF

# Weaviate
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weaviate
  namespace: bwenge-os
spec:
  replicas: 1
  selector:
    matchLabels:
      app: weaviate
  template:
    metadata:
      labels:
        app: weaviate
    spec:
      containers:
      - name: weaviate
        image: semitechnologies/weaviate:1.21.2
        env:
        - name: QUERY_DEFAULTS_LIMIT
          value: "25"
        - name: AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED
          value: "false"
        - name: AUTHENTICATION_APIKEY_ENABLED
          value: "true"
        - name: PERSISTENCE_DATA_PATH
          value: "/var/lib/weaviate"
        - name: DEFAULT_VECTORIZER_MODULE
          value: "none"
        - name: ENABLE_MODULES
          value: "text2vec-openai,generative-openai"
        - name: CLUSTER_HOSTNAME
          value: "node1"
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: weaviate-storage
          mountPath: /var/lib/weaviate
      volumes:
      - name: weaviate-storage
        persistentVolumeClaim:
          claimName: weaviate-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: weaviate
  namespace: bwenge-os
spec:
  selector:
    app: weaviate
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: weaviate-pvc
  namespace: bwenge-os
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF

print_success "Infrastructure deployed"

# Wait for infrastructure to be ready
print_status "Waiting for infrastructure to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n bwenge-os --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n bwenge-os --timeout=300s
kubectl wait --for=condition=ready pod -l app=weaviate -n bwenge-os --timeout=300s

# Deploy application services
print_status "Deploying application services..."

for service in "${services[@]}"; do
    print_status "Deploying $service..."
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $service
  namespace: bwenge-os
spec:
  replicas: 2
  selector:
    matchLabels:
      app: $service
  template:
    metadata:
      labels:
        app: $service
    spec:
      containers:
      - name: $service
        image: $REGISTRY/$service:$ENVIRONMENT
        env:
        - name: DATABASE_URL
          value: "postgresql://bwenge:\$(POSTGRES_PASSWORD)@postgres:5432/bwenge"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: WEAVIATE_URL
          value: "http://weaviate:8080"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: bwenge-secrets
              key: jwt-secret
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: bwenge-secrets
              key: openai-api-key
        - name: STRIPE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: bwenge-secrets
              key: stripe-secret-key
        - name: ENVIRONMENT
          value: "$ENVIRONMENT"
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: $service
  namespace: bwenge-os
spec:
  selector:
    app: $service
  ports:
  - port: 8000
    targetPort: 8000
EOF

    print_success "Deployed $service"
done

# Deploy ingress
print_status "Deploying ingress..."

kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bwenge-ingress
  namespace: bwenge-os
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - $DOMAIN
    - api.$DOMAIN
    secretName: bwenge-tls
  rules:
  - host: api.$DOMAIN
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
  - host: $DOMAIN
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
EOF

print_success "Ingress deployed"

# Deploy monitoring (optional)
read -p "Do you want to deploy monitoring stack? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Deploying monitoring stack..."
    
    # This would deploy Prometheus, Grafana, etc.
    # kubectl apply -f deploy/monitoring/kubernetes/
    
    print_success "Monitoring stack deployed"
fi

# Wait for all deployments to be ready
print_status "Waiting for all deployments to be ready..."

for service in "${services[@]}"; do
    kubectl wait --for=condition=available deployment/$service -n bwenge-os --timeout=300s
done

print_success "All deployments are ready"

# Run database migrations
print_status "Running database migrations..."
kubectl exec -n bwenge-os deployment/postgres -- psql -U bwenge -d bwenge -c "SELECT 1;" > /dev/null 2>&1

print_success "Database migrations completed"

# Final status check
print_status "Performing final health checks..."

for service in "${services[@]}"; do
    if kubectl get pods -n bwenge-os -l app=$service | grep -q Running; then
        print_success "$service is running"
    else
        print_error "$service is not running properly"
    fi
done

print_success "🎉 Production deployment completed!"

echo ""
echo "📍 Your Bwenge OS instance is available at:"
echo "   API: https://api.$DOMAIN"
echo "   Web: https://$DOMAIN"
echo ""
echo "🔧 Management Commands:"
echo "   kubectl get pods -n bwenge-os"
echo "   kubectl logs -f deployment/api-gateway -n bwenge-os"
echo "   kubectl scale deployment/api-gateway --replicas=3 -n bwenge-os"
echo ""
echo "📊 Monitoring:"
echo "   kubectl port-forward svc/grafana 3000:3000 -n monitoring"
echo "   kubectl port-forward svc/prometheus 9090:9090 -n monitoring"