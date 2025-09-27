"""Health check endpoint."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app import __version__
from app.database import get_db, engine
from app.schemas import HealthResponseSchema

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponseSchema)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponseSchema:
    """
    Health check endpoint to verify API and database connectivity.
    
    Args:
        db: Database session
        
    Returns:
        Health status information
        
    Raises:
        HTTPException: If database connection fails
    """
    try:
        # Test database connectivity
        await db.execute(text("SELECT 1"))
        
        return HealthResponseSchema(
            status="healthy",
            timestamp=datetime.utcnow(),
            version=__version__
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )


@router.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Detailed database health check.
    
    Args:
        db: Database session
        
    Returns:
        Database health status
        
    Raises:
        HTTPException: If database connection fails
    """
    try:
        # Test database connectivity with more detailed check
        result = await db.execute(text("SELECT version(), current_database(), current_user"))
        db_info = result.fetchone()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "version": db_info[0],
                "name": db_info[1],
                "user": db_info[2]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Detailed health check including system information.
    
    Args:
        db: Database session
        
    Returns:
        Detailed health status
    """
    import sys
    import os
    
    try:
        # Basic database check
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": __version__,
        "system": {
            "python_version": sys.version,
            "platform": sys.platform,
            "environment": os.getenv("ENVIRONMENT", "unknown")
        },
        "database": {
            "status": db_status,
            "url": "postgresql+asyncpg://***:***@db:5432/flight_claim"  # Masked for security
        }
    }