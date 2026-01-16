# EasyAirClaim MCP Server

Model Context Protocol (MCP) Server for EasyAirClaim development and testing.

## ⚠️ Development Only

**This server is for DEVELOPMENT AND TESTING ONLY!**

- Full database access without authentication
- Never use with production data
- Only connect to development/test databases

## Features

- 🔍 **Query Data**: Check customers, claims, files existence
- ✨ **Create Test Data**: Quickly generate realistic test scenarios
- 🔄 **Manage Claims**: Update statuses, add notes, track workflow
- 🛠️ **Dev Utilities**: Seed data, reset database, validate integrity

## Quick Start

### 1. Start the Server

```bash
cd /home/david/easyairclaim-mcp
cp .env.example .env
docker-compose up -d
```

### 2. Configure Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "easyairclaim-dev": {
      "command": "curl",
      "args": ["-N", "-H", "Accept: text/event-stream", "http://localhost:39128/sse"]
    }
  }
}
```

Restart Claude Desktop.

### 3. Test Connection

In Claude Desktop:
```
Check the EasyAirClaim MCP server health
```

## Available Tools (18)

### Health & System
- `health_check` - Server and database connectivity
- `get_database_stats` - Entity counts and statistics
- `get_environment_info` - Configuration details

### Customer Management
- `create_customer` - Create new customer
- `get_customer` - Get customer by ID
- `get_customer_by_email` - Find by email
- `list_customers` - Paginated list
- `delete_customer` - Remove customer

### Claim Management
- `create_claim` - Create claim with EU261 calculation
- `get_claim` - Get claim details
- `list_claims` - List with filters
- `transition_claim_status` - Update status
- `add_claim_note` - Add admin note

### Development Utilities
- `seed_realistic_data` - Generate test data
- `create_test_scenario` - Create customer + claim
- `reset_database` - Clear test data (⚠️ destructive)
- `validate_data_integrity` - Check for issues

## Example Usage

```
# Check if customer exists
Is customer test@example.com in the database?

# Create test data
Create a customer and a delayed Lufthansa flight claim

# List claims
Show me all claims in 'under_review' status

# Update claim
Move claim CLM-12345 to approved status

# Seed data
Create 10 realistic test claims

# Get overview
Show me database statistics
```

## Architecture

- **FastAPI** with SSE support for MCP protocol
- **Direct SQLAlchemy** connection to EasyAirClaim database
- **Imports** main app models/services (read-only)
- **Docker** container with health checks

## Project Structure

```
easyairclaim-mcp/
├── server.py              # MCP server with SSE endpoint
├── config.py              # Configuration management
├── database.py            # Async database connection
├── tools/                 # MCP tool implementations
│   ├── health_tools.py    # System tools
│   ├── customer_tools.py  # Customer management
│   ├── claim_tools.py     # Claim management
│   └── dev_tools.py       # Development utilities
├── docker-compose.yml     # Container configuration
├── Dockerfile             # Container image
├── requirements.txt       # Python dependencies
└── MCP_USAGE_GUIDE.md     # Comprehensive guide
```

## Configuration

Edit `.env` file:

```bash
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/flight_claim
MCP_PORT=39128
ENABLE_DESTRUCTIVE_OPS=true
```

## Ports

- **39128** - MCP SSE endpoint
- **8083** - Status dashboard (optional)

## Safety Features

- Environment validation (blocks production)
- Destructive operation guards
- Read-only main app code mount
- Health check monitoring

## Troubleshooting

### Server not responding
```bash
docker logs easyairclaim-mcp-server
docker-compose restart
```

### Database connection issues
Check that main app database is running:
```bash
docker ps | grep postgres
```

### Tool errors in Claude
- Verify parameter types
- Check UUID format for IDs
- Use YYYY-MM-DD date format
- Use uppercase IATA airport codes

## Documentation

See **[MCP_USAGE_GUIDE.md](MCP_USAGE_GUIDE.md)** for:
- Detailed tool documentation
- Usage examples
- Development workflows
- Troubleshooting guide

## Development

### Run locally (without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python server.py
```

### View logs

```bash
docker-compose logs -f
```

### Stop server

```bash
docker-compose down
```

## Security Note

This MCP server has:
- ❌ No authentication
- ❌ No authorization
- ❌ No rate limiting
- ✅ Full database access

**NEVER connect to production databases or use with real customer data!**

---

**Version**: 1.0.0  
**Created**: 2026-01-14  
**Location**: `/home/david/easyairclaim-mcp/`
