"""Custom exceptions for the flight claim system."""


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