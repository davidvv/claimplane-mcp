"""Error handling middleware and utilities."""
from datetime import datetime
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError

from app.exceptions import FlightClaimException
from app.schemas import ErrorResponseSchema


async def flight_claim_exception_handler(request: Request, exc: FlightClaimException):
    """Handle custom FlightClaim exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.__class__.__name__.upper().replace("EXCEPTION", "_ERROR"),
                "message": exc.message,
                "details": getattr(exc, 'details', [])
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def validation_exception_handler(request: Request, exc: Union[RequestValidationError, ValidationError]):
    """Handle Pydantic validation errors."""
    errors = []
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
    else:
        errors.append({
            "message": str(exc),
            "type": "validation_error"
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors."""
    if isinstance(exc, IntegrityError):
        # Handle unique constraint violations
        if "unique" in str(exc).lower():
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "success": False,
                    "error": {
                        "code": "DUPLICATE_ENTRY",
                        "message": "A record with this information already exists",
                        "details": [str(exc.orig) if hasattr(exc, 'orig') else str(exc)]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Handle foreign key violations
        if "foreign key" in str(exc).lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "FOREIGN_KEY_ERROR",
                        "message": "Referenced record does not exist",
                        "details": [str(exc.orig) if hasattr(exc, 'orig') else str(exc)]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    # Handle other database errors
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database operation failed",
                "details": [str(exc)]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
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


def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI app."""
    app.add_exception_handler(FlightClaimException, flight_claim_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)