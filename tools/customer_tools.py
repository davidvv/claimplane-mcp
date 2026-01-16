"""Customer management tools."""
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from database import get_db_session
from app.models import Customer
from app.repositories import CustomerRepository


async def create_customer(
    email: str,
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    street: Optional[str] = None,
    city: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new customer.
    
    Args:
        email: Customer email address
        first_name: First name
        last_name: Last name
        phone: Phone number (optional)
        street: Street address (optional)
        city: City (optional)
        postal_code: Postal code (optional)
        country: Country (optional)
    
    Returns:
        Created customer details
    """
    try:
        async with get_db_session() as session:
            repo = CustomerRepository(session)
            
            customer = await repo.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                street=street,
                city=city,
                postal_code=postal_code,
                country=country
            )
            
            return {
                "success": True,
                "customer_id": str(customer.id),
                "email": customer.email,
                "name": f"{customer.first_name} {customer.last_name}",
                "message": f"Customer created successfully with ID: {customer.id}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create customer"
        }


async def get_customer(customer_id: str) -> Dict[str, Any]:
    """Get customer by ID.
    
    Args:
        customer_id: Customer ID (UUID)
    
    Returns:
        Customer details
    """
    try:
        async with get_db_session() as session:
            repo = CustomerRepository(session)
            customer = await repo.get_by_id(customer_id)
            
            if not customer:
                return {
                    "success": False,
                    "message": f"Customer not found: {customer_id}"
                }
            
            return {
                "success": True,
                "customer": {
                    "id": str(customer.id),
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "phone": customer.phone,
                    "address": customer.address,
                    "created_at": customer.created_at.isoformat() if customer.created_at else None
                },
                "message": "Customer retrieved successfully"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve customer"
        }


async def get_customer_by_email(email: str) -> Dict[str, Any]:
    """Get customer by email address.
    
    Args:
        email: Customer email
    
    Returns:
        Customer details or not found
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                select(Customer).where(Customer.email == email)
            )
            customer = result.scalar_one_or_none()
            
            if not customer:
                return {
                    "success": False,
                    "found": False,
                    "message": f"No customer found with email: {email}"
                }
            
            return {
                "success": True,
                "found": True,
                "customer": {
                    "id": str(customer.id),
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "phone": customer.phone,
                    "address": customer.address,
                    "created_at": customer.created_at.isoformat() if customer.created_at else None
                },
                "message": f"Customer found: {customer.first_name} {customer.last_name}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to search for customer"
        }


async def list_customers(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """List customers with pagination.
    
    Args:
        limit: Number of results to return (default: 10)
        offset: Number of results to skip (default: 0)
    
    Returns:
        List of customers
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                select(Customer)
                .order_by(Customer.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            customers = result.scalars().all()
            
            return {
                "success": True,
                "count": len(customers),
                "customers": [
                    {
                        "id": str(c.id),
                        "email": c.email,
                        "name": f"{c.first_name} {c.last_name}",
                        "phone": c.phone,
                        "created_at": c.created_at.isoformat() if c.created_at else None
                    }
                    for c in customers
                ],
                "message": f"Retrieved {len(customers)} customers"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list customers"
        }


async def delete_customer(customer_id: str) -> Dict[str, Any]:
    """Delete a customer.
    
    Args:
        customer_id: Customer ID (UUID)
    
    Returns:
        Deletion status
    """
    try:
        async with get_db_session() as session:
            repo = CustomerRepository(session)
            customer = await repo.get_by_id(customer_id)
            
            if not customer:
                return {
                    "success": False,
                    "message": f"Customer not found: {customer_id}"
                }
            
            await repo.delete(customer_id)
            
            return {
                "success": True,
                "message": f"Customer deleted successfully: {customer_id}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to delete customer"
        }
