# Bwenge OS Deployment Guide

This guide covers deploying Bwenge OS in different environments.

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for production)
- Domain name and SSL certificates
- External service accounts (OpenAI, Stripe, etc.)

## Environment Setup

### Development

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd bwenge-os
   ./scripts/setup-dev.sh
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start services**
   ```bash
   make up
   ```

### Staging

1. **Create staging environment file**
   ```bash
   cp .env.example .env.staging
   # Configure staging-specific settings
   ```

2. **Deploy to staging**
   ```bash
   docker-compose -f docker-compose.staging.yml up -d
   ```

### Production

#### Option 1: Docker Compose

1. **Prepare production environment**
   ```bash
   cp .env.example .env.production
   # Configure production settings
   ```

2. **Deploy**
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```

#### Option 2: Kubernetes

1. **Configure secrets**
   ```bash
   kubectl create namespace bwenge-os
   kubectl apply -f deploy/kubernetes/secrets.yaml
   ```

2. **Deploy services**
   ```bash
   kubectl apply -f deploy/kubernetes/
   ```

## Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/bwenge

# Redis
REDIS_URL=redis://host:6379

# JWT Secret (generate a secure random string)
JWT_SECRET=your-secure-jwt-secret

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key

# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_your-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Weaviate
WEAVIATE_URL=http://weaviate:8080

# File Storage
UPLOAD_DIR=/app/uploads
ASSETS_DIR=/app/assets

# Base URL for signed URLs
BASE_URL=https://your-domain.com
```

### SSL/TLS Configuration

For production, configure SSL termination at the load balancer or reverse proxy level.

#### Nginx Configuration Example

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws/ {
        proxy_pass http://localhost:8004;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Database Setup

### PostgreSQL

1. **Create database and user**
   ```sql
   CREATE DATABASE bwenge;
   CREATE USER bwenge WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE bwenge TO bwenge;
   ```

2. **Run migrations**
   ```bash
   psql -U bwenge -d bwenge -f scripts/init-db.sql
   ```

### Backup Strategy

```bash
# Daily backup
pg_dump -U bwenge bwenge > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U bwenge bwenge | gzip > $BACKUP_DIR/bwenge_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "bwenge_*.sql.gz" -mtime +7 -delete
```

## Monitoring and Logging

### Health Checks

All services expose `/health` endpoints. Configure your load balancer to use these for health checks.

### Logging

Configure centralized logging:

```yaml
# docker-compose.yml logging section
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Metrics

Services expose Prometheus metrics at `/metrics` endpoints.

Example Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'bwenge-services'
    static_configs:
      - targets: 
        - 'api-gateway:8000'
        - 'auth-service:8001'
        - 'ingest-service:8002'
        # ... other services
```

## Security Considerations

### Network Security

1. **Use internal networks for service communication**
2. **Expose only necessary ports**
3. **Configure firewall rules**

### Application Security

1. **Use strong JWT secrets**
2. **Enable HTTPS everywhere**
3. **Implement rate limiting**
4. **Regular security updates**

### Data Security

1. **Encrypt sensitive data at rest**
2. **Use secure database connections**
3. **Implement proper access controls**
4. **Regular backups with encryption**

## Scaling

### Horizontal Scaling

Services can be scaled horizontally:

```bash
# Docker Compose
docker-compose up -d --scale auth-service=3 --scale persona-service=2

# Kubernetes
kubectl scale deployment auth-service --replicas=3
```

### Database Scaling

1. **Read replicas for read-heavy workloads**
2. **Connection pooling (PgBouncer)**
3. **Database partitioning for large datasets**

### Caching

1. **Redis for session storage and caching**
2. **CDN for static assets**
3. **Application-level caching**

## Troubleshooting

### Common Issues

1. **Service won't start**
   - Check logs: `docker-compose logs service-name`
   - Verify environment variables
   - Check database connectivity

2. **Database connection errors**
   - Verify DATABASE_URL
   - Check network connectivity
   - Ensure database is running

3. **Authentication issues**
   - Verify JWT_SECRET is consistent across services
   - Check token expiration
   - Validate user permissions

### Log Analysis

```bash
# View logs for specific service
docker-compose logs -f auth-service

# Search for errors
docker-compose logs | grep ERROR

# Monitor real-time logs
docker-compose logs -f --tail=100
```

## Performance Optimization

### Database Optimization

1. **Add appropriate indexes**
2. **Optimize queries**
3. **Use connection pooling**
4. **Regular VACUUM and ANALYZE**

### Application Optimization

1. **Enable caching**
2. **Optimize API responses**
3. **Use async processing for heavy tasks**
4. **Implement pagination**

### Infrastructure Optimization

1. **Use SSD storage**
2. **Adequate RAM for caching**
3. **Load balancing**
4. **CDN for static content**

## Maintenance

### Regular Tasks

1. **Database backups**
2. **Log rotation**
3. **Security updates**
4. **Performance monitoring**
5. **Capacity planning**

### Update Process

1. **Test updates in staging**
2. **Create database backup**
3. **Deploy with rolling updates**
4. **Monitor for issues**
5. **Rollback if necessary**

## Support

For deployment issues:

1. Check the troubleshooting section
2. Review service logs
3. Consult the system architecture document
4. Create an issue in the repository