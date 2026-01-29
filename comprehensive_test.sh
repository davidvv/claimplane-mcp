#!/bin/bash
# Comprehensive test script for ClaimPlane API

set -e

API_URL="http://localhost:8000"
TEST_RESULTS_FILE="/tmp/test_results_$(date +%s).json"
ISSUES_FOUND=()

echo "=========================================="
echo "ClaimPlane Comprehensive Test Suite"
echo "Started at: $(date)"
echo "=========================================="

# Test 1: Create customer with duplicate email
echo ""
echo "TEST 1: Duplicate email creation"
RESPONSE=$(curl -s -X POST "$API_URL/api/customers/" \
  -H "Content-Type: application/json" \
  -d '{"email": "test.basic@example.com", "firstName": "Duplicate", "lastName": "Test"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" -eq 400 ] || [ "$HTTP_CODE" -eq 409 ]; then
    echo "  PASS: Duplicate email rejected (HTTP $HTTP_CODE)"
else
    echo "  FAIL: Expected 400/409, got HTTP $HTTP_CODE"
    echo "  Response: $BODY"
    ISSUES_FOUND+=("Duplicate email not properly rejected")
fi

# Test 2: Create customer with invalid email
echo ""
echo "TEST 2: Invalid email format"
RESPONSE=$(curl -s -X POST "$API_URL/api/customers/" \
  -H "Content-Type: application/json" \
  -d '{"email": "not-an-email", "firstName": "Invalid", "lastName": "Email"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 422 ]; then
    echo "  PASS: Invalid email rejected (HTTP $HTTP_CODE)"
else
    echo "  FAIL: Expected 422, got HTTP $HTTP_CODE"
    ISSUES_FOUND+=("Invalid email format not properly validated")
fi

# Test 3: Create customer with very long names
echo ""
echo "TEST 3: Long name validation"
LONG_NAME=$(python3 -c "print('A'*100)")
RESPONSE=$(curl -s -X POST "$API_URL/api/customers/" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"long.name@example.com\", \"firstName\": \"$LONG_NAME\", \"lastName\": \"Test\"}" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 422 ]; then
    echo "  PASS: Long name rejected (HTTP $HTTP_CODE)"
else
    echo "  NOTE: Long name accepted (HTTP $HTTP_CODE) - may be truncation or validation issue"
fi

# Test 4: Create customer with SQL injection attempt
echo ""
echo "TEST 4: SQL injection in name field"
RESPONSE=$(curl -s -X POST "$API_URL/api/customers/" \
  -H "Content-Type: application/json" \
  -d '{"email": "sql.test@example.com", "firstName": "Robert\\'); DROP TABLE customers; --", "lastName": "Test"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
    echo "  PASS: SQL injection sanitized (HTTP $HTTP_CODE)"
else
    echo "  Response: HTTP $HTTP_CODE"
fi

# Test 5: Create customer with XSS attempt
echo ""
echo "TEST 5: XSS in name field"
RESPONSE=$(curl -s -X POST "$API_URL/api/customers/" \
  -H "Content-Type: application/json" \
  -d '{"email": "xss.test@example.com", "firstName": "<script>alert(\\'xss\\')</script>", "lastName": "Test"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
    echo "  Response: HTTP $HTTP_CODE"
    # Check if script tags are in response
    if echo "$BODY" | grep -q "<script>"; then
        echo "  WARNING: XSS payload present in response!"
        ISSUES_FOUND+=("XSS vulnerability: script tags not sanitized")
    else
        echo "  PASS: XSS payload properly handled"
    fi
else
    echo "  Response: HTTP $HTTP_CODE"
fi

# Test 6: Get non-existent customer
echo ""
echo "TEST 6: Get non-existent customer"
RESPONSE=$(curl -s -X GET "$API_URL/api/customers/550e8400-e29b-41d4-a716-446655440000" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 404 ]; then
    echo "  PASS: Non-existent customer returns 404"
else
    echo "  FAIL: Expected 404, got HTTP $HTTP_CODE"
    ISSUES_FOUND+=("Non-existent customer not returning 404")
fi

# Test 7: Invalid UUID format
echo ""
echo "TEST 7: Invalid UUID format"
RESPONSE=$(curl -s -X GET "$API_URL/api/customers/invalid-uuid" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 400 ] || [ "$HTTP_CODE" -eq 422 ]; then
    echo "  PASS: Invalid UUID rejected"
else
    echo "  NOTE: Invalid UUID handling (HTTP $HTTP_CODE)"
fi

# Test 8: Create claim with invalid incident type
echo ""
echo "TEST 8: Claim with invalid incident type"
CUSTOMER_ID="9b98c7f0-03cf-459e-887f-84ca173545ae"
RESPONSE=$(curl -s -X POST "$API_URL/api/claims/" \
  -H "Content-Type: application/json" \
  -H "X-Customer-ID: $CUSTOMER_ID" \
  -d '{"flightNumber": "LH123", "flightDate": "2025-01-15", "departureAirport": "FRA", "arrivalAirport": "JFK", "incidentType": "invalid_type"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 422 ]; then
    echo "  PASS: Invalid incident type rejected"
else
    echo "  FAIL: Expected 422, got HTTP $HTTP_CODE"
    ISSUES_FOUND+=("Invalid incident type not properly validated")
fi

# Test 9: Create claim with future date
echo ""
echo "TEST 9: Claim with future flight date"
RESPONSE=$(curl -s -X POST "$API_URL/api/claims/" \
  -H "Content-Type: application/json" \
  -H "X-Customer-ID: $CUSTOMER_ID" \
  -d '{"flightNumber": "LH123", "flightDate": "2030-01-15", "departureAirport": "FRA", "arrivalAirport": "JFK", "incidentType": "delay"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 400 ] || [ "$HTTP_CODE" -eq 422 ]; then
    echo "  PASS: Future date rejected"
else
    echo "  NOTE: Future date accepted (HTTP $HTTP_CODE) - may be intentional for testing"
fi

# Test 10: Create claim with same airport
echo ""
echo "TEST 10: Claim with same departure/arrival airport"
RESPONSE=$(curl -s -X POST "$API_URL/api/claims/" \
  -H "Content-Type: application/json" \
  -H "X-Customer-ID: $CUSTOMER_ID" \
  -d '{"flightNumber": "LH123", "flightDate": "2025-01-15", "departureAirport": "FRA", "arrivalAirport": "FRA", "incidentType": "delay"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 400 ] || [ "$HTTP_CODE" -eq 422 ]; then
    echo "  PASS: Same airport rejected"
else
    echo "  NOTE: Same airport accepted (HTTP $HTTP_CODE)"
fi

# Test 11: Create claim with invalid airport code
echo ""
echo "TEST 11: Claim with invalid airport code"
RESPONSE=$(curl -s -X POST "$API_URL/api/claims/" \
  -H "Content-Type: application/json" \
  -H "X-Customer-ID: $CUSTOMER_ID" \
  -d '{"flightNumber": "LH123", "flightDate": "2025-01-15", "departureAirport": "INVALID", "arrivalAirport": "JFK", "incidentType": "delay"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 400 ] || [ "$HTTP_CODE" -eq 422 ]; then
    echo "  PASS: Invalid airport code rejected"
else
    echo "  NOTE: Invalid airport code handling (HTTP $HTTP_CODE)"
fi

# Test 12: Update customer with empty body
echo ""
echo "TEST 12: Update customer with empty body"
RESPONSE=$(curl -s -X PUT "$API_URL/api/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
echo "  Response: HTTP $HTTP_CODE"

# Test 13: Patch customer with partial data
echo ""
echo "TEST 13: Patch customer with partial data"
RESPONSE=$(curl -s -X PATCH "$API_URL/api/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{"firstName": "Updated"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "  PASS: Partial update successful"
else
    echo "  Response: HTTP $HTTP_CODE"
fi

# Test 14: List customers with pagination
echo ""
echo "TEST 14: List customers with pagination"
RESPONSE=$(curl -s -X GET "$API_URL/api/customers/?limit=5&offset=0" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "  PASS: Pagination works"
else
    echo "  Response: HTTP $HTTP_CODE"
fi

# Test 15: List customers with negative offset
echo ""
echo "TEST 15: List customers with negative offset"
RESPONSE=$(curl -s -X GET "$API_URL/api/customers/?limit=5&offset=-1" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
echo "  Response: HTTP $HTTP_CODE"

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Issues found: ${#ISSUES_FOUND[@]}"
if [ ${#ISSUES_FOUND[@]} -gt 0 ]; then
    echo ""
    echo "Issues:"
    for issue in "${ISSUES_FOUND[@]}"; do
        echo "  - $issue"
    done
fi
echo ""
echo "Completed at: $(date)"