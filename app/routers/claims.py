"""Claims API endpoints."""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form, Query
from sqlalchemy import select, or_, and_, bindparam, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Claim, Customer, ClaimFile, Passenger
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
from app.dependencies.rate_limit import limiter
from app.dependencies.auth import get_current_user, get_optional_current_user, get_current_user_with_claim_access
from app.utils.db_encryption import generate_blind_index

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claims", tags=["claims"])


def validate_no_html(value: Optional[str]) -> Optional[str]:
    """Validate that string does not contain HTML tags to prevent XSS."""
    if value and ('<' in value or '>' in value):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="HTML tags are not allowed in description field"
        )
    return value


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
@limiter.limit("5/hour")
async def create_claim(
    claim_data: ClaimCreateSchema,
    request: Request,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """Create a new claim for the authenticated user."""
    claim_repo = ClaimRepository(db)

    # Create claim for the authenticated user or specified customer if admin
    customer_id = claim_data.customer_id if current_user.role in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN] else current_user.id

    if customer_id != current_user.id:
        customer_repo = CustomerRepository(db)
        customer = await customer_repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    else:
        customer = current_user

    flight_data = claim_data.flight_info
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
        terms_acceptance_ip=ip_address,
        privacy_consent_at=datetime.now(timezone.utc),
        privacy_consent_ip=ip_address
    )

    # Send claim submitted email notification
    if config.NOTIFICATIONS_ENABLED and customer:
        try:
            ip_address, user_agent = get_client_info(request)
            magic_token, _ = await AuthService.create_magic_link_token(
                session=db, user_id=customer.id, claim_id=claim.id,
                ip_address=ip_address, user_agent=user_agent
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
        except Exception as e:
            logger.error(f"Failed to queue claim submitted email: {str(e)}")

    return ClaimResponseSchema.from_orm(claim)


@router.post("/draft", response_model=ClaimDraftResponseSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def create_draft_claim(
    draft_data: ClaimDraftSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ClaimDraftResponseSchema:
    """Create a draft claim after eligibility check (Step 2)."""
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in draft claim creation: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while creating draft claim")


@router.post("/submit", response_model=ClaimSubmitResponseSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def submit_claim_with_customer(
    claim_request: ClaimRequestSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ClaimSubmitResponseSchema:
    """Submit a claim with customer information or finalize a draft."""
    ip_address, user_agent = get_client_info(request)
    session_id = request.headers.get("x-session-id")
    draft_service = ClaimDraftService(db)

    try:
        customer_repo = CustomerRepository(db)
        claim_repo = ClaimRepository(db)
        customer_data = claim_request.customer_info
        flight_data = claim_request.flight_info

        if claim_request.claim_id:
            # Finalize draft
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
        else:
            # Create new from scratch
            customer = await customer_repo.get_by_email(customer_data.email)
            if not customer:
                address_data = customer_data.address.dict() if customer_data.address else {}
                customer = await customer_repo.create_customer(
                    email=customer_data.email, first_name=customer_data.first_name,
                    last_name=customer_data.last_name, phone=customer_data.phone, **address_data
                )

            claim = await claim_repo.create_claim(
                customer_id=customer.id, flight_number=flight_data.flight_number,
                airline=flight_data.airline, departure_date=flight_data.departure_date,
                departure_airport=flight_data.departure_airport, arrival_airport=flight_data.arrival_airport,
                incident_type=claim_request.incident_type, notes=claim_request.notes,
                booking_reference=claim_request.booking_reference, ticket_number=claim_request.ticket_number,
                terms_accepted_at=datetime.now(timezone.utc), terms_acceptance_ip=ip_address,
                privacy_consent_at=datetime.now(timezone.utc), privacy_consent_ip=ip_address
            )
            await db.commit()

        # Flight verification
        try:
            from app.services.flight_data_service import FlightDataService
            enriched_data = await FlightDataService.verify_and_enrich_claim(
                session=db, claim=claim, user_id=customer.id, force_refresh=False
            )
            if enriched_data.get("verified"):
                if enriched_data.get("compensation_amount") is not None:
                    claim.calculated_compensation = enriched_data["compensation_amount"]
                if enriched_data.get("distance_km") is not None:
                    claim.flight_distance_km = enriched_data["distance_km"]
                if enriched_data.get("delay_hours") is not None:
                    claim.delay_hours = enriched_data["delay_hours"]
                await db.commit()
        except Exception as e:
            logger.error(f"Flight verification failed for claim {claim.id}: {str(e)}")

    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error in claim submission: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while submitting your claim")

    # Send email and generate token
    magic_token, _ = await AuthService.create_magic_link_token(
        session=db, user_id=customer.id, claim_id=claim.id,
        ip_address=ip_address, user_agent=user_agent
    )
    await db.commit()

    send_claim_submitted_email.delay(
        customer_email=customer.email, customer_name=f"{customer.first_name} {customer.last_name}",
        claim_id=str(claim.id), flight_number=claim.flight_number, airline=claim.airline,
        magic_link_token=magic_token
    )

    access_token = AuthService.create_access_token(
        user_id=str(customer.id), email=customer.email, role=customer.role, claim_id=str(claim.id)
    )

    await db.refresh(claim)
    # Ensure relationships are loaded for the response
    claim = await claim_repo.get_by_id_with_details(claim.id)
    return ClaimSubmitResponseSchema(
        claim=ClaimResponseSchema.from_orm(claim, include_details=True), accessToken=access_token, tokenType="bearer"
    )


@router.get("/", response_model=List[ClaimResponseSchema])
async def list_claims(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    customer_id: UUID = None,
    include_drafts: bool = Query(False, description="Include draft claims"),
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ClaimResponseSchema]:
    """List claims with filtering."""
    repo = ClaimRepository(db)

    if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
        customer_id = current_user.id

    if status:
        claims = await repo.get_by_status(status, skip=skip, limit=limit)
        if customer_id:
            claims = [c for c in claims if c.customer_id == customer_id]
    elif customer_id:
        all_claims = await repo.get_by_customer_id(customer_id, skip=skip, limit=limit)
        if include_drafts:
            claims = all_claims
        else:
            claims = [c for c in all_claims if c.status != Claim.STATUS_DRAFT]
    else:
        # Admins
        if include_drafts:
            claims = await repo.get_all(skip=skip, limit=limit)
        else:
            all_claims = await repo.get_all(skip=skip, limit=limit)
            claims = [c for c in all_claims if c.status != Claim.STATUS_DRAFT]

    return [ClaimResponseSchema.from_orm(claim) for claim in claims]


@router.get("/customer/{customer_id}", response_model=List[ClaimResponseSchema])
async def get_customer_claims(
    customer_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ClaimResponseSchema]:
    """Get all claims for a specific customer."""
    if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN] and customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    claim_repo = ClaimRepository(db)
    claims = await claim_repo.get_by_customer_id(customer_id, skip=skip, limit=limit)
    return [ClaimResponseSchema.from_orm(claim) for claim in claims]


@router.patch("/{claim_id}/draft", response_model=ClaimResponseSchema)
async def update_draft_claim(
    claim_id: UUID,
    update_data: ClaimDraftUpdateSchema,
    request: Request,
    user_data: tuple = Depends(get_current_user_with_claim_access),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """Partially update a draft claim (auto-save)."""
    current_user, token_claim_id = user_data
    
    try:
        ip_address, user_agent = get_client_info(request)
        session_id = request.headers.get("x-session-id")
        
        draft_service = ClaimDraftService(db)
        claim_repo = ClaimRepository(db)
        claim = await claim_repo.get_by_id(claim_id)
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        verify_claim_access(claim, current_user, token_claim_id)
        
        # Convert Pydantic model to dict, using internal names (snake_case)
        # exclude_unset=True ensures we only update fields that were actually provided
        data_dict = update_data.dict(exclude_unset=True, by_alias=False)

        updated_claim = await draft_service.update_draft(
            claim_id=claim_id, update_data=data_dict,
            ip_address=ip_address, user_agent=user_agent, session_id=session_id
        )
        return ClaimResponseSchema.from_orm(updated_claim)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in draft update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{claim_id}", response_model=ClaimResponseSchema)
async def get_claim(
    claim_id: UUID,
    include_details: bool = Query(False),
    user_data: tuple = Depends(get_current_user_with_claim_access),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """Get claim by ID."""
    current_user, token_claim_id = user_data
    repo = ClaimRepository(db)
    
    if include_details:
        claim = await repo.get_by_id_with_details(claim_id)
    else:
        claim = await repo.get_by_id(claim_id)

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    verify_claim_access(claim, current_user, token_claim_id)
    return ClaimResponseSchema.from_orm(claim, include_details=include_details)


@router.get("/{claim_id}/verification", response_model=Dict[str, Any])
async def get_claim_verification(
    claim_id: UUID,
    user_data: tuple = Depends(get_current_user_with_claim_access),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Check claim completeness."""
    current_user, token_claim_id = user_data
    repo = ClaimRepository(db)
    claim = await repo.get_by_id(claim_id)

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    verify_claim_access(claim, current_user, token_claim_id)
    
    customer_repo = CustomerRepository(db)
    customer = await customer_repo.get_by_id(claim.customer_id)
    file_repo = FileRepository(db)
    files = await file_repo.get_by_claim_id(claim_id, include_deleted=False)
    
    from app.services.claim_verification_service import ClaimVerificationService
    return ClaimVerificationService.verify_claim(claim, customer, files)


@router.post("/{claim_id}/sign-poa", response_model=FileResponseSchema)
async def sign_power_of_attorney(
    claim_id: UUID,
    signature_data: SignatureRequest,
    request: Request,
    current_user: tuple = Depends(get_current_user_with_claim_access),
    db: AsyncSession = Depends(get_db)
):
    """Sign POA and generate PDF."""
    import base64
    from app.services.poa_service import POAService
    
    current_user_obj, token_claim_id = current_user
    repo = ClaimRepository(db)
    claim = await repo.get_by_id(claim_id)
    if not claim: raise HTTPException(status_code=404, detail="Claim not found")
    verify_claim_access(claim, current_user_obj, token_claim_id)
    
    # Idempotency
    file_repo = FileRepository(db)
    existing_files = await file_repo.get_by_claim_id(claim_id, include_deleted=False)
    existing_poa = next((f for f in existing_files if f.document_type == ClaimFile.DOCUMENT_POWER_OF_ATTORNEY), None)
    if existing_poa: return FileResponseSchema.model_validate(existing_poa)
    
    # Update claim with consent information
    now = datetime.now(timezone.utc)
    ip_address = request.client.host if request.client else "unknown"
    
    claim.terms_accepted_at = now
    claim.terms_acceptance_ip = ip_address
    claim.privacy_consent_at = now
    claim.privacy_consent_ip = ip_address
    
    customer_repo = CustomerRepository(db)
    customer = await customer_repo.get_by_id(claim.customer_id)
    
    try:
        encoded = signature_data.signature_image.split(",", 1)[1] if "," in signature_data.signature_image else signature_data.signature_image
        signature_bytes = base64.b64decode(encoded)
    except:
        raise HTTPException(status_code=400, detail="Invalid signature image")

    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Get passengers
    from sqlalchemy import select
    result = await db.execute(select(Passenger).where(Passenger.claim_id == claim.id))
    all_passengers = result.scalars().all()
    pax_names = ", ".join([f"{p.first_name} {p.last_name}" for p in all_passengers])

    pdf_bytes = POAService.generate_signed_poa(
        flight_number=claim.flight_number,
        flight_date=claim.departure_date.isoformat() if claim.departure_date else "-",
        departure_airport=claim.departure_airport or "-",
        arrival_airport=claim.arrival_airport or "-",
        booking_reference=claim.booking_reference or "N/A",
        primary_passenger_name=f"{customer.first_name} {customer.last_name}",
        additional_passengers=pax_names,
        address=f"{customer.street}, {customer.city}, {customer.country}",
        signer_name=signature_data.signer_name,
        signature_image_bytes=signature_bytes,
        ip_address=ip_address, user_agent=user_agent, signed_at=datetime.now(timezone.utc)
    )

    file_service = get_file_service(db)
    file_record = await file_service.upload_generated_document(
        file_content=pdf_bytes, filename=f"POA_{claim.id}.pdf",
        claim_id=str(claim.id), customer_id=str(customer.id),
        document_type=ClaimFile.DOCUMENT_POWER_OF_ATTORNEY,
        description="Signed Power of Attorney"
    )
    await db.commit()
    return FileResponseSchema.model_validate(file_record)


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(
    claim_id: UUID,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a claim."""
    claim_repo = ClaimRepository(db)
    claim = await claim_repo.get_by_id(claim_id)
    if not claim: raise HTTPException(status_code=404, detail="Claim not found")
    verify_claim_access(claim, current_user)

    if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
        if claim.status != Claim.STATUS_DRAFT:
            raise HTTPException(status_code=403, detail="Only draft claims can be deleted")

    await claim_repo.delete(claim)


@router.post("/{claim_id}/documents", response_model=FileResponseSchema, status_code=status.HTTP_201_CREATED)
async def upload_claim_document(
    claim_id: UUID,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document."""
    description = validate_no_html(description)
    claim_repo = ClaimRepository(db)
    claim = await claim_repo.get_by_id(claim_id)
    if not claim: raise HTTPException(status_code=404, detail="Claim not found")
    verify_claim_access(claim, current_user)

    file_service = get_file_service(db)
    file_info = await file_service.upload_file(
        file=file, claim_id=str(claim_id), customer_id=str(current_user.id),
        document_type=document_type, description=description
    )
    await db.commit()
    return FileResponseSchema.model_validate(file_info)


@router.get("/{claim_id}/documents", response_model=List[FileResponseSchema])
async def list_claim_documents(
    claim_id: UUID,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List documents."""
    claim_repo = ClaimRepository(db)
    claim = await claim_repo.get_by_id(claim_id)
    if not claim: raise HTTPException(status_code=404, detail="Claim not found")
    verify_claim_access(claim, current_user)

    file_repo = FileRepository(db)
    files = await file_repo.get_by_claim_id(claim_id, include_deleted=False)
    return [FileResponseSchema.model_validate(f) for f in files]


@router.post("/ocr-boarding-pass", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def extract_boarding_pass_data(
    request: Request,
    file: UploadFile = File(...),
    current_user: Customer = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """OCR boarding pass extraction."""
    from app.schemas.ocr_schemas import OCRResponseSchema, BoardingPassDataSchema, FieldConfidenceSchema
    from app.services.ocr_service import ocr_service
    from app.services.email_parser_service import EmailParserService

    content_type = file.content_type or "application/octet-stream"
    file_content = await file.read()
    
    if content_type == "message/rfc822" or file.filename.lower().endswith('.eml'):
        email_data = EmailParserService.parse_eml(file_content)
        extracted = await ocr_service.extract_from_email_text(email_data["subject"], email_data["body"])
        return OCRResponseSchema(
            success=True, data=BoardingPassDataSchema(**extracted),
            confidence_score=0.95, field_confidence={k: 0.95 for k in extracted if extracted[k]}
        )

    result = await ocr_service.extract_boarding_pass_data(file_content, content_type)
    response = OCRResponseSchema(
        success=result.get("success", False),
        data=BoardingPassDataSchema(**result["data"]) if result.get("data") else None,
        confidence_score=result.get("confidence_score", 0.0),
        field_confidence=FieldConfidenceSchema(**result["field_confidence"]) if result.get("field_confidence") else None
    )

    file_service = get_file_service(db)
    file_record = await file_service.upload_orphan_file(
        file_content, file.filename, content_type, "boarding_pass", 
        str(current_user.id) if current_user else None
    )
    await db.commit()
    response.uploaded_file_id = str(file_record.id)
    return response
