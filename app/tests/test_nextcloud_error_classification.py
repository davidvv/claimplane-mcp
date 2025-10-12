"""Test script for Nextcloud enhanced error classification system."""
import asyncio
import json
from unittest.mock import Mock, MagicMock

import httpx
import pytest

from app.services.nextcloud_service import NextcloudService
from app.exceptions import (
    NextcloudNetworkError, NextcloudTimeoutError, NextcloudAuthenticationError,
    NextcloudFileNotFoundError, NextcloudQuotaExceededError, NextcloudServerError
)


class TestNextcloudErrorClassification:
    """Test cases for the enhanced Nextcloud error classification system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = NextcloudService(max_retries=1)  # Minimal retries for testing

    def test_error_classification_network_timeout(self):
        """Test classification of network timeout errors."""
        timeout_error = asyncio.TimeoutError("Request timed out")

        classified_error = self.service._classify_error(
            timeout_error,
            context="test_upload",
            operation="file_upload"
        )

        assert isinstance(classified_error, NextcloudTimeoutError)
        assert classified_error.retryable is True
        assert classified_error.error_code == "NC_TIMEOUT_ERROR"
        assert "test_upload" in classified_error.context
        assert "file_upload" in classified_error.details.get("operation")
        assert "suggestion" in classified_error.to_dict()

    def test_error_classification_connection_error(self):
        """Test classification of connection errors."""
        connection_error = httpx.ConnectError("Connection failed")

        classified_error = self.service._classify_error(
            connection_error,
            context="test_download",
            operation="file_download"
        )

        assert isinstance(classified_error, NextcloudConnectionError)
        assert classified_error.retryable is True
        assert classified_error.error_code == "NC_CONNECTION_ERROR"
        assert "test_download" in classified_error.context

    def test_error_classification_authentication_error(self):
        """Test classification of authentication errors."""
        # Mock HTTP 401 response
        response = Mock()
        response.status_code = 401
        response.text = "Unauthorized"
        response.headers = {}

        http_error = httpx.HTTPStatusError("401 Unauthorized", request=Mock(), response=response)

        classified_error = self.service._classify_http_error(
            response,
            context="test_auth",
            operation="authentication"
        )

        assert isinstance(classified_error, NextcloudAuthenticationError)
        assert classified_error.retryable is False
        assert classified_error.error_code == "NC_AUTH_ERROR"
        assert classified_error.status_code == 401

    def test_error_classification_file_not_found(self):
        """Test classification of file not found errors."""
        # Mock HTTP 404 response
        response = Mock()
        response.status_code = 404
        response.text = "File not found"
        response.headers = {}

        http_error = httpx.HTTPStatusError("404 Not Found", request=Mock(), response=response)

        classified_error = self.service._classify_http_error(
            response,
            context="test_file_lookup",
            operation="file_access"
        )

        assert isinstance(classified_error, NextcloudFileNotFoundError)
        assert classified_error.retryable is False
        assert classified_error.error_code == "NC_FILE_NOT_FOUND"
        assert classified_error.status_code == 404

    def test_error_classification_quota_exceeded(self):
        """Test classification of quota exceeded errors."""
        # Mock HTTP 507 response with quota information
        response = Mock()
        response.status_code = 507
        response.text = "Storage quota exceeded: 5GB of 5GB used"
        response.headers = {}

        http_error = httpx.HTTPStatusError("507 Insufficient Storage", request=Mock(), response=response)

        classified_error = self.service._classify_http_error(
            response,
            context="test_upload",
            operation="file_upload"
        )

        assert isinstance(classified_error, NextcloudQuotaExceededError)
        assert classified_error.retryable is False
        assert classified_error.error_code == "NC_QUOTA_EXCEEDED"
        assert classified_error.status_code == 507
        assert "quota_info" in classified_error.details

    def test_error_classification_server_error(self):
        """Test classification of server errors."""
        # Mock HTTP 500 response
        response = Mock()
        response.status_code = 500
        response.text = "Internal server error"
        response.headers = {"Retry-After": "30"}

        http_error = httpx.HTTPStatusError("500 Internal Server Error", request=Mock(), response=response)

        classified_error = self.service._classify_http_error(
            response,
            context="test_operation",
            operation="server_request"
        )

        assert isinstance(classified_error, NextcloudServerError)
        assert classified_error.retryable is True
        assert classified_error.error_code == "NC_SERVER_ERROR_500"
        assert classified_error.retry_after == 30

    def test_context_aware_error_messages(self):
        """Test that error messages are context-aware."""
        # Test different contexts produce different messages
        response = Mock()
        response.status_code = 404
        response.text = "Not found"
        response.headers = {}

        # Upload context
        upload_error = self.service._classify_http_error(
            response,
            context="upload_file:/test/file.txt",
            operation="file_upload"
        )

        # Download context
        download_error = self.service._classify_http_error(
            response,
            context="download_file:/test/file.txt",
            operation="file_download"
        )

        # Both should be file not found errors but with different context
        assert isinstance(upload_error, NextcloudFileNotFoundError)
        assert isinstance(download_error, NextcloudFileNotFoundError)
        assert upload_error.context != download_error.context

    def test_error_response_structure(self):
        """Test that error responses have the correct structure."""
        timeout_error = NextcloudTimeoutError(
            message="Upload timed out",
            timeout_seconds=30,
            context="test_upload",
            details={"file_size": 1024}
        )

        error_dict = timeout_error.to_dict()

        # Verify required fields are present
        required_fields = ["error_code", "message", "suggestion", "retryable", "context", "details"]
        for field in required_fields:
            assert field in error_dict

        # Verify specific values
        assert error_dict["error_code"] == "NC_TIMEOUT_ERROR"
        assert error_dict["retryable"] is True
        assert error_dict["context"] == "test_upload"
        assert error_dict["details"]["timeout_seconds"] == 30
        assert error_dict["details"]["file_size"] == 1024

    def test_retry_logic_with_classified_errors(self):
        """Test that retry logic works correctly with classified errors."""
        # Test that retryable errors are identified correctly
        retryable_error = NextcloudTimeoutError("Timeout error")
        permanent_error = NextcloudFileNotFoundError("File not found")

        is_retryable, retry_after = self.service._is_retryable_error(retryable_error)
        assert is_retryable is True

        is_retryable, retry_after = self.service._is_retryable_error(permanent_error)
        assert is_retryable is False

    def test_analyze_response_text_quota_info(self):
        """Test analysis of response text for quota information."""
        response_text = "Storage quota exceeded: You have used 4.5 GB of 5 GB"

        details = self.service._analyze_response_text(response_text, "upload")

        assert "quota_info" in details
        assert "used" in details["quota_info"]
        assert "limit" in details["quota_info"]
        assert details["operation"] == "upload"

    def test_analyze_response_text_file_path(self):
        """Test analysis of response text for file path information."""
        response_text = 'File "/uploads/document.pdf" not found'

        details = self.service._analyze_response_text(response_text, "download")

        assert details["file_path"] == "/uploads/document.pdf"
        assert details["operation"] == "download"


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestNextcloudErrorClassification()

    print("Testing Nextcloud Error Classification System...")
    print("=" * 50)

    # Test error classification
    print("1. Testing network timeout classification...")
    test_instance.test_error_classification_network_timeout()
    print("   ✓ Network timeout errors classified correctly")

    print("2. Testing connection error classification...")
    test_instance.test_error_classification_connection_error()
    print("   ✓ Connection errors classified correctly")

    print("3. Testing authentication error classification...")
    test_instance.test_error_classification_authentication_error()
    print("   ✓ Authentication errors classified correctly")

    print("4. Testing file not found error classification...")
    test_instance.test_error_classification_file_not_found()
    print("   ✓ File not found errors classified correctly")

    print("5. Testing quota exceeded error classification...")
    test_instance.test_error_classification_quota_exceeded()
    print("   ✓ Quota exceeded errors classified correctly")

    print("6. Testing server error classification...")
    test_instance.test_error_classification_server_error()
    print("   ✓ Server errors classified correctly")

    print("7. Testing context-aware error messages...")
    test_instance.test_context_aware_error_messages()
    print("   ✓ Context-aware messages working correctly")

    print("8. Testing error response structure...")
    test_instance.test_error_response_structure()
    print("   ✓ Error response structure is correct")

    print("9. Testing retry logic with classified errors...")
    test_instance.test_retry_logic_with_classified_errors()
    print("   ✓ Retry logic works with classified errors")

    print("10. Testing response text analysis...")
    test_instance.test_analyze_response_text_quota_info()
    test_instance.test_analyze_response_text_file_path()
    print("   ✓ Response text analysis working correctly")

    print("\n" + "=" * 50)
    print("✅ All tests passed! Enhanced error classification system is working correctly.")
    print("\nError response format example:")
    example_error = NextcloudTimeoutError(
        message="Upload timed out after 30 seconds",
        timeout_seconds=30,
        context="upload_file:/test/file.txt",
        details={"file_size": 1024, "file_path": "/test/file.txt"}
    )
    print(json.dumps(example_error.to_dict(), indent=2))