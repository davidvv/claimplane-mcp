"""Claims API endpoints."""
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Claim, Customer, ClaimFile
from app.repositories import ClaimRepository, CustomerRepository
from app.repositories.file_repository import FileRepository
from app.schemas import (
    ClaimCreateSchema,
    ClaimResponseSchema,
    ClaimRequestSchema,
    ClaimSubmitResponseSchema,
    ClaimUpdateSchema,
    ClaimPatchSchema,
    ClaimDraftSchema,
    ClaimDraftResponseSchema,
    ClaimDraftUpdateSchema,
    FileResponseSchema,
    SignatureRequest
)
from app.services.auth_service import AuthService
from app.services.file_service import FileService, get_file_service
from app.services.claim_draft_service import ClaimDraftService
from app.tasks.claim_tasks import send_claim_submitted_email
from app.config import config
from app.dependencies.auth import get_current_user, get_optional_current_user, get_current_user_with_claim_access


def validate_no_html(value: Optional[str]) -> Optional[str]:
    """Validate that string does not contain HTML tags to prevent XSS."""
    if value and ('<' in value or '>' in value):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="HTML tags are not allowed in description field"
        )
    return value
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claims", tags=["claims"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


def verify_claim_access(claim: Claim, current_user: Customer, token_claim_id: Optional[UUID] = None) -> None:
    """
    Verify that the current user has access to the claim.
    Admins and superadmins can access all claims.
    Customers can access their own claims OR claims via magic link (token_claim_id).

    Args:
        claim: Claim to verify access for
        current_user: Currently authenticated user
        token_claim_id: Optional claim ID from JWT token (magic link access)

    Raises:
        HTTPException: 403 if user doesn't have access
    """
    # Admins can access all claims
    if current_user.role in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
        return

    # Magic link holders can access the specific claim
    if token_claim_id and claim.id == token_claim_id:
        return

    # Customers can only access their own claims
    if claim.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own claims"
        )


@router.post("/", response_model=ClaimResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: ClaimCreateSchema,
    request: Request,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """
    Create a new claim for the authenticated user.

    Requires authentication via JWT token.

    Args:
        claim_data: Claim creation data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created claim data

    Raises:
        HTTPException: If validation fails
    """
    claim_repo = ClaimRepository(db)

    # Create claim for the authenticated user
    # Admins can create claims for other customers if customer_id is specified
    customer_id = claim_data.customer_id if current_user.role in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN] else current_user.id

    # If admin specified a different customer, verify that customer exists
    if customer_id != current_user.id:
        customer_repo = CustomerRepository(db)
        customer = await customer_repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found"
            )
    else:
        customer = current_user

    # Create claim
    flight_data = claim_data.flight_info

    # Get client IP for terms acceptance tracking (if applicable)
    from datetime import datetime, timezone
    ip_address, _ = get_client_info(request)

    claim = await claim_repo.create_claim(
        customer_id=customer_id,
        flight_number=flight_data.flight_number,
        airline=flight_data.airline,
        departure_date=flight_data.departure_date,
        departure_airport=flight_data.departure_airport,
        arrival_airport=flight_data.arrival_airport,
        incident_type=claim_data.incident_type,
        notes=claim_data.notes,
        booking_reference=getattr(claim_data, 'booking_reference', None),
        ticket_number=getattr(claim_data, 'ticket_number', None),
        terms_accepted_at=datetime.now(timezone.utc),
        terms_acceptance_ip=ip_address
    )

    # Send claim submitted email notification (Phase 2)
    if config.NOTIFICATIONS_ENABLED and customer:
        try:
            # Get client info
            ip_address, user_agent = get_client_info(request)

            # Create magic link token
            magic_token, _ = await AuthService.create_magic_link_token(
                session=db,
                user_id=customer.id,
                claim_id=claim.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            await db.commit()

            # Trigger async email task with magic link token
            send_claim_submitted_email.delay(
                customer_email=customer.email,
                customer_name=f"{customer.first_name} {customer.last_name}",
                claim_id=str(claim.id),
                flight_number=claim.flight_number,
                airline=claim.airline,
                magic_link_token=magic_token
            )
            logger.info(f"Claim submitted email task queued for customer {customer.email}")
        except Exception as e:
            # Don't fail the API request if email queueing fails
            logger.error(f"Failed to queue claim submitted email: {str(e)}")

    return ClaimResponseSchema.from_orm(claim)


@router.post("/draft", response_model=ClaimDraftResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_draft_claim(
    draft_data: ClaimDraftSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ClaimDraftResponseSchema:
    """
    Create a draft claim after eligibility check (Step 2).

    This enables progressive file upload before form completion.
    No authentication required - anyone with a valid email can create a draft.

    The access token is returned immediately for use in the current browser session.
    A magic link will be sent to the email after 30 minutes of inactivity
    for abandoned cart recovery.

    Args:
        draft_data: Draft claim data with email and flight info
        request: FastAPI request object

    Returns:
        Draft claim ID and access token for immediate file upload

    Raises:
        HTTPException: If validation fails
    """
    try:
        ip_address, user_agent = get_client_info(request)
        session_id = request.headers.get("x-session-id")

        draft_service = ClaimDraftService(db)
        flight_data = draft_data.flight_info

        claim, customer, access_token = await draft_service.create_draft(
            email=draft_data.email,
            flight_number=flight_data.flight_number,
            airline=flight_data.airline,
            departure_date=flight_data.departure_date,
            departure_airport=flight_data.departure_airport,
            arrival_airport=flight_data.arrival_airport,
            incident_type=draft_data.incident_type,
            compensation_amount=float(draft_data.compensation_amount) if draft_data.compensation_amount else None,
            currency=draft_data.currency or "EUR",
            boarding_pass_file_id=draft_data.boarding_pass_file_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )

        logger.info(f"Draft claim created: {claim.id} for customer {customer.id}")

        return ClaimDraftResponseSchema(
            claimId=claim.id,
            customerId=customer.id,
            accessToken=access_token,
            tokenType="bearer",
            compensationAmount=claim.compensation_amount,
            currency=claim.currency or "EUR"
        )

    except ValueError as e:
        logger.error(f"Validation error in draft claim creation: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in draft claim creation: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating draft claim"
        )


@router.post("/submit", response_model=ClaimSubmitResponseSchema, status_code=status.HTTP_201_CREATED)
async def submit_claim_with_customer(
    claim_request: ClaimRequestSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ClaimSubmitResponseSchema:
    """
    Submit a claim with customer information.

    If claim_id is provided, finalizes an existing draft claim.
    Otherwise, creates a new claim from scratch.

    Returns an access token for immediate authentication.

    Args:
        claim_request: Claim request with customer and flight info
        request: FastAPI request object
        db: Database session

    Returns:
        Created/finalized claim data with access token

    Raises:
        HTTPException: If validation fails
    """
    from datetime import datetime, timezone

    ip_address, user_agent = get_client_info(request)
    session_id = request.headers.get("x-session-id")
    draft_service = ClaimDraftService(db)

    try:
        customer_repo = CustomerRepository(db)
        claim_repo = ClaimRepository(db)
        customer_data = claim_request.customer_info
        flight_data = claim_request.flight_info

        # Check if we're finalizing a draft
        if claim_request.claim_id:
            logger.info(f"Finalizing draft claim: {claim_request.claim_id}")

            # Use draft service to finalize
            address = customer_data.address
            claim, customer = await draft_service.finalize_draft(
                claim_id=claim_request.claim_id,
                customer_email=customer_data.email,
                first_name=customer_data.first_name,
                last_name=customer_data.last_name,
                phone=customer_data.phone,
                street=address.street if address else None,
                city=address.city if address else None,
                postal_code=address.postal_code if address else None,
                country=address.country if address else None,
                notes=claim_request.notes,
                booking_reference=claim_request.booking_reference,
                ticket_number=claim_request.ticket_number,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            logger.info(f"Draft claim {claim.id} finalized")

        else:
            # Original flow: Create new customer and claim
            logger.info(f"Creating new claim (no draft)")

            customer = await customer_repo.get_by_email(customer_data.email)

            if not customer:
                logger.info(f"Creating new customer: {customer_data.email}")
                address_data = customer_data.address.dict() if customer_data.address else {}
                customer = await customer_repo.create_customer(
                    email=customer_data.email,
                    first_name=customer_data.first_name,
                    last_name=customer_data.last_name,
                    phone=customer_data.phone,
                    **address_data
                )
                logger.info(f"Customer created: {customer.id}")

            claim = await claim_repo.create_claim(
                customer_id=customer.id,
                flight_number=flight_data.flight_number,
                airline=flight_data.airline,
                departure_date=flight_data.departure_date,
                departure_airport=flight_data.departure_airport,
                arrival_airport=flight_data.arrival_airport,
                incident_type=claim_request.incident_type,
                notes=claim_request.notes,
                booking_reference=claim_request.booking_reference,
                ticket_number=claim_request.ticket_number,
                terms_accepted_at=datetime.now(timezone.utc),
                terms_acceptance_ip=ip_address
            )
            logger.info(f"Claim created: {claim.id}")

            await db.commit()
            logger.info(f"Claim {claim.id} committed to database")

            # Log analytics event for new claims
            await draft_service.log_event(
                event_type="claim_submitted",
                claim_id=claim.id,
                customer_id=customer.id,
                event_data={"from_draft": False},
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )

        # Flight verification (for both draft and new claims)
        try:
            from app.services.flight_data_service import FlightDataService

            logger.info(f"Starting flight verification for claim {claim.id}")
            enriched_data = await FlightDataService.verify_and_enrich_claim(
                session=db,
                claim=claim,
                user_id=customer.id,
                force_refresh=False
            )

            if enriched_data.get("verified"):
                logger.info(f"Flight verified for claim {claim.id}")
                if enriched_data.get("compensation_amount") is not None:
                    claim.calculated_compensation = enriched_data["compensation_amount"]
                if enriched_data.get("distance_km") is not None:
                    claim.flight_distance_km = enriched_data["distance_km"]
                if enriched_data.get("delay_hours") is not None:
                    claim.delay_hours = enriched_data["delay_hours"]
                await db.commit()
            else:
                logger.warning(f"Flight not verified for claim {claim.id}")

        except Exception as e:
            logger.error(f"Flight verification failed for claim {claim.id}: {str(e)}")

    except ValueError as e:
        logger.error(f"Validation error in claim submission: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in claim submission: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while submitting your claim"
        )

    # Send claim submitted email notification
    if config.NOTIFICATIONS_ENABLED and customer:
        try:
            magic_token, _ = await AuthService.create_magic_link_token(
                session=db,
                user_id=customer.id,
                claim_id=claim.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            await db.commit()

            send_claim_submitted_email.delay(
                customer_email=customer.email,
                customer_name=f"{customer.first_name} {customer.last_name}",
                claim_id=str(claim.id),
                flight_number=claim.flight_number,
                airline=claim.airline,
                magic_link_token=magic_token
            )
            logger.info(f"Claim submitted email task queued for customer {customer.email}")
        except Exception as e:
            logger.error(f"Failed to queue claim submitted email: {str(e)}")

    # Generate access token
    access_token = AuthService.create_access_token(
        user_id=str(customer.id),
        email=customer.email,
        role=customer.role,
        claim_id=str(claim.id)
    )
    logger.info(f"Generated access token for customer {customer.id} with claim {claim.id}")

    # Refresh claim to get latest state
    await db.refresh(claim)

    return ClaimSubmitResponseSchema(
        claim=ClaimResponseSchema.from_orm(claim),
        accessToken=access_token,
        tokenType="bearer"
    )


@router.patch("/{claim_id}/draft", response_model=ClaimResponseSchema)
async def update_draft_claim(
    claim_id: UUID,
    update_data: Dict[str, Any],
    request: Request,
    user_data: tuple = Depends(get_current_user_with_claim_access),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """
    Partially update a draft claim (auto-save).
    
    Requires authentication (JWT or draft token).
    """
    current_user, token_claim_id = user_data
    
    try:
        ip_address, user_agent = get_client_info(request)
        session_id = request.headers.get("x-session-id")
        
        logger.info(f"[update_draft_claim] Updating claim {claim_id}")
        
        draft_service = ClaimDraftService(db)
        
        # Verify access
        claim_repo = ClaimRepository(db)
        claim = await claim_repo.get_by_id(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        verify_claim_access(claim, current_user, token_claim_id)
        
        # Manually validate and transform data
        data_dict = update_data.copy()
        
        # Handle aliases and nested objects
        if 'postalCode' in data_dict:
            data_dict['postal_code'] = data_dict.pop('postalCode')
        
        if 'incidentType' in data_dict:
            data_dict['incident_type'] = data_dict.pop('incidentType')

        if 'bookingReference' in data_dict:
            data_dict['booking_reference'] = data_dict.pop('bookingReference')

        if 'boardingPassFileId' in data_dict:
            data_dict['boarding_pass_file_id'] = data_dict.pop('boardingPassFileId')

        # Robust passenger transformation
        if 'passengers' in data_dict and isinstance(data_dict['passengers'], list):
            valid_passengers = []
            for p in data_dict['passengers']:
                if not isinstance(p, dict):
                    continue
                
                # Transform aliases
                p_transformed = p.copy()
                if 'firstName' in p_transformed:
                    p_transformed['first_name'] = p_transformed.pop('firstName')
                if 'lastName' in p_transformed:
                    p_transformed['last_name'] = p_transformed.pop('lastName')
                if 'ticketNumber' in p_transformed:
                    p_transformed['ticket_number'] = p_transformed.pop('ticketNumber')
                
                # Skip if essential fields are missing to prevent DB errors
                if not p_transformed.get('first_name') or not p_transformed.get('last_name'):
                    logger.warning(f"[update_draft_claim] Skipping invalid passenger record: {p}")
                    continue
                    
                valid_passengers.append(p_transformed)
            
            data_dict['passengers'] = valid_passengers

        updated_claim = await draft_service.update_draft(
            claim_id=claim_id,
            update_data=data_dict,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        
        return ClaimResponseSchema.from_orm(updated_claim)

    except ValueError as e:
        logger.error(f"Validation error in draft claim update for {claim_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        # Re-raise HTTP exceptions (like 404, 403)
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in draft claim update for {claim_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while updating draft claim")


@router.get("/{claim_id}", response_model=ClaimResponseSchema)
async def get_claim(
    claim_id: UUID,
    include_details: bool = Query(False, description="Include passengers and contact info (for draft resume)"),
    user_data: tuple = Depends(get_current_user_with_claim_access),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """
    Get claim by ID.

    Requires authentication. Customers can access their own claims or claims via magic link.
    Admins and superadmins can access all claims.

    Args:
        claim_id: Claim UUID
        include_details: If True, include passengers and contact info (useful for draft resume)
        user_data: Tuple of (current_user, token_claim_id) from JWT
        db: Database session

    Returns:
        Claim data

    Raises:
        HTTPException: If claim not found or access denied
    """
    # Validate description for XSS
    description = validate_no_html(description)
    
    # Verify claim exists
    claim_repo = ClaimRepository(db)
    claim = await claim_repo.get_by_id(claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )

    # Verify access
    verify_claim_access(claim, current_user)

    # Get documents
    file_repo = FileRepository(db)
    files = await file_repo.get_by_claim_id(claim_id, include_deleted=False)

    logger.info(f"[list_claim_documents] Found {len(files)} documents for claim {claim_id}")
    return [FileResponseSchema.model_validate(f) for f in files]


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(
    claim_id: UUID,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a claim.

    Customers can only delete their own claims, and ONLY if they are in DRAFT status.
    Admins can delete any claim.

    Args:
        claim_id: ID of the claim to delete
        current_user: Currently authenticated user
        db: Database session

    Raises:
        HTTPException: If claim not found, access denied, or cannot be deleted
    """
    claim_repo = ClaimRepository(db)
    claim = await claim_repo.get_by_id(claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )

    # Verify access
    verify_claim_access(claim, current_user)

    # Customers can only delete DRAFT claims
    if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
        if claim.status != Claim.STATUS_DRAFT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete draft claims. Please contact support to cancel submitted claims."
            )

    await claim_repo.delete(claim)
    logger.info(f"Deleted claim {claim_id}")


@router.post("/{claim_id}/documents", response_model=FileResponseSchema, status_code=status.HTTP_201_CREATED)
async def upload_claim_document(
    claim_id: UUID,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document for a specific claim.

    Customers can only upload documents to their own claims.
    Admins can upload documents to any claim.

    Args:
        claim_id: ID of the claim to attach document to
        file: File to upload
        document_type: Type of document (boarding_pass, id_document, etc.)
        description: Optional description
        current_user: Currently authenticated user
        db: Database session

    Returns:
        FileResponseSchema: Uploaded file information

    Raises:
        HTTPException: If claim not found or access denied
    """
    # Verify claim exists
    claim_repo = ClaimRepository(db)
    claim = await claim_repo.get_by_id(claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )

    # Verify access
    verify_claim_access(claim, current_user)

    # Upload file
    try:
        logger.info(f"[upload_claim_document] Uploading {file.filename} for claim {claim_id}")
        file_service = get_file_service(db)
        file_info = await file_service.upload_file(
            file=file,
            claim_id=str(claim_id),
            customer_id=str(current_user.id),
            document_type=document_type,
            description=description,
            access_level="private"
        )

        # Commit the transaction to persist the file record
        await db.commit()

        logger.info(f"[upload_claim_document] Successfully uploaded file {file_info.id}")
        return FileResponseSchema.model_validate(file_info)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[upload_claim_document] Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.post("/ocr-boarding-pass", status_code=status.HTTP_200_OK)
async def extract_boarding_pass_data(
    file: UploadFile = File(...),
    current_user: Customer = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload boarding pass image and extract flight details via OCR.

    No claim required - returns extracted data for form pre-filling.
    Supports: JPEG, PNG, PDF (max 10MB)

    Args:
        file: Boarding pass image file
        current_user: Optionally authenticated user
        db: Database session

    Returns:
        OCRResponseSchema with extracted flight data and confidence scores

    Raises:
        HTTPException: 400 if file invalid, 500 if OCR fails
    """
    from app.schemas.ocr_schemas import OCRResponseSchema, BoardingPassDataSchema, FieldConfidenceSchema
    from app.services.ocr_service import ocr_service
    from app.services.email_parser_service import EmailParserService

    # Validate file type
    allowed_mimetypes = [
        "image/jpeg", "image/png", "image/webp", "application/pdf",
        "message/rfc822", "application/octet-stream"  # Added support for .eml
    ]
    content_type = file.content_type or "application/octet-stream"

    if content_type not in allowed_mimetypes and not file.filename.lower().endswith('.eml'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{content_type}'. Allowed types: JPEG, PNG, WebP, PDF, EML"
        )

    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error(f"[ocr-boarding-pass] Failed to read file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file"
        )

    # Validate file size (10MB limit)
    max_size = 10 * 1024 * 1024
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds 10MB limit (got {len(file_content) / 1024 / 1024:.1f}MB)"
        )

    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    # Handle .eml files (Email Processing)
    if content_type == "message/rfc822" or file.filename.lower().endswith('.eml'):
        try:
            logger.info(f"[ocr-email] Processing email file: {file.filename}")
            import time
            start_time = time.time()
            
            # Parse email structure
            email_data = EmailParserService.parse_eml(file_content)
            
            # Extract flight data using Gemini
            extracted = await ocr_service.extract_from_email_text(
                email_subject=email_data["subject"],
                email_body=email_data["body"]
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return OCRResponseSchema(
                success=True,
                data=BoardingPassDataSchema(**extracted),
                raw_text=email_data["body"][:2000],  # Return first 2KB of text for context
                confidence_score=0.95,  # Email text is usually very accurate
                field_confidence={k: 0.95 for k in extracted if extracted[k]},
                errors=[],
                warnings=[],
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"[ocr-email] Email processing failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process email file: {str(e)}"
            )

    # Run OCR extraction (Images/PDFs)
    try:
        logger.info(f"[ocr-boarding-pass] Processing file: {file.filename} ({content_type}, {len(file_content)} bytes)")

        result = await ocr_service.extract_boarding_pass_data(
            file_content=file_content,
            mime_type=content_type,
            preprocessing=True
        )

        # Build response
        response = OCRResponseSchema(
            success=result.get("success", False),
            data=BoardingPassDataSchema(**result["data"]) if result.get("data") else None,
            raw_text=result.get("raw_text", ""),
            confidence_score=result.get("confidence_score", 0.0),
            field_confidence=FieldConfidenceSchema(**result["field_confidence"]) if result.get("field_confidence") else None,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            processing_time_ms=result.get("processing_time_ms")
        )

        # Save file to temp storage for later linking to claim
        uploaded_file_id = None
        try:
            from app.services.file_service import get_file_service
            file_service = get_file_service(db)
            
            file_record = await file_service.upload_orphan_file(
                file_content=file_content,
                filename=file.filename,
                mime_type=content_type,
                document_type="boarding_pass",
                customer_id=str(current_user.id) if current_user else None
            )
            await db.commit()
            uploaded_file_id = str(file_record.id)
            
            logger.info(f"[ocr-boarding-pass] File saved to temp storage: {uploaded_file_id}")
        except Exception as save_error:
            logger.error(f"[ocr-boarding-pass] Failed to save file to temp storage for {file.filename}: {str(save_error)}", exc_info=True)
            # Continue - OCR data is still valuable even if file save fails
            # User can manually upload boarding pass in Step 3 if needed

        # Add file ID to response
        response.uploaded_file_id = uploaded_file_id

        logger.info(
            f"[ocr-boarding-pass] Extraction complete: success={response.success}, "
            f"confidence={response.confidence_score}, time={response.processing_time_ms}ms, "
            f"file_id={uploaded_file_id}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ocr-boarding-pass] OCR extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract boarding pass data. Please try again or enter details manually."
        )