## 7. Docker Configuration and Deployment

### 7.1 Complete Docker Compose Configuration

```yaml
# docker-compose.file-management.yml
version: '3.8'

services:
  # Nextcloud Database
  nextcloud-db:
    image: postgres:15-alpine
    container_name: nextcloud_db
    environment:
      POSTGRES_DB: nextcloud
      POSTGRES_USER: nextcloud
      POSTGRES_PASSWORD: ${NEXTCLOUD_DB_PASSWORD:-nextcloud_secure_password}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
    volumes:
      - nextcloud_db_data:/var/lib/postgresql/data
      - ./init-scripts/nextcloud-init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - file_management_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nextcloud"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nextcloud Redis Cache
  nextcloud-redis:
    image: redis:7-alpine
    container_name: nextcloud_redis
    command: >
      redis-server
      --requirepass ${NEXTCLOUD_REDIS_PASSWORD:-redis_secure_password}
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 60 1
      --save 300 10
      --save 900 100
    volumes:
      - nextcloud_redis_data:/data
    networks:
      - file_management_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Nextcloud Application
  nextcloud-app:
    image: nextcloud:27-apache
    container_name: nextcloud_app
    environment:
      # Database Configuration
      POSTGRES_HOST: nextcloud-db
      POSTGRES_DB: nextcloud
      POSTGRES_USER: nextcloud
      POSTGRES_PASSWORD: ${NEXTCLOUD_DB_PASSWORD:-nextcloud_secure_password}
      
      # Admin Configuration
      NEXTCLOUD_ADMIN_USER: ${NEXTCLOUD_ADMIN_USER:-admin}
      NEXTCLOUD_ADMIN_PASSWORD: ${NEXTCLOUD_ADMIN_PASSWORD:-admin_secure_password}
      
      # Domain Configuration
      NEXTCLOUD_TRUSTED_DOMAINS: ${NEXTCLOUD_TRUSTED_DOMAINS:-nextcloud.localhost localhost 127.0.0.1}
      OVERWRITEPROTOCOL: https
      OVERWRITEHOST: ${NEXTCLOUD_DOMAIN:-nextcloud.localhost}
      OVERWRITEWEBROOT: /
      OVERWRITECONDADDR: 172.16.0.0/12
      
      # Redis Configuration
      REDIS_HOST: nextcloud-redis
      REDIS_HOST_PASSWORD: ${NEXTCLOUD_REDIS_PASSWORD:-redis_secure_password}
      
      # Security Configuration
      NEXTCLOUD_UPDATE_NOTIFICATION_ENABLED: false
      NEXTCLOUD_INSTALL: true
      
      # PHP Configuration
      PHP_MEMORY_LIMIT: 512M
      PHP_UPLOAD_MAX_FILESIZE: 50M
      PHP_POST_MAX_SIZE: 50M
      PHP_MAX_EXECUTION_TIME: 300
      
      # Application Configuration
      NEXTCLOUD_DEFAULT_APP: files
      NEXTCLOUD_DEFAULT_LANGUAGE: en
    volumes:
      - nextcloud_data:/var/www/html
      - ./nextcloud/config:/var/www/html/config:ro
      - ./nextcloud/custom_apps:/var/www/html/custom_apps
      - ./nextcloud/data:/var/www/html/data
      - ./nextcloud/themes:/var/www/html/themes
      - ./nextcloud/php.ini:/usr/local/etc/php/conf.d/custom.ini:ro
    depends_on:
      nextcloud-db:
        condition: service_healthy
      nextcloud-redis:
        condition: service_healthy
    networks:
      - file_management_network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.nextcloud.rule=Host(`${NEXTCLOUD_DOMAIN:-nextcloud.localhost}`)"
      - "traefik.http.routers.nextcloud.tls=true"
      - "traefik.http.routers.nextcloud.tls.certresolver=letsencrypt"
      - "traefik.http.services.nextcloud.loadbalancer.server.port=80"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/status.php"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Nextcloud Cron Job
  nextcloud-cron:
    image: nextcloud:27-apache
    container_name: nextcloud_cron
    volumes:
      - nextcloud_data:/var/www/html
      - ./nextcloud/config:/var/www/html/config:ro
      - ./nextcloud/custom_apps:/var/www/html/custom_apps
      - ./nextcloud/data:/var/www/html/data
      - ./nextcloud/themes:/var/www/html/themes
    entrypoint: /cron.sh
    depends_on:
      - nextcloud-db
      - nextcloud-redis
    networks:
      - file_management_network

  # File Processing Service
  file-processor:
    build:
      context: .
      dockerfile: Dockerfile.file-processor
    container_name: file_processor
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/flight_claim
      NEXTCLOUD_URL: http://nextcloud-app
      NEXTCLOUD_USERNAME: ${NEXTCLOUD_ADMIN_USER:-admin}
      NEXTCLOUD_PASSWORD: ${NEXTCLOUD_ADMIN_PASSWORD:-admin_secure_password}
      REDIS_URL: redis://nextcloud-redis:6379/1
      FILE_ENCRYPTION_KEY: ${FILE_ENCRYPTION_KEY:-your-encryption-key-here}
      VIRUS_SCAN_ENABLED: ${VIRUS_SCAN_ENABLED:-false}
      CLAMAV_URL: ${CLAMAV_URL:-clamav:3310}
    volumes:
      - ./app:/app/app:ro
      - file_processing_temp:/tmp/file_processing
    depends_on:
      - nextcloud-app
      - nextcloud-redis
    networks:
      - file_management_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Antivirus Scanner (ClamAV)
  clamav:
    image: clamav/clamav:stable
    container_name: clamav
    environment:
      CLAMAV_NO_FRESHCLAMD: false
      CLAMAV_NO_CLAMD: false
    volumes:
      - clamav_data:/var/lib/clamav
    networks:
      - file_management_network
    healthcheck:
      test: ["CMD", "clamdscan", "--version"]
      interval: 60s
      timeout: 30s
      retries: 3

  # Traefik Reverse Proxy
  traefik:
    image: traefik:v2.10
    container_name: traefik
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL:-admin@example.com}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt_data:/letsencrypt
    networks:
      - file_management_network
    healthcheck:
      test: ["CMD", "traefik", "healthcheck"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  nextcloud_db_data:
    driver: local
  nextcloud_redis_data:
    driver: local
  nextcloud_data:
    driver: local
  file_processing_temp:
    driver: local
  clamav_data:
    driver: local
  letsencrypt_data:
    driver: local

networks:
  file_management_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 7.2 Environment Configuration

```bash
# .env.nextcloud
# Nextcloud Configuration
NEXTCLOUD_DOMAIN=nextcloud.yourdomain.com
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=your_secure_admin_password
NEXTCLOUD_DB_PASSWORD=your_secure_db_password
NEXTCLOUD_REDIS_PASSWORD=your_secure_redis_password
NEXTCLOUD_TRUSTED_DOMAINS=nextcloud.yourdomain.com localhost 127.0.0.1

# File Processing Configuration
FILE_ENCRYPTION_KEY=your_32_character_encryption_key_here
VIRUS_SCAN_ENABLED=true
CLAMAV_URL=clamav:3310

# SSL/TLS Configuration
ACME_EMAIL=admin@yourdomain.com

# Security Configuration
FILE_UPLOAD_MAX_SIZE=52428800
FILE_UPLOAD_TIMEOUT=300
FILE_SCAN_ENABLED=true
FILE_ENCRYPTION_ENABLED=true

# Storage Configuration
NEXTCLOUD_STORAGE_QUOTA=10GB
FILE_RETENTION_DAYS=2555  # 7 years for legal compliance

# Performance Configuration
FILE_PROCESSING_WORKERS=4
FILE_CACHE_TTL=3600
FILE_DOWNLOAD_TIMEOUT=600
```

### 7.3 File Processor Dockerfile

```dockerfile
# Dockerfile.file-processor
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    libmagic-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.files.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.files.txt

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 fileprocessor && \
    chown -R fileprocessor:fileprocessor /app

# Switch to non-root user
USER fileprocessor

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start command
CMD ["python", "-m", "app.file_processor.main"]
```

## 8. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up Nextcloud infrastructure
- [ ] Implement database schema
- [ ] Create basic file models and repositories
- [ ] Set up Docker environment

### Phase 2: Core Functionality (Weeks 3-4)
- [ ] Implement file upload/download endpoints
- [ ] Create Nextcloud integration service
- [ ] Add basic file validation
- [ ] Implement file metadata storage

### Phase 3: Security & Access Control (Weeks 5-6)
- [ ] Implement RBAC system
- [ ] Add file encryption
- [ ] Create access control service
- [ ] Implement audit logging

### Phase 4: Advanced Features (Weeks 7-8)
- [ ] Add file sharing functionality
- [ ] Implement virus scanning
- [ ] Add content validation
- [ ] Create file processing pipeline

### Phase 5: Performance & Monitoring (Weeks 9-10)
- [ ] Add caching layer
- [ ] Implement monitoring
- [ ] Add performance optimization
- [ ] Create alerting system

### Phase 6: Testing & Documentation (Weeks 11-12)
- [ ] Comprehensive testing
- [ ] Security auditing
- [ ] Performance testing
- [ ] Final documentation

## 9. Security Considerations

### 9.1 Data Protection
- **Encryption at Rest**: All files encrypted using AES-256
- **Encryption in Transit**: TLS 1.3 for all communications
- **Key Management**: Hardware Security Module (HSM) integration
- **Data Residency**: Compliance with GDPR, CCPA, and local regulations

### 9.2 Access Control
- **Multi-Factor Authentication**: Required for sensitive operations
- **Session Management**: Secure session handling with timeout
- **API Rate Limiting**: Prevent abuse and DoS attacks
- **IP Whitelisting**: Restrict access to trusted networks

### 9.3 Compliance
- **GDPR Compliance**: Right to erasure, data portability, consent management
- **PCI DSS**: Secure handling of payment-related documents
- **SOX Compliance**: Audit trails and data integrity
- **Industry Standards**: ISO 27001, SOC 2 Type II

## 10. Performance Optimization

### 10.1 Caching Strategy
- **Redis Cache**: File metadata and access permissions
- **CDN Integration**: Global content delivery for downloads
- **Browser Caching**: Optimized cache headers
- **Database Query Optimization**: Indexed queries and connection pooling

### 10.2 Scalability
- **Horizontal Scaling**: Multiple file processor instances
- **Load Balancing**: Distribute traffic across services
- **Auto-scaling**: Dynamic resource allocation
- **Database Sharding**: Partition data by customer or claim

### 10.3 Storage Optimization
- **File Deduplication**: Prevent duplicate storage
- **Compression**: Optimize storage usage
- **Tiered Storage**: Hot/warm/cold storage tiers
- **Archival Strategy**: Long-term storage optimization

## 11. Monitoring and Observability

### 11.1 Metrics Collection
- **Application Metrics**: Request latency, error rates, throughput
- **Infrastructure Metrics**: CPU, memory, disk usage, network I/O
- **Business Metrics**: File uploads, downloads, sharing activity
- **Security Metrics**: Failed access attempts, suspicious activities

### 11.2 Logging Strategy
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Log Aggregation**: Centralized log collection and analysis
- **Audit Logging**: Comprehensive access and change tracking
- **Error Tracking**: Detailed error reporting and analysis

### 11.3 Alerting
- **Real-time Alerts**: Critical system issues
- **Threshold Alerts**: Performance degradation, capacity limits
- **Security Alerts**: Unauthorized access, suspicious patterns
- **Compliance Alerts**: Policy violations, audit failures

## 12. Disaster Recovery and Business Continuity

### 12.1 Backup Strategy
- **Automated Backups**: Daily incremental, weekly full backups
- **Off-site Storage**: Geographic redundancy
- **Point-in-Time Recovery**: Minimize data loss
- **Backup Testing**: Regular restoration testing

### 12.2 High Availability
- **Multi-region Deployment**: Geographic distribution
- **Failover Mechanisms**: Automatic service recovery
- **Data Replication**: Real-time data synchronization
- **Load Balancing**: Traffic distribution and health checks

### 12.3 Recovery Procedures
- **Disaster Recovery Plan**: Documented recovery procedures
- **Recovery Time Objective (RTO)**: < 4 hours
- **Recovery Point Objective (RPO)**: < 15 minutes
- **Regular Testing**: Quarterly disaster recovery drills

This comprehensive design provides a robust, secure, and scalable file management system that integrates seamlessly with the existing flight claim application while meeting all security, compliance, and performance requirements.