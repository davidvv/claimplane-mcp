"""GDPR compliance service for data export and deletion."""
import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Customer, Claim, ClaimFile, AccountDeletionRequest

logger = logging.getLogger(__name__)


class GDPRService:
    """Service for GDPR Article 20 (Data Portability) and Article 17 (Right to Erasure) compliance."""

    @staticmethod
    async def export_customer_data(
        session: AsyncSession,
        customer_id: UUID
    ) -> Dict[str, Any]:
        """
        Export all customer data for GDPR Article 20 (Right to Data Portability).

        Args:
            session: Database session
            customer_id: UUID of the customer

        Returns:
            Dictionary with complete customer data in structured JSON format

        Raises:
            ValueError: If customer not found
        """
        # Fetch customer
        customer = await session.get(Customer, customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Fetch all claims with related data
        claims_query = select(Claim).options(
            selectinload(Claim.files),
            selectinload(Claim.claim_notes),
            selectinload(Claim.status_history)
        ).where(Claim.customer_id == customer_id)

        result = await session.execute(claims_query)
        claims = result.scalars().all()

        # Build export data structure
        export_data = {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "customer_id": str(customer.id),
            "profile": {
                "email": customer.email,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
                "address": customer.address,
                "created_at": customer.created_at.isoformat() if customer.created_at else None,
                "last_login_at": customer.last_login_at.isoformat() if customer.last_login_at else None,
                "is_email_verified": customer.is_email_verified,
                "role": customer.role
            },
            "claims": [
                {
                    "id": str(claim.id),
                    "flight_number": claim.flight_number,
                    "airline": claim.airline,
                    "departure_airport": claim.departure_airport,
                    "arrival_airport": claim.arrival_airport,
                    "departure_date": claim.departure_date.isoformat() if claim.departure_date else None,
                    "scheduled_departure_time": claim.scheduled_departure_time.isoformat() if claim.scheduled_departure_time else None,
                    "actual_departure_time": claim.actual_departure_time.isoformat() if claim.actual_departure_time else None,
                    "scheduled_arrival_time": claim.scheduled_arrival_time.isoformat() if claim.scheduled_arrival_time else None,
                    "actual_arrival_time": claim.actual_arrival_time.isoformat() if claim.actual_arrival_time else None,
                    "incident_type": claim.incident_type,
                    "incident_description": claim.incident_description,
                    "delay_hours": float(claim.delay_hours) if claim.delay_hours else None,
                    "status": claim.status,
                    "compensation_amount": float(claim.compensation_amount) if claim.compensation_amount else None,
                    "currency": claim.currency,
                    "calculated_compensation": float(claim.calculated_compensation) if claim.calculated_compensation else None,
                    "flight_distance_km": claim.flight_distance_km,
                    "extraordinary_circumstances": claim.extraordinary_circumstances,
                    "rejection_reason": claim.rejection_reason,
                    "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
                    "updated_at": claim.updated_at.isoformat() if claim.updated_at else None,
                    "files": [
                        {
                            "id": str(f.id),
                            "filename": f.original_filename,
                            "document_type": f.document_type,
                            "file_size": f.file_size,
                            "mime_type": f.mime_type,
                            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
                            "status": f.status
                        }
                        for f in claim.files
                    ],
                    "notes": [
                        {
                            "id": str(note.id),
                            "text": note.note_text,
                            "is_internal": note.is_internal,
                            "created_at": note.created_at.isoformat() if note.created_at else None
                        }
                        for note in claim.claim_notes if not note.is_internal  # Only export customer-visible notes
                    ],
                    "status_history": [
                        {
                            "id": str(h.id),
                            "previous_status": h.previous_status,
                            "new_status": h.new_status,
                            "change_reason": h.change_reason,
                            "changed_at": h.changed_at.isoformat() if h.changed_at else None
                        }
                        for h in claim.status_history
                    ]
                }
                for claim in claims
            ],
            "statistics": {
                "total_claims": len(claims),
                "claims_by_status": {},
                "total_files_uploaded": sum(len(c.files) for c in claims),
                "total_compensation_amount": sum(
                    float(c.compensation_amount or 0) for c in claims
                )
            }
        }

        # Calculate claims by status
        status_counts = {}
        for claim in claims:
            status = claim.status
            status_counts[status] = status_counts.get(status, 0) + 1
        export_data["statistics"]["claims_by_status"] = status_counts

        logger.info(f"Exported data for customer {customer_id}: {len(claims)} claims, {export_data['statistics']['total_files_uploaded']} files")

        return export_data

    @staticmethod
    async def delete_customer_data(
        session: AsyncSession,
        customer_id: UUID,
        deletion_request_id: UUID
    ) -> Dict[str, Any]:
        """
        Perform GDPR-compliant data deletion (Article 17 - Right to Erasure).

        Strategy:
        - Delete uploaded files from Nextcloud
        - Anonymize claims (keep for legal retention, remove PII)
        - Anonymize customer profile
        - Mark deletion request as completed

        NOTE: Claims are retained for 7 years (EU financial law) but anonymized.
        Files are permanently deleted (no retention requirement).

        Args:
            session: Database session
            customer_id: UUID of the customer
            deletion_request_id: UUID of the deletion request

        Returns:
            Dictionary with deletion summary and any errors

        Raises:
            ValueError: If customer not found
        """
        from app.services.nextcloud_service import NextcloudService

        customer = await session.get(Customer, customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        deletion_summary = {
            "customer_id": str(customer_id),
            "deletion_started_at": datetime.now(timezone.utc).isoformat(),
            "files_deleted": 0,
            "files_failed": 0,
            "claims_anonymized": 0,
            "errors": []
        }

        # 1. Delete files from Nextcloud and database
        files_query = select(ClaimFile).where(ClaimFile.customer_id == customer_id)
        result = await session.execute(files_query)
        files = result.scalars().all()

        nextcloud = NextcloudService()
        for file in files:
            try:
                # Delete from Nextcloud
                await nextcloud.delete_file(file.storage_path)
                deletion_summary["files_deleted"] += 1
                logger.info(f"Deleted file {file.id} from Nextcloud: {file.storage_path}")
            except Exception as e:
                deletion_summary["files_failed"] += 1
                error_msg = f"Failed to delete file {file.id} from Nextcloud: {str(e)}"
                deletion_summary["errors"].append(error_msg)
                logger.error(error_msg)

        # Delete file records from database
        for file in files:
            await session.delete(file)

        # 2. Anonymize claims (keep for legal retention)
        claims_query = select(Claim).where(Claim.customer_id == customer_id)
        result = await session.execute(claims_query)
        claims = result.scalars().all()

        for claim in claims:
            # Remove PII but keep claim data for financial/legal compliance (7-year retention)
            claim.incident_description = "DELETED - Customer requested account deletion"
            deletion_summary["claims_anonymized"] += 1

        logger.info(f"Anonymized {len(claims)} claims for customer {customer_id}")

        # 3. Anonymize customer profile
        original_email = customer.email
        customer.email = f"deleted_user_{customer.id}@deleted.local"
        customer.first_name = "DELETED"
        customer.last_name = "USER"
        customer.phone = None
        customer.street = None
        customer.city = None
        customer.postal_code = None
        customer.country = None
        customer.password_hash = None
        customer.is_active = False
        customer.is_blacklisted = True

        logger.warning(
            f"Anonymized customer profile: {original_email} -> {customer.email}"
        )

        # 4. Mark deletion request as completed
        deletion_request = await session.get(AccountDeletionRequest, deletion_request_id)
        if deletion_request:
            deletion_request.status = AccountDeletionRequest.STATUS_COMPLETED

        await session.commit()

        deletion_summary["deletion_completed_at"] = datetime.now(timezone.utc).isoformat()
        deletion_summary["original_email"] = original_email

        logger.warning(
            f"GDPR deletion completed for customer {customer_id}. "
            f"Files deleted: {deletion_summary['files_deleted']}, "
            f"Files failed: {deletion_summary['files_failed']}, "
            f"Claims anonymized: {deletion_summary['claims_anonymized']}"
        )

        return deletion_summary
