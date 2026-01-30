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


class NextcloudError(FlightClaimException):
    """Base class for Nextcloud errors with enhanced error information."""

    def __init__(self, message: str, error_code: str, status_code: int = 400,
                 original_error: Exception = None, context: str = None,
                 suggestion: str = None, retryable: bool = False, details: dict = None):
        self.error_code = error_code
        self.original_error = original_error
        self.context = context
        self.suggestion = suggestion
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message, status_code=status_code)

    def to_dict(self) -> dict:
        """Convert error to structured response format."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "suggestion": self.suggestion,
            "retryable": self.retryable,
            "context": self.context,
            "details": self.details
        }


class NextcloudRetryableError(NextcloudError):
    """Exception raised for Nextcloud errors that should trigger retries."""

    def __init__(self, message: str, error_code: str = "NC_RETRYABLE_ERROR",
                 original_error: Exception = None, retry_after: int = None,
                 context: str = None, suggestion: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            original_error=original_error,
            context=context,
            suggestion=suggestion,
            retryable=True,
            details=details or {}
        )
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class NextcloudPermanentError(NextcloudError):
    """Exception raised for Nextcloud errors that should not be retried."""

    def __init__(self, message: str, error_code: str = "NC_PERMANENT_ERROR",
                 status_code: int = 400, original_error: Exception = None,
                 context: str = None, suggestion: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            original_error=original_error,
            context=context,
            suggestion=suggestion,
            retryable=False,
            details=details or {}
        )


# Network Error Classes
class NextcloudNetworkError(NextcloudRetryableError):
    """Network-related errors (timeouts, connection failures, DNS errors)."""

    def __init__(self, message: str, original_error: Exception = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="NC_NETWORK_ERROR",
            original_error=original_error,
            context=context,
            suggestion="Check your internet connection and Nextcloud server availability",
            details=details or {}
        )


class NextcloudTimeoutError(NextcloudNetworkError):
    """Timeout errors for Nextcloud operations."""

    def __init__(self, message: str, timeout_seconds: int = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            context=context,
            details=details or {}
        )
        self.error_code = "NC_TIMEOUT_ERROR"
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds
        self.suggestion = f"Operation timed out after {timeout_seconds or 'unknown'} seconds. Try again or contact support if the issue persists"


class NextcloudConnectionError(NextcloudNetworkError):
    """Connection-related errors."""

    def __init__(self, message: str, original_error: Exception = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="NC_CONNECTION_ERROR",
            original_error=original_error,
            context=context,
            suggestion="Unable to connect to Nextcloud server. Check server status and network connectivity",
            details=details or {}
        )


# Authentication Error Classes
class NextcloudAuthenticationError(NextcloudPermanentError):
    """Authentication errors (invalid credentials, expired tokens)."""

    def __init__(self, message: str, original_error: Exception = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="NC_AUTH_ERROR",
            status_code=401,
            original_error=original_error,
            context=context,
            suggestion="Check your Nextcloud credentials and ensure they have not expired",
            details=details or {}
        )


class NextcloudAuthorizationError(NextcloudPermanentError):
    """Authorization errors (insufficient permissions)."""

    def __init__(self, message: str, required_permission: str = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="NC_AUTHORIZATION_ERROR",
            status_code=403,
            context=context,
            suggestion="You don't have permission to perform this operation. Contact your administrator",
            details=details or {}
        )
        if required_permission:
            self.details["required_permission"] = required_permission


# Storage Error Classes
class NextcloudStorageError(NextcloudPermanentError):
    """Storage-related errors (insufficient space, quota exceeded)."""

    def __init__(self, message: str, storage_info: dict = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="NC_STORAGE_ERROR",
            status_code=507,
            context=context,
            suggestion="Free up space or contact your administrator to increase storage quota",
            details=details or {}
        )
        if storage_info:
            self.details.update(storage_info)


class NextcloudQuotaExceededError(NextcloudStorageError):
    """Quota exceeded errors."""

    def __init__(self, message: str, quota_used: str = None, quota_limit: str = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            context=context,
            details=details or {}
        )
        self.error_code = "NC_QUOTA_EXCEEDED"
        if quota_used and quota_limit:
            self.details.update({
                "quota_used": quota_used,
                "quota_limit": quota_limit,
                "usage_percentage": round((float(quota_used) / float(quota_limit)) * 100, 2)
            })
        self.suggestion = "Storage quota exceeded. Delete some files or request a quota increase"


# File Operation Error Classes
class NextcloudFileNotFoundError(NextcloudPermanentError):
    """File not found errors."""

    def __init__(self, message: str, file_path: str = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="NC_FILE_NOT_FOUND",
            status_code=404,
            context=context,
            suggestion="Verify the file path and ensure the file exists",
            details=details or {}
        )
        if file_path:
            self.details["file_path"] = file_path


class NextcloudFileAlreadyExistsError(NextcloudPermanentError):
    """File already exists errors."""

    def __init__(self, message: str, file_path: str = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="NC_FILE_ALREADY_EXISTS",
            status_code=409,
            context=context,
            suggestion="File already exists. Use overwrite option or choose a different filename",
            details=details or {}
        )
        if file_path:
            self.details["file_path"] = file_path


class NextcloudFileOperationError(NextcloudPermanentError):
    """General file operation errors."""

    def __init__(self, message: str, operation: str = None, file_path: str = None,
                 original_error: Exception = None, context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="NC_FILE_OPERATION_ERROR",
            status_code=400,
            original_error=original_error,
            context=context,
            suggestion=f"File {operation or 'operation'} failed. Check file permissions and path",
            details=details or {}
        )
        if operation:
            self.details["operation"] = operation
        if file_path:
            self.details["file_path"] = file_path


# Server Error Classes
class NextcloudServerError(NextcloudRetryableError):
    """Server errors (5xx range)."""

    def __init__(self, message: str, status_code: int = 500,
                 original_error: Exception = None, context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code=f"NC_SERVER_ERROR_{status_code}",
            original_error=original_error,
            context=context,
            suggestion="Nextcloud server is experiencing issues. Please try again later",
            details=details or {}
        )
        self.status_code = status_code
        self.details["server_status_code"] = status_code


class NextcloudServiceUnavailableError(NextcloudServerError):
    """Service unavailable errors."""

    def __init__(self, message: str, retry_after: int = None,
                 original_error: Exception = None, context: str = None, details: dict = None):
        super().__init__(
            message=message,
            status_code=503,
            original_error=original_error,
            context=context,
            details=details or {}
        )
        self.error_code = "NC_SERVICE_UNAVAILABLE"
        if retry_after:
            self.retry_after = retry_after
            self.details["retry_after"] = retry_after
        self.suggestion = "Nextcloud service is temporarily unavailable. Please try again later"


# Client Error Classes
class NextcloudClientError(NextcloudPermanentError):
    """Client errors (4xx range, excluding auth)."""

    def __init__(self, message: str, status_code: int = 400,
                 original_error: Exception = None, context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code=f"NC_CLIENT_ERROR_{status_code}",
            status_code=status_code,
            original_error=original_error,
            context=context,
            suggestion="Check your request parameters and try again",
            details=details or {}
        )
        self.details["client_status_code"] = status_code


class NextcloudInvalidRequestError(NextcloudClientError):
    """Invalid request errors."""

    def __init__(self, message: str, invalid_fields: list = None,
                 original_error: Exception = None, context: str = None, details: dict = None):
        super().__init__(
            message=message,
            status_code=400,
            original_error=original_error,
            context=context,
            details=details or {}
        )
        self.error_code = "NC_INVALID_REQUEST"
        if invalid_fields:
            self.details["invalid_fields"] = invalid_fields
        self.suggestion = "Check your request data and ensure all required fields are provided correctly"


# ============================================================================
# PHASE 6: AeroDataBox API Error Classes
# ============================================================================


class AeroDataBoxError(FlightClaimException):
    """Base class for AeroDataBox API errors with enhanced error information."""

    def __init__(self, message: str, error_code: str, status_code: int = 400,
                 original_error: Exception = None, context: str = None,
                 suggestion: str = None, retryable: bool = False, details: dict = None):
        self.error_code = error_code
        self.original_error = original_error
        self.context = context
        self.suggestion = suggestion
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message, status_code=status_code)

    def to_dict(self) -> dict:
        """Convert error to structured response format."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "suggestion": self.suggestion,
            "retryable": self.retryable,
            "context": self.context,
            "details": self.details
        }


class AeroDataBoxRetryableError(AeroDataBoxError):
    """Exception raised for AeroDataBox errors that should trigger retries."""

    def __init__(self, message: str, error_code: str = "AERO_RETRYABLE_ERROR",
                 original_error: Exception = None, retry_after: int = None,
                 context: str = None, suggestion: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            original_error=original_error,
            context=context,
            suggestion=suggestion,
            retryable=True,
            details=details or {}
        )
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class AeroDataBoxPermanentError(AeroDataBoxError):
    """Exception raised for AeroDataBox errors that should not be retried."""

    def __init__(self, message: str, error_code: str = "AERO_PERMANENT_ERROR",
                 status_code: int = 400, original_error: Exception = None,
                 context: str = None, suggestion: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            original_error=original_error,
            context=context,
            suggestion=suggestion,
            retryable=False,
            details=details or {}
        )


# Network Error Classes
class AeroDataBoxNetworkError(AeroDataBoxRetryableError):
    """Network-related errors (timeouts, connection failures, DNS errors)."""

    def __init__(self, message: str, original_error: Exception = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="AERO_NETWORK_ERROR",
            original_error=original_error,
            context=context,
            suggestion="Check your internet connection and AeroDataBox API availability",
            details=details or {}
        )


class AeroDataBoxTimeoutError(AeroDataBoxNetworkError):
    """Timeout errors for AeroDataBox operations."""

    def __init__(self, message: str, timeout_seconds: int = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            context=context,
            details=details or {}
        )
        self.error_code = "AERO_TIMEOUT_ERROR"
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds
        self.suggestion = f"Operation timed out after {timeout_seconds or 'unknown'} seconds. Try again or contact support if the issue persists"


# Authentication Error Classes
class AeroDataBoxAuthenticationError(AeroDataBoxPermanentError):
    """Authentication errors (invalid API key, expired tokens)."""

    def __init__(self, message: str, original_error: Exception = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="AERO_AUTH_ERROR",
            status_code=401,
            original_error=original_error,
            context=context,
            suggestion="Check your AeroDataBox API key and ensure it has not expired",
            details=details or {}
        )


# Flight Data Error Classes
class AeroDataBoxFlightNotFoundError(AeroDataBoxPermanentError):
    """Flight not found errors."""

    def __init__(self, message: str, flight_number: str = None, flight_date: str = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="AERO_FLIGHT_NOT_FOUND",
            status_code=404,
            context=context,
            suggestion="Verify the flight number and date. The flight may not be in the AeroDataBox database",
            details=details or {}
        )
        if flight_number:
            self.details["flight_number"] = flight_number
        if flight_date:
            self.details["flight_date"] = flight_date


# Quota Error Classes
class AeroDataBoxQuotaExceededError(AeroDataBoxPermanentError):
    """Quota exceeded errors."""

    def __init__(self, message: str, quota_used: int = None, quota_limit: int = None,
                 context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="AERO_QUOTA_EXCEEDED",
            status_code=429,
            context=context,
            suggestion="API quota exceeded. Upgrade to Pro tier or wait for quota reset",
            details=details or {}
        )
        if quota_used and quota_limit:
            self.details.update({
                "quota_used": quota_used,
                "quota_limit": quota_limit,
                "usage_percentage": round((quota_used / quota_limit) * 100, 2)
            })


class AeroDataBoxRateLimitError(AeroDataBoxRetryableError):
    """Rate limit errors (429 with Retry-After header)."""

    def __init__(self, message: str, retry_after: int = None,
                 original_error: Exception = None, context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code="AERO_RATE_LIMIT",
            original_error=original_error,
            retry_after=retry_after,
            context=context,
            suggestion="API rate limit reached. Request will be retried automatically",
            details=details or {}
        )


# Server Error Classes
class AeroDataBoxServerError(AeroDataBoxRetryableError):
    """Server errors (5xx range)."""

    def __init__(self, message: str, status_code: int = 500,
                 original_error: Exception = None, context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code=f"AERO_SERVER_ERROR_{status_code}",
            original_error=original_error,
            context=context,
            suggestion="AeroDataBox API is experiencing issues. Request will be retried automatically",
            details=details or {}
        )
        self.status_code = status_code
        self.details["server_status_code"] = status_code


# Client Error Classes
class AeroDataBoxClientError(AeroDataBoxPermanentError):
    """Client errors (4xx range, excluding auth and rate limit)."""

    def __init__(self, message: str, status_code: int = 400,
                 original_error: Exception = None, context: str = None, details: dict = None):
        super().__init__(
            message=message,
            error_code=f"AERO_CLIENT_ERROR_{status_code}",
            status_code=status_code,
            original_error=original_error,
            context=context,
            suggestion="Check your request parameters and try again",
            details=details or {}
        )
        self.details["client_status_code"] = status_code


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers for the FastAPI app."""
    
    @app.exception_handler(FlightClaimException)
    async def flight_claim_exception_handler(request, exc: FlightClaimException):
        """Handle custom FlightClaimException."""
        # Handle Nextcloud errors with enhanced structure
        if isinstance(exc, NextcloudError):
            error_content = {
                "success": False,
                "error": exc.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Handle other FlightClaimException types
            error_content = {
                "success": False,
                "error": {
                    "code": exc.__class__.__name__.upper(),
                    "message": exc.message,
                    "details": getattr(exc, 'details', [])
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        return JSONResponse(
            status_code=exc.status_code,
            content=error_content
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
        """Handle unexpected exceptions - Fix WP-309: Sanitize error output."""
        import logging
        logger = logging.getLogger("app.main")
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later or contact support.",
                    "details": [] # Hide str(exc) in production
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
