"""Main FastAPI application for the flight claim system."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.database import init_db
from app.routers import customers_router, claims_router, health_router
from app.middleware import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting up flight claim system...")
    
    # Initialize database tables
    try:
        await init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        # Continue even if database init fails, might be in development
        pass
    
    yield
    
    # Shutdown
    print("Shutting down flight claim system...")


# Create FastAPI app
app = FastAPI(
    title="Flight Claim System API",
    description="API for managing flight compensation claims",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup exception handlers
setup_exception_handlers(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(customers_router)
app.include_router(claims_router)
app.include_router(health_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Flight Claim System API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/info")
async def info():
    """API information endpoint."""
    return {
        "name": "Flight Claim System API",
        "version": __version__,
        "description": "API for managing flight compensation claims",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": [
            "Customer management",
            "Claim submission and tracking",
            "Flight incident reporting",
            "Compensation calculation"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )