"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import redis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base
from app.routers import health, customers, claims, files, admin_claims, admin_files, admin_deletion_requests, eligibility, auth, flights, account, claim_groups, admin_claim_groups
from app.exceptions import setup_exception_handlers
from app.config import get_config
from app.dependencies.rate_limit import limiter
# Import middleware classes - use direct import to avoid file/directory conflict
from app.middleware.file_security import FileSecurityMiddleware, FileContentSecurityMiddleware

# Get configuration
config = get_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Redis client for middleware
redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ClaimPlane API...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created successfully")

    # Load airport taxi times for accurate EU261 delay calculations
    from app.services.airport_taxi_time_service import AirportTaxiTimeService
    try:
        AirportTaxiTimeService.load_taxi_times(config.AIRPORT_TAXI_TIMES_CSV_PATH)
        airport_count = AirportTaxiTimeService.get_airport_count()
        logger.info(f"Airport taxi times loaded successfully ({airport_count} airports)")
    except Exception as e:
        logger.warning(
            f"Failed to load airport taxi times: {e}. "
            f"Will use default {config.FLIGHT_TAXI_TIME_DEFAULT_MINUTES} min fallback."
        )

    yield

    # Shutdown
    logger.info("Shutting down ClaimPlane API...")


# Create FastAPI app
app = FastAPI(
    title="ClaimPlane API",
    description="API for managing flight compensation claims with file management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    redirect_slashes=False  # Disable automatic slash redirects to avoid CORS issues
)

# Add rate limiting state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup CORS - Use config to prevent wildcard with credentials vulnerability
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,  # No longer uses wildcard ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.ALLOWED_HOSTS
)

# Setup exception handlers
setup_exception_handlers(app)

# Add file security middleware
app.add_middleware(FileSecurityMiddleware, redis_client=redis_client)
app.add_middleware(FileContentSecurityMiddleware)

# Add security headers middleware including CSP
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses including CSP for XSS protection."""
    response = await call_next(request)
    
    # Content Security Policy - prevents XSS by restricting script sources
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' https://eac.dvvcloud.work; "
        "frame-ancestors 'none'; "
        "upgrade-insecure-requests;"
    )
    
    # Additional security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), interest-cohort=()"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    
    # Strict-Transport-Security (HSTS) - only in production and if using HTTPS
    if config.SECURITY_HEADERS_ENABLED:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    return response


# Include routers
app.include_router(health.router)
app.include_router(auth.router)  # Phase 3: Authentication
app.include_router(account.router)  # Phase 4: Account Management
app.include_router(flights.router)  # Mock flight lookup
app.include_router(eligibility.router)

app.include_router(customers.router)
app.include_router(claims.router)
app.include_router(files.router)

# Admin routers (Phase 1)
app.include_router(admin_claims.router)
app.include_router(admin_files.router)
app.include_router(admin_deletion_requests.router)  # Phase 4: Deletion Request Management
app.include_router(admin_claim_groups.router)  # Phase 5: Multi-Passenger Claim Groups

# Phase 5: Multi-Passenger Claims
app.include_router(claim_groups.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ClaimPlane API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/info")
async def info():
    """API information endpoint."""
    return {
        "name": "ClaimPlane API",
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
            "Public eligibility check endpoint (no auth required)",
            "JWT-based authentication (Phase 3)",
            "User registration and login",
            "Password reset flow",
            "Role-based access control (RBAC)",
            "Email verification support"
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