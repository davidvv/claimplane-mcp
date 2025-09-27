"""Customer API endpoints."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer
from app.repositories import CustomerRepository
from app.schemas import CustomerCreateSchema, CustomerResponseSchema

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