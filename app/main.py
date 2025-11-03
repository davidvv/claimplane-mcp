"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.database import engine, Base
from app.routers import health, customers, claims, files, admin_claims, admin_files, eligibility, auth, flights
from app.exceptions import setup_exception_handlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Flight Claim System API...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Flight Claim System API...")


# Create FastAPI app
app = FastAPI(
    title="Flight Claim System API",
    description="API for managing flight compensation claims with file management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Setup exception handlers
setup_exception_handlers(app)


# Include routers
app.include_router(health.router)
app.include_router(auth.router)  # Phase 3: Authentication
app.include_router(flights.router)  # Mock flight lookup
app.include_router(eligibility.router)
app.include_router(customers.router)
app.include_router(claims.router)
app.include_router(files.router)

# Admin routers (Phase 1)
app.include_router(admin_claims.router)
app.include_router(admin_files.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Flight Claim System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/info")
async def info():
    """API information endpoint."""
    return {
        "name": "Flight Claim System API",
        "version": "1.0.0",
        "description": "API for managing flight compensation claims with file management",
        "environment": "development",
        "features": [
            "Customer management",
            "Claim submission and tracking",
            "Flight incident reporting",
            "File management with Nextcloud integration",
            "Secure file uploads with encryption",
            "Document validation and scanning",
            "Admin claim management and workflow (Phase 1)",
            "EU261/2004 compensation calculation",
            "Document review and approval system",
            "Bulk operations and analytics",
            "Public eligibility check endpoint (no auth required)"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )