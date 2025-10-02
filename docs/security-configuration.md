# Security Configuration Guide

## Flight Claim System - Enterprise Security Setup

This guide documents the comprehensive security configuration implemented for production deployment, including secrets management, encryption, and secure environment variable usage.

## Security Architecture Overview

### 1. Secrets Management System

#### **Generated Security Files:**
- `.env.production` - Production environment variables with cryptographically secure secrets
- `docker-secrets.example.txt` - Docker Swarm secrets configuration guide
- `k8s-secrets.example.yaml` - Kubernetes secrets template
- `scripts/setup_production_env.sh` - Automated production environment setup

#### **Secret Generation Process:**
```bash
# Generate all production secrets
python scripts/generate_secrets.py

# This creates:
# - .env.production with float32-based entropy secrets
# - Docker secrets configuration
# - Kubernetes secrets manifest
# - Production setup script
```

### 2. Environment Variable Security

#### **Production Environment Variables:**
```bash
# Application Security
SECRET_KEY=k_ozG8_y_wQF8mxV8ZYe_V_EqfN_mKm1FjJcOFC_O_ZOs_5gfzIk_sv7a_E_I_
JWT_SECRET=n_kJEc_5gI_Sisf_8_EFSmk1_ql26X93gT_kELTL7gnDN_Nj08_Cyip9_T_W_e
ENCRYPTION_KEY=_R_3kgZT_aWc_7gr_9xpN_HF_p44i_
API_KEY=flight_claim_xB_Q1AwV2n0R_yMX_pDqgl_S_HZYs_ks8a_m_y_2_Q_Wj_

# Database Security
POSTGRES_PASSWORD=Z_xWU_9_q_p_CX4_5_Yf
DATABASE_URL=postgresql+asyncpg://postgres:Z_xWU_9_q_p_CX4_5_Yf@db:5432/flight_claim

# File Security
FILE_ENCRYPTION_KEY=_Wf_Dk_O5Q_OX_oJh_b_jJ_vV_8
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,jpg,jpeg,png,doc,docx

# Security Features
VIRUS_SCAN_ENABLED=true
CLAMAV_URL=clamav:3310
SECURITY_HEADERS_ENABLED=true
RATE_LIMIT_UPLOAD=5/minute
RATE_LIMIT_DOWNLOAD=50/minute
```

### 3. Docker Compose Security Configuration

#### **Updated docker-compose.yml:**
```yaml
services:
  api:
    environment:
      # Security Configuration
      SECRET_KEY: ${SECRET_KEY:-development-secret-key}
      FILE_ENCRYPTION_KEY: ${FILE_ENCRYPTION_KEY:-development-encryption-key}
      ENVIRONMENT: ${ENVIRONMENT:-development}
      
      # Database Security
      DATABASE_URL: ${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@db:5432/flight_claim}
      
      # File Security
      VIRUS_SCAN_ENABLED: ${VIRUS_SCAN_ENABLED:-false}
      CLAMAV_URL: ${CLAMAV_URL:-clamav:3310}
      
      # Rate Limiting
      RATE_LIMIT_UPLOAD: ${RATE_LIMIT_UPLOAD:-100/minute}
      RATE_LIMIT_DOWNLOAD: ${RATE_LIMIT_DOWNLOAD:-1000/minute}
      
      # CORS Security
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000,http://localhost:8080}
      
      # Security Headers
      SECURITY_HEADERS_ENABLED: ${SECURITY_HEADERS_ENABLED:-false}
```

### 4. Production Deployment with Security

#### **Deploy with Production Secrets:**
```bash
# Generate production secrets
python scripts/generate_secrets.py

# Deploy with production environment file
docker-compose --env-file .env.production up -d

# Verify security configuration
docker-compose exec api env | grep -E "(ENVIRONMENT|SECURITY_HEADERS_ENABLED|VIRUS_SCAN_ENABLED)"
```

#### **Verify Security Implementation:**
```bash
# Check production environment
curl http://localhost/health

# Verify encryption is working
docker-compose exec api python -c "
from app.services.encryption_service import EncryptionService
service = EncryptionService()
test_data = b'sensitive flight claim data'
encrypted = service.encrypt_file(test_data)
decrypted = service.decrypt_file(encrypted)
print('Encryption working:', decrypted == test_data)
"

# Check security headers
curl -I http://localhost/health
```

### 5. Security Features Implemented

#### **File Security:**
- **AES-256 Encryption**: All uploaded files encrypted with Fernet
- **Virus Scanning**: ClamAV integration for malware detection
- **File Validation**: Size limits, type restrictions, content scanning
- **Secure Filenames**: Sanitization to prevent directory traversal

#### **API Security:**
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Upload/download request throttling
- **CORS Protection**: Cross-origin request validation
- **Security Headers**: XSS, CSRF, and clickjacking protection

#### **Database Security:**
- **Connection Encryption**: PostgreSQL SSL/TLS support
- **Password Hashing**: Secure password storage
- **Input Validation**: SQL injection prevention
- **Audit Logging**: Security event tracking

#### **Network Security:**
- **SSL/TLS**: HTTPS encryption ready
- **Reverse Proxy**: Nginx security headers
- **Container Isolation**: Docker network segmentation
- **Secret Management**: Environment variable isolation

### 6. Security Monitoring and Maintenance

#### **Security Audit Commands:**
```bash
# Check for security vulnerabilities
docker-compose exec api pip list --outdated

# Verify file encryption
docker-compose exec api python -c "
from app.config import config
print('Encryption key valid:', config.SecureConfig.validate_encryption_key(config.FILE_ENCRYPTION_KEY))
"

# Monitor security logs
docker-compose logs api | grep -i "security\|error\|warning"
```

#### **Security Update Process:**
```bash
# Update security dependencies
docker-compose exec api pip install --upgrade cryptography

# Rotate secrets (recommended quarterly)
python scripts/generate_secrets.py
docker-compose --env-file .env.production restart

# Verify after updates
docker-compose exec api python -c "from app.config import config; print('Security config loaded:', config.ENVIRONMENT)"
```

### 7. Security Best Practices

#### **Never Commit Secrets:**
```bash
# Add to .gitignore
echo ".env.production" >> .gitignore
echo "docker-secrets.txt" >> .gitignore
echo "ssl/" >> .gitignore
```

#### **Use Docker Secrets in Production:**
```bash
# Create Docker secrets (for Docker Swarm)
echo "your-secret-key" | docker secret create flight_claim_secret_key -
echo "your-db-password" | docker secret create flight_claim_db_password -

# Use in production Docker Swarm
docker stack deploy -c docker-compose.prod.yml flight-claim
```

#### **Regular Security Audits:**
- Monthly: Check for dependency vulnerabilities
- Quarterly: Rotate all secrets and keys
- Annually: Full security penetration testing
- Ongoing: Monitor security logs and alerts

### 8. Troubleshooting Security Issues

#### **Common Security Problems:**
```bash
# Encryption key invalid
docker-compose exec api python -c "
from app.config import config
print('Key valid:', config.SecureConfig.validate_encryption_key(config.FILE_ENCRYPTION_KEY))
"

# Environment variables not loading
docker-compose exec api env | grep -E "(SECRET_KEY|ENVIRONMENT)"

# Security headers not applied
curl -I http://localhost/health | grep -i "security\|x-frame\|x-content"
```

#### **Security Log Analysis:**
```bash
# Check for security events
docker-compose logs api | grep -E "(security|encrypt|auth|unauthorized)"

# Monitor failed authentication attempts
docker-compose logs api | grep -i "401\|403\|unauthorized"
```

This comprehensive security configuration ensures your Flight Claim System meets enterprise-grade security standards for production deployment.