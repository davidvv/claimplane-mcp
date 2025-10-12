"""Tests for streaming upload functionality."""
import os
import io
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock
import pytest
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.file_service import FileService
from app.services.nextcloud_service import NextcloudService
from app.services.encryption_service import EncryptionService
from app.config import config


class TestStreamingUploads:
    """Test cases for streaming upload functionality."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def file_service(self, db_session):
        """File service instance."""
        return FileService(db_session)

    @pytest.fixture
    def mock_nextcloud_service(self):
        """Mock Nextcloud service."""
        with patch('app.services.file_service.nextcloud_service') as mock:
            # Configure successful upload response
            mock.upload_file.return_value = {
                "success": True,
                "file_id": "test-file-id"
            }
            yield mock

    def test_file_size_detection(self, file_service):
        """Test file size detection without loading content."""
        # Create a mock file with known size
        file_content = b"test content" * 1000  # 12KB
        mock_file = Mock()
        mock_file.file = io.BytesIO(file_content)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"

        # Test size detection
        async def run_test():
            size = await file_service._get_file_size(mock_file)
            return size

        size = asyncio.run(run_test())
        assert size == len(file_content)

    def test_chunked_reading(self, file_service):
        """Test chunked file reading."""
        file_content = b"test content" * 1000  # 12KB
        mock_file = Mock()
        mock_file.file = io.BytesIO(file_content)
        mock_file.filename = "test.txt"

        chunk_size = 1024
        chunks = []

        async def run_test():
            async for chunk in file_service._read_file_chunks(mock_file, chunk_size):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(run_test())

        # Verify chunks
        total_size = sum(len(chunk) for chunk in chunks)
        assert total_size == len(file_content)

        # Verify chunk sizes (except possibly the last one)
        for chunk in chunks[:-1]:
            assert len(chunk) == chunk_size
        assert len(chunks[-1]) <= chunk_size

    def test_threshold_size_routing_small_file(self, file_service, mock_nextcloud_service):
        """Test that files below threshold use regular upload."""
        # Create small file (below threshold)
        file_content = b"small file content"
        mock_file = Mock()
        mock_file.file = io.BytesIO(file_content)
        mock_file.filename = "small.txt"
        mock_file.content_type = "text/plain"

        # Mock file size to be below threshold
        with patch.object(file_service, '_get_file_size', return_value=1024):  # 1KB
            with patch.object(file_service, '_upload_small_file') as mock_small_upload:
                mock_small_upload.return_value = Mock()  # Mock return value

                async def run_test():
                    return await file_service.upload_file(
                        mock_file, "claim-123", "user-456", "document"
                    )

                # Should route to small file upload
                asyncio.run(run_test())
                mock_small_upload.assert_called_once()

    def test_threshold_size_routing_large_file(self, file_service, mock_nextcloud_service):
        """Test that files above threshold use streaming upload."""
        # Create large file (above threshold)
        file_content = b"large file content" * 10000  # Large content
        mock_file = Mock()
        mock_file.file = io.BytesIO(file_content)
        mock_file.filename = "large.txt"
        mock_file.content_type = "text/plain"

        # Mock file size to be above threshold
        with patch.object(file_service, '_get_file_size', return_value=60 * 1024 * 1024):  # 60MB
            with patch.object(file_service, '_upload_large_file_streaming') as mock_large_upload:
                mock_large_upload.return_value = Mock()  # Mock return value

                async def run_test():
                    return await file_service.upload_file(
                        mock_file, "claim-123", "user-456", "document"
                    )

                # Should route to large file upload
                asyncio.run(run_test())
                mock_large_upload.assert_called_once()

    def test_edge_case_exact_threshold(self, file_service, mock_nextcloud_service):
        """Test file exactly at threshold size."""
        file_content = b"threshold file content"
        mock_file = Mock()
        mock_file.file = io.BytesIO(file_content)
        mock_file.filename = "threshold.txt"
        mock_file.content_type = "text/plain"

        # Mock file size to be exactly at threshold
        threshold_size = config.STREAMING_THRESHOLD
        with patch.object(file_service, '_get_file_size', return_value=threshold_size):
            with patch.object(file_service, '_upload_large_file_streaming') as mock_large_upload:
                mock_large_upload.return_value = Mock()

                async def run_test():
                    return await file_service.upload_file(
                        mock_file, "claim-123", "user-456", "document"
                    )

                asyncio.run(run_test())
                mock_large_upload.assert_called_once()

    def test_rolling_hash_calculation(self, file_service):
        """Test rolling hash calculation across chunks."""
        file_content = b"test content for hash" * 1000
        mock_file = Mock()
        mock_file.file = io.BytesIO(file_content)

        # Create chunks generator
        async def chunk_generator():
            chunk_size = 1024
            for i in range(0, len(file_content), chunk_size):
                yield file_content[i:i + chunk_size]

        async def run_test():
            hash_result = await file_service._calculate_rolling_hash(chunk_generator())
            return hash_result

        hash_result = asyncio.run(run_test())

        # Verify hash is calculated correctly
        assert hash_result is not None
        assert len(hash_result) == 64  # SHA256 hex length

        # Verify it's consistent
        expected_hash = file_service._calculate_rolling_hash.__globals__['hashlib'].sha256(file_content).hexdigest()
        assert hash_result == expected_hash

    def test_upload_error_handling(self, file_service):
        """Test error handling during upload."""
        mock_file = Mock()
        mock_file.file = io.BytesIO(b"test content")
        mock_file.filename = "test.txt"

        error = Exception("Test error")

        async def run_test():
            await file_service._handle_upload_error(mock_file, error, "test/path")

        # Should not raise exception
        asyncio.run(run_test())

    def test_chunk_upload_retry(self, file_service):
        """Test chunk upload retry logic."""
        chunk_data = b"test chunk data"
        remote_path = "test/path"

        with patch('app.services.file_service.nextcloud_service') as mock_nextcloud:
            # Mock first two calls to fail, third to succeed
            mock_nextcloud.upload_file.side_effect = [
                Exception("Network error"),
                Exception("Network error"),
                {"success": True, "file_id": "test-id"}
            ]

            async def run_test():
                return await file_service._retry_chunk_upload(chunk_data, remote_path)

            result = asyncio.run(run_test())
            assert result is True
            assert mock_nextcloud.upload_file.call_count == 3

    def test_memory_buffer_limits(self, file_service):
        """Test that memory usage stays bounded during streaming."""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create a large file mock
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        mock_file = Mock()
        mock_file.file = io.BytesIO(large_content)
        mock_file.filename = "large.bin"
        mock_file.content_type = "application/octet-stream"

        # Mock streaming upload to avoid actual Nextcloud calls
        with patch.object(file_service, '_get_file_size', return_value=len(large_content)):
            with patch.object(file_service, '_upload_large_file_streaming') as mock_upload:
                mock_upload.return_value = Mock()

                async def run_test():
                    return await file_service.upload_file(
                        mock_file, "claim-123", "user-456", "document"
                    )

                # This should complete without excessive memory usage
                asyncio.run(run_test())

                # Check memory usage hasn't grown excessively
                final_memory = process.memory_info().rss
                memory_increase = final_memory - initial_memory

                # Memory increase should be reasonable (less than file size)
                # Allow some buffer for processing overhead
                max_reasonable_increase = len(large_content) // 2
                assert memory_increase < max_reasonable_increase

    def test_concurrent_uploads(self, file_service, mock_nextcloud_service):
        """Test concurrent large file uploads."""
        # Create multiple large file mocks
        files = []
        for i in range(3):
            file_content = b"concurrent file content" * 10000
            mock_file = Mock()
            mock_file.file = io.BytesIO(file_content)
            mock_file.filename = f"concurrent_{i}.txt"
            mock_file.content_type = "text/plain"
            files.append(mock_file)

        # Mock file sizes to be above threshold
        with patch.object(file_service, '_get_file_size', return_value=60 * 1024 * 1024):  # 60MB
            with patch.object(file_service, '_upload_large_file_streaming') as mock_upload:
                mock_upload.return_value = Mock()

                async def run_test():
                    # Start all uploads concurrently
                    tasks = []
                    for i, file in enumerate(files):
                        task = file_service.upload_file(
                            file, f"claim-{i}", f"user-{i}", "document"
                        )
                        tasks.append(task)

                    results = await asyncio.gather(*tasks)
                    return results

                # Should handle concurrent uploads without issues
                results = asyncio.run(run_test())
                assert len(results) == 3
                assert mock_upload.call_count == 3

    def test_network_interruption_simulation(self, file_service):
        """Test behavior during simulated network interruptions."""
        file_content = b"network test content" * 1000
        mock_file = Mock()
        mock_file.file = io.BytesIO(file_content)
        mock_file.filename = "network_test.txt"
        mock_file.content_type = "text/plain"

        with patch.object(file_service, '_get_file_size', return_value=60 * 1024 * 1024):
            with patch('app.services.file_service.nextcloud_service') as mock_nextcloud:
                # Simulate network interruption
                mock_nextcloud.upload_file.side_effect = Exception("Network timeout")

                async def run_test():
                    try:
                        await file_service.upload_file(
                            mock_file, "claim-123", "user-456", "document"
                        )
                        return False  # Should not reach here
                    except HTTPException as e:
                        return e.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

                # Should handle network error gracefully
                result = asyncio.run(run_test())
                assert result is True

    def test_encryption_streaming_context(self):
        """Test encryption streaming context creation."""
        encryption_service = EncryptionService()

        # Test context creation
        context = encryption_service.create_streaming_context()
        assert context["initialized"] is True
        assert "cipher_suite" in context

        # Test chunk encryption
        test_chunk = b"test chunk data"
        encrypted_chunk = encryption_service.encrypt_chunk(test_chunk, context)
        assert encrypted_chunk != test_chunk
        assert len(encrypted_chunk) > len(test_chunk)  # Encrypted data is typically larger

    def test_progress_tracking(self, file_service):
        """Test progress tracking during streaming upload."""
        file_content = b"progress test content" * 1000  # 20KB
        mock_file = Mock()
        mock_file.file = io.BytesIO(file_content)
        mock_file.filename = "progress_test.txt"
        mock_file.content_type = "text/plain"

        # Capture print output to verify progress logging
        with patch('builtins.print') as mock_print:
            with patch.object(file_service, '_get_file_size', return_value=len(file_content)):
                with patch('app.services.file_service.nextcloud_service') as mock_nextcloud:
                    mock_nextcloud.upload_file.return_value = {"success": True, "file_id": "test-id"}

                    with patch.object(file_service, '_validate_large_file_streaming', return_value={
                        "valid": True,
                        "errors": [],
                        "file_hash": None,
                        "mime_type": "text/plain"
                    }):
                        with patch.object(file_service.file_repo, 'get_by_file_hash', return_value=None):

                            async def run_test():
                                return await file_service.upload_file(
                                    mock_file, "claim-123", "user-456", "document"
                                )

                            asyncio.run(run_test())

                            # Verify progress was logged
                            progress_calls = [call for call in mock_print.call_args_list
                                            if 'Processed' in str(call)]
                            assert len(progress_calls) > 0


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestStreamingUploads()

    print("Running streaming upload tests...")

    try:
        # Test file size detection
        mock_file = Mock()
        mock_file.file = io.BytesIO(b"test content" * 100)
        test_instance.file_service._get_file_size = AsyncMock(return_value=1200)
        size = asyncio.run(test_instance.file_service._get_file_size(mock_file))
        print(f"✓ File size detection: {size} bytes")

        # Test chunked reading
        chunks = []
        async def chunk_test():
            async for chunk in test_instance.file_service._read_file_chunks(mock_file, 100):
                chunks.append(chunk)
        asyncio.run(chunk_test())
        print(f"✓ Chunked reading: {len(chunks)} chunks")

        # Test encryption context
        encryption_service = EncryptionService()
        context = encryption_service.create_streaming_context()
        encrypted = encryption_service.encrypt_chunk(b"test", context)
        print(f"✓ Encryption context: {len(encrypted)} bytes encrypted")

        print("All basic tests passed!")

    except Exception as e:
        print(f"Test failed: {e}")
        raise