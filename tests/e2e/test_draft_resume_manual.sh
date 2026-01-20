#!/bin/bash
# Manual E2E test for draft resume UX fix (WP 196)
# This script simulates the browser flow using curl and database queries

set -e

BASE_URL="http://localhost:3000"
API_URL="http://localhost:3000/api"
DRAFT_ID="5a3b5eb8-8825-4729-aa8e-8c1cf9cb4e0f"
TEST_EMAIL="florian.luhn@outlook.com"

echo "================================================================================"
echo "DRAFT RESUME UX TEST - WP 196 (Manual API Test)"
echo "================================================================================"
echo ""

# Step 1: Request magic link
echo "Step 1: Requesting magic link for $TEST_EMAIL..."
RESPONSE=$(curl -s -X POST "$API_URL/auth/magic-link/request" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\"}")

echo "Response: $RESPONSE"
echo ""

# Step 2: Get magic link token from database
echo "Step 2: Fetching magic link token from database..."
sleep 2  # Give server time to create token

# First get customer ID
CUSTOMER_ID=$(docker exec flight_claim_db psql -U postgres -d flight_claim -t -c \
  "SELECT id FROM customers WHERE email = '$TEST_EMAIL';" | tr -d ' ')

echo "Customer ID: $CUSTOMER_ID"

# Then get token for that customer
TOKEN=$(docker exec flight_claim_db psql -U postgres -d flight_claim -t -c \
  "SELECT token FROM magic_link_tokens WHERE user_id = '$CUSTOMER_ID' ORDER BY created_at DESC LIMIT 1;" | tr -d ' ')

if [ -z "$TOKEN" ]; then
  echo "✗ FAILED: No token found in database"
  exit 1
fi

echo "✓ Token retrieved: ${TOKEN:0:20}..."
echo ""

# Step 3: Verify magic link
echo "Step 3: Verifying magic link token..."
VERIFY_RESPONSE=$(curl -s -X POST "$API_URL/auth/magic-link/verify/$TOKEN" \
  -c cookies.txt)

echo "Verify Response: $VERIFY_RESPONSE"

# Extract access_token from response
ACCESS_TOKEN=$(echo "$VERIFY_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "✗ FAILED: No access token in response"
  exit 1
fi

echo "✓ Access token received: ${ACCESS_TOKEN:0:20}..."
echo ""

# Step 4: Check if draft claim exists and is accessible
echo "Step 4: Fetching draft claim with resume parameter..."
CLAIM_RESPONSE=$(curl -s -X GET "$API_URL/claims/$DRAFT_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Claim Response: $CLAIM_RESPONSE"
echo ""

# Check if claim is draft status
STATUS=$(echo "$CLAIM_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$STATUS" = "draft" ]; then
  echo "✓✓✓ SUCCESS: Draft claim is accessible!"
  echo "✓ Status: $STATUS"
else
  echo "✗ FAILED: Claim status is not 'draft': $STATUS"
  exit 1
fi

# Cleanup
rm -f cookies.txt

echo ""
echo "================================================================================"
echo "TEST PASSED - Draft resume flow working correctly"
echo "================================================================================"
echo ""
echo "NEXT STEP: Test the actual browser UX to verify:"
echo "1. Redirect to /auth shows 'Welcome back!' banner"
echo "2. After magic link login, redirected to /claim/new?resume=$DRAFT_ID"
echo "3. NOT redirected to /my-claims"
echo ""
echo "Manual test instructions:"
echo "1. Open browser in incognito mode"
echo "2. Navigate to: $BASE_URL/claim/new?resume=$DRAFT_ID"
echo "3. Verify redirect to /auth with 'Welcome back!' banner"
echo "4. Login with email: $TEST_EMAIL"
echo "5. Click magic link from email"
echo "6. Verify final URL is /claim/new?resume=$DRAFT_ID (NOT /my-claims)"
echo "================================================================================"
