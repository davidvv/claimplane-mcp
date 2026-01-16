"""EasyAirClaim MCP Server with SSE support."""
import asyncio
import json
import logging
from typing import Dict, Any, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse

from config import MCPConfig
from database import init_database, close_database
import tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, MCPConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Tool Registry: Maps tool names to functions
TOOL_REGISTRY: Dict[str, Callable] = {
    # Health & System
    "health_check": tools.health_check,
    "get_database_stats": tools.get_database_stats,
    "get_environment_info": tools.get_environment_info,
    
    # Customer Management
    "create_customer": tools.create_customer,
    "get_customer": tools.get_customer,
    "get_customer_by_email": tools.get_customer_by_email,
    "list_customers": tools.list_customers,
    "delete_customer": tools.delete_customer,
    
    # Claim Management
    "create_claim": tools.create_claim,
    "get_claim": tools.get_claim,
    "list_claims": tools.list_claims,
    "transition_claim_status": tools.transition_claim_status,
    "add_claim_note": tools.add_claim_note,
    
    # File Management
    "list_claim_files": tools.list_claim_files,
    "get_file_metadata": tools.get_file_metadata,
    "get_file_validation_status": tools.get_file_validation_status,
    "approve_file": tools.approve_file,
    "reject_file": tools.reject_file,
    "delete_file": tools.delete_file,
    "get_files_by_status": tools.get_files_by_status,
    
    # User/Admin Management
    "create_user": tools.create_user,
    "create_admin": tools.create_admin,
    "get_user": tools.get_user,
    "get_user_by_email": tools.get_user_by_email,
    "list_users": tools.list_users,
    "update_user": tools.update_user,
    "delete_user": tools.delete_user,
    "activate_user": tools.activate_user,
    "deactivate_user": tools.deactivate_user,
    "verify_user_email": tools.verify_user_email,
    
    # Development Tools
    "seed_realistic_data": tools.seed_realistic_data,
    "create_test_scenario": tools.create_test_scenario,
    "reset_database": tools.reset_database,
    "validate_data_integrity": tools.validate_data_integrity,
}


# Tool Schemas for MCP Protocol
TOOL_SCHEMAS = [
    {
        "name": "health_check",
        "description": "Check MCP server and database connectivity",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_database_stats",
        "description": "Get database statistics (counts of customers, claims, files, users)",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_environment_info",
        "description": "Get environment and configuration information",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "create_customer",
        "description": "Create a new customer with contact and address details",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "phone": {"type": "string"},
                "street": {"type": "string"},
                "city": {"type": "string"},
                "postal_code": {"type": "string"},
                "country": {"type": "string"}
            },
            "required": ["email", "first_name", "last_name"]
        }
    },
    {
        "name": "get_customer",
        "description": "Get customer details by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"}
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "get_customer_by_email",
        "description": "Find customer by email address",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"}
            },
            "required": ["email"]
        }
    },
    {
        "name": "list_customers",
        "description": "List customers with pagination",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer"},
                "offset": {"type": "integer"}
            },
            "required": []
        }
    },
    {
        "name": "delete_customer",
        "description": "Delete a customer by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"}
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "create_claim",
        "description": "Create a new flight compensation claim with EU261 calculation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "flight_number": {"type": "string"},
                "flight_date": {"type": "string"},
                "departure_airport": {"type": "string"},
                "arrival_airport": {"type": "string"},
                "incident_type": {"type": "string"},
                "scheduled_departure": {"type": "string"},
                "actual_departure": {"type": "string"},
                "scheduled_arrival": {"type": "string"},
                "actual_arrival": {"type": "string"},
                "delay_minutes": {"type": "integer"},
                "description": {"type": "string"}
            },
            "required": ["customer_id", "flight_number", "flight_date", "departure_airport", "arrival_airport", "incident_type"]
        }
    },
    {
        "name": "get_claim",
        "description": "Get complete claim details by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"}
            },
            "required": ["claim_id"]
        }
    },
    {
        "name": "list_claims",
        "description": "List claims with optional filters (customer_id, status)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "status": {"type": "string"},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"}
            },
            "required": []
        }
    },
    {
        "name": "transition_claim_status",
        "description": "Update claim status (submitted, under_review, approved, rejected, paid)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"},
                "new_status": {"type": "string"},
                "admin_id": {"type": "string"},
                "note": {"type": "string"}
            },
            "required": ["claim_id", "new_status"]
        }
    },
    {
        "name": "add_claim_note",
        "description": "Add an admin note to a claim",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"},
                "note": {"type": "string"},
                "admin_id": {"type": "string"}
            },
            "required": ["claim_id", "note"]
        }
    },
    {
        "name": "seed_realistic_data",
        "description": "Populate database with realistic test data (customers and claims)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scenario": {"type": "string"},
                "count": {"type": "integer"}
            },
            "required": []
        }
    },
    {
        "name": "create_test_scenario",
        "description": "Create a complete test scenario (customer + claim)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "scenario_type": {"type": "string"}
            },
            "required": []
        }
    },
    {
        "name": "reset_database",
        "description": "⚠️ WARNING: Delete all test data from database",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "validate_data_integrity",
        "description": "Check for data integrity issues (orphaned records, etc)",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    # File Management Tools
    {
        "name": "list_claim_files",
        "description": "List all files for a specific claim",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"}
            },
            "required": ["claim_id"]
        }
    },
    {
        "name": "get_file_metadata",
        "description": "Get detailed file metadata and validation status",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"}
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "get_file_validation_status",
        "description": "Get file validation and security scan status",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"}
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "approve_file",
        "description": "Approve a file (admin action)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"},
                "admin_id": {"type": "string"}
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "reject_file",
        "description": "Reject a file with reason (admin action)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"},
                "reason": {"type": "string"},
                "admin_id": {"type": "string"}
            },
            "required": ["file_id", "reason"]
        }
    },
    {
        "name": "delete_file",
        "description": "Delete a file by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"}
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "get_files_by_status",
        "description": "Get files filtered by validation status",
        "inputSchema": {
            "type": "object",
            "properties": {
                "validation_status": {"type": "string"},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"}
            },
            "required": ["validation_status"]
        }
    },
    # User/Admin Management Tools
    {
        "name": "create_user",
        "description": "Create a new user account",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "password": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "role": {"type": "string"}
            },
            "required": ["email", "password", "first_name", "last_name"]
        }
    },
    {
        "name": "create_admin",
        "description": "Create a new admin user account",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "password": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"}
            },
            "required": ["email", "password", "first_name", "last_name"]
        }
    },
    {
        "name": "get_user",
        "description": "Get user details by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_user_by_email",
        "description": "Find user by email address",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"}
            },
            "required": ["email"]
        }
    },
    {
        "name": "list_users",
        "description": "List users with optional role filter",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"}
            },
            "required": []
        }
    },
    {
        "name": "update_user",
        "description": "Update user details",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "email": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "role": {"type": "string"},
                "is_active": {"type": "boolean"},
                "is_email_verified": {"type": "boolean"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "delete_user",
        "description": "Delete a user by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "activate_user",
        "description": "Activate a user account",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "deactivate_user",
        "description": "Deactivate a user account",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "verify_user_email",
        "description": "Mark user email as verified",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.warning(
        "\n"
        "═══════════════════════════════════════════════════════════════\n"
        "  ⚠️  EASYAIRCLAIM MCP SERVER - DEVELOPMENT MODE ONLY  ⚠️\n"
        "═══════════════════════════════════════════════════════════════\n"
        f"  Environment: {MCPConfig.ENVIRONMENT}\n"
        f"  MCP Port: {MCPConfig.MCP_PORT}\n"
        f"  Dashboard Port: {MCPConfig.DASHBOARD_PORT}\n"
        "  Database: Full access enabled\n"
        "  Destructive Operations: " + ("✓ ENABLED" if MCPConfig.ENABLE_DESTRUCTIVE_OPS else "✗ DISABLED") + "\n"
        "═══════════════════════════════════════════════════════════════\n"
        "  WARNING: This server has unrestricted database access!\n"
        "           DO NOT run in production!\n"
        "═══════════════════════════════════════════════════════════════\n"
    )
    
    # Initialize database connection
    try:
        await init_database()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down EasyAirClaim MCP Server...")
    await close_database()


# Create FastAPI app
app = FastAPI(
    title="EasyAirClaim MCP Server",
    description="Model Context Protocol Server for EasyAirClaim Development",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "EasyAirClaim MCP Server",
        "version": "1.0.0",
        "environment": MCPConfig.ENVIRONMENT,
        "tools_available": len(TOOL_REGISTRY),
        "sse_endpoint": "/sse"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return await tools.health_check()


@app.get("/tools")
async def list_tools():
    """List available tools."""
    return {
        "tools": TOOL_SCHEMAS
    }


async def handle_mcp_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool call request."""
    try:
        method = request_data.get("method")
        params = request_data.get("params", {})
        
        if method == "initialize":
            return {
                "protocolVersion": "0.1.0",
                "serverInfo": {
                    "name": "easyairclaim-dev",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        
        elif method == "tools/list":
            return {
                "tools": TOOL_SCHEMAS
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name not in TOOL_REGISTRY:
                return {
                    "error": f"Unknown tool: {tool_name}"
                }
            
            # Call the tool
            tool_func = TOOL_REGISTRY[tool_name]
            result = await tool_func(**tool_args)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        else:
            return {"error": f"Unknown method: {method}"}
            
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}", exc_info=True)
        return {"error": str(e)}


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP protocol."""
    async def event_generator():
        try:
            while True:
                # Wait for client messages (simplified for now)
                # In a full implementation, this would handle bi-directional communication
                
                # Send periodic heartbeat
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": asyncio.get_event_loop().time()})
                }
                
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            logger.info("SSE connection closed")
    
    return EventSourceResponse(event_generator())


@app.post("/rpc")
async def rpc_endpoint(request: Request):
    """JSON-RPC endpoint for MCP calls."""
    try:
        request_data = await request.json()
        result = await handle_mcp_request(request_data)
        
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "result": result
        }
    except Exception as e:
        logger.error(f"RPC error: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if 'request_data' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server:app",
        host=MCPConfig.MCP_HOST,
        port=MCPConfig.MCP_PORT,
        reload=True,
        log_level=MCPConfig.LOG_LEVEL.lower()
    )
