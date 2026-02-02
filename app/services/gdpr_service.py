"""GDPR compliance service for data export and deletion."""
import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Customer, Claim, ClaimFile, AccountDeletionRequest,
    Passenger, ClaimNote, ClaimEvent, FlightSearchLog,
    RefreshToken, PasswordResetToken, MagicLinkToken
)

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
            selectinload(Claim.status_history),
            selectinload(Claim.passengers)
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
                    "incident_type": claim.incident_type,
                    "notes": claim.notes,
                    "booking_reference": claim.booking_reference,
                    "ticket_number": claim.ticket_number,
                    "status": claim.status,
                    "compensation_amount": float(claim.compensation_amount) if claim.compensation_amount else None,
                    "currency": claim.currency,
                    "calculated_compensation": float(claim.calculated_compensation) if claim.calculated_compensation else None,
                    "flight_distance_km": float(claim.flight_distance_km) if claim.flight_distance_km else None,
                    "delay_hours": float(claim.delay_hours) if claim.delay_hours else None,
                    "extraordinary_circumstances": claim.extraordinary_circumstances,
                    "rejection_reason": claim.rejection_reason,
                    "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
                    "updated_at": claim.updated_at.isoformat() if claim.updated_at else None,
                    "passengers": [
                        {
                            "first_name": p.first_name,
                            "last_name": p.last_name,
                            "email": p.email,
                            "ticket_number": p.ticket_number
                        }
                        for p in claim.passengers
                    ],
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
        - Delete physical files from Nextcloud
        - Deep anonymize claims, passengers, notes and events (remove all PII)
        - Physically delete all authentication and session tokens
        - Anonymize customer profile
        - Mark deletion request as completed
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
            "tokens_deleted": 0,
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

        # 2. Physically delete all authentication tokens
        for token_model in [RefreshToken, PasswordResetToken, MagicLinkToken]:
            token_delete_stmt = delete(token_model).where(token_model.user_id == customer_id)
            result = await session.execute(token_delete_stmt)
            deletion_summary["tokens_deleted"] += result.rowcount

        # 3. Deep anonymize claims and related entities
        # Load claims with relationships to ensure they are cleaned up
        claims_query = select(Claim).options(
            selectinload(Claim.passengers),
            selectinload(Claim.claim_notes),
            selectinload(Claim.status_history)
        ).where(Claim.customer_id == customer_id)
        
        result = await session.execute(claims_query)
        claims = result.scalars().all()

        for claim in claims:
            # Clear high-entropy identifiers
            claim.booking_reference = None
            claim.ticket_number = None
            claim.terms_acceptance_ip = "0.0.0.0"
            claim.privacy_consent_ip = "0.0.0.0"
            claim.notes = "DELETED - Customer requested account deletion"
            
            # Anonymize linked passengers
            for passenger in claim.passengers:
                passenger.first_name = "DELETED"
                passenger.last_name = "USER"
                passenger.email = f"deleted_p_{passenger.id}@deleted.local"
                passenger.ticket_number = None
            
            # Scrub notes
            for note in claim.claim_notes:
                note.note_text = "DELETED - GDPR erasure request"
            
            # Scrub status history
            for history in claim.status_history:
                history.change_reason = "DELETED"

            deletion_summary["claims_anonymized"] += 1

        # 4. Scrub analytics and logs
        # Anonymize IPs in claim events
        await session.execute(
            update(ClaimEvent)
            .where(ClaimEvent.customer_id == customer_id)
            .values(ip_address="0.0.0.0", event_data=None)
        )
        
        # Anonymize IPs in flight search logs
        await session.execute(
            update(FlightSearchLog)
            .where(FlightSearchLog.user_id == customer_id)
            .values(ip_address="0.0.0.0")
        )

        # 5. Anonymize customer profile
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
        customer.failed_login_attempts = 0
        customer.locked_until = None

        logger.warning(f"Anonymized customer profile: {original_email} -> {customer.email}")

        # 6. Mark deletion request as completed
        deletion_request = await session.get(AccountDeletionRequest, deletion_request_id)
        if deletion_request:
            deletion_request.status = AccountDeletionRequest.STATUS_COMPLETED

        await session.commit()

        deletion_summary["deletion_completed_at"] = datetime.now(timezone.utc).isoformat()
        deletion_summary["original_email"] = original_email

        logger.warning(
            f"GDPR deletion completed for customer {customer_id}. "
            f"Files deleted: {deletion_summary['files_deleted']}, "
            f"Claims anonymized: {deletion_summary['claims_anonymized']}, "
            f"Tokens purged: {deletion_summary['tokens_deleted']}"
        )

        return deletion_summary

    @staticmethod
    async def anonymize_specific_claim(
        session: AsyncSession,
        claim_id: UUID,
        reason: str = "7-year retention policy"
    ) -> Dict[str, Any]:
        """
        Anonymize a specific claim after retention period (GDPR Article 5.1.e).
        PII is removed but statistical data is preserved for reporting.
        """
        from app.services.nextcloud_service import NextcloudService

        claim = await session.get(Claim, claim_id, options=[
            selectinload(Claim.passengers),
            selectinload(Claim.claim_notes),
            selectinload(Claim.status_history),
            selectinload(Claim.files)
        ], populate_existing=True)

        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        summary = {
            "claim_id": str(claim_id),
            "files_deleted": 0,
            "passengers_anonymized": 0,
            "notes_anonymized": 0,
            "events_scrubbed": 0
        }

        # 1. Delete files from Nextcloud and database
        nextcloud = NextcloudService()
        for file in claim.files:
            try:
                if file.storage_path:
                    await nextcloud.delete_file(file.storage_path)
                    summary["files_deleted"] += 1
            except Exception as e:
                logger.error(f"Failed to delete file {file.id} from Nextcloud: {e}")
            
            await session.delete(file)

        # 2. Anonymize claim fields (clear high-entropy PII)
        claim.booking_reference = None
        claim.ticket_number = None
        claim.terms_acceptance_ip = "0.0.0.0"
        claim.privacy_consent_ip = "0.0.0.0"
        claim.notes = f"ANONYMIZED - {reason}"
        
        # 3. Anonymize linked passengers
        for passenger in claim.passengers:
            passenger.first_name = "DELETED"
            passenger.last_name = "USER"
            passenger.email = f"deleted_p_{passenger.id}@deleted.local"
            passenger.ticket_number = None
            summary["passengers_anonymized"] += 1

        # 4. Scrub notes
        for note in claim.claim_notes:
            note.note_text = f"DELETED - {reason}"
            summary["notes_anonymized"] += 1

        # 5. Scrub status history
        for history in claim.status_history:
            history.change_reason = "DELETED"

        # 6. Scrub analytics events for this claim
        result = await session.execute(
            update(ClaimEvent)
            .where(ClaimEvent.claim_id == claim_id)
            .values(ip_address="0.0.0.0", event_data=None)
        )
        summary["events_scrubbed"] = result.rowcount

        logger.info(f"Successfully anonymized claim {claim_id} ({reason})")
        return summary

    @staticmethod
    async def get_expired_claims(
        session: AsyncSession,
        years: int = 7
    ):
        """
        Identify claims older than specified years that are eligible for purge.
        Eligible: Finished status (paid, rejected, withdrawn) AND not locked.
        """
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=years * 365.25)

        # Build query for eligible claims
        query = select(Claim).where(
            Claim.updated_at < cutoff_date,
            Claim.status.in_([
                Claim.STATUS_PAID,
                Claim.STATUS_REJECTED,
                Claim.STATUS_WITHDRAWN,
                Claim.STATUS_CLOSED,
                Claim.STATUS_ABANDONED
            ]),
            Claim.is_retention_locked == False,
            Claim.is_legal_proceeding == False
        )

        result = await session.execute(query)
        return result.scalars().all()
