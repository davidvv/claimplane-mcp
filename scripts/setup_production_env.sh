#!/bin/bash
# Production Environment Setup Script
# Generated on: 2025-10-02T21:05:54.207421

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
    openssl req -x509 -nodes -days 365 -newkey rsa:2048         -keyout ssl/private/flight_claim.key         -out ssl/certs/flight_claim.crt         -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
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
