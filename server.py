"""EasyAirClaim MCP Server using official MCP SDK (FastMCP).

This server provides tools for interacting with the EasyAirClaim database
for development and testing purposes.
"""
import contextlib
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Dict, Any, Optional

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

from mcp.server.fastmcp import FastMCP

from config import MCPConfig
from database import init_database, close_database
import tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, MCPConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Lifespan Context for Database Management
# =============================================================================

@dataclass
class AppContext:
    """Application context with database connection status."""
    db_ready: bool


@contextlib.asynccontextmanager
async def mcp_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage database lifecycle for FastMCP server."""
    logger.warning("=" * 60)
    logger.warning("  EasyAirClaim MCP Server - DEVELOPMENT MODE ONLY")
    logger.warning("  Full database access - NO authentication!")
    logger.warning("=" * 60)
    
    try:
        await init_database()
        logger.info("Database connection established")
        yield AppContext(db_ready=True)
    finally:
        await close_database()
        logger.info("Database connection closed")


# =============================================================================
# Create FastMCP Server
# =============================================================================

mcp = FastMCP(
    name="easyairclaim-dev",
    instructions="""
    EasyAirClaim Development MCP Server.
    
    This server provides tools for managing:
    - Customers (create, read, list, delete)
    - Claims (create, read, list, status transitions)
    - Files (list, metadata, approve/reject)
    - Users (create, read, update, delete, activate/deactivate)
    - Development utilities (seed data, reset, validation)
    
    All operations are for DEVELOPMENT/TESTING only.
    """,
    lifespan=mcp_lifespan,
    stateless_http=True,
    json_response=True,
)


# =============================================================================
# Health & System Tools
# =============================================================================

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Check MCP server and database connectivity.
    
    Returns health status with database connection info.
    """
    return await tools.health_check()


@mcp.tool()
async def get_database_stats() -> Dict[str, Any]:
    """Get database statistics (counts of various entities).
    
    Returns counts of customers, claims, and files.
    """
    return await tools.get_database_stats()


@mcp.tool()
async def get_environment_info() -> Dict[str, Any]:
    """Get environment and configuration information.
    
    Returns environment details and configuration.
    """
    return await tools.get_environment_info()


# =============================================================================
# Customer Management Tools
# =============================================================================

@mcp.tool()
async def create_customer(
    email: str,
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    street: Optional[str] = None,
    city: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new customer with contact and address details.
    
    Args:
        email: Customer email address
        first_name: First name
        last_name: Last name
        phone: Phone number (optional)
        street: Street address (optional)
        city: City (optional)
        postal_code: Postal code (optional)
        country: Country (optional)
    """
    return await tools.create_customer(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        street=street,
        city=city,
        postal_code=postal_code,
        country=country
    )


@mcp.tool()
async def get_customer(customer_id: str) -> Dict[str, Any]:
    """Get customer details by ID.
    
    Args:
        customer_id: Customer ID (UUID)
    """
    return await tools.get_customer(customer_id=customer_id)


@mcp.tool()
async def get_customer_by_email(email: str) -> Dict[str, Any]:
    """Find customer by email address.
    
    Args:
        email: Customer email address
    """
    return await tools.get_customer_by_email(email=email)


@mcp.tool()
async def list_customers(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """List customers with pagination.
    
    Args:
        limit: Number of results to return (default: 10)
        offset: Number of results to skip (default: 0)
    """
    return await tools.list_customers(limit=limit, offset=offset)


@mcp.tool()
async def delete_customer(customer_id: str) -> Dict[str, Any]:
    """Delete a customer by ID.
    
    Args:
        customer_id: Customer ID (UUID)
    """
    return await tools.delete_customer(customer_id=customer_id)


# =============================================================================
# Claim Management Tools
# =============================================================================

@mcp.tool()
async def create_claim(
    customer_id: str,
    flight_number: str,
    flight_date: str,
    departure_airport: str,
    arrival_airport: str,
    incident_type: str,
    scheduled_departure: Optional[str] = None,
    actual_departure: Optional[str] = None,
    scheduled_arrival: Optional[str] = None,
    actual_arrival: Optional[str] = None,
    delay_minutes: Optional[int] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new flight compensation claim with EU261 calculation.
    
    Args:
        customer_id: Customer ID (UUID)
        flight_number: Flight number (e.g., "LH123")
        flight_date: Flight date (YYYY-MM-DD)
        departure_airport: Departure airport IATA code
        arrival_airport: Arrival airport IATA code
        incident_type: Type of incident (delay, cancellation, denied_boarding, missed_connection)
        scheduled_departure: Scheduled departure time (ISO format, optional)
        actual_departure: Actual departure time (ISO format, optional)
        scheduled_arrival: Scheduled arrival time (ISO format, optional)
        actual_arrival: Actual arrival time (ISO format, optional)
        delay_minutes: Delay in minutes (optional)
        description: Claim description (optional)
    """
    return await tools.create_claim(
        customer_id=customer_id,
        flight_number=flight_number,
        flight_date=flight_date,
        departure_airport=departure_airport,
        arrival_airport=arrival_airport,
        incident_type=incident_type,
        scheduled_departure=scheduled_departure,
        actual_departure=actual_departure,
        scheduled_arrival=scheduled_arrival,
        actual_arrival=actual_arrival,
        delay_minutes=delay_minutes,
        description=description
    )


@mcp.tool()
async def get_claim(claim_id: str) -> Dict[str, Any]:
    """Get complete claim details by ID.
    
    Args:
        claim_id: Claim ID (UUID)
    """
    return await tools.get_claim(claim_id=claim_id)


@mcp.tool()
async def list_claims(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """List claims with optional filters.
    
    Args:
        customer_id: Filter by customer ID (optional)
        status: Filter by status (optional)
        limit: Number of results (default: 10)
        offset: Number to skip (default: 0)
    """
    return await tools.list_claims(
        customer_id=customer_id,
        status=status,
        limit=limit,
        offset=offset
    )


@mcp.tool()
async def transition_claim_status(
    claim_id: str,
    new_status: str,
    admin_id: Optional[str] = None,
    note: Optional[str] = None
) -> Dict[str, Any]:
    """Update claim status (submitted, under_review, approved, rejected, paid).
    
    Args:
        claim_id: Claim ID (UUID)
        new_status: New status
        admin_id: Admin user ID performing transition (optional)
        note: Note about the transition (optional)
    """
    return await tools.transition_claim_status(
        claim_id=claim_id,
        new_status=new_status,
        admin_id=admin_id,
        note=note
    )


@mcp.tool()
async def add_claim_note(
    claim_id: str,
    note: str,
    admin_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add an admin note to a claim.
    
    Args:
        claim_id: Claim ID (UUID)
        note: Note content
        admin_id: Admin user ID (optional)
    """
    return await tools.add_claim_note(
        claim_id=claim_id,
        note=note,
        admin_id=admin_id
    )


# =============================================================================
# File Management Tools
# =============================================================================

@mcp.tool()
async def list_claim_files(claim_id: str) -> Dict[str, Any]:
    """List all files for a specific claim.
    
    Args:
        claim_id: Claim ID (UUID)
    """
    return await tools.list_claim_files(claim_id=claim_id)


@mcp.tool()
async def get_file_metadata(file_id: str) -> Dict[str, Any]:
    """Get detailed file metadata and validation status.
    
    Args:
        file_id: File ID (UUID)
    """
    return await tools.get_file_metadata(file_id=file_id)


@mcp.tool()
async def get_file_validation_status(file_id: str) -> Dict[str, Any]:
    """Get file validation and security scan status.
    
    Args:
        file_id: File ID (UUID)
    """
    return await tools.get_file_validation_status(file_id=file_id)


@mcp.tool()
async def approve_file(file_id: str, admin_id: Optional[str] = None) -> Dict[str, Any]:
    """Approve a file (admin action).
    
    Args:
        file_id: File ID (UUID)
        admin_id: Admin user ID (optional)
    """
    return await tools.approve_file(file_id=file_id, admin_id=admin_id)


@mcp.tool()
async def reject_file(
    file_id: str,
    reason: str,
    admin_id: Optional[str] = None
) -> Dict[str, Any]:
    """Reject a file (admin action).
    
    Args:
        file_id: File ID (UUID)
        reason: Rejection reason
        admin_id: Admin user ID (optional)
    """
    return await tools.reject_file(file_id=file_id, reason=reason, admin_id=admin_id)


@mcp.tool()
async def delete_file(file_id: str) -> Dict[str, Any]:
    """Delete a file.
    
    Args:
        file_id: File ID (UUID)
    """
    return await tools.delete_file(file_id=file_id)


@mcp.tool()
async def get_files_by_status(
    validation_status: str,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """Get files by validation status.
    
    Args:
        validation_status: Status (pending, approved, rejected)
        limit: Number of results (default: 10)
        offset: Number to skip (default: 0)
    """
    return await tools.get_files_by_status(
        validation_status=validation_status,
        limit=limit,
        offset=offset
    )


# =============================================================================
# User Management Tools
# =============================================================================

@mcp.tool()
async def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "customer"
) -> Dict[str, Any]:
    """Create a new user.
    
    Args:
        email: User email address
        password: User password
        first_name: First name
        last_name: Last name
        role: User role (customer, admin, support)
    """
    return await tools.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role
    )


@mcp.tool()
async def create_admin(
    email: str,
    password: str,
    first_name: str,
    last_name: str
) -> Dict[str, Any]:
    """Create a new admin user.
    
    Args:
        email: Admin email address
        password: Admin password
        first_name: First name
        last_name: Last name
    """
    return await tools.create_admin(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )


@mcp.tool()
async def get_user(user_id: str) -> Dict[str, Any]:
    """Get user by ID.
    
    Args:
        user_id: User ID (UUID)
    """
    return await tools.get_user(user_id=user_id)


@mcp.tool()
async def get_user_by_email(email: str) -> Dict[str, Any]:
    """Find user by email address.
    
    Args:
        email: User email address
    """
    return await tools.get_user_by_email(email=email)


@mcp.tool()
async def list_users(
    role: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """List users with optional role filter.
    
    Args:
        role: Filter by role (customer, admin, support)
        limit: Number of results (default: 10)
        offset: Number to skip (default: 0)
    """
    return await tools.list_users(role=role, limit=limit, offset=offset)


@mcp.tool()
async def update_user(
    user_id: str,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_email_verified: Optional[bool] = None
) -> Dict[str, Any]:
    """Update user details.
    
    Args:
        user_id: User ID (UUID)
        email: New email (optional)
        first_name: New first name (optional)
        last_name: New last name (optional)
        role: New role (optional)
        is_active: Active status (optional)
        is_email_verified: Email verified status (optional)
    """
    return await tools.update_user(
        user_id=user_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=is_active,
        is_email_verified=is_email_verified
    )


@mcp.tool()
async def delete_user(user_id: str) -> Dict[str, Any]:
    """Delete a user.
    
    Args:
        user_id: User ID (UUID)
    """
    return await tools.delete_user(user_id=user_id)


@mcp.tool()
async def activate_user(user_id: str) -> Dict[str, Any]:
    """Activate a user account.
    
    Args:
        user_id: User ID (UUID)
    """
    return await tools.activate_user(user_id=user_id)


@mcp.tool()
async def deactivate_user(user_id: str) -> Dict[str, Any]:
    """Deactivate a user account.
    
    Args:
        user_id: User ID (UUID)
    """
    return await tools.deactivate_user(user_id=user_id)


@mcp.tool()
async def verify_user_email(user_id: str) -> Dict[str, Any]:
    """Mark user email as verified.
    
    Args:
        user_id: User ID (UUID)
    """
    return await tools.verify_user_email(user_id=user_id)


# =============================================================================
# Development Tools
# =============================================================================

@mcp.tool()
async def seed_realistic_data(
    scenario: str = "basic",
    count: int = 5
) -> Dict[str, Any]:
    """Populate database with realistic test data (customers and claims).
    
    Args:
        scenario: Type of scenario (basic, complex, mixed)
        count: Number of test entities to create
    """
    return await tools.seed_realistic_data(scenario=scenario, count=count)


@mcp.tool()
async def create_test_scenario(
    email: str = "test@example.com",
    scenario_type: str = "delayed_flight"
) -> Dict[str, Any]:
    """Create a complete test scenario (customer + claim).
    
    Args:
        email: Customer email
        scenario_type: Type (delayed_flight, cancelled_flight, denied_boarding)
    """
    return await tools.create_test_scenario(email=email, scenario_type=scenario_type)


@mcp.tool()
async def reset_database() -> Dict[str, Any]:
    """WARNING: Delete all test data from database.
    
    This operation requires ENABLE_DESTRUCTIVE_OPS=true.
    """
    return await tools.reset_database()


@mcp.tool()
async def validate_data_integrity() -> Dict[str, Any]:
    """Check for data integrity issues (orphaned records, etc)."""
    return await tools.validate_data_integrity()


# =============================================================================
# HTTP Health Check Endpoint (for Docker)
# =============================================================================

async def health_endpoint(request):
    """HTTP health check endpoint for Docker/load balancers."""
    try:
        result = await tools.health_check()
        status_code = 200 if result.get("success") else 503
        return JSONResponse(result, status_code=status_code)
    except Exception as e:
        return JSONResponse(
            {"success": False, "status": "unhealthy", "error": str(e)},
            status_code=503
        )


async def root_endpoint(request):
    """Root endpoint with server info."""
    return JSONResponse({
        "name": "easyairclaim-dev",
        "version": "2.0.0",
        "protocol": "MCP (Model Context Protocol)",
        "sdk": "FastMCP",
        "mcp_endpoint": "/mcp",
        "health_endpoint": "/health",
        "environment": MCPConfig.ENVIRONMENT,
        "message": "EasyAirClaim MCP Server running with official MCP SDK"
    })


# =============================================================================
# Combined Starlette Application
# =============================================================================

@contextlib.asynccontextmanager
async def app_lifespan(app: Starlette):
    """Combined lifespan for Starlette app with MCP session manager."""
    async with mcp.session_manager.run():
        # Initialize database
        logger.warning("=" * 60)
        logger.warning("  EasyAirClaim MCP Server - DEVELOPMENT MODE ONLY")
        logger.warning("  Full database access - NO authentication!")
        logger.warning("=" * 60)
        
        try:
            await init_database()
            logger.info("Database connection established")
            yield
        finally:
            await close_database()
            logger.info("Database connection closed")


# Create combined app with health endpoint and MCP
app = Starlette(
    routes=[
        Route("/", root_endpoint),
        Route("/health", health_endpoint),
        Mount("/mcp", app=mcp.streamable_http_app()),
    ],
    lifespan=app_lifespan,
)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server:app",
        host=MCPConfig.MCP_HOST,
        port=MCPConfig.MCP_PORT,
        reload=True,
        log_level=MCPConfig.LOG_LEVEL.lower()
    )
