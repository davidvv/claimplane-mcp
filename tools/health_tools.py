"""Health check and system information tools."""
from typing import Dict, Any
from sqlalchemy import select, func, text
from database import get_db_session
from app.models import Customer, Claim, ClaimFile


async def health_check() -> Dict[str, Any]:
    """Check MCP server and database connectivity.
    
    Returns:
        Health status with database connection info
    """
    try:
        async with get_db_session() as session:
            # Test database connection
            result = await session.execute(text("SELECT version()"))
            db_version = result.scalar()
            
            return {
                "success": True,
                "status": "healthy",
                "database": {
                    "connected": True,
                    "version": db_version
                },
                "message": "MCP server is running and database is connected"
            }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "message": "Database connection failed"
        }


async def get_database_stats() -> Dict[str, Any]:
    """Get database statistics (counts of various entities).
    
    Returns:
        Counts of customers, claims, files
    """
    try:
        async with get_db_session() as session:
            # Count customers
            customers_count = await session.scalar(select(func.count(Customer.id)))
            
            # Count claims
            claims_count = await session.scalar(select(func.count(Claim.id)))
            
            # Count files
            files_count = await session.scalar(select(func.count(ClaimFile.id)))
            
            # Count claims by status
            claims_by_status = {}
            result = await session.execute(
                select(Claim.status, func.count(Claim.id))
                .group_by(Claim.status)
            )
            for status, count in result:
                claims_by_status[status] = count
            
            return {
                "success": True,
                "stats": {
                    "customers": customers_count,
                    "claims": claims_count,
                    "files": files_count,
                    "claims_by_status": claims_by_status
                },
                "message": "Database statistics retrieved successfully"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve database statistics"
        }


async def get_environment_info() -> Dict[str, Any]:
    """Get environment and configuration information.
    
    Returns:
        Environment details and configuration
    """
    from config import MCPConfig
    import sys
    
    return {
        "success": True,
        "environment": {
            "mode": MCPConfig.ENVIRONMENT,
            "python_version": sys.version,
            "database_url": MCPConfig.DATABASE_URL.split("@")[-1] if "@" in MCPConfig.DATABASE_URL else "***",
            "mcp_port": MCPConfig.MCP_PORT,
            "dashboard_port": MCPConfig.DASHBOARD_PORT,
            "destructive_ops_enabled": MCPConfig.ENABLE_DESTRUCTIVE_OPS
        },
        "message": "Environment information retrieved successfully"
    }
