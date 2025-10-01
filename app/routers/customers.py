"""Customer API endpoints."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer
from app.repositories import CustomerRepository
from app.schemas import CustomerCreateSchema, CustomerResponseSchema, CustomerUpdateSchema, CustomerPatchSchema

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/", response_model=CustomerResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponseSchema:
    """
    Create a new customer.
    
    Args:
        customer_data: Customer creation data
        db: Database session
        
    Returns:
        Created customer data
        
    Raises:
        HTTPException: If customer with email already exists
    """
    repo = CustomerRepository(db)
    
    # Check if customer with email already exists
    existing_customer = await repo.get_by_email(customer_data.email)
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with email {customer_data.email} already exists"
        )
    
    # Create customer
    address_data = customer_data.address.dict() if customer_data.address else {}
    
    customer = await repo.create_customer(
        email=customer_data.email,
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        phone=customer_data.phone,
        **address_data
    )
    
    return CustomerResponseSchema.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponseSchema)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponseSchema:
    """
    Get customer by ID.
    
    Args:
        customer_id: Customer UUID
        db: Database session
        
    Returns:
        Customer data
        
    Raises:
        HTTPException: If customer not found
    """
    repo = CustomerRepository(db)
    customer = await repo.get_by_id(customer_id)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    return CustomerResponseSchema.model_validate(customer)


@router.get("/", response_model=List[CustomerResponseSchema])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[CustomerResponseSchema]:
    """
    List all customers with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of customers
    """
    repo = CustomerRepository(db)
    customers = await repo.get_all(skip=skip, limit=limit)
    
    return [CustomerResponseSchema.model_validate(customer) for customer in customers]


@router.get("/search/by-email/{email}", response_model=List[CustomerResponseSchema])
async def search_customers_by_email(
    email: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[CustomerResponseSchema]:
    """
    Search customers by email (partial match).
    
    Args:
        email: Email search term
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of matching customers
    """
    repo = CustomerRepository(db)
    customers = await repo.search_by_email(email, skip=skip, limit=limit)
    
    return [CustomerResponseSchema.model_validate(customer) for customer in customers]


@router.get("/search/by-name/{name}", response_model=List[CustomerResponseSchema])
async def search_customers_by_name(
    name: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[CustomerResponseSchema]:
    """
    Search customers by name (first name or last name).
    
    Args:
        name: Name search term
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of matching customers
    """
    repo = CustomerRepository(db)
    customers = await repo.search_by_name(name, skip=skip, limit=limit)
    
    return [CustomerResponseSchema.model_validate(customer) for customer in customers]


@router.put("/{customer_id}", response_model=CustomerResponseSchema)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponseSchema:
    """
    Update a customer completely (all fields required).
    
    Args:
        customer_id: Customer UUID
        customer_data: Complete customer update data
        db: Database session
        
    Returns:
        Updated customer data
        
    Raises:
        HTTPException: If customer not found or email already exists
    """
    repo = CustomerRepository(db)
    
    # Check if customer exists
    existing_customer = await repo.get_by_id(customer_id)
    if not existing_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    # Check if email is being changed and if new email already exists
    if customer_data.email != existing_customer.email:
        email_customer = await repo.get_by_email(customer_data.email)
        if email_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with email {customer_data.email} already exists"
            )
    
    # Update customer with all fields (allow null values for PUT)
    address_data = customer_data.address.dict() if customer_data.address else {}
    
    updated_customer = await repo.update_customer(
        customer_id=customer_id,
        allow_null_values=True,  # PUT should allow setting fields to null
        email=customer_data.email,
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        phone=customer_data.phone,
        **address_data
    )
    
    return CustomerResponseSchema.model_validate(updated_customer)


@router.patch("/{customer_id}", response_model=CustomerResponseSchema)
async def patch_customer(
    customer_id: UUID,
    customer_data: CustomerPatchSchema,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponseSchema:
    """
    Partially update a customer (only specified fields are updated).
    
    Args:
        customer_id: Customer UUID
        customer_data: Partial customer update data
        db: Database session
        
    Returns:
        Updated customer data
        
    Raises:
        HTTPException: If customer not found or email already exists
    """
    logger.info(f"PATCH request received for customer {customer_id}")
    logger.info(f"Request data: {customer_data.model_dump()}")
    
    repo = CustomerRepository(db)
    
    # Check if customer exists
    existing_customer = await repo.get_by_id(customer_id)
    if not existing_customer:
        logger.warning(f"Customer {customer_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    logger.info(f"Found existing customer: {existing_customer.email}")
    
    # Check if email is being changed and if new email already exists
    # Handle edge cases: empty strings, whitespace, and case sensitivity
    if (customer_data.email is not None and
        customer_data.email.strip() and  # Not empty or whitespace
        customer_data.email.lower() != existing_customer.email.lower()):
        
        logger.info(f"Email change detected: {existing_customer.email} -> {customer_data.email}")
        email_customer = await repo.get_by_email(customer_data.email)
        if email_customer:
            logger.warning(f"Email {customer_data.email} already exists for another customer")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with email {customer_data.email} already exists"
            )
    
    # Build update data, filtering out None values and empty strings
    update_data = {}
    
    # Only update email if it's provided and not empty/whitespace
    if (customer_data.email is not None and
        customer_data.email.strip()):  # Not empty or whitespace
        update_data['email'] = customer_data.email.strip()
    
    if customer_data.first_name is not None:
        update_data['first_name'] = customer_data.first_name.strip() if customer_data.first_name else customer_data.first_name
    if customer_data.last_name is not None:
        update_data['last_name'] = customer_data.last_name.strip() if customer_data.last_name else customer_data.last_name
    if customer_data.phone is not None:
        update_data['phone'] = customer_data.phone.strip() if customer_data.phone else customer_data.phone
    
    # Handle address updates
    if customer_data.address is not None:
        address_data = customer_data.address.dict()
        # Only update address fields that are explicitly provided (not None)
        if address_data.get('street') is not None:
            update_data['street'] = address_data.get('street')
        if address_data.get('city') is not None:
            update_data['city'] = address_data.get('city')
        if address_data.get('postal_code') is not None:
            update_data['postal_code'] = address_data.get('postal_code')
        if address_data.get('country') is not None:
            update_data['country'] = address_data.get('country')
    
    logger.info(f"Update data after filtering: {update_data}")
    
    # If no fields to update, return existing customer
    if not update_data:
        logger.info("No fields to update, returning existing customer")
        return CustomerResponseSchema.model_validate(existing_customer)
    
    # Update customer
    logger.info(f"Updating customer with data: {update_data}")
    updated_customer = await repo.update_customer(customer_id=customer_id, **update_data)
    
    logger.info(f"Customer updated successfully: {updated_customer.email}")
    return CustomerResponseSchema.model_validate(updated_customer)