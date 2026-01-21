"""Claim draft service for managing the draft claim workflow.

This service handles:
- Draft claim creation (Step 2 - after eligibility check)
- Progressive file upload support
- Draft claim finalization (Step 4 - submit)
- Analytics event logging
- Activity tracking for abandonment detection
"""
import logging
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Claim, Customer, ClaimEvent
from app.repositories import ClaimRepository, CustomerRepository, ClaimEventRepository
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class ClaimDraftService:
    """Service for managing draft claims and the claim submission workflow."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.claim_repo = ClaimRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.event_repo = ClaimEventRepository(session)

    async def create_draft(
        self,
        email: str,
        flight_number: str,
        airline: str,
        departure_date,
        departure_airport: str,
        arrival_airport: str,
        incident_type: str,
        compensation_amount: Optional[float] = None,
        currency: str = "EUR",
        boarding_pass_file_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Tuple[Claim, Customer, str]:
        """Create a draft claim and return claim, customer, and access token.

        This is called after Step 2 (eligibility check) to:
        - Enable progressive file upload
        - Allow abandoned cart recovery
        - Track user journey analytics

        Args:
            email: Customer email address
            flight_number: Flight number
            airline: Airline name
            departure_date: Date of departure
            departure_airport: IATA code
            arrival_airport: IATA code
            incident_type: Type of incident (delay, cancellation, etc.)
            compensation_amount: Estimated compensation
            currency: Currency code (default EUR)
            ip_address: Client IP for logging
            user_agent: Client user agent for logging
            session_id: Browser session ID for analytics

        Returns:
            Tuple of (claim, customer, access_token)
        """
        # Find or create customer
        customer = await self.customer_repo.get_by_email(email)

        if not customer:
            logger.info(f"Creating new customer for draft claim: {email}")
            customer = await self.customer_repo.create_customer(
                email=email,
                first_name="",  # Will be filled in Step 3
                last_name="",   # Will be filled in Step 3
                phone=None,
                street=None,
                city=None,
                postal_code=None,
                country=None
            )
            logger.info(f"Customer created: {customer.id}")

        # Create draft claim
        logger.info(f"Creating draft claim for customer {customer.id}")
        claim = await self.claim_repo.create_draft_claim(
            customer_id=customer.id,
            flight_number=flight_number,
            airline=airline,
            departure_date=departure_date,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            incident_type=incident_type,
            compensation_amount=compensation_amount,
            currency=currency,
            current_step=2
        )
        logger.info(f"Draft claim created: {claim.id}")

        # Link boarding pass if provided
        if boarding_pass_file_id:
            try:
                from app.services.file_service import get_file_service
                file_service = get_file_service(self.session)
                await file_service.link_file_to_claim(
                    file_id=UUID(boarding_pass_file_id),
                    claim_id=claim.id,
                    customer_id=customer.id
                )
                logger.info(f"Linked boarding pass {boarding_pass_file_id} to claim {claim.id}")
            except Exception as e:
                logger.error(f"Failed to link boarding pass to claim {claim.id}: {str(e)}")

        # Commit the draft
        await self.session.commit()
        await self.session.refresh(claim)
        await self.session.refresh(customer)

        # Log analytics event
        await self.log_event(
            event_type=ClaimEvent.EVENT_DRAFT_CREATED,
            claim_id=claim.id,
            customer_id=customer.id,
            event_data={
                "flight_number": flight_number,
                "incident_type": incident_type,
                "compensation_amount": float(compensation_amount) if compensation_amount else None,
                "currency": currency
            },
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )

        # Create access token for immediate use (progressive upload)
        access_token = AuthService.create_access_token(
            user_id=str(customer.id),
            email=customer.email,
            role=customer.role,
            claim_id=str(claim.id)
        )

        logger.info(f"Draft claim {claim.id} created with access token")
        return claim, customer, access_token

    async def finalize_draft(
        self,
        claim_id: UUID,
        customer_email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        street: Optional[str] = None,
        city: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        notes: Optional[str] = None,
        booking_reference: Optional[str] = None,
        ticket_number: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Tuple[Claim, Customer]:
        """Finalize a draft claim to submitted status.

        This is called at Step 4 (review & submit) to:
        - Update customer with full personal info
        - Change claim status from draft to submitted
        - Record terms acceptance
        - Trigger confirmation email

        Args:
            claim_id: Draft claim UUID
            customer_email: Email address (for ownership verification)
            first_name: Customer first name
            last_name: Customer last name
            phone: Customer phone number
            street: Street address
            city: City
            postal_code: Postal code
            country: Country
            notes: Additional notes
            booking_reference: Airline booking reference
            ticket_number: Ticket number
            ip_address: Client IP for terms acceptance
            user_agent: Client user agent
            session_id: Browser session ID

        Returns:
            Tuple of (finalized_claim, customer)

        Raises:
            ValueError: If claim not found, not a draft, or email doesn't match
        """
        # Get the draft claim
        claim = await self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        if claim.status != Claim.STATUS_DRAFT:
            raise ValueError(f"Claim {claim_id} is not a draft (status: {claim.status})")

        # Get the customer
        customer = await self.customer_repo.get_by_id(claim.customer_id)
        if not customer:
            raise ValueError(f"Customer not found for claim {claim_id}")

        # Verify ownership - email must match
        if customer.email.lower() != customer_email.lower():
            logger.warning(
                f"Draft finalization rejected: email mismatch. "
                f"Draft owner: {customer.email}, Submitted: {customer_email}"
            )
            raise ValueError("Email does not match draft claim owner")

        # Update customer with full information
        logger.info(f"Updating customer {customer.id} with full information")
        customer = await self.customer_repo.update_customer(
            customer_id=customer.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            street=street,
            city=city,
            postal_code=postal_code,
            country=country
        )

        # Finalize the draft claim
        logger.info(f"Finalizing draft claim {claim.id}")
        now = datetime.now(timezone.utc)
        claim = await self.claim_repo.finalize_draft(
            claim_id=claim_id,
            notes=notes,
            booking_reference=booking_reference,
            ticket_number=ticket_number,
            terms_accepted_at=now,
            terms_acceptance_ip=ip_address
        )

        # Commit changes
        await self.session.commit()
        await self.session.refresh(claim)
        await self.session.refresh(customer)

        # Log analytics event
        await self.log_event(
            event_type=ClaimEvent.EVENT_CLAIM_SUBMITTED,
            claim_id=claim.id,
            customer_id=customer.id,
            event_data={
                "from_draft": True,
                "booking_reference": booking_reference,
                "has_notes": bool(notes)
            },
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )

        logger.info(f"Draft claim {claim.id} finalized to submitted status")
        return claim, customer

    async def update_activity(
        self,
        claim_id: UUID,
        current_step: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[Claim]:
        """Update claim activity timestamp and optionally step.

        Called on any user action to reset the abandonment timer.

        Args:
            claim_id: Claim UUID
            current_step: Current wizard step (2, 3, or 4)
            ip_address: Client IP
            user_agent: Client user agent
            session_id: Browser session ID

        Returns:
            Updated claim or None if not found
        """
        claim = await self.claim_repo.update_activity(claim_id)
        if not claim:
            return None

        if current_step is not None:
            claim.current_step = current_step
            await self.session.flush()

        # Log step completion if step changed
        if current_step is not None:
            await self.log_event(
                event_type=ClaimEvent.EVENT_STEP_COMPLETED,
                claim_id=claim_id,
                customer_id=claim.customer_id,
                event_data={"step": current_step},
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )

        return claim

    async def log_event(
        self,
        event_type: str,
        claim_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ClaimEvent:
        """Log an analytics event.

        Args:
            event_type: Type of event from ClaimEvent.EVENT_TYPES
            claim_id: Optional claim UUID
            customer_id: Optional customer UUID
            event_data: Optional event-specific data
            ip_address: Client IP
            user_agent: Client user agent
            session_id: Browser session ID

        Returns:
            Created ClaimEvent
        """
        event = await self.event_repo.log_event(
            event_type=event_type,
            claim_id=claim_id,
            customer_id=customer_id,
            event_data=event_data,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        await self.session.flush()
        return event

    async def log_file_upload(
        self,
        claim_id: UUID,
        customer_id: UUID,
        filename: str,
        document_type: str,
        file_size: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ClaimEvent:
        """Log a file upload event."""
        return await self.log_event(
            event_type=ClaimEvent.EVENT_FILE_UPLOADED,
            claim_id=claim_id,
            customer_id=customer_id,
            event_data={
                "filename": filename,
                "document_type": document_type,
                "file_size": file_size
            },
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )

    async def log_reminder_sent(
        self,
        claim_id: UUID,
        customer_id: UUID,
        reminder_number: int
    ) -> ClaimEvent:
        """Log that a reminder email was sent."""
        return await self.log_event(
            event_type=ClaimEvent.EVENT_REMINDER_SENT,
            claim_id=claim_id,
            customer_id=customer_id,
            event_data={"reminder_number": reminder_number}
        )

    async def log_claim_resumed(
        self,
        claim_id: UUID,
        customer_id: UUID,
        from_reminder: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ClaimEvent:
        """Log that a user resumed their draft claim."""
        return await self.log_event(
            event_type=ClaimEvent.EVENT_CLAIM_RESUMED,
            claim_id=claim_id,
            customer_id=customer_id,
            event_data={"from_reminder": from_reminder},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )

    async def update_draft(
        self,
        claim_id: UUID,
        update_data: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Claim:
        """Partially update a draft claim (auto-save)."""
        # Get the draft claim
        claim = await self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        if claim.status != Claim.STATUS_DRAFT:
            raise ValueError(f"Claim {claim_id} is not a draft (status: {claim.status})")

        # Update customer if contact info provided
        customer = await self.customer_repo.get_by_id(claim.customer_id)
        if not customer:
            raise ValueError(f"Customer not found for claim {claim_id}")

        customer_updates = {}
        for field in ['email', 'first_name', 'last_name', 'phone', 'street', 'city', 'postal_code', 'country']:
            if field in update_data and update_data[field] is not None:
                customer_updates[field] = update_data[field]
        
        if customer_updates:
            await self.customer_repo.update_customer(customer.id, **customer_updates)

        # Update claim info
        claim_updates = {}
        for field in ['booking_reference', 'incident_type', 'notes']:
            if field in update_data and update_data[field] is not None:
                claim_updates[field] = update_data[field]
        
        if claim_updates:
            await self.claim_repo.update_claim(claim.id, **claim_updates)

        # Link boarding pass if provided
        if 'boarding_pass_file_id' in update_data and update_data['boarding_pass_file_id']:
            try:
                from app.services.file_service import get_file_service
                file_service = get_file_service(self.session)
                await file_service.link_file_to_claim(
                    file_id=UUID(update_data['boarding_pass_file_id']),
                    claim_id=claim.id,
                    customer_id=claim.customer_id
                )
                logger.info(f"Linked boarding pass {update_data['boarding_pass_file_id']} to claim {claim_id}")
            except Exception as e:
                logger.error(f"Failed to link boarding pass to claim {claim_id}: {str(e)}")

        # Update passengers if provided
        if 'passengers' in update_data and update_data['passengers'] is not None:
            await self.claim_repo.update_passengers(claim.id, update_data['passengers'])

        # Update activity timestamp
        await self.update_activity(claim_id, ip_address=ip_address, user_agent=user_agent, session_id=session_id)

        await self.session.commit()
        await self.session.refresh(claim)
        
        return claim

    async def get_draft_for_resume(
        self,
        claim_id: UUID,
        customer_email: str
    ) -> Optional[Dict[str, Any]]:
        """Get draft claim data for resuming the form.

        Verifies email ownership before returning data.

        Args:
            claim_id: Draft claim UUID
            customer_email: Email for ownership verification

        Returns:
            Dict with claim and customer data for form pre-population,
            or None if not found or not owned by this email
        """
        claim = await self.claim_repo.get_by_id(claim_id)
        if not claim:
            return None

        if claim.status != Claim.STATUS_DRAFT:
            return None  # Only return data for drafts

        customer = await self.customer_repo.get_by_id(claim.customer_id)
        if not customer:
            return None

        # Verify ownership
        if customer.email.lower() != customer_email.lower():
            logger.warning(
                f"Draft resume rejected: email mismatch. "
                f"Draft owner: {customer.email}, Requested: {customer_email}"
            )
            return None

        return {
            "claim": {
                "id": str(claim.id),
                "flight_number": claim.flight_number,
                "airline": claim.airline,
                "departure_date": claim.departure_date.isoformat() if claim.departure_date else None,
                "departure_airport": claim.departure_airport,
                "arrival_airport": claim.arrival_airport,
                "incident_type": claim.incident_type,
                "compensation_amount": float(claim.compensation_amount) if claim.compensation_amount else None,
                "currency": claim.currency,
                "current_step": claim.current_step or 3,
            },
            "customer": {
                "email": customer.email,
                "first_name": customer.first_name or "",
                "last_name": customer.last_name or "",
                "phone": customer.phone or "",
                "street": customer.street or "",
                "city": customer.city or "",
                "postal_code": customer.postal_code or "",
                "country": customer.country or "",
            }
        }
