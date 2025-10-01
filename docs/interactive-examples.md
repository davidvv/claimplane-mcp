# Interactive Examples & Usage Guide

## Flight Claim System - Comprehensive API Usage Examples

This guide provides practical, hands-on examples for interacting with the Flight Claim System API using curl commands, Swagger UI, and various HTTP clients. All examples include expected responses and common variations.

## Getting Started

### Prerequisites

Ensure the Flight Claim System is running:

```bash
# Using Docker (recommended)
docker-compose up -d

# Verify system is running
curl http://localhost/health

# Access interactive documentation
# Open browser: http://localhost/docs (Swagger UI)
# Open browser: http://localhost/redoc (ReDoc)
```

### Base URLs

- **Docker Deployment**: `http://localhost`
- **Local Development**: `http://localhost:8000`
- **Development with port**: `http://localhost:8001` (if running on port 8001)

**Note**: All examples use `http://localhost` - adjust the base URL according to your setup.

## Complete Customer Lifecycle Examples

### 1. Create Customer

#### Basic Customer Creation

```bash
# Create customer with minimal required fields
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "firstName": "John",
    "lastName": "Doe"
  }'
```

**Expected Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "phone": null,
  "address": null,
  "createdAt": "2024-01-15T10:30:00.123456Z",
  "updatedAt": "2024-01-15T10:30:00.123456Z"
}
```

#### Customer with Complete Information

```bash
# Create customer with all optional fields
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane.smith@example.com",
    "firstName": "Jane",
    "lastName": "Smith",
    "phone": "+1-555-123-4567",
    "address": {
      "street": "123 Main Street, Apt 4B",
      "city": "New York",
      "postalCode": "10001",
      "country": "United States"
    }
  }'
```

**Expected Response** (201 Created):
```json
{
  "id": "660f9511-f30c-52e5-b827-557766551111",
  "email": "jane.smith@example.com",
  "firstName": "Jane",
  "lastName": "Smith",
  "phone": "+1-555-123-4567",
  "address": {
    "street": "123 Main Street, Apt 4B",
    "city": "New York",
    "postalCode": "10001",
    "country": "United States"
  },
  "createdAt": "2024-01-15T10:35:00.789012Z",
  "updatedAt": "2024-01-15T10:35:00.789012Z"
}
```

#### Error Example: Duplicate Email

```bash
# Attempt to create customer with existing email
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "firstName": "Another",
    "lastName": "Person"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_ENTRY",
    "message": "Customer with email john.doe@example.com already exists",
    "details": []
  },
  "timestamp": "2024-01-15T10:40:00.456789Z"
}
```

### 2. Retrieve Customers

#### Get Customer by ID

```bash
# Get specific customer
curl "http://localhost/customers/550e8400-e29b-41d4-a716-446655440000"
```

#### List All Customers

```bash
# Get all customers (default pagination)
curl "http://localhost/customers"

# Get customers with custom pagination
curl "http://localhost/customers?skip=0&limit=5"

# Get next page
curl "http://localhost/customers?skip=5&limit=5"
```

#### Search Customers

```bash
# Search by email (partial matching)
curl "http://localhost/customers/search/by-email/john"

# Search by name (first name or last name)
curl "http://localhost/customers/search/by-name/doe"

# URL encode spaces in search terms
curl "http://localhost/customers/search/by-name/Jane%20Smith"
```

### 3. Update Customer (PUT - Complete Replacement)

#### Complete Customer Update

```bash
# Store customer ID for examples
CUSTOMER_ID="550e8400-e29b-41d4-a716-446655440000"

# Update customer with all fields (PUT)
curl -X PUT "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe.updated@example.com",
    "firstName": "Jonathan",
    "lastName": "Doe",
    "phone": "+1-555-987-6543",
    "address": {
      "street": "456 Oak Avenue",
      "city": "Los Angeles",
      "postalCode": "90210",
      "country": "United States"
    }
  }'
```

#### PUT with Null Values (Remove Optional Data)

```bash
# Remove phone and address by setting to null
curl -X PUT "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "phone": null,
    "address": null
  }'
```

### 4. Update Customer (PATCH - Partial Update)

#### Update Single Field

```bash
# Update only email
curl -X PATCH "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.newemail@example.com"
  }'

# Update only name
curl -X PATCH "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Johnny"
  }'
```

#### Update Multiple Fields

```bash
# Update name and phone
curl -X PATCH "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Smith",
    "phone": "+1-555-111-2222"
  }'
```

#### Update Address Only

```bash
# Update just the address
curl -X PATCH "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "address": {
      "street": "789 Pine Street",
      "city": "Chicago",
      "postalCode": "60601",
      "country": "United States"
    }
  }'
```

#### PATCH Edge Cases

```bash
# Empty string handling (converted to null, then ignored)
curl -X PATCH "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "",
    "firstName": "John"
  }'

# Only firstName will be updated; email remains unchanged

# No fields to update (returns existing customer)
curl -X PATCH "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Complete Claim Lifecycle Examples

### 1. Create Claim for Existing Customer

```bash
# Create claim for existing customer
curl -X POST "http://localhost/claims" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "AA1234",
      "airline": "American Airlines",
      "departureDate": "2024-03-15",
      "departureAirport": "JFK",
      "arrivalAirport": "LAX"
    },
    "incidentType": "delay",
    "notes": "Flight was delayed by 4 hours due to weather conditions. Original departure time was 2:00 PM, actual departure was 6:00 PM."
  }'
```

**Expected Response** (201 Created):
```json
{
  "id": "770f8400-e29b-41d4-a716-446655440001",
  "customerId": "550e8400-e29b-41d4-a716-446655440000",
  "flightNumber": "AA1234",
  "airline": "American Airlines",
  "departureDate": "2024-03-15",
  "departureAirport": "JFK",
  "arrivalAirport": "LAX",
  "incidentType": "delay",
  "status": "submitted",
  "compensationAmount": null,
  "currency": "EUR",
  "notes": "Flight was delayed by 4 hours due to weather conditions...",
  "submittedAt": "2024-01-15T14:30:00.123456Z",
  "updatedAt": "2024-01-15T14:30:00.123456Z"
}
```

### 2. Submit Claim with Customer Info (One-Step Process)

```bash
# Create customer and claim in one request
curl -X POST "http://localhost/claims/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "customerInfo": {
      "email": "traveler@example.com",
      "firstName": "Sarah",
      "lastName": "Wilson",
      "phone": "+44-20-7946-0958",
      "address": {
        "street": "10 Downing Street",
        "city": "London",
        "postalCode": "SW1A 2AA",
        "country": "United Kingdom"
      }
    },
    "flightInfo": {
      "flightNumber": "BA456",
      "airline": "British Airways",
      "departureDate": "2024-04-20",
      "departureAirport": "LHR",
      "arrivalAirport": "CDG"
    },
    "incidentType": "cancellation",
    "notes": "Flight was cancelled 2 hours before departure with no alternative offered until the next day."
  }'
```

### 3. Different Incident Types

#### Flight Delay Claim
```bash
curl -X POST "http://localhost/claims" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "UA789",
      "airline": "United Airlines",
      "departureDate": "2024-05-10",
      "departureAirport": "ORD",
      "arrivalAirport": "SFO"
    },
    "incidentType": "delay",
    "notes": "Mechanical issues caused 6-hour delay. Missed connecting flight to Tokyo."
  }'
```

#### Denied Boarding Claim
```bash
curl -X POST "http://localhost/claims" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "DL567",
      "airline": "Delta Air Lines",
      "departureDate": "2024-06-05",
      "departureAirport": "ATL",
      "arrivalAirport": "MIA"
    },
    "incidentType": "denied_boarding",
    "notes": "Overbooked flight. Despite having confirmed reservation and checking in early, was denied boarding."
  }'
```

#### Baggage Delay Claim
```bash
curl -X POST "http://localhost/claims" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "LH890",
      "airline": "Lufthansa",
      "departureDate": "2024-07-12",
      "departureAirport": "FRA",
      "arrivalAirport": "JFK"
    },
    "incidentType": "baggage_delay",
    "notes": "Checked baggage was delayed by 48 hours. Had to purchase essential items for business trip."
  }'
```

### 4. Retrieve Claims

#### Get Specific Claim
```bash
CLAIM_ID="770f8400-e29b-41d4-a716-446655440001"
curl "http://localhost/claims/$CLAIM_ID"
```

#### List All Claims
```bash
# Get all claims
curl "http://localhost/claims"

# Get claims with pagination
curl "http://localhost/claims?skip=0&limit=10"
```

#### Filter Claims by Status
```bash
# Get submitted claims
curl "http://localhost/claims/status/submitted"

# Get approved claims
curl "http://localhost/claims/status/approved"

# Get all claims with status filter
curl "http://localhost/claims?status=under_review"
```

#### Get Claims for Specific Customer
```bash
# Get all claims for a customer
curl "http://localhost/claims/customer/550e8400-e29b-41d4-a716-446655440000"

# With pagination
curl "http://localhost/claims/customer/550e8400-e29b-41d4-a716-446655440000?skip=0&limit=5"
```

### 5. Update Claims (PUT vs PATCH)

#### Complete Claim Update (PUT)
```bash
CLAIM_ID="770f8400-e29b-41d4-a716-446655440001"

curl -X PUT "http://localhost/claims/$CLAIM_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "AA1234",
      "airline": "American Airlines",
      "departureDate": "2024-03-15",
      "departureAirport": "JFK",
      "arrivalAirport": "LAX"
    },
    "incidentType": "cancellation",
    "notes": "Flight was actually cancelled, not just delayed. Received notification 1 hour before departure."
  }'
```

#### Partial Claim Update (PATCH)
```bash
# Update only incident type and notes
curl -X PATCH "http://localhost/claims/$CLAIM_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "incidentType": "cancellation",
    "notes": "Corrected: Flight was cancelled, not delayed."
  }'

# Update only notes
curl -X PATCH "http://localhost/claims/$CLAIM_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Additional information: Airline provided hotel voucher for overnight stay."
  }'
```

## System Health and Information Examples

### Health Checks

```bash
# Basic health check
curl "http://localhost/health"

# Database-specific health check
curl "http://localhost/health/db"

# Detailed system health
curl "http://localhost/health/detailed"
```

### API Information

```bash
# Basic API info
curl "http://localhost/"

# Detailed API information
curl "http://localhost/info"
```

## Error Handling Examples

### Validation Errors

#### Missing Required Fields
```bash
# Missing required firstName
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "incomplete@example.com",
    "lastName": "User"
  }'
```

**Expected Response** (422 Unprocessable Entity):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "firstName",
        "message": "field required",
        "type": "value_error.missing"
      }
    ]
  },
  "timestamp": "2024-01-15T15:45:00.123456Z"
}
```

#### Invalid Email Format
```bash
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email-format",
    "firstName": "Test",
    "lastName": "User"
  }'
```

#### Field Length Validation
```bash
# First name too long (>50 characters)
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "firstName": "ThisIsAnExtremelyLongFirstNameThatExceedsFiftyCharacters",
    "lastName": "User"
  }'
```

### Business Logic Errors

#### Customer Not Found
```bash
# Try to get non-existent customer
curl "http://localhost/customers/00000000-0000-0000-0000-000000000000"
```

#### Invalid Airport Codes
```bash
curl -X POST "http://localhost/claims" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "TEST123",
      "airline": "Test Airlines",
      "departureDate": "2024-08-15",
      "departureAirport": "INVALID",
      "arrivalAirport": "XYZ"
    },
    "incidentType": "delay"
  }'
```

#### Invalid Incident Type
```bash
curl -X POST "http://localhost/claims" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "550e8400-e29b-41d4-a716-446655440000",
    "flightInfo": {
      "flightNumber": "TEST456",
      "airline": "Test Airlines",
      "departureDate": "2024-09-20",
      "departureAirport": "LAX",
      "arrivalAirport": "JFK"
    },
    "incidentType": "invalid_incident"
  }'
```

## Swagger UI Interactive Examples

### Accessing Swagger UI

1. **Open Swagger UI**: Navigate to `http://localhost/docs` in your browser
2. **Interactive Documentation**: All endpoints are displayed with "Try it out" functionality
3. **Authentication**: Currently no authentication required (all endpoints open)

### Using Swagger UI

#### Customer Operations Example

1. **Navigate to Customer Section**
2. **Click "POST /customers"** to expand
3. **Click "Try it out"** button
4. **Edit the request body**:
   ```json
   {
     "email": "swagger.test@example.com",
     "firstName": "Swagger",
     "lastName": "Test",
     "phone": "+1-555-SWAGGER",
     "address": {
       "street": "123 API Street",
       "city": "Documentation City",
       "postalCode": "12345",
       "country": "Testing Nation"
     }
   }
   ```
5. **Click "Execute"**
6. **Review the response** in the Response section

#### PATCH vs PUT Demonstration in Swagger

**PATCH Example**:
1. Find a customer ID from a previous GET request
2. Navigate to **PATCH /customers/{customer_id}**
3. Enter the customer ID
4. Use this partial update body:
   ```json
   {
     "phone": "+1-555-UPDATED"
   }
   ```
5. Execute and note that only the phone is updated

**PUT Example**:
1. Use the same customer ID
2. Navigate to **PUT /customers/{customer_id}**
3. Use complete customer data:
   ```json
   {
     "email": "complete.update@example.com",
     "firstName": "Complete",
     "lastName": "Update",
     "phone": "+1-555-COMPLETE",
     "address": {
       "street": "456 PUT Street",
       "city": "Update City",
       "postalCode": "67890",
       "country": "PUT Nation"
     }
   }
   ```
4. Execute and note all fields are replaced

### Testing Error Scenarios in Swagger

#### Duplicate Email Test
1. Create a customer with a specific email
2. Try to create another customer with the same email
3. Observe the 400 Bad Request response

#### Validation Error Test
1. Try to create a customer with missing required fields
2. Observe the 422 Unprocessable Entity response
3. Review the detailed validation errors

## Advanced Usage Patterns

### Batch Operations Workflow

```bash
# 1. Create multiple customers
for name in "Alice Johnson" "Bob Wilson" "Carol Davis"; do
  first_name=$(echo $name | cut -d' ' -f1)
  last_name=$(echo $name | cut -d' ' -f2)
  email="$(echo $first_name | tr '[:upper:]' '[:lower:]').$(echo $last_name | tr '[:upper:]' '[:lower:]')@batch.example.com"
  
  curl -X POST "http://localhost/customers" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"$email\",
      \"firstName\": \"$first_name\",
      \"lastName\": \"$last_name\"
    }"
  echo # New line for readability
done

# 2. List all customers to get IDs
curl "http://localhost/customers" | jq '.[] | {id: .id, email: .email}'

# 3. Create claims for each customer
# (Use IDs from step 2)
```

### Search and Filter Workflow

```bash
# 1. Search for customers by partial email
curl "http://localhost/customers/search/by-email/example.com" | jq '.[] | .email'

# 2. Get claims for each customer
# (Use customer IDs from step 1)
curl "http://localhost/claims/customer/CUSTOMER_ID"

# 3. Filter claims by status
curl "http://localhost/claims/status/submitted" | jq '.[] | {id: .id, customerId: .customerId, flightNumber: .flightNumber}'
```

### Data Consistency Testing

```bash
# Test PUT vs PATCH behavior
CUSTOMER_ID="your-customer-id-here"

# 1. Get current customer data
echo "Original customer:"
curl "http://localhost/customers/$CUSTOMER_ID" | jq

# 2. PATCH update (partial)
echo "After PATCH (phone only):"
curl -X PATCH "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1-555-PATCH"}' | jq

# 3. PUT update (complete)
echo "After PUT (all fields):"
curl -X PUT "http://localhost/customers/$CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "put.test@example.com",
    "firstName": "PUT",
    "lastName": "Test",
    "phone": "+1-555-PUT",
    "address": null
  }' | jq
```

### Performance Testing Workflow

```bash
# Simple load test using curl
for i in {1..10}; do
  echo "Request $i:"
  time curl -s "http://localhost/health" > /dev/null
done

# Test with different endpoints
endpoints=("/health" "/customers" "/claims")
for endpoint in "${endpoints[@]}"; do
  echo "Testing $endpoint:"
  time curl -s "http://localhost$endpoint" > /dev/null
done
```

## Best Practices for API Usage

### 1. Error Handling in Scripts

```bash
#!/bin/bash
# Example script with proper error handling

BASE_URL="http://localhost"

# Function to make API call with error handling
api_call() {
  local method="$1"
  local endpoint="$2"
  local data="$3"
  
  if [ -n "$data" ]; then
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" "$BASE_URL$endpoint" \
      -H "Content-Type: application/json" \
      -d "$data")
  else
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$BASE_URL$endpoint")
  fi
  
  body=$(echo "$response" | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
  http_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
  
  if [ "$http_code" -lt 200 ] || [ "$http_code" -gt 299 ]; then
    echo "Error: HTTP $http_code"
    echo "$body" | jq
    return 1
  else
    echo "$body" | jq
    return 0
  fi
}

# Usage example
if api_call "POST" "/customers" '{
  "email": "script@example.com",
  "firstName": "Script",
  "lastName": "User"
}'; then
  echo "Customer created successfully"
else
  echo "Failed to create customer"
  exit 1
fi
```

### 2. Data Validation Before API Calls

```bash
# Validate email format before sending
validate_email() {
  local email="$1"
  if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "Invalid email format: $email"
    return 1
  fi
  return 0
}

# Validate airport code format
validate_airport_code() {
  local code="$1"
  if [[ ! "$code" =~ ^[A-Z]{3}$ ]]; then
    echo "Invalid airport code format: $code (must be 3 uppercase letters)"
    return 1
  fi
  return 0
}

# Usage in script
email="user@example.com"
if validate_email "$email"; then
  # Proceed with API call
  api_call "POST" "/customers" "{\"email\": \"$email\", ...}"
fi
```

### 3. Response Processing

```bash
# Extract specific data from responses
get_customer_id_by_email() {
  local email="$1"
  curl -s "http://localhost/customers/search/by-email/$email" | jq -r '.[0].id // empty'
}

# Use in workflow
customer_id=$(get_customer_id_by_email "john.doe@example.com")
if [ -n "$customer_id" ]; then
  echo "Found customer ID: $customer_id"
  # Use the ID for subsequent operations
else
  echo "Customer not found"
fi
```

This comprehensive interactive examples guide provides practical, real-world usage patterns for the Flight Claim System API, covering both basic operations and advanced workflows using curl commands, Swagger UI, and scripting techniques.