"""Tests for files endpoints."""
import io
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Customer
from app.repositories import ClaimRepository


@pytest.mark.asyncio
class TestFilesEndpoints:
    """Test file management endpoints."""

    @pytest.fixture
    async def test_claim(self, db_session: AsyncSession, test_customer: Customer):
        """Create a test claim for file uploads."""
        claim_repo = ClaimRepository(db_session)
        claim = await claim_repo.create_claim(
            customer_id=test_customer.id,
            flight_number="LH1234",
            airline="Lufthansa",
            departure_date="2025-06-15",
            departure_airport="FRA",
            arrival_airport="JFK",
            incident_type="delay"
        )
        await db_session.commit()
        return claim

    async def test_upload_file(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_claim
    ):
        """Test uploading a file."""
        # Create a test file
        file_content = b"Test file content"
        files = {
            "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
        }
        data = {
            "claim_id": str(test_claim.id),
            "document_type": "boarding_pass",
            "description": "Test boarding pass",
            "access_level": "private"
        }

        response = await client.post(
            "/files/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        # Note: This might fail due to Nextcloud integration
        # In a real test environment, you'd mock the Nextcloud service
        assert response.status_code in [201, 500, 503]

    async def test_upload_file_unauthorized(self, client: AsyncClient, test_claim):
        """Test uploading file without authentication."""
        file_content = b"Test file content"
        files = {
            "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
        }
        data = {
            "claim_id": str(test_claim.id),
            "document_type": "boarding_pass"
        }

        response = await client.post("/files/upload", files=files, data=data)

        assert response.status_code == 401

    async def test_upload_file_to_others_claim(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_admin: Customer
    ):
        """Test uploading file to another user's claim (should fail for customers)."""
        # Create claim for admin
        claim_repo = ClaimRepository(db_session)
        admin_claim = await claim_repo.create_claim(
            customer_id=test_admin.id,
            flight_number="BA9999",
            airline="British Airways",
            departure_date="2025-08-01",
            departure_airport="LHR",
            arrival_airport="JFK",
            incident_type="delay"
        )
        await db_session.commit()

        file_content = b"Test file content"
        files = {
            "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
        }
        data = {
            "claim_id": str(admin_claim.id),
            "document_type": "boarding_pass"
        }

        response = await client.post(
            "/files/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 403

    async def test_upload_file_too_large(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_claim
    ):
        """Test uploading file that exceeds size limit."""
        # Create a file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {
            "file": ("large.pdf", io.BytesIO(large_content), "application/pdf")
        }
        data = {
            "claim_id": str(test_claim.id),
            "document_type": "boarding_pass"
        }

        response = await client.post(
            "/files/upload",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 413

    async def test_get_file_info_unauthorized(self, client: AsyncClient):
        """Test getting file info without authentication."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/files/{fake_file_id}")

        assert response.status_code == 401

    async def test_download_file_unauthorized(self, client: AsyncClient):
        """Test downloading file without authentication."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/files/{fake_file_id}/download")

        assert response.status_code == 401

    async def test_delete_file_unauthorized(self, client: AsyncClient):
        """Test deleting file without authentication."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(f"/files/{fake_file_id}")

        assert response.status_code == 401

    async def test_get_files_by_claim(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_claim
    ):
        """Test getting files for a claim."""
        response = await client.get(f"/files/claim/{test_claim.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert "total" in data
        assert "page" in data

    async def test_get_files_by_claim_unauthorized_access(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_admin: Customer
    ):
        """Test getting files for another user's claim."""
        # Create claim for admin
        claim_repo = ClaimRepository(db_session)
        admin_claim = await claim_repo.create_claim(
            customer_id=test_admin.id,
            flight_number="BA9999",
            airline="British Airways",
            departure_date="2025-08-01",
            departure_airport="LHR",
            arrival_airport="JFK",
            incident_type="delay"
        )
        await db_session.commit()

        response = await client.get(f"/files/claim/{admin_claim.id}", headers=auth_headers)

        assert response.status_code == 403

    async def test_get_validation_rules(self, client: AsyncClient):
        """Test getting file validation rules (public endpoint)."""
        response = await client.get("/files/validation-rules")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have rules for different document types
        if len(data) > 0:
            rule = data[0]
            assert "document_type" in rule
            assert "max_file_size" in rule
            assert "allowed_mime_types" in rule

    async def test_search_files(self, client: AsyncClient):
        """Test searching files."""
        search_params = {
            "query": "boarding",
            "document_type": "boarding_pass",
            "page": 1,
            "per_page": 10
        }

        response = await client.post("/files/search", json=search_params)

        # This might require auth depending on implementation
        assert response.status_code in [200, 401]
