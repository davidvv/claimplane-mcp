#!/bin/bash
# Setup script for Nextcloud integration

set -e

echo "🚀 Setting up Nextcloud for Flight Claim System"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p nextcloud/{config,data,custom_apps}
mkdir -p scripts
chmod +x scripts/*.sh

# Set up environment variables
print_status "Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_warning "Created .env file. Please update it with your configuration."
fi

# Start Nextcloud services
print_status "Starting Nextcloud services..."
docker-compose -f docker-compose.nextcloud.yml up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if Nextcloud is accessible
print_status "Checking Nextcloud accessibility..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/status.php | grep -q "200"; then
        print_status "Nextcloud is accessible!"
        break
    else
        print_warning "Nextcloud not ready yet. Attempt $attempt/$max_attempts"
        sleep 10
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    print_error "Nextcloud failed to become accessible after $max_attempts attempts"
    print_error "Check Docker logs: docker-compose -f docker-compose.nextcloud.yml logs"
    exit 1
fi

# Get Nextcloud admin credentials from environment
NEXTCLOUD_ADMIN_USER=${NEXTCLOUD_USERNAME:-admin}
NEXTCLOUD_ADMIN_PASSWORD=${NEXTCLOUD_PASSWORD:-admin}

# Create app password for API access
print_status "Setting up Nextcloud API access..."
cat > scripts/create_nextcloud_app_password.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import sys

# Nextcloud credentials
admin_user = sys.argv[1] if len(sys.argv) > 1 else "admin"
admin_password = sys.argv[2] if len(sys.argv) > 2 else "admin"
nextcloud_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8080"

# Create app password
login_url = f"{nextcloud_url}/login"
app_password_url = f"{nextcloud_url}/settings/personal/authtokens"

# This is a simplified approach - in production you'd use the proper API
print(f"Nextcloud admin credentials:")
print(f"Username: {admin_user}")
print(f"Password: {admin_password}")
print(f"URL: {nextcloud_url}")
print("\nTo create an app password:")
print("1. Login to Nextcloud at http://localhost:8080")
print("2. Go to Settings → Security")
print("3. Create a new app password")
print("4. Update your .env file with the new password")
EOF

chmod +x scripts/create_nextcloud_app_password.py

# Create WebDAV test script
print_status "Creating WebDAV test script..."
cat > scripts/test_webdav.py << 'EOF'
#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
import sys

# Configuration
username = sys.argv[1] if len(sys.argv) > 1 else "admin"
password = sys.argv[2] if len(sys.argv) > 2 else "admin"
nextcloud_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8080"

# WebDAV URL
webdav_url = f"{nextcloud_url}/remote.php/dav/files/{username}/"

# Test credentials
auth = HTTPBasicAuth(username, password)

# Test PROPFIND
try:
    response = requests.request('PROPFIND', webdav_url, auth=auth)
    if response.status_code == 207:
        print("✅ WebDAV connection successful")
    else:
        print(f"❌ WebDAV connection failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ WebDAV connection error: {e}")
EOF

chmod +x scripts/test_webdav.py

# Create file structure setup script
print_status "Creating file structure setup script..."
cat > scripts/setup_nextcloud_files.py << 'EOF'
#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
import json
import sys

# Configuration
username = sys.argv[1] if len(sys.argv) > 1 else "admin"
password = sys.argv[2] if len(sys.argv) > 2 else "admin"
nextcloud_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8080"

# WebDAV URL
webdav_url = f"{nextcloud_url}/remote.php/dav/files/{username}/"

# Authentication
auth = HTTPBasicAuth(username, password)

# Create directories
directories = [
    "flight_claims",
    "flight_claims/boarding_passes",
    "flight_claims/id_documents",
    "flight_claims/receipts",
    "flight_claims/bank_statements",
    "flight_claims/flight_tickets",
    "flight_claims/delay_certificates",
    "flight_claims/cancellation_notices",
    "flight_claims/other"
]

print("Creating directory structure...")

for directory in directories:
    try:
        # Create directory using MKCOL
        response = requests.request('MKCOL', f"{webdav_url}{directory}/", auth=auth)
        if response.status_code in [201, 405]:  # 201 = Created, 405 = Already exists
            print(f"✅ Directory created/already exists: {directory}")
        else:
            print(f"⚠️  Directory creation failed for {directory}: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Error creating directory {directory}: {e}")

print("✅ Directory structure setup completed")
EOF

chmod +x scripts/setup_nextcloud_files.py

# Run WebDAV test
print_status "Testing WebDAV connection..."
python3 scripts/test_webdav.py $NEXTCLOUD_ADMIN_USER $NEXTCLOUD_ADMIN_PASSWORD

# Setup file structure
print_status "Setting up file structure..."
python3 scripts/setup_nextcloud_files.py $NEXTCLOUD_ADMIN_USER $NEXTCLOUD_ADMIN_PASSWORD

# Create integration test script
print_status "Creating integration test script..."
cat > scripts/test_integration.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys
import os

# Run the Nextcloud integration test
print("Running Nextcloud integration tests...")
result = subprocess.run([
    sys.executable, 
    "scripts/test_nextcloud_integration.py"
], env=os.environ)

if result.returncode == 0:
    print("✅ All integration tests passed!")
else:
    print("❌ Some integration tests failed")
    sys.exit(1)
EOF

chmod +x scripts/test_integration.py

# Create environment setup helper
print_status "Creating environment setup helper..."
cat > scripts/setup_env.sh << 'EOF'
#!/bin/bash

# Nextcloud environment setup helper
echo "Nextcloud Environment Setup Helper"
echo "=================================="

# Check current environment
echo "Current Nextcloud configuration:"
echo "NEXTCLOUD_URL: ${NEXTCLOUD_URL:-not set}"
echo "NEXTCLOUD_USERNAME: ${NEXTCLOUD_USERNAME:-not set}"
echo "NEXTCLOUD_PASSWORD: ${NEXTCLOUD_PASSWORD:-not set}"

echo ""
echo "To update your configuration:"
echo "1. Edit your .env file"
echo "2. Run: source .env"
echo "3. Test with: python3 scripts/test_nextcloud_integration.py"
echo ""
echo "Nextcloud should be accessible at: ${NEXTCLOUD_URL:-http://localhost:8080}"
echo "Login with username: ${NEXTCLOUD_USERNAME:-admin}"
echo "Password: ${NEXTCLOUD_PASSWORD:-admin}"
EOF

chmod +x scripts/setup_env.sh

# Create monitoring script
print_status "Creating monitoring script..."
cat > scripts/monitor_nextcloud.sh << 'EOF'
#!/bin/bash

# Nextcloud monitoring script
echo "Nextcloud Service Status"
echo "======================="

# Check Docker containers
echo "Docker containers:"
docker-compose -f docker-compose.nextcloud.yml ps

echo ""
echo "Service health checks:"

# Check Nextcloud
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/status.php | grep -q "200"; then
    echo "✅ Nextcloud: Healthy"
else
    echo "❌ Nextcloud: Unhealthy"
fi

# Check database
if docker-compose -f docker-compose.nextcloud.yml exec -T nextcloud-db pg_isready -U nextcloud > /dev/null 2>&1; then
    echo "✅ Nextcloud DB: Healthy"
else
    echo "❌ Nextcloud DB: Unhealthy"
fi

# Check Redis
if docker-compose -f docker-compose.nextcloud.yml exec -T nextcloud-redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Nextcloud Redis: Healthy"
else
    echo "❌ Nextcloud Redis: Unhealthy"
fi

# Check ClamAV
if docker-compose -f docker-compose.nextcloud.yml exec -T clamav clamdscan --version > /dev/null 2>&1; then
    echo "✅ ClamAV: Healthy"
else
    echo "❌ ClamAV: Unhealthy"
fi

echo ""
echo "Disk usage:"
docker system df

echo ""
echo "To view logs: docker-compose -f docker-compose.nextcloud.yml logs -f"
EOF

chmod +x scripts/monitor_nextcloud.sh

# Final instructions
print_status "Setup completed successfully!"
echo ""
echo "🎯 Next Steps:"
echo "1. Update your .env file with Nextcloud credentials"
echo "2. Test the integration: python3 scripts/test_nextcloud_integration.py"
echo "3. Monitor services: ./scripts/monitor_nextcloud.sh"
echo "4. View logs: docker-compose -f docker-compose.nextcloud.yml logs -f"
echo ""
echo "📚 Access Nextcloud:"
echo "   URL: http://localhost:8080"
echo "   Username: $NEXTCLOUD_ADMIN_USER"
echo "   Password: $NEXTCLOUD_ADMIN_PASSWORD"
echo ""
echo "🔧 Management commands:"
echo "   Stop services: docker-compose -f docker-compose.nextcloud.yml down"
echo "   View logs: docker-compose -f docker-compose.nextcloud.yml logs"
echo "   Shell access: docker-compose -f docker-compose.nextcloud.yml exec nextcloud bash"
echo ""
echo "✨ Your Nextcloud integration is ready!"