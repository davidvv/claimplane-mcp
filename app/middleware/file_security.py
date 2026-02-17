"""Security middleware for file operations."""
import time
import hashlib
import ipaddress
from app.utils.request_utils import get_real_ip, get_client_info
from typing import Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
import redis
import json
import os

logger = structlog.get_logger(__name__)


class FileSecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for file operations."""
    
    def __init__(self, app: ASGIApp, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limit_window = 60  # 1 minute
        self.max_requests_per_window = 60
        self.max_file_uploads_per_hour = 50
        self.max_downloads_per_hour = 100
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with security checks."""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # Skip security checks for health and info endpoints
            if request.url.path in ["/health", "/info", "/"]:
                return await call_next(request)
            
            # Rate limiting
            if await self._is_rate_limited(client_ip, request):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": "Too many requests. Please try again later.",
                        "retry_after": self.rate_limit_window
                    }
                )
            
            # Content type validation for file uploads
            if self._is_file_upload_request(request):
                is_valid = await self._validate_upload_request(request)
                if not is_valid:
                    await self._log_security_event(
                        request, 
                        {"status_code": 400, "error": "Invalid upload request"},
                        time.time() - start_time
                    )
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid upload request"}
                    )
                
                # Check upload limits
                if await self._is_upload_limited(client_ip):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Upload limit exceeded",
                            "detail": "Too many file uploads. Please try again later."
                        }
                    )
            
            # Download limits
            if self._is_file_download_request(request):
                if await self._is_download_limited(client_ip):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Download limit exceeded",
                            "detail": "Too many file downloads. Please try again later."
                        }
                    )
            
            # Suspicious activity detection
            if await self._is_suspicious_activity(client_ip):
                logger.warning(
                    "Suspicious activity detected",
                    client_ip=client_ip,
                    path=request.url.path,
                    method=request.method
                )
                await self._log_security_event(
                    request,
                    {"status_code": 403, "error": "Suspicious activity detected"},
                    time.time() - start_time
                )
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied due to suspicious activity"}
                )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Log security events
            await self._log_security_event(request, response, time.time() - start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"File security middleware error: {e}", exc_info=True)
            await self._log_security_event(
                request,
                {"status_code": 500, "error": "Internal server error"},
                time.time() - start_time
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy and Cloudflare support."""
        return get_real_ip(request)
    
    def _is_file_upload_request(self, request: Request) -> bool:
        """Check if request is a file upload."""
        return (request.method == "POST" and 
                request.url.path.endswith("/upload") and
                "files" in request.url.path)
    
    def _is_file_download_request(self, request: Request) -> bool:
        """Check if request is a file download."""
        return (request.method == "GET" and 
                request.url.path.endswith("/download") and
                "files" in request.url.path)
    
    async def _is_rate_limited(self, client_ip: str, request: Request) -> bool:
        """Check if request is rate limited."""
        # Different limits for different endpoints
        if self._is_file_upload_request(request):
            max_requests = 5  # Stricter for uploads
        elif self._is_file_download_request(request):
            max_requests = 20  # More lenient for downloads
        else:
            max_requests = self.max_requests_per_window
        
        key = f"rate_limit:{client_ip}:{int(time.time() / self.rate_limit_window)}"
        
        try:
            current_count = self.redis.incr(key)
            if current_count == 1:
                self.redis.expire(key, self.rate_limit_window)
            
            return current_count > max_requests
        except redis.RedisError:
            logger.error("Redis connection error for rate limiting")
            return False  # Fail open
    
    async def _is_upload_limited(self, client_ip: str) -> bool:
        """Check if uploads are limited for this IP."""
        key = f"upload_limit:{client_ip}:{int(time.time() / 3600)}"  # Hourly limit
        
        try:
            current_count = self.redis.incr(key)
            if current_count == 1:
                self.redis.expire(key, 3600)
            
            return current_count > self.max_file_uploads_per_hour
        except redis.RedisError:
            logger.error("Redis connection error for upload limiting")
            return False
    
    async def _is_download_limited(self, client_ip: str) -> bool:
        """Check if downloads are limited for this IP."""
        key = f"download_limit:{client_ip}:{int(time.time() / 3600)}"  # Hourly limit
        
        try:
            current_count = self.redis.incr(key)
            if current_count == 1:
                self.redis.expire(key, 3600)
            
            return current_count > self.max_downloads_per_hour
        except redis.RedisError:
            logger.error("Redis connection error for download limiting")
            return False
    
    async def _validate_upload_request(self, request: Request) -> bool:
        """Validate file upload request."""
        content_type = request.headers.get("content-type", "")
        
        # Check for multipart form data
        if not content_type.startswith("multipart/form-data"):
            return False
        
        # Check content length
        content_length = request.headers.get("content-length", "0")
        try:
            length = int(content_length)
            max_size = int(os.getenv('MAX_FILE_SIZE', '52428800'))  # 50MB
            if length > max_size:
                return False
        except ValueError:
            return False
        
        # Validate file extension in filename (if provided)
        content_disposition = request.headers.get("content-disposition", "")
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip('"')
            if not self._is_safe_filename(filename):
                return False
        
        return True
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe with comprehensive extension validation.
        
        SECURITY: Checks for double extensions and dangerous file types
        to prevent bypass attacks like 'malicious.pdf.exe'
        """
        if not filename or len(filename) > 255:
            return False
        
        # Check for path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            return False
        
        # Check for suspicious characters
        suspicious_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
        if any(char in filename for char in suspicious_chars):
            return False
        
        # SECURITY: Check for dangerous extensions anywhere in filename
        # Prevents double extension attacks like 'malicious.pdf.exe'
        dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.sh', '.php', '.jsp', '.asp', '.aspx',
            '.dll', '.scr', '.jar', '.py', '.rb', '.pl', '.cgi'
        }
        filename_lower = filename.lower()
        for dangerous in dangerous_extensions:
            if dangerous in filename_lower:
                logger.warning(f"Dangerous extension detected in filename: {filename}")
                return False
        
        # Check file extension (last extension only)
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt', '.csv'}
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            logger.warning(f"Disallowed file extension: {ext}")
            return False
        
        return True
    
    async def _is_suspicious_activity(self, client_ip: str) -> bool:
        """Detect suspicious activity patterns."""
        try:
            # Check for too many failed requests
            failed_key = f"failed_requests:{client_ip}:{int(time.time() / 300)}"  # 5-minute window
            failed_count = self.redis.get(failed_key)
            if failed_count and int(failed_count) > 10:
                return True
            
            # Check for requests from suspicious IP ranges
            try:
                ip_obj = ipaddress.ip_address(client_ip)
                # Block private IP ranges if not in development
                if ip_obj.is_private and os.getenv("ENVIRONMENT") != "development":
                    return True
            except ValueError:
                return True  # Invalid IP format is suspicious
            
            # Check for geographic anomalies (if geoip is available)
            # This would require additional setup
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking suspicious activity: {e}")
            return False
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # File-specific headers
        response.headers["X-Download-Options"] = "noopen"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        return response
    
    async def _log_security_event(self, request: Request, response: Response, response_time: float):
        """Log security events for monitoring."""
        event = {
            'timestamp': time.time(),
            'method': request.method,
            'path': request.url.path,
            'status_code': getattr(response, 'status_code', 500),
            'response_time': response_time,
            'client_ip': self._get_client_ip(request),
            'user_agent': request.headers.get('user-agent', ''),
            'content_type': request.headers.get('content-type', ''),
            'content_length': request.headers.get('content-length', '0')
        }
        
        # Store in Redis for real-time monitoring
        try:
            key = f"security_events:{int(time.time() / 60)}"
            self.redis.lpush(key, json.dumps(event))
            self.redis.expire(key, 3600)  # Keep for 1 hour
            
            # Also log to structlog
            logger.info("Security event logged", **event)
            
        except redis.RedisError:
            # Fallback to file logging if Redis is unavailable
            logger.info("Security event (Redis unavailable)", **event)


class FileContentSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for file content security checks."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', '52428800'))  # 50MB
        self.allowed_mime_types = {
            'application/pdf',
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/gif',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/csv'
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Check file content security."""
        if not self._is_file_upload_request(request):
            return await call_next(request)
        
        # Validate content length
        content_length = request.headers.get("content-length", "0")
        try:
            length = int(content_length)
            if length > self.max_file_size:
                return JSONResponse(
                    status_code=413,
                    content={"error": "File too large"}
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid content length"}
            )
        
        return await call_next(request)
    
    def _is_file_upload_request(self, request: Request) -> bool:
        """Check if request is a file upload."""
        return (request.method == "POST" and 
                request.url.path.endswith("/upload") and
                "files" in request.url.path)