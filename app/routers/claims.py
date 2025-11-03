"""Claims API endpoints."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Claim, Customer
from app.repositories import ClaimRepository, CustomerRepository
from app.schemas import (
    ClaimCreateSchema,
    ClaimResponseSchema,
    ClaimRequestSchema,
    ClaimUpdateSchema,
    ClaimPatchSchema
)
from app.tasks.claim_tasks import send_claim_submitted_email
from app.config import config
from app.dependencies.auth import get_current_user, get_optional_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claims", tags=["claims"])


def verify_claim_access(claim: Claim, current_user: Customer) -> None:
    """
    Verify that the current user has access to the claim.
    Admins and superadmins can access all claims.
    Customers can only access their own claims.

    Args:
        claim: Claim to verify access for
        current_user: Currently authenticated user

    Raises:
        HTTPException: 403 if user doesn't have access
    """
    # Admins can access all claims
    if current_user.role in [Customer.ROLE_ADMIN, Customer.ROLE_SUPERADMIN]:
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

    claim = await claim_repo.create_claim(
        customer_id=customer_id,
        flight_number=flight_data.flight_number,
        airline=flight_data.airline,
        departure_date=flight_data.departure_date,
        departure_airport=flight_data.departure_airport,
        arrival_airport=flight_data.arrival_airport,
        incident_type=claim_data.incident_type,
        notes=claim_data.notes
    )

    # Send claim submitted email notification (Phase 2)
    if config.NOTIFICATIONS_ENABLED and customer:
        try:
            # Trigger async email task
            send_claim_submitted_email.delay(
                customer_email=customer.email,
                customer_name=f"{customer.first_name} {customer.last_name}",
                claim_id=str(claim.id),
                flight_number=claim.flight_number,
                airline=claim.airline
            )
            logger.info(f"Claim submitted email task queued for customer {customer.email}")
        except Exception as e:
            # Don't fail the API request if email queueing fails
            logger.error(f"Failed to queue claim submitted email: {str(e)}")

    return ClaimResponseSchema.model_validate(claim)


@router.post("/submit", response_model=ClaimResponseSchema, status_code=status.HTTP_201_CREATED)
async def submit_claim_with_customer(
    claim_request: ClaimRequestSchema,
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """
    Submit a new claim with customer information (creates customer if needed).
    
    Args:
        claim_request: Claim request with customer and flight info
        db: Database session
        
    Returns:
        Created claim data
        
    Raises:
        HTTPException: If validation fails
    """
    customer_repo = CustomerRepository(db)
    claim_repo = ClaimRepository(db)
    
    # Check if customer exists by email
    customer_data = claim_request.customer_info
    customer = await customer_repo.get_by_email(customer_data.email)
    
    if not customer:
        # Create new customer
        address_data = customer_data.address.dict() if customer_data.address else {}
        customer = await customer_repo.create_customer(
            email=customer_data.email,
            first_name=customer_data.first_name,
            last_name=customer_data.last_name,
            phone=customer_data.phone,
            **address_data
        )
    
    # Create claim
    flight_data = claim_request.flight_info
    
    claim = await claim_repo.create_claim(
        customer_id=customer.id,
        flight_number=flight_data.flight_number,
        airline=flight_data.airline,
        departure_date=flight_data.departure_date,
        departure_airport=flight_data.departure_airport,
        arrival_airport=flight_data.arrival_airport,
        incident_type=claim_request.incident_type,
        notes=claim_request.notes
    )

    # Send claim submitted email notification (Phase 2)
    if config.NOTIFICATIONS_ENABLED and customer:
        try:
            # Trigger async email task
            send_claim_submitted_email.delay(
                customer_email=customer.email,
                customer_name=f"{customer.first_name} {customer.last_name}",
                claim_id=str(claim.id),
                flight_number=claim.flight_number,
                airline=claim.airline
            )
            logger.info(f"Claim submitted email task queued for customer {customer.email}")
        except Exception as e:
            # Don't fail the API request if email queueing fails
            logger.error(f"Failed to queue claim submitted email: {str(e)}")

    return ClaimResponseSchema.model_validate(claim)


@router.get("/{claim_id}", response_model=ClaimResponseSchema)
async def get_claim(
    claim_id: UUID,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ClaimResponseSchema:
    """
    Get claim by ID.

    Requires authentication. Customers can only access their own claims.
    Admins and superadmins can access all claims.

    Args:
        claim_id: Claim UUID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Claim data

    Raises:
        HTTPException: If claim not found or access denied
    """
    repo = ClaimRepository(db)
    claim = await repo.get_by_id(claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found"
        )

    # Verify access
    verify_claim_access(claim, current_user)

    return ClaimResponseSchema.model_validate(claim)


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

    return [ClaimResponseSchema.model_validate(claim) for claim in claims]


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

    return [ClaimResponseSchema.model_validate(claim) for claim in claims]


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

    return [ClaimResponseSchema.model_validate(claim) for claim in claims]