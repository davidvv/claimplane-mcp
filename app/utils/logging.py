"""Logging configuration for the Flight Compensation Claim API."""

import logging
import sys
from typing import Any, Dict

import structlog
from app.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        structlog.BoundLogger: Structured logger
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log API request details.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: User ID if authenticated
        request_id: Request ID for tracing
        **kwargs: Additional context
    """
    logger = get_logger("api")
    
    log_data: Dict[str, Any] = {
        "event": "api_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="api", level=logging.INFO, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        )),
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if request_id:
        log_data["request_id"] = request_id
    
    log_data.update(kwargs)
    
    if status_code >= 400:
        logger.error(**log_data)
    else:
        logger.info(**log_data)


def log_database_query(
    query: str,
    duration_ms: float,
    success: bool = True,
    error: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log database query details.
    
    Args:
        query: SQL query
        duration_ms: Query duration in milliseconds
        success: Whether query succeeded
        error: Error message if failed
        **kwargs: Additional context
    """
    logger = get_logger("database")
    
    log_data: Dict[str, Any] = {
        "event": "database_query",
        "query": query,
        "duration_ms": duration_ms,
        "success": success,
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="database", level=logging.INFO, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        )),
    }
    
    if error:
        log_data["error"] = error
    
    log_data.update(kwargs)
    
    if success:
        logger.debug(**log_data)
    else:
        logger.error(**log_data)


def log_file_operation(
    operation: str,
    filename: str,
    success: bool = True,
    error: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log file operation details.
    
    Args:
        operation: Operation type (upload, download, delete, etc.)
        filename: File name
        success: Whether operation succeeded
        error: Error message if failed
        **kwargs: Additional context
    """
    logger = get_logger("files")
    
    log_data: Dict[str, Any] = {
        "event": "file_operation",
        "operation": operation,
        "filename": filename,
        "success": success,
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="files", level=logging.INFO, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        )),
    }
    
    if error:
        log_data["error"] = error
    
    log_data.update(kwargs)
    
    if success:
        logger.info(**log_data)
    else:
        logger.error(**log_data)


def log_authentication_event(
    event: str,
    email: str,
    success: bool = True,
    error: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log authentication event details.
    
    Args:
        event: Event type (login, logout, token_refresh, etc.)
        email: User email
        success: Whether authentication succeeded
        error: Error message if failed
        **kwargs: Additional context
    """
    logger = get_logger("auth")
    
    log_data: Dict[str, Any] = {
        "event": f"auth_{event}",
        "email": email,
        "success": success,
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="auth", level=logging.INFO, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        )),
    }
    
    if error:
        log_data["error"] = error
    
    log_data.update(kwargs)
    
    if success:
        logger.info(**log_data)
    else:
        logger.warning(**log_data)


def log_claim_event(
    event: str,
    claim_id: str,
    user_id: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log claim-related event details.
    
    Args:
        event: Event type (created, updated, status_changed, etc.)
        claim_id: Claim ID
        user_id: User ID if applicable
        success: Whether operation succeeded
        error: Error message if failed
        **kwargs: Additional context
    """
    logger = get_logger("claims")
    
    log_data: Dict[str, Any] = {
        "event": f"claim_{event}",
        "claim_id": claim_id,
        "success": success,
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="claims", level=logging.INFO, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        )),
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if error:
        log_data["error"] = error
    
    log_data.update(kwargs)
    
    if success:
        logger.info(**log_data)
    else:
        logger.error(**log_data)


def log_security_event(
    event: str,
    severity: str = "medium",
    details: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> None:
    """Log security-related event details.
    
    Args:
        event: Event type (suspicious_request, rate_limit_exceeded, etc.)
        severity: Event severity (low, medium, high, critical)
        details: Additional event details
        **kwargs: Additional context
    """
    logger = get_logger("security")
    
    log_data: Dict[str, Any] = {
        "event": f"security_{event}",
        "severity": severity,
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="security", level=logging.INFO, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        )),
    }
    
    if details:
        log_data["details"] = details
    
    log_data.update(kwargs)
    
    if severity in ["high", "critical"]:
        logger.critical(**log_data)
    elif severity == "medium":
        logger.warning(**log_data)
    else:
        logger.info(**log_data)


# Initialize logging configuration
configure_logging()