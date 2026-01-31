"""Customer repository for data access operations."""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, bindparam

from app.models import Customer
from app.repositories.base import BaseRepository
from app.utils.db_encryption import generate_blind_index


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Customer, session)
    
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        # Use blind index for exact lookup
        email_idx = generate_blind_index(email)
        return await self.get_by_field('email_idx', email_idx)
    
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        """
        Search customers by name.
        NOTE: Due to encryption, partial name search is currently disabled.
        This will return empty results until phonetic search is implemented.
        """
        # Return empty list to prevent confusion (encrypted fields cannot be searched with ILIKE)
        return []
    
    async def search_by_email(self, email: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        """
        Search customers by email address.
        NOTE: Due to encryption, only EXACT matches are supported.
        """
        # Use blind index for exact lookup
        email_idx = generate_blind_index(email)
        
        stmt = select(Customer).where(
            Customer.email_idx == email_idx
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
        email_idx = generate_blind_index(email)
        return await self.create(
            email=email,
            email_idx=email_idx,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            street=street,
            city=city,
            postal_code=postal_code,
            country=country
        )
    
    async def update_customer(self, customer_id: UUID, allow_null_values: bool = False, **kwargs) -> Optional[Customer]:
        """Update customer information."""
        customer = await self.get_by_id(customer_id)
        if not customer:
            return None
        
        # Handle index updates for email
        if 'email' in kwargs and kwargs['email']:
            kwargs['email_idx'] = generate_blind_index(kwargs['email'])
            
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
        # Use blind index for lookup
        existing = await self.get_by_email(email)
        if existing and existing.id != customer_id:
            return None
        
        email_idx = generate_blind_index(email)
        return await self.update(customer, email=email, email_idx=email_idx)
