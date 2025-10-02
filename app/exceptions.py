"""Custom exceptions for the flight claim system."""
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class FlightClaimException(Exception):
    """Base exception for flight claim system."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(FlightClaimException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier {identifier} not found"
        super().__init__(message, status_code=404)


class ValidationException(FlightClaimException):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, details: list = None):
        self.details = details or []
        super().__init__(message, status_code=400)


class ConflictException(FlightClaimException):
    """Exception raised for resource conflicts."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class DatabaseException(FlightClaimException):
    """Exception raised for database errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class AuthenticationException(FlightClaimException):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationException(FlightClaimException):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, status_code=403)


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers for the FastAPI app."""
    
    @app.exception_handler(FlightClaimException)
    async def flight_claim_exception_handler(request, exc: FlightClaimException):
        """Handle custom FlightClaimException."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.__class__.__name__.upper(),
                    "message": exc.message,
                    "details": getattr(exc, 'details', [])
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        """Handle FastAPI HTTPException."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": []
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """Handle unexpected exceptions."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": [str(exc)]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )