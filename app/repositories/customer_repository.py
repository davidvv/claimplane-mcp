"""Customer repository for data access operations."""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, bindparam

from app.models import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Customer, session)
    
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        return await self.get_by_field('email', email)
    
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Search customers by name (first name or last name)."""
        # Search in both first_name and last_name
        # Using bindparam to prevent SQL injection
        stmt = select(Customer).where(
            or_(
                Customer.first_name.ilike(bindparam('name_param')),
                Customer.last_name.ilike(bindparam('name_param'))
            )
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt, {"name_param": f"%{name}%"})
        return result.scalars().all()
    
    async def search_by_email(self, email: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Search customers by email address (partial match)."""
        # Using bindparam to prevent SQL injection
        stmt = select(Customer).where(
            Customer.email.ilike(bindparam('email_param'))
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt, {"email_param": f"%{email}%"})
        return result.scalars().all()
    
    async def get_active_customers(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get customers who have submitted at least one claim."""
        stmt = select(Customer).join(Customer.claims).distinct().offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create_customer(self, email: str, first_name: str, last_name: str, 
                             phone: Optional[str] = None, street: Optional[str] = None,
                             city: Optional[str] = None, postal_code: Optional[str] = None,
                             country: Optional[str] = None) -> Customer:
        """Create a new customer with all fields."""
        return await self.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            street=street,
            city=city,
            postal_code=postal_code,
            country=country
        )
    
    async def update_customer(self, customer_id: UUID, allow_null_values: bool = False, **kwargs) -> Optional[Customer]:
        """Update customer information.
        
        Args:
            customer_id: UUID of the customer to update
            allow_null_values: If True, None values will be set to null. If False, None values are filtered out.
            **kwargs: Fields to update
        """
        customer = await self.get_by_id(customer_id)
        if not customer:
            return None
        
        if allow_null_values:
            # For PUT operations: allow None values to be set to null
            update_data = kwargs
        else:
            # For PATCH operations: filter out None values to avoid overwriting with null
            update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return customer
        
        return await self.update(customer, **update_data)
    
    async def update_customer_email(self, customer_id: UUID, email: str) -> Optional[Customer]:
        """Update customer email specifically."""
        customer = await self.get_by_id(customer_id)
        if not customer:
            return None
        
        # Check if email already exists for another customer
        existing = await self.get_by_email(email)
        if existing and existing.id != customer_id:
            return None
        
        return await self.update(customer, email=email)