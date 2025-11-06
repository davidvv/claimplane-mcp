"""Tests for admin files endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Customer
from app.repositories import ClaimRepository


@pytest.mark.asyncio
class TestAdminFilesEndpoints:
    """Test admin file management endpoints."""

    @pytest.fixture
    async def test_claim(self, db_session: AsyncSession, test_customer: Customer):
        """Create a test claim."""
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

    async def test_list_claim_documents(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_claim
    ):
        """Test listing all documents for a claim."""
        response = await client.get(
            f"/admin/files/claim/{test_claim.id}/documents",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_claim_documents_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_claim
    ):
        """Test listing documents as regular user (should fail)."""
        response = await client.get(
            f"/admin/files/claim/{test_claim.id}/documents",
            headers=auth_headers
        )

        assert response.status_code == 403

    async def test_get_file_metadata(self, client: AsyncClient, admin_headers: dict):
        """Test getting file metadata."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/admin/files/{fake_file_id}/metadata",
            headers=admin_headers
        )

        assert response.status_code == 404

    async def test_review_file_approve(self, client: AsyncClient, admin_headers: dict):
        """Test approving a file."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        review_data = {
            "approved": True,
            "rejection_reason": None
        }

        response = await client.put(
            f"/admin/files/{fake_file_id}/review",
            json=review_data,
            headers=admin_headers
        )

        # Will return 404 since file doesn't exist
        assert response.status_code == 404

    async def test_review_file_reject(self, client: AsyncClient, admin_headers: dict):
        """Test rejecting a file."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        review_data = {
            "approved": False,
            "rejection_reason": "Document quality is insufficient"
        }

        response = await client.put(
            f"/admin/files/{fake_file_id}/review",
            json=review_data,
            headers=admin_headers
        )

        # Will return 404 since file doesn't exist
        assert response.status_code == 404

    async def test_request_file_reupload(self, client: AsyncClient, admin_headers: dict):
        """Test requesting file re-upload."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        reupload_data = {
            "reason": "Document is not readable",
            "deadline_days": 7
        }

        response = await client.post(
            f"/admin/files/{fake_file_id}/request-reupload",
            json=reupload_data,
            headers=admin_headers
        )

        # Will return 404 since file doesn't exist
        assert response.status_code == 404

    async def test_get_pending_review_files(self, client: AsyncClient, admin_headers: dict):
        """Test getting files pending review."""
        response = await client.get("/admin/files/pending-review", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_files_by_document_type(self, client: AsyncClient, admin_headers: dict):
        """Test getting files by document type."""
        response = await client.get(
            "/admin/files/by-document-type/boarding_pass",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_file_statistics(self, client: AsyncClient, admin_headers: dict):
        """Test getting file statistics."""
        response = await client.get("/admin/files/statistics", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "status_counts" in data
        assert "document_type_counts" in data
        assert "validation_status_counts" in data
        assert "total_size_bytes" in data
        assert "pending_review_count" in data

    async def test_get_file_statistics_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting file statistics as regular user (should fail)."""
        response = await client.get("/admin/files/statistics", headers=auth_headers)

        assert response.status_code == 403

    async def test_delete_file(self, client: AsyncClient, admin_headers: dict):
        """Test deleting (soft delete) a file."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(f"/admin/files/{fake_file_id}", headers=admin_headers)

        # Will return 404 since file doesn't exist
        assert response.status_code == 404

    async def test_delete_file_as_regular_user(self, client: AsyncClient, auth_headers: dict):
        """Test deleting file as regular user (should fail)."""
        fake_file_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(f"/admin/files/{fake_file_id}", headers=auth_headers)

        assert response.status_code == 403
