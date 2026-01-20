#!/bin/bash
# Helper script to get the latest magic link token for testing

echo "========================================="
echo "Magic Link Token Retriever"
echo "========================================="
echo ""

# Get the latest magic link token for the test user
echo "Retrieving latest magic link token for florian.luhn@outlook.com..."
echo ""

TOKEN=$(docker compose exec -T db psql -U postgres -d flight_claim_db -t -c "SELECT token FROM magic_link_tokens WHERE user_id = '548f8da6-e539-40d5-8050-e5ee73ddca81' ORDER BY created_at DESC LIMIT 1;" | xargs)

if [ -z "$TOKEN" ]; then
    echo "❌ No token found!"
    echo ""
    echo "Make sure you've requested a magic link first:"
    echo "1. Go to http://localhost:3000/auth"
    echo "2. Enter email: florian.luhn@outlook.com"
    echo "3. Click 'Send Magic Link'"
    echo "4. Run this script again"
else
    echo "✅ Token found!"
    echo ""
    echo "Magic Link URL:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "http://localhost:3000/auth/verify?token=$TOKEN"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Token details:"
    docker compose exec -T db psql -U postgres -d flight_claim_db -c "SELECT token, expires_at, used_at, created_at FROM magic_link_tokens WHERE user_id = '548f8da6-e539-40d5-8050-e5ee73ddca81' ORDER BY created_at DESC LIMIT 1;"
fi

echo ""
echo "========================================="
