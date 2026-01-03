"""Claims API endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Claim, Customer
from app.repositories import ClaimRepository, CustomerRepository
from app.repositories.file_repository import FileRepository
from app.schemas import (
    ClaimCreateSchema,
    ClaimResponseSchema,
    ClaimRequestSchema,
    ClaimSubmitResponseSchema,
    ClaimUpdateSchema,
    ClaimPatchSchema,
    FileResponseSchema
)
from app.services.auth_service import AuthService
from app.services.file_service import FileService, get_file_service
from app.tasks.claim_tasks import send_claim_submitted_email
from app.config import config
from app.dependencies.auth import get_current_user, get_optional_current_user, get_current_user_with_claim_access
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


@router.post("/submit", response_model=ClaimSubmitResponseSchema, status_code=status.HTTP_201_CREATED)
async def submit_claim_with_customer(
    claim_request: ClaimRequestSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ClaimSubmitResponseSchema:
    """
    Submit a new claim with customer information (creates customer if needed).

    Returns an access token for immediate authentication, allowing the user
    to upload documents without needing to click the magic link first.

    Args:
        claim_request: Claim request with customer and flight info
        db: Database session

    Returns:
        Created claim data with access token for immediate authentication

    Raises:
        HTTPException: If validation fails
    """
    try:
        customer_repo = CustomerRepository(db)
        claim_repo = ClaimRepository(db)

        # Check if customer exists by email
        customer_data = claim_request.customer_info
        customer = await customer_repo.get_by_email(customer_data.email)

        if not customer:
            # Create new customer
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

        # Create claim
        flight_data = claim_request.flight_info
        logger.info(f"Creating claim for customer {customer.id}")
        logger.info(f"Flight data: {flight_data.dict()}")
        logger.info(f"Incident type: {claim_request.incident_type}")

        # Get client IP for terms acceptance tracking
        from datetime import datetime, timezone
        ip_address, _ = get_client_info(request)

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

        # Commit the claim to database before flight verification
        await db.commit()
        logger.info(f"Claim {claim.id} committed to database")

        # Phase 6: Flight verification and enrichment (after commit, before email)
        try:
            from app.services.flight_data_service import FlightDataService

            logger.info(f"Starting flight verification for claim {claim.id}")
            enriched_data = await FlightDataService.verify_and_enrich_claim(
                session=db,
                claim=claim,
                user_id=customer.id,
                force_refresh=False
            )

            # Update claim with verified flight data
            if enriched_data.get("verified"):
                logger.info(f"Flight verified for claim {claim.id}: compensation={enriched_data.get('compensation_amount')} EUR")

                # Update claim with calculated fields
                if enriched_data.get("compensation_amount") is not None:
                    claim.calculated_compensation = enriched_data["compensation_amount"]

                if enriched_data.get("distance_km") is not None:
                    claim.flight_distance_km = enriched_data["distance_km"]

                if enriched_data.get("delay_hours") is not None:
                    claim.delay_hours = enriched_data["delay_hours"]

                # Commit updated claim
                await db.commit()
                logger.info(f"Updated claim {claim.id} with verified flight data")
            else:
                logger.warning(
                    f"Flight not verified for claim {claim.id}: "
                    f"source={enriched_data.get('verification_source')}"
                )

        except Exception as e:
            # CRITICAL: Never fail claim submission due to flight verification errors
            # Graceful degradation - claim will use manual verification
            logger.error(
                f"Flight verification failed for claim {claim.id}: {str(e)}",
                exc_info=True
            )
            # Continue with claim submission - admin will verify manually

    except ValueError as e:
        logger.error(f"Validation error in claim submission: {str(e)}", exc_info=True)
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
            detail=f"An error occurred while submitting your claim: {str(e)}"
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

    # Generate access token for immediate authentication
    # This allows users to upload documents without clicking the magic link first
    access_token = AuthService.create_access_token(
        user_id=customer.id,
        email=customer.email,
        role=customer.role,
        claim_id=claim.id
    )
    logger.info(f"Generated access token for customer {customer.id} with claim {claim.id}")

    return ClaimSubmitResponseSchema(
        claim=ClaimResponseSchema.from_orm(claim),
        accessToken=access_token,
        tokenType="bearer"
    )


@router.get("/{claim_id}", response_model=ClaimResponseSchema)
async def get_claim(
    claim_id: UUID,
    user_data: tuple = Depends(get_current_user_with_claim_access),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """
    Get claim by ID.

    Requires authentication. Customers can access their own claims or claims via magic link.
    Admins and superadmins can access all claims.

    Args:
        claim_id: Claim UUID
        user_data: Tuple of (current_user, token_claim_id) from JWT
        db: Database session

    Returns:
        Claim data

    Raises:
        HTTPException: If claim not found or access denied
    """
    current_user, token_claim_id = user_data

    logger.info(f"[get_claim] Request for claim_id={claim_id}, user={current_user.id}, token_claim_id={token_claim_id}")

    repo = ClaimRepository(db)
    claim = await repo.get_by_id(claim_id)

    if not claim:
        logger.warning(f"[get_claim] Claim {claim_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )

    logger.info(f"[get_claim] Found claim: id={claim.id}, customer_id={claim.customer_id}")

    # Verify access (pass token_claim_id for magic link access)
    verify_claim_access(claim, current_user, token_claim_id)

    logger.info(f"[get_claim] Access verified, returning claim")

    return ClaimResponseSchema.from_orm(claim)


@router.get("/", response_model=List[ClaimResponseSchema])
async def list_claims(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    customer_id: UUID = None,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ClaimResponseSchema]:
    """
    List claims with optional filtering.

    Requires authentication. Customers see only their own claims.
    Admins and superadmins can see all claims or filter by customer_id.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by claim status
        customer_id: Filter by customer ID (admin only)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of claims accessible to the user
    """
    repo = ClaimRepository(db)

    # Customers can only see their own claims (ignore customer_id parameter)
    if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
        customer_id = current_user.id

    if status:
        claims = await repo.get_by_status(status, skip=skip, limit=limit)
        # Filter by customer_id if specified
        if customer_id:
            claims = [c for c in claims if c.customer_id == customer_id]
    elif customer_id:
        claims = await repo.get_by_customer_id(customer_id, skip=skip, limit=limit)
    else:
        # Customers: get their own claims; Admins: get all claims
        if current_user.role in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
            claims = await repo.get_all(skip=skip, limit=limit)
        else:
            claims = await repo.get_by_customer_id(current_user.id, skip=skip, limit=limit)

    # Debug logging to verify claim IDs
    logger.info(f"[list_claims] Returning {len(claims)} claims for user {current_user.id}")
    for claim in claims:
        logger.info(f"[list_claims] Claim: id={claim.id}, customer_id={claim.customer_id}, flight={claim.flight_number}")

    response_claims = [ClaimResponseSchema.from_orm(claim) for claim in claims]

    # Log the serialized response
    for idx, resp_claim in enumerate(response_claims):
        logger.info(f"[list_claims] Response[{idx}]: id={resp_claim.id}, customerId={resp_claim.customer_id}")

    return response_claims


@router.get("/customer/{customer_id}", response_model=List[ClaimResponseSchema])
async def get_customer_claims(
    customer_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ClaimResponseSchema]:
    """
    Get all claims for a specific customer.

    Requires authentication. Customers can only access their own claims.
    Admins and superadmins can access claims for any customer.

    Args:
        customer_id: Customer UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of customer claims

    Raises:
        HTTPException: If customer not found or access denied
    """
    # Customers can only access their own claims
    if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
        if customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own claims"
            )

    customer_repo = CustomerRepository(db)
    claim_repo = ClaimRepository(db)

    # Verify customer exists
    customer = await customer_repo.get_by_id(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )

    claims = await claim_repo.get_by_customer_id(customer_id, skip=skip, limit=limit)

    return [ClaimResponseSchema.from_orm(claim) for claim in claims]


@router.put("/{claim_id}", response_model=ClaimResponseSchema)
async def update_claim(
    claim_id: UUID,
    claim_data: ClaimUpdateSchema,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """
    Update a claim completely (all fields required).

    Requires authentication. Customers can only update their own claims.
    Admins and superadmins can update any claim.

    Args:
        claim_id: Claim UUID
        claim_data: Complete claim update data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated claim data

    Raises:
        HTTPException: If claim not found, access denied, customer not found, or validation fails
    """
    customer_repo = CustomerRepository(db)
    claim_repo = ClaimRepository(db)

    # Check if claim exists
    existing_claim = await claim_repo.get_by_id(claim_id)
    if not existing_claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )

    # Verify access
    verify_claim_access(existing_claim, current_user)

    # Verify customer exists
    customer = await customer_repo.get_by_id(claim_data.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {claim_data.customer_id} not found"
        )

    # Update claim with all fields (allow null values for PUT)
    flight_data = claim_data.flight_info

    updated_claim = await claim_repo.update_claim(
        claim_id=claim_id,
        allow_null_values=True,  # PUT should allow setting fields to null
        customer_id=claim_data.customer_id,
        flight_number=flight_data.flight_number,
        airline=flight_data.airline,
        departure_date=flight_data.departure_date,
        departure_airport=flight_data.departure_airport,
        arrival_airport=flight_data.arrival_airport,
        incident_type=claim_data.incident_type,
        notes=claim_data.notes
    )

    return ClaimResponseSchema.model_validate(updated_claim)


@router.patch("/{claim_id}", response_model=ClaimResponseSchema)
async def patch_claim(
    claim_id: UUID,
    claim_data: ClaimPatchSchema,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """
    Partially update a claim (only specified fields are updated).

    Requires authentication. Customers can only update their own claims.
    Admins and superadmins can update any claim.

    Args:
        claim_id: Claim UUID
        claim_data: Partial claim update data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated claim data

    Raises:
        HTTPException: If claim not found, access denied, customer not found, or validation fails
    """
    customer_repo = CustomerRepository(db)
    claim_repo = ClaimRepository(db)

    # Check if claim exists
    existing_claim = await claim_repo.get_by_id(claim_id)
    if not existing_claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )

    # Verify access
    verify_claim_access(existing_claim, current_user)

    # Build update data, filtering out None values
    update_data = {}

    if claim_data.customer_id is not None:
        # Verify customer exists
        customer = await customer_repo.get_by_id(claim_data.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {claim_data.customer_id} not found"
            )
        update_data['customer_id'] = claim_data.customer_id

    if claim_data.flight_info is not None:
        flight_data = claim_data.flight_info
        update_data.update({
            'flight_number': flight_data.flight_number.upper(),
            'airline': flight_data.airline,
            'departure_date': flight_data.departure_date,
            'departure_airport': flight_data.departure_airport.upper(),
            'arrival_airport': flight_data.arrival_airport.upper()
        })

    if claim_data.incident_type is not None:
        update_data['incident_type'] = claim_data.incident_type

    if claim_data.notes is not None:
        update_data['notes'] = claim_data.notes

    # If no fields to update, return existing claim
    if not update_data:
        return ClaimResponseSchema.model_validate(existing_claim)

    # Update claim
    updated_claim = await claim_repo.update_claim(claim_id=claim_id, **update_data)

    return ClaimResponseSchema.model_validate(updated_claim)


@router.get("/status/{status}", response_model=List[ClaimResponseSchema])
async def get_claims_by_status(
    status: str,
    skip: int = 0,
    limit: int = 100,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ClaimResponseSchema]:
    """
    Get claims by status.

    Requires authentication. Customers see only their own claims with the specified status.
    Admins and superadmins can see all claims with the specified status.

    Args:
        status: Claim status
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of claims with specified status (filtered by user access)
    """
    repo = ClaimRepository(db)
    claims = await repo.get_by_status(status, skip=skip, limit=limit)

    # Customers can only see their own claims
    if current_user.role not in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
        claims = [c for c in claims if c.customer_id == current_user.id]

    return [ClaimResponseSchema.from_orm(claim) for claim in claims]


@router.get("/{claim_id}/documents", response_model=List[FileResponseSchema])
async def list_claim_documents(
    claim_id: UUID,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[FileResponseSchema]:
    """
    List all documents for a specific claim.

    Customers can only access documents for their own claims.
    Admins can access documents for any claim.

    Args:
        claim_id: ID of the claim
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of documents for the claim

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

    # Get documents
    file_repo = FileRepository(db)
    files = await file_repo.get_by_claim_id(claim_id, include_deleted=False)

    logger.info(f"[list_claim_documents] Found {len(files)} documents for claim {claim_id}")
    return [FileResponseSchema.model_validate(f) for f in files]


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