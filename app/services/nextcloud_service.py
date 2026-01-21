"""Nextcloud integration service for file storage."""
import asyncio
import base64
import json
import logging
import os
import random
import re
import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException, status

from app.config import config
from app.exceptions import (
    NextcloudError, NextcloudRetryableError, NextcloudPermanentError,
    NextcloudNetworkError, NextcloudTimeoutError, NextcloudConnectionError,
    NextcloudAuthenticationError, NextcloudAuthorizationError,
    NextcloudStorageError, NextcloudQuotaExceededError,
    NextcloudFileNotFoundError, NextcloudFileAlreadyExistsError, NextcloudFileOperationError,
    NextcloudServerError, NextcloudServiceUnavailableError,
    NextcloudClientError, NextcloudInvalidRequestError
)

logger = logging.getLogger(__name__)


class NextcloudService:
    """Service for integrating with Nextcloud WebDAV and OCS APIs."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """Initialize Nextcloud service with configuration."""
        self.base_url = config.NEXTCLOUD_URL
        self.username = config.NEXTCLOUD_USERNAME
        self.password = config.NEXTCLOUD_PASSWORD
        self.timeout = config.NEXTCLOUD_TIMEOUT

        # Retry configuration
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        logger.info(f"Nextcloud service initialized with URL: {self.base_url}, username: {self.username}, timeout: {self.timeout}, max_retries: {max_retries}")

        # WebDAV base URL
        self.webdav_url = urljoin(self.base_url, "/remote.php/dav/files/")

        # OCS API base URL
        self.ocs_url = urljoin(self.base_url, "/ocs/v2.php/")

        # Basic auth credentials
        self.auth = (self.username, self.password)

        # OCS API headers
        self.ocs_headers = {
            "OCS-APIRequest": "true",
            "Content-Type": "application/json"
        }

        # Error classification mappings
        self._error_mappings = self._build_error_mappings()

    def _build_error_mappings(self) -> Dict[str, Dict[int, type]]:
        """Build comprehensive error mappings for different HTTP status codes and error types."""
        return {
            # Network errors (connection, timeout, DNS issues)
            "network": {
                "connection_error": NextcloudConnectionError,
                "timeout": NextcloudTimeoutError,
                "dns_error": NextcloudNetworkError,
                "ssl_error": NextcloudNetworkError,
            },

            # HTTP status code mappings
            "http_status": {
                # Authentication & Authorization (4xx)
                401: NextcloudAuthenticationError,
                403: NextcloudAuthorizationError,

                # File not found
                404: NextcloudFileNotFoundError,

                # File already exists
                409: NextcloudFileAlreadyExistsError,

                # Client errors
                400: NextcloudInvalidRequestError,
                413: NextcloudClientError,  # Payload too large
                415: NextcloudClientError,  # Unsupported media type
                422: NextcloudInvalidRequestError,  # Unprocessable entity

                # Storage errors
                507: NextcloudQuotaExceededError,

                # Server errors (5xx) - all retryable
                500: NextcloudServerError,
                502: NextcloudServerError,
                503: NextcloudServiceUnavailableError,
                504: NextcloudServerError,
            },

            # Nextcloud specific error patterns in response text
            "response_patterns": {
                "quota": re.compile(r".*(quota|storage|space).*", re.IGNORECASE),
                "permission": re.compile(r".*(permission|access|denied|forbidden).*", re.IGNORECASE),
                "not_found": re.compile(r".*(not found|does not exist|missing).*", re.IGNORECASE),
                "already_exists": re.compile(r".*(already exists|duplicate|conflict).*", re.IGNORECASE),
                "invalid_request": re.compile(r".*(invalid|malformed|bad request).*", re.IGNORECASE),
            }
        }

    def _classify_error(self, error: Exception, context: str = None, operation: str = None,
                       http_status: int = None, response_text: str = None) -> NextcloudError:
        """Classify an error into appropriate Nextcloud exception with context-aware information."""

        # Network and connection errors
        if isinstance(error, (httpx.TimeoutException, asyncio.TimeoutError)):
            return NextcloudTimeoutError(
                message=f"Operation timed out: {str(error)}",
                timeout_seconds=self.timeout,
                context=context,
                details={"operation": operation, "timeout": self.timeout}
            )

        if isinstance(error, (httpx.ConnectError, httpx.NetworkError)):
            return NextcloudConnectionError(
                message=f"Connection failed: {str(error)}",
                original_error=error,
                context=context,
                details={"operation": operation}
            )

        if isinstance(error, httpx.HTTPStatusError):
            return self._classify_http_error(error.response, context, operation)

        # SSL/TLS errors
        if isinstance(error, httpx.SSLError):
            return NextcloudNetworkError(
                message=f"SSL/TLS error: {str(error)}",
                original_error=error,
                context=context,
                details={"operation": operation, "error_type": "ssl_error"}
            )

        # DNS resolution errors
        if isinstance(error, httpx.ResolveError):
            return NextcloudNetworkError(
                message=f"DNS resolution failed: {str(error)}",
                original_error=error,
                context=context,
                details={"operation": operation, "error_type": "dns_error"}
            )

        # Default network error for other httpx errors
        if isinstance(error, httpx.RequestError):
            return NextcloudNetworkError(
                message=f"Request error: {str(error)}",
                original_error=error,
                context=context,
                details={"operation": operation}
            )

        # Unknown errors - treat as permanent
        return NextcloudPermanentError(
            message=f"Unexpected error: {str(error)}",
            error_code="NC_UNKNOWN_ERROR",
            original_error=error,
            context=context,
            suggestion="An unexpected error occurred. Please contact support if this persists",
            details={"operation": operation}
        )

    def _classify_http_error(self, response: httpx.Response, context: str = None,
                           operation: str = None) -> NextcloudError:
        """Classify HTTP errors based on status code and response content."""
        status_code = response.status_code
        response_text = response.text or ""

        # Get error class from status code mapping
        error_class = self._error_mappings["http_status"].get(status_code, NextcloudPermanentError)

        # Analyze response text for better error classification
        error_details = self._analyze_response_text(response_text, operation)

        # Create context-aware message
        message = self._create_context_aware_message(status_code, response_text, context, operation)

        # Create error instance with appropriate details
        if error_class == NextcloudQuotaExceededError:
            return error_class(
                message=message,
                context=context,
                details=error_details
            )
        elif error_class in [NextcloudAuthenticationError, NextcloudAuthorizationError]:
            return error_class(
                message=message,
                context=context,
                details=error_details
            )
        elif error_class == NextcloudFileNotFoundError:
            return error_class(
                message=message,
                context=context,
                details=error_details
            )
        elif error_class == NextcloudFileAlreadyExistsError:
            return error_class(
                message=message,
                context=context,
                details=error_details
            )
        elif error_class in [NextcloudServerError, NextcloudServiceUnavailableError]:
            # Server errors are retryable
            retry_after = self._extract_retry_after(response.headers)
            return NextcloudRetryableError(
                message=message,
                error_code=f"NC_SERVER_ERROR_{status_code}",
                original_error=httpx.HTTPStatusError(f"HTTP {status_code}: {response_text}", request=response.request, response=response),
                retry_after=retry_after,
                context=context,
                suggestion="Server is experiencing issues. Please try again later",
                details=error_details
            )
        else:
            # Default error handling
            return error_class(
                message=message,
                status_code=status_code,
                original_error=httpx.HTTPStatusError(f"HTTP {status_code}: {response_text}", request=response.request, response=response),
                context=context,
                details=error_details
            )

    def _analyze_response_text(self, response_text: str, operation: str = None) -> Dict[str, Any]:
        """Analyze response text to extract additional error details."""
        details = {}

        if not response_text:
            return details

        # Check for quota information
        quota_match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB|KB|B)\s*(?:of|\/)\s*(\d+(?:\.\d+)?)\s*(GB|MB|KB|B)',
                              response_text, re.IGNORECASE)
        if quota_match:
            details["quota_info"] = {
                "used": quota_match.group(1),
                "used_unit": quota_match.group(2),
                "limit": quota_match.group(3),
                "limit_unit": quota_match.group(4)
            }

        # Check for file path information
        path_match = re.search(r'(?:file|path)[:\s]*["\']?([^"\']+)["\']?', response_text, re.IGNORECASE)
        if path_match:
            details["file_path"] = path_match.group(1)

        # Check for permission information
        perm_match = re.search(r'(?:permission|access)[:\s]*["\']?([^"\']+)["\']?', response_text, re.IGNORECASE)
        if perm_match:
            details["permission"] = perm_match.group(1)

        details["operation"] = operation
        details["response_text"] = response_text[:500]  # Limit response text length

        return details

    def _create_context_aware_message(self, status_code: int, response_text: str,
                                    context: str = None, operation: str = None) -> str:
        """Create context-aware error messages based on operation type."""
        base_messages = {
            400: "Bad request",
            401: "Authentication required",
            403: "Access forbidden",
            404: "Resource not found",
            409: "Resource conflict",
            413: "File too large",
            415: "Unsupported file type",
            422: "Invalid request data",
            507: "Storage quota exceeded",
            500: "Internal server error",
            502: "Bad gateway",
            503: "Service unavailable",
            504: "Gateway timeout"
        }

        base_message = base_messages.get(status_code, f"HTTP error {status_code}")

        # Add context-specific information
        context_parts = [base_message]

        if operation:
            context_parts.append(f"during {operation}")

        if context:
            context_parts.append(f"({context})")

        message = " ".join(context_parts)

        # Add response-specific details if available
        if response_text and len(response_text) < 200:
            # Clean up the response text for display
            clean_text = re.sub(r'<[^>]+>', '', response_text)  # Remove HTML tags
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Normalize whitespace

            if clean_text and clean_text.lower() not in ['ok', 'success', '']:
                message += f": {clean_text}"

        return message

    def _extract_retry_after(self, headers: httpx.Headers) -> Optional[int]:
        """Extract retry-after value from response headers."""
        retry_after = headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        return None

    def _is_retryable_error(self, error: Exception) -> Tuple[bool, int]:
        """Determine if an error should be retried and get retry-after seconds if available."""
        retry_after = None

        # Network and connection errors - always retryable
        if isinstance(error, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError, httpx.ConnectTimeout)):
            return True, retry_after

        # HTTP status code based classification
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            response = error.response

            # Check for Retry-After header
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                except ValueError:
                    pass

            # Retryable status codes (5xx server errors and rate limiting)
            if status_code >= 500 or status_code == 429:
                return True, retry_after

        # Check if it's already a classified Nextcloud error
        if isinstance(error, NextcloudError):
            return error.retryable, getattr(error, 'retry_after', None)

        # Default: not retryable
        return False, retry_after

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        # Exponential backoff: base_delay * (2 ^ attempt)
        delay = self.base_delay * (2 ** attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter (±25% randomization)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay += jitter

        return max(0.1, delay)  # Minimum 0.1 seconds

    async def _retry_with_backoff(self, operation, *args, **kwargs):
        """Execute operation with exponential backoff retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.max_retries} for Nextcloud operation")

                result = await operation(*args, **kwargs)

                if attempt > 0:
                    logger.info(f"Nextcloud operation succeeded after {attempt} retries")

                return result

            except Exception as e:
                last_exception = e

                # Check if this is the last attempt
                if attempt == self.max_retries:
                    logger.error(f"Nextcloud operation failed after {self.max_retries + 1} attempts: {str(e)}")
                    break

                # Classify error for retry decision
                is_retryable, retry_after = self._is_retryable_error(e)

                if not is_retryable:
                    logger.error(f"Nextcloud operation failed with non-retryable error: {str(e)}")
                    break

                # Determine delay (use Retry-After header if available, otherwise calculate backoff)
                if retry_after:
                    delay = retry_after
                    logger.info(f"Retrying after {delay}s due to Retry-After header")
                else:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.info(f"Retrying after {delay:.2f}s due to exponential backoff")

                await asyncio.sleep(delay)

        # If we get here, all retries failed
        if isinstance(last_exception, NextcloudError):
            # Add retry information to the error details
            last_exception.details["retry_attempts"] = self.max_retries + 1
            last_exception.details["final_attempt"] = True
            raise last_exception
        else:
            # Classify and wrap the original exception
            classified_error = self._classify_error(
                last_exception,
                context="retry_operation",
                operation="unknown"
            )
            classified_error.details.update({
                "retry_attempts": self.max_retries + 1,
                "final_attempt": True,
                "original_error": str(last_exception)
            })
            raise classified_error

    async def upload_file(self, file_content: bytes, remote_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """Upload file to Nextcloud via WebDAV with retry logic."""

        async def _perform_upload() -> Dict[str, Any]:
            """Internal upload operation that can be retried."""
            # Ensure parent directory exists
            logger.info(f"Ensuring directory exists for path: {remote_path}")
            dir_created = await self.ensure_directory_exists(remote_path)
            if not dir_created:
                logger.warning(f"Failed to ensure directory exists for: {remote_path}")

            # Construct full WebDAV URL
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            upload_url = urljoin(self.webdav_url, full_path)

            logger.info(f"Nextcloud config - Base URL: {self.base_url}, WebDAV URL: {self.webdav_url}, Username: {self.username}, Timeout: {self.timeout}")
            logger.info(f"Attempting to upload file to Nextcloud URL: {upload_url}, File size: {len(file_content)} bytes")

            # Set headers
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(file_content))
            }

            # Upload file
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                method = "PUT" if overwrite else "PUT"
                logger.info(f"Making {method} request to {upload_url}")
                response = await client.request(
                    method=method,
                    url=upload_url,
                    content=file_content,
                    headers=headers,
                    auth=self.auth
                )

                logger.info(f"Nextcloud upload response status: {response.status_code}, headers: {dict(response.headers)}")

                # Classify HTTP status codes for proper error handling
                if response.status_code in [200, 201, 204]:
                    return {
                        "success": True,
                        "file_id": remote_path,
                        "url": upload_url,
                        "status_code": response.status_code
                    }
                else:
                    # Use enhanced error classification system
                    classified_error = self._classify_http_error(
                        response,
                        context=f"upload_file:{remote_path}",
                        operation="file_upload"
                    )

                    # Add upload-specific details
                    classified_error.details.update({
                        "file_path": remote_path,
                        "file_size": len(file_content),
                        "upload_url": upload_url,
                        "overwrite": overwrite
                    })

                    raise classified_error

        # Execute upload with retry logic
        return await self._retry_with_backoff(_perform_upload)

    async def upload_file_chunked(self, file_content: bytes, remote_path: str, chunk_size: int = None) -> Dict[str, Any]:
        """Upload large file in chunks for memory efficiency."""
        if chunk_size is None:
            chunk_size = config.CHUNK_SIZE

        # For now, this is a placeholder that uses the regular upload method
        # In a full implementation, this would use Nextcloud's chunked upload API
        # or implement custom chunking logic
        return await self.upload_file(file_content, remote_path)

    async def resume_upload(self, remote_path: str, offset: int) -> Dict[str, Any]:
        """Resume a partial upload from a specific offset."""
        # Placeholder for resume functionality
        # In a full implementation, this would check for partial uploads
        # and resume from the specified offset
        return {
            "success": True,
            "resumed": False,
            "offset": offset,
            "message": "Resume functionality not yet implemented"
        }

    async def cancel_upload(self, remote_path: str) -> bool:
        """Cancel a partial upload and clean up resources."""
        # Placeholder for cancel functionality
        # In a full implementation, this would clean up partial upload data
        return True
    
    async def download_file(self, remote_path: str) -> bytes:
        """Download file from Nextcloud via WebDAV."""
        try:
            # Construct full WebDAV URL
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            download_url = urljoin(self.webdav_url, full_path)
            
            # Download file
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url=download_url,
                    auth=self.auth
                )
                
                if response.status_code == 404:
                    classified_error = NextcloudFileNotFoundError(
                        message=f"File not found: {remote_path}",
                        file_path=remote_path,
                        context="download_file",
                        details={"download_url": download_url}
                    )
                    raise classified_error
                elif response.status_code != 200:
                    classified_error = self._classify_http_error(
                        response,
                        context=f"download_file:{remote_path}",
                        operation="file_download"
                    )
                    classified_error.details.update({
                        "file_path": remote_path,
                        "download_url": download_url
                    })
                    raise classified_error
                
                return response.content
                
        except Exception as e:
            # Use enhanced error classification for all exceptions
            classified_error = self._classify_error(
                e,
                context=f"download_file:{remote_path}",
                operation="file_download"
            )
            classified_error.details.update({
                "file_path": remote_path,
                "download_url": download_url
            })
            raise classified_error

    async def verify_upload_integrity(self, original_content: bytes, remote_path: str,
                                    verification_strategy: str = "auto") -> Dict[str, Any]:
        """Verify uploaded file integrity by downloading and comparing with original content.

        Args:
            original_content: Original file content that was uploaded
            remote_path: Remote path of the uploaded file
            verification_strategy: Strategy to use - "full", "hash", "sampling", "metadata", or "auto"

        Returns:
            Dict containing verification results and metadata
        """
        import hashlib
        import time

        start_time = time.time()
        verification_result = {
            "verified": False,
            "strategy_used": verification_strategy,
            "download_time": 0,
            "comparison_time": 0,
            "total_time": 0,
            "file_size": len(original_content),
            "error": None,
            "details": {}
        }

        try:
            # Check if verification is enabled in config
            if not config.UPLOAD_VERIFICATION_ENABLED:
                verification_result["verified"] = True
                verification_result["strategy_used"] = "disabled"
                verification_result["details"]["reason"] = "Verification disabled in configuration"
                return verification_result

            # Check file size constraints
            file_size = len(original_content)
            if file_size < config.VERIFICATION_MIN_FILE_SIZE:
                verification_result["verified"] = True
                verification_result["strategy_used"] = "skipped"
                verification_result["details"]["reason"] = f"File size {file_size} below minimum threshold {config.VERIFICATION_MIN_FILE_SIZE}"
                return verification_result

            if file_size > config.VERIFICATION_MAX_FILE_SIZE:
                verification_result["verified"] = True
                verification_result["strategy_used"] = "skipped"
                verification_result["details"]["reason"] = f"File size {file_size} above maximum threshold {config.VERIFICATION_MAX_FILE_SIZE}"
                return verification_result

            # Determine verification strategy
            if verification_strategy == "auto":
                if file_size <= 10 * 1024 * 1024:  # 10MB
                    verification_strategy = "full"
                elif file_size <= 100 * 1024 * 1024:  # 100MB
                    verification_strategy = "hash"
                else:
                    verification_strategy = "sampling"

            verification_result["strategy_used"] = verification_strategy

            # Download the uploaded file
            download_start = time.time()
            downloaded_content = await self.download_file(remote_path)
            download_time = time.time() - download_start
            verification_result["download_time"] = download_time

            # Verify based on strategy
            comparison_start = time.time()

            if verification_strategy == "full":
                verification_result["verified"] = self._compare_full_content(original_content, downloaded_content)
                verification_result["details"]["comparison_method"] = "byte_for_byte"

            elif verification_strategy == "hash":
                verification_result["verified"] = self._compare_hashes(original_content, downloaded_content)
                verification_result["details"]["comparison_method"] = "hash_comparison"
                verification_result["details"]["hash_algorithm"] = "sha256"

            elif verification_strategy == "sampling":
                verification_result["verified"] = self._compare_sampling(original_content, downloaded_content)
                verification_result["details"]["comparison_method"] = "random_sampling"
                verification_result["details"]["sample_size"] = min(config.VERIFICATION_SAMPLE_SIZE, file_size)

            elif verification_strategy == "metadata":
                verification_result["verified"] = self._compare_metadata(original_content, downloaded_content)
                verification_result["details"]["comparison_method"] = "metadata_only"

            else:
                raise ValueError(f"Unknown verification strategy: {verification_strategy}")

            comparison_time = time.time() - comparison_start
            verification_result["comparison_time"] = comparison_time

            # Add verification details
            verification_result["details"].update({
                "original_size": len(original_content),
                "downloaded_size": len(downloaded_content),
                "size_match": len(original_content) == len(downloaded_content)
            })

            if not verification_result["verified"]:
                verification_result["error"] = "Content verification failed"
                verification_result["details"]["error_type"] = "content_mismatch"

        except Exception as e:
            verification_result["verified"] = False
            verification_result["error"] = str(e)
            verification_result["details"]["error_type"] = "verification_exception"

            # Classify the error for better handling
            try:
                classified_error = self._classify_error(
                    e,
                    context=f"verify_upload_integrity:{remote_path}",
                    operation="file_verification"
                )
                verification_result["details"]["classified_error"] = {
                    "type": type(classified_error).__name__,
                    "message": str(classified_error),
                    "retryable": getattr(classified_error, 'retryable', False)
                }
            except Exception:
                verification_result["details"]["classified_error"] = {
                    "type": "unknown",
                    "message": str(e),
                    "retryable": False
                }

        finally:
            total_time = time.time() - start_time
            verification_result["total_time"] = total_time

            # Log verification results
            if verification_result["verified"]:
                logger.info(f"File verification successful for {remote_path} using {verification_strategy} strategy in {total_time:.2f}s")
            else:
                logger.error(f"File verification failed for {remote_path}: {verification_result.get('error', 'Unknown error')}")

        return verification_result

    def _compare_full_content(self, original: bytes, downloaded: bytes) -> bool:
        """Compare files byte-for-byte."""
        return original == downloaded

    def _compare_hashes(self, original: bytes, downloaded: bytes) -> bool:
        """Compare files using SHA256 hashes."""
        import hashlib

        original_hash = hashlib.sha256(original).hexdigest()
        downloaded_hash = hashlib.sha256(downloaded).hexdigest()

        return original_hash == downloaded_hash

    def _compare_sampling(self, original: bytes, downloaded: bytes) -> bool:
        """Compare files using random sampling for large files."""
        import random

        if len(original) != len(downloaded):
            return False

        file_size = len(original)
        sample_size = min(config.VERIFICATION_SAMPLE_SIZE, file_size)

        # Take multiple random samples
        samples_verified = 0
        total_samples = min(5, max(1, sample_size // (1024 * 1024)))  # Up to 5 samples

        for _ in range(total_samples):
            # Choose random position
            if file_size > sample_size:
                position = random.randint(0, file_size - sample_size)
            else:
                position = 0

            # Extract sample
            original_sample = original[position:position + sample_size]
            downloaded_sample = downloaded[position:position + sample_size]

            if original_sample != downloaded_sample:
                return False

            samples_verified += 1

        return samples_verified > 0

    def _compare_metadata(self, original: bytes, downloaded: bytes) -> bool:
        """Compare files using only metadata (size and basic properties)."""
        return len(original) == len(downloaded)

    async def move_file(self, source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        Move/rename a file in Nextcloud via WebDAV MOVE method.
        
        Args:
            source_path: Current path of the file (relative to user root)
            dest_path: New path for the file (relative to user root)
            
        Returns:
            Dictionary with move operation result
            
        Raises:
            NextcloudError: If move operation fails
        """
        try:
            # Construct full WebDAV URLs
            source_full_path = f"{self.username}/{source_path.lstrip('/')}"
            dest_full_path = f"{self.username}/{dest_path.lstrip('/')}"
            
            source_url = urljoin(self.webdav_url, source_full_path)
            dest_url = urljoin(self.webdav_url, dest_full_path)
            
            # Ensure destination directory exists
            dest_dir = "/".join(dest_path.split("/")[:-1])
            if dest_dir:
                await self.ensure_directory_exists(dest_dir)
            
            # Move file using WebDAV MOVE method
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method="MOVE",
                    url=source_url,
                    auth=self.auth,
                    headers={
                        "Destination": dest_url,
                        "Overwrite": "F"  # Don't overwrite if destination exists
                    }
                )
                
                if response.status_code == 404:
                    classified_error = NextcloudFileNotFoundError(
                        message=f"Source file not found: {source_path}",
                        file_path=source_path,
                        context="move_file",
                        details={
                            "source_path": source_path,
                            "dest_path": dest_path,
                            "source_url": source_url
                        }
                    )
                    raise classified_error
                elif response.status_code == 412:  # Precondition Failed - destination exists
                    classified_error = NextcloudPermanentError(
                        message=f"Destination file already exists: {dest_path}",
                        status_code=412,
                        context="move_file",
                        details={
                            "source_path": source_path,
                            "dest_path": dest_path,
                            "reason": "destination_exists"
                        }
                    )
                    raise classified_error
                elif response.status_code not in [201, 204]:  # 201 Created or 204 No Content
                    classified_error = self._classify_http_error(
                        response,
                        context=f"move_file:{source_path}",
                        operation="file_move"
                    )
                    classified_error.details.update({
                        "source_path": source_path,
                        "dest_path": dest_path,
                        "source_url": source_url,
                        "dest_url": dest_url
                    })
                    raise classified_error
                
                return {
                    "success": True,
                    "source_path": source_path,
                    "dest_path": dest_path,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            # Use enhanced error classification for all exceptions
            classified_error = self._classify_error(
                e,
                context=f"move_file:{source_path}",
                operation="file_move"
            )
            classified_error.details.update({
                "source_path": source_path,
                "dest_path": dest_path
            })
            raise classified_error

    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from Nextcloud via WebDAV."""
        try:
            # Construct full WebDAV URL
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            delete_url = urljoin(self.webdav_url, full_path)
            
            # Delete file
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    url=delete_url,
                    auth=self.auth
                )
                
                if response.status_code == 404:
                    return False  # File didn't exist
                elif response.status_code not in [200, 204]:
                    classified_error = self._classify_http_error(
                        response,
                        context=f"delete_file:{remote_path}",
                        operation="file_delete"
                    )
                    classified_error.details.update({
                        "file_path": remote_path,
                        "delete_url": delete_url
                    })
                    raise classified_error
                
                return True
                
        except Exception as e:
            # Use enhanced error classification for all exceptions
            classified_error = self._classify_error(
                e,
                context=f"delete_file:{remote_path}",
                operation="file_delete"
            )
            classified_error.details.update({
                "file_path": remote_path,
                "delete_url": delete_url
            })
            raise classified_error
    
    async def create_share(self, path: str, share_type: int = 3, permissions: int = 1) -> Dict[str, Any]:
        """Create a share link for a file."""
        try:
            share_url = urljoin(self.ocs_url, "apps/files_sharing/api/v1/shares")
            
            data = {
                "path": path,
                "shareType": share_type,  # 3 = public link
                "permissions": permissions,  # 1 = read
                "password": "",  # Optional password protection
                "expireDate": ""  # Optional expiration date
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=share_url,
                    json=data,
                    headers=self.ocs_headers,
                    auth=self.auth
                )
                
                if response.status_code != 200:
                    classified_error = self._classify_http_error(
                        response,
                        context=f"create_share:{path}",
                        operation="share_creation"
                    )
                    classified_error.details.update({
                        "share_path": path,
                        "share_type": share_type,
                        "permissions": permissions,
                        "share_url": share_url
                    })
                    raise classified_error
                
                # Parse OCS response
                share_data = response.json()
                return share_data
                
        except Exception as e:
            # Use enhanced error classification for all exceptions
            classified_error = self._classify_error(
                e,
                context=f"create_share:{path}",
                operation="share_creation"
            )
            classified_error.details.update({
                "share_path": path,
                "share_type": share_type,
                "permissions": permissions,
                "share_url": share_url
            })
            raise classified_error
    
    async def get_file_info(self, remote_path: str) -> Dict[str, Any]:
        """Get file information from Nextcloud."""
        try:
            # Use WebDAV PROPFIND to get file properties
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            propfind_url = urljoin(self.webdav_url, full_path)
            
            # PROPFIND request body
            propfind_body = """<?xml version="1.0" encoding="utf-8"?>
            <D:propfind xmlns:D="DAV:">
                <D:prop>
                    <D:getcontentlength/>
                    <D:getcontenttype/>
                    <D:getlastmodified/>
                    <D:creationdate/>
                </D:prop>
            </D:propfind>"""
            
            headers = {
                "Content-Type": "application/xml",
                "Depth": "0"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method="PROPFIND",
                    url=propfind_url,
                    content=propfind_body,
                    headers=headers,
                    auth=self.auth
                )
                
                if response.status_code == 404:
                    classified_error = NextcloudFileNotFoundError(
                        message=f"File not found: {remote_path}",
                        file_path=remote_path,
                        context="get_file_info",
                        details={"propfind_url": propfind_url}
                    )
                    raise classified_error
                elif response.status_code != 207:  # 207 Multi-Status for PROPFIND
                    classified_error = self._classify_http_error(
                        response,
                        context=f"get_file_info:{remote_path}",
                        operation="file_info_retrieval"
                    )
                    classified_error.details.update({
                        "file_path": remote_path,
                        "propfind_url": propfind_url
                    })
                    raise classified_error
                
                # Parse XML response (simplified)
                # In a real implementation, you'd parse the XML properly
                return {
                    "path": remote_path,
                    "exists": True,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            # Use enhanced error classification for all exceptions
            classified_error = self._classify_error(
                e,
                context=f"get_file_info:{remote_path}",
                operation="file_info_retrieval"
            )
            classified_error.details.update({
                "file_path": remote_path,
                "propfind_url": propfind_url
            })
            raise classified_error
    
    async def create_directory(self, remote_path: str) -> bool:
        """Create directory in Nextcloud via WebDAV MKCOL."""
        try:
            # Construct full WebDAV URL
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            dir_url = urljoin(self.webdav_url, full_path)

            logger.info(f"Creating Nextcloud directory: {dir_url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method="MKCOL",
                    url=dir_url,
                    auth=self.auth
                )

                logger.info(f"Nextcloud MKCOL response status: {response.status_code}")

                # 201 = Created, 405 = Already exists (some servers return this)
                if response.status_code in [201, 405]:
                    return True
                elif response.status_code == 409:
                    # 409 = Conflict, might mean parent doesn't exist
                    logger.warning(f"Nextcloud directory creation conflict: {response.status_code} - {response.text}")
                    return False
                else:
                    logger.error(f"Nextcloud directory creation failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Nextcloud directory creation error: {str(e)}", exc_info=True)
            return False

    async def ensure_directory_exists(self, remote_path: str) -> bool:
        """Ensure the directory exists, creating all parent directories recursively."""
        if not remote_path:
            return True

        logger.info(f"Ensuring directory exists: {remote_path}")

        # Split path into components and create each level
        path_parts = remote_path.strip("/").split("/")
        current_path = ""

        for part in path_parts:
            if not part:
                continue

            current_path = f"{current_path}/{part}" if current_path else part
            logger.info(f"Ensuring directory exists level: {current_path}")

            # Try to create the directory (405 means it already exists)
            result = await self.create_directory(current_path)
            if not result:
                logger.warning(f"Failed to ensure directory exists level: {current_path}")
                # Continue anyway - the directory might already exist

        return True

    async def test_connection(self) -> bool:
        """Test connection to Nextcloud."""
        try:
            # Try to get status.php
            status_url = urljoin(self.base_url, "/status.php")
            
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(status_url)
                
                if response.status_code == 200:
                    status_data = response.json()
                    return status_data.get("installed", False)
                
                return False
                
        except Exception:
            return False


# Global Nextcloud service instance with default retry configuration
nextcloud_service = NextcloudService(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0
)