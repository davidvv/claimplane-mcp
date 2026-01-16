# EasyAirClaim MCP Server - Usage Guide

This guide explains how to use the EasyAirClaim MCP (Model Context Protocol) Server for development and testing.

## ⚠️ IMPORTANT WARNING ⚠️

**This MCP server is for DEVELOPMENT AND TESTING ONLY!**

- ❌ **DO NOT** use in production environments
- ❌ **DO NOT** connect to production databases
- ❌ **DO NOT** use with real customer data
- ✅ **ONLY** use with development/test databases
- ✅ **ONLY** use for local development workflows

This server has unrestricted database access and no authentication.

---

## What is This MCP Server?

This MCP server provides Claude Desktop with direct integration to your EasyAirClaim development database, allowing you to:

- **Query Data**: Check if customers/claims exist, get details
- **Create Test Data**: Quickly create customers, claims, and complete scenarios
- **Manage Claims**: Update statuses, add notes, view history
- **Development Utilities**: Seed realistic data, reset database, validate integrity

---

## Quick Start

### 1. Start the MCP Server

#### Option A: Using Docker (Recommended)

```bash
cd /home/david/easyairclaim-mcp

# Start the server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

#### Option B: Local Python

```bash
cd /home/david/easyairclaim-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your database connection
nano .env

# Run the server
python server.py
```

### 2. Configure Claude Desktop

Add this to your Claude Desktop MCP settings file:

**Location**:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration**:
```json
{
  "mcpServers": {
    "easyairclaim-dev": {
      "command": "curl",
      "args": [
        "-N",
        "-H",
        "Accept: text/event-stream",
        "http://localhost:39128/sse"
      ]
    }
  }
}
```

**After adding, restart Claude Desktop.**

### 3. Verify Connection

In Claude Desktop, ask:
```
Can you check the EasyAirClaim MCP server health?
```

You should see database connection info and statistics.

---

## Available Tools (18 Total)

### Health & System (3 tools)

**health_check**
- Check MCP server and database connectivity
- No parameters required

**get_database_stats**
- Get counts of customers, claims, files, users
- Shows claims grouped by status
- No parameters required

**get_environment_info**
- Get configuration and environment details
- No parameters required

### Customer Management (5 tools)

**create_customer**
- Create a new customer with full details
- Required: email, first_name, last_name
- Optional: phone, street, city, postal_code, country

**get_customer**
- Get customer details by ID
- Required: customer_id

**get_customer_by_email**
- Find customer by email address
- Required: email

**list_customers**
- List customers with pagination
- Optional: limit (default: 10), offset (default: 0)

**delete_customer**
- Delete a customer by ID
- Required: customer_id

### Claim Management (5 tools)

**create_claim**
- Create a new flight compensation claim
- Required: customer_id, flight_number, flight_date, departure_airport, arrival_airport, incident_type
- Optional: delay_minutes, description, scheduled/actual times
- Automatically calculates EU261 compensation

**get_claim**
- Get complete claim details by ID
- Required: claim_id

**list_claims**
- List claims with optional filters
- Optional: customer_id, status, limit, offset

**transition_claim_status**
- Update claim status
- Required: claim_id, new_status
- Optional: admin_id, note
- Valid statuses: submitted, under_review, approved, rejected, paid

**add_claim_note**
- Add an admin note to a claim
- Required: claim_id, note
- Optional: admin_id

### Development Utilities (4 tools)

**seed_realistic_data**
- Populate database with realistic test data
- Optional: scenario (basic/complex/mixed), count (default: 5)
- Creates customers with claims, realistic flight data

**create_test_scenario**
- Create a complete test scenario (customer + claim)
- Optional: email (default: test@example.com), scenario_type
- Types: delayed_flight, cancelled_flight, denied_boarding

**reset_database**
- ⚠️ WARNING: Delete all test data from database
- No parameters required
- Requires ENABLE_DESTRUCTIVE_OPS=true

**validate_data_integrity**
- Check for orphaned records and data issues
- No parameters required

---

## Common Usage Examples

### Example 1: Check if Customer Exists

```
Is customer test@example.com in the database?
```

Claude will use `get_customer_by_email` and tell you if found.

### Example 2: Create Test Customer and Claim

```
Create a test customer with email john.doe@test.com and a delayed Lufthansa flight claim
```

Claude will:
1. Create customer with `create_customer`
2. Create claim with `create_claim`
3. Show you the IDs and compensation amount

### Example 3: List All Pending Claims

```
Show me all claims with status 'under_review'
```

Claude will use `list_claims` with status filter.

### Example 4: Update Claim Status

```
Move claim CLM-12345 to approved status
```

Claude will use `transition_claim_status` to update it.

### Example 5: Seed Test Data

```
Create 10 realistic test claims for me
```

Claude will use `seed_realistic_data` to generate customers and claims.

### Example 6: Get Database Overview

```
Give me an overview of the database
```

Claude will use `get_database_stats` to show counts.

---

## Claim Incident Types

When creating claims, use these incident types:

- **delay** - Flight delayed (requires delay_minutes)
- **cancellation** - Flight cancelled
- **denied_boarding** - Passenger denied boarding
- **missed_connection** - Missed connecting flight

---

## Claim Status Values

Valid claim statuses:

- **submitted** - Initial status when claim created
- **under_review** - Claim being reviewed by admin
- **approved** - Claim approved for payment
- **rejected** - Claim rejected
- **paid** - Compensation paid to customer

---

## EU261 Compensation Calculation

The MCP server automatically calculates compensation based on:

- **Distance**: Between departure and arrival airports
- **Delay**: Minutes of delay at arrival
- **Incident Type**: Type of disruption

Compensation amounts (EUR):
- ≤ 1,500 km: €250
- 1,500 - 3,500 km: €400
- > 3,500 km: €600

---

## Tips for Using the MCP Server

### 1. Always Check First

Before creating test data, check if it already exists:
```
Is customer test@example.com already in the database?
```

### 2. Use Realistic Flight Codes

When creating claims, use real IATA airport codes:
- FRA (Frankfurt), LHR (London), CDG (Paris), MAD (Madrid)
- Use real airline codes: LH (Lufthansa), BA (British Airways), AF (Air France)

### 3. Seed Data for Testing

Instead of creating individual records:
```
Seed 5 realistic test scenarios for me
```

### 4. Clean Up Regularly

Reset test data when needed:
```
Reset the database and clear all test data
```

### 5. Check Data Integrity

After bulk operations:
```
Validate the data integrity
```

---

## Connection Information

### Server Details
- **SSE Endpoint**: `http://localhost:39128/sse`
- **Health Check**: `http://localhost:39128/health`
- **Tools List**: `http://localhost:39128/tools`
- **Container Name**: `easyairclaim-mcp-server`

### Database Connection
- Uses same database as main EasyAirClaim app
- Connects via async SQLAlchemy
- Full access to all tables (customers, claims, files, users)

---

## Troubleshooting

### MCP Server Not Responding

1. Check if container is running:
   ```bash
   docker ps | grep easyairclaim-mcp
   ```

2. Check logs:
   ```bash
   docker logs easyairclaim-mcp-server
   ```

3. Restart container:
   ```bash
   cd /home/david/easyairclaim-mcp
   docker-compose restart
   ```

### Database Connection Errors

1. Verify main app database is running:
   ```bash
   docker ps | grep postgres
   ```

2. Check DATABASE_URL in .env file

3. Test connection manually:
   ```bash
   docker exec easyairclaim-mcp-server python -c "from database import init_database; import asyncio; asyncio.run(init_database())"
   ```

### Tool Errors in Claude

- Check tool parameters match schema
- Verify IDs are valid UUIDs
- Check date formats (YYYY-MM-DD)
- Ensure airport codes are uppercase IATA codes

---

## Advanced Features

### Custom Test Scenarios

Create specific test scenarios:
```
Create a test scenario for a cancelled British Airways flight from London to Paris
```

### Bulk Operations

Process multiple claims:
```
Create 20 test claims with different statuses for testing the admin dashboard
```

### Data Validation

Check for issues:
```
Check if there are any orphaned records in the database
```

---

## Safety Features

### Environment Check
- Server refuses to start if ENVIRONMENT=production
- Validates configuration on startup

### Destructive Operations
- `reset_database` requires explicit enablement
- Confirmation prompts before data deletion

### Read-Only Mounts
- Main app code mounted read-only in Docker
- MCP server cannot modify main app code

---

## Development Workflow Example

Here's a typical development workflow:

1. **Start fresh**:
   ```
   Reset the database
   ```

2. **Create test data**:
   ```
   Seed 10 realistic test claims
   ```

3. **Test a feature**:
   ```
   Show me all claims in 'submitted' status
   Update claim CLM-XXX to 'under_review'
   ```

4. **Verify results**:
   ```
   Get database statistics
   Validate data integrity
   ```

---

## API Reference

For detailed tool schemas, ask Claude:
```
What tools are available in the EasyAirClaim MCP server?
```

Or view directly:
```bash
curl http://localhost:39128/tools
```

---

## Need Help?

### View Server Status
```
Check the EasyAirClaim MCP server environment info
```

### List All Tools
```
What can the EasyAirClaim MCP server do?
```

### Get Tool Parameters
```
What parameters does create_claim accept?
```

---

**Server Location**: `/home/david/easyairclaim-mcp/`
**Last Updated**: 2026-01-14
**Version**: 1.0.0
