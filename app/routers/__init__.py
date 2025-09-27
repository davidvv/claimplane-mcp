"""API routers for the flight claim system."""
from .customers import router as customers_router
from .claims import router as claims_router
from .health import router as health_router

__all__ = ["customers_router", "claims_router", "health_router"]