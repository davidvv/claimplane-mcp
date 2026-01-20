#!/bin/bash
# Run browser E2E test in Docker container with Playwright

set -e

echo "==================================================================="
echo "Running Draft Resume UX Test (WP 196) with Playwright"
echo "==================================================================="

# Create screenshots directory
mkdir -p tests/e2e/screenshots

# Run Playwright test in Docker
docker run --rm \
  --network host \
  -v "$(pwd)/tests/e2e:/tests" \
  -v "$(pwd)/tests/e2e/screenshots:/screenshots" \
  -e DB_HOST=localhost \
  -e DB_PORT=5432 \
  -e DB_NAME=easyair_db \
  -e DB_USER=easyair_user \
  -e DB_PASSWORD=easyair_password \
  mcr.microsoft.com/playwright/python:v1.40.0-jammy \
  bash -c "
    cd /tests && \
    pip install playwright psycopg2-binary && \
    python test_draft_resume_wp196.py
  "

echo ""
echo "==================================================================="
echo "Test complete! Screenshots saved to tests/e2e/screenshots/"
echo "==================================================================="
