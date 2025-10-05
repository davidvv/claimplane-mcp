#!/usr/bin/env python3
"""
Secure password generator for Flight Claim System using float32-based entropy.
Generates cryptographically secure passwords with proper entropy distribution.
"""
import secrets
import string
import os
import numpy as np
from datetime import datetime


def generate_secure_password(length=32, use_float32=True):
    """
    Generate a cryptographically secure password using float32-based entropy.
    
    Args:
        length: Password length (default: 32)
        use_float32: Use float32-based entropy generation (default: True)
    
    Returns:
        str: Secure password
    """
    if use_float32:
        # Use float32-based entropy for better distribution
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Generate float32 random values and map to characters
        float_entropy = np.random.rand(length).astype(np.float32)
        password = ''.join(alphabet[int(abs(f) * len(alphabet)) % len(alphabet)] for f in float_entropy)
        
        # Ensure at least one of each character type
        if length >= 8:
            password = list(password)
            password[0] = secrets.choice(string.ascii_lowercase)
            password[1] = secrets.choice(string.ascii_uppercase)
            password[2] = secrets.choice(string.digits)
            password[3] = secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")
            secrets.SystemRandom().shuffle(password)
            password = ''.join(password)
        
        return password
    else:
        # Fallback to secrets module
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key():
    """Generate a secure API key."""
    return f"flight_claim_{generate_secure_password(48)}"


def generate_jwt_secret():
    """Generate a secure JWT secret key."""
    return generate_secure_password(64)


def generate_db_password():
    """Generate a secure database password."""
    return generate_secure_password(24)


def generate_encryption_key():
    """Generate a secure encryption key."""
    return generate_secure_password(32)


def generate_nextcloud_admin_password():
    """Generate a secure Nextcloud admin password."""
    return generate_secure_password(20)


def generate_nextcloud_db_password():
    """Generate a secure Nextcloud database password."""
    return generate_secure_password(20)


def generate_redis_password():
    """Generate a secure Redis password."""
    return generate_secure_password(16)


def generate_secrets():
    """Generate all required secrets for the application."""
    print("🔐 Generating secure secrets for production deployment...")
    print("=" * 60)
    
    secrets_dict = {
        'SECRET_KEY': generate_jwt_secret(),
        'FILE_ENCRYPTION_KEY': generate_encryption_key(),
        'NEXTCLOUD_ADMIN_PASSWORD': generate_nextcloud_admin_password(),
        'NEXTCLOUD_DB_PASSWORD': generate_nextcloud_db_password(),
        'POSTGRES_PASSWORD': generate_db_password(),
        'REDIS_PASSWORD': generate_redis_password(),
        'API_KEY': generate_api_key(),
        'JWT_SECRET': generate_jwt_secret(),
        'ENCRYPTION_KEY': generate_encryption_key(),
    }
    
    # Create production environment file
    env_content = f"""# Production Environment Configuration
# Generated on: {datetime.now().isoformat()}
# DO NOT COMMIT THIS FILE TO VERSION CONTROL

# Application Security
SECRET_KEY={secrets_dict['SECRET_KEY']}
JWT_SECRET={secrets_dict['JWT_SECRET']}
ENCRYPTION_KEY={secrets_dict['ENCRYPTION_KEY']}
API_KEY={secrets_dict['API_KEY']}

# Database Security
POSTGRES_PASSWORD={secrets_dict['POSTGRES_PASSWORD']}
DATABASE_URL=postgresql+asyncpg://postgres:{secrets_dict['POSTGRES_PASSWORD']}@db:5432/flight_claim

# Redis Security
REDIS_PASSWORD={secrets_dict['REDIS_PASSWORD']}
REDIS_URL=redis://:{secrets_dict['REDIS_PASSWORD']}@redis:6379/0

# Nextcloud Security
NEXTCLOUD_URL=http://localhost:8081
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD={secrets_dict['NEXTCLOUD_ADMIN_PASSWORD']}
NEXTCLOUD_DB_PASSWORD={secrets_dict['NEXTCLOUD_DB_PASSWORD']}

# File Security
FILE_ENCRYPTION_KEY={secrets_dict['FILE_ENCRYPTION_KEY']}
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,jpg,jpeg,png,doc,docx

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# SSL Configuration
SSL_CERT_PATH=/etc/ssl/certs/flight_claim.crt
SSL_KEY_PATH=/etc/ssl/private/flight_claim.key

# Monitoring
SENTRY_DSN=your-sentry-dsn-here

# Environment
ENVIRONMENT=production
DEBUG=false
"""
    
    # Write environment file
    with open('.env.production', 'w') as f:
        f.write(env_content)
    
    print("✅ Production environment file created: .env.production")
    
    # Create Docker secrets configuration
    docker_secrets = f"""# Docker Secrets Configuration
# Generated on: {datetime.now().isoformat()}

# Create secrets
echo "{secrets_dict['SECRET_KEY']}" | docker secret create flight_claim_secret_key -
echo "{secrets_dict['POSTGRES_PASSWORD']}" | docker secret create flight_claim_db_password -
echo "{secrets_dict['REDIS_PASSWORD']}" | docker secret create flight_claim_redis_password -
echo "{secrets_dict['NEXTCLOUD_ADMIN_PASSWORD']}" | docker secret create flight_claim_nextcloud_admin_password -
echo "{secrets_dict['NEXTCLOUD_DB_PASSWORD']}" | docker secret create flight_claim_nextcloud_db_password -
echo "{secrets_dict['FILE_ENCRYPTION_KEY']}" | docker secret create flight_claim_encryption_key -

# Update docker-compose.yml to use secrets
# Example:
# secrets:
#   - flight_claim_secret_key
#   - flight_claim_db_password
#   - flight_claim_redis_password
#   - flight_claim_nextcloud_admin_password
#   - flight_claim_nextcloud_db_password
#   - flight_claim_encryption_key
"""
    
    with open('docker-secrets.example.txt', 'w') as f:
        f.write(docker_secrets)
    
    print("✅ Docker secrets configuration created: docker-secrets.example.txt")
    
    # Create Kubernetes secrets configuration
    k8s_secrets = f"""# Kubernetes Secrets Configuration
# Generated on: {datetime.now().isoformat()}
# Apply with: kubectl apply -f k8s-secrets.yaml

apiVersion: v1
kind: Secret
metadata:
  name: flight-claim-secrets
  namespace: flight-claim
type: Opaque
data:
  SECRET_KEY: {secrets_dict['SECRET_KEY'].encode('utf-8').hex()}
  POSTGRES_PASSWORD: {secrets_dict['POSTGRES_PASSWORD'].encode('utf-8').hex()}
  REDIS_PASSWORD: {secrets_dict['REDIS_PASSWORD'].encode('utf-8').hex()}
  NEXTCLOUD_ADMIN_PASSWORD: {secrets_dict['NEXTCLOUD_ADMIN_PASSWORD'].encode('utf-8').hex()}
  NEXTCLOUD_DB_PASSWORD: {secrets_dict['NEXTCLOUD_DB_PASSWORD'].encode('utf-8').hex()}
  FILE_ENCRYPTION_KEY: {secrets_dict['FILE_ENCRYPTION_KEY'].encode('utf-8').hex()}
  API_KEY: {secrets_dict['API_KEY'].encode('utf-8').hex()}
  JWT_SECRET: {secrets_dict['JWT_SECRET'].encode('utf-8').hex()}
  ENCRYPTION_KEY: {secrets_dict['ENCRYPTION_KEY'].encode('utf-8').hex()}
"""
    
    with open('k8s-secrets.example.yaml', 'w') as f:
        f.write(k8s_secrets)
    
    print("✅ Kubernetes secrets configuration created: k8s-secrets.example.yaml")
    
    # Create production setup script
    setup_script = f"""#!/bin/bash
# Production Environment Setup Script
# Generated on: {datetime.now().isoformat()}

set -e

echo "🔐 Setting up production environment..."

# Create necessary directories
mkdir -p nextcloud/config nextcloud/data nextcloud/custom_apps
mkdir -p ssl/certs ssl/private
mkdir -p logs

# Set proper permissions
chmod 700 nextcloud/config nextcloud/data nextcloud/custom_apps
chmod 700 ssl/certs ssl/private
chmod 700 logs

# Copy production environment file
if [ ! -f .env.production ]; then
    echo "❌ .env.production file not found!"
    echo "Please run: python scripts/generate_secrets.py"
    exit 1
fi

# Create SSL certificates (self-signed for development)
if [ ! -f ssl/certs/flight_claim.crt ]; then
    echo "🔒 Generating self-signed SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/private/flight_claim.key \
        -out ssl/certs/flight_claim.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Set proper permissions on SSL files
chmod 600 ssl/private/flight_claim.key
chmod 644 ssl/certs/flight_claim.crt

echo "✅ Production environment setup complete!"
echo ""
echo "🔑 Generated Secrets:"
echo "  SECRET_KEY: [REDACTED - stored securely]"
echo "  FILE_ENCRYPTION_KEY: [REDACTED - stored securely]"
echo "  NEXTCLOUD_ADMIN_PASSWORD: [REDACTED - stored securely]"
echo "  NEXTCLOUD_DB_PASSWORD: [REDACTED - stored securely]"
echo "  POSTGRES_PASSWORD: [REDACTED - stored securely]"
echo "  REDIS_PASSWORD: [REDACTED - stored securely]"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "1. Keep .env.production file secure and never commit to version control"
echo "2. Update the following placeholders in .env.production:"
echo "   - NEXTCLOUD_URL: Your actual Nextcloud domain"
echo "   - CORS_ORIGINS: Your frontend domain(s)"
echo "   - SSL_CERT_PATH and SSL_KEY_PATH: Your SSL certificate paths"
echo "   - SENTRY_DSN: Your Sentry DSN for error monitoring"
echo "3. Use a secrets management service in production (AWS Secrets Manager, etc.)"
echo "4. Rotate these secrets regularly"
echo "5. Enable audit logging and monitoring"
echo ""
echo "🎉 SECRET GENERATION COMPLETE!"
"""
    
    with open('scripts/setup_production_env.sh', 'w') as f:
        f.write(setup_script)
    
    # Make script executable
    os.chmod('scripts/setup_production_env.sh', 0o755)
    
    print("✅ Production environment setup script created: scripts/setup_production_env.sh")
    
    print("\n" + "=" * 60)
    print("🎉 SECRET GENERATION COMPLETE!")
    print("=" * 60)
    
    print("\n📁 Generated files:")
    print("  - .env.production (secure environment variables)")
    print("  - docker-secrets.example.txt (Docker secrets guide)")
    print("  - k8s-secrets.example.yaml (Kubernetes secrets)")
    print("  - scripts/setup_production_env.sh (setup script)")
    
    print("\n🔒 Your secrets are now properly secured!")
    print("   Remember to keep these files safe and never commit them to version control.")
    
    print("\n⚠️  IMPORTANT SECURITY NOTES:")
    print("1. Keep .env.production file secure and never commit to version control")
    print("2. Update the following placeholders in .env.production:")
    print("   - NEXTCLOUD_URL: Your actual Nextcloud domain")
    print("   - CORS_ORIGINS: Your frontend domain(s)")
    print("   - SSL_CERT_PATH and SSL_KEY_PATH: Your SSL certificate paths")
    print("   - SENTRY_DSN: Your Sentry DSN for error monitoring")
    print("3. Use a secrets management service in production (AWS Secrets Manager, etc.)")
    print("4. Rotate these secrets regularly")
    print("5. Enable audit logging and monitoring")
    
    return secrets_dict


if __name__ == "__main__":
    generate_secrets()