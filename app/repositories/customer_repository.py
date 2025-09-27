"""Customer repository for data access operations."""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

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
        stmt = select(Customer).where(
            or_(
                Customer.first_name.ilike(f"%{name}%"),
                Customer.last_name.ilike(f"%{name}%")
            )
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def search_by_email(self, email: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Search customers by email address (partial match)."""
        stmt = select(Customer).where(
            Customer.email.ilike(f"%{email}%")
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
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
    
    async def update_customer(self, customer_id: UUID, **kwargs) -> Optional[Customer]:
        """Update customer information."""
        customer = await self.get_by_id(customer_id)
        if not customer:
            return None
        
        # Filter out None values to avoid overwriting with null
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        return await self.update(customer, **update_data)