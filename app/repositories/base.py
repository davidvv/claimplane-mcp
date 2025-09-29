"""Base repository class with common CRUD operations."""
import logging
from typing import TypeVar, Generic, Type, Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import Base

# Set up logging
logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.session.get(self.model, id)
        return result
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        await self.session.commit()
        return instance
    
    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update an existing record."""
        logger.info(f"Updating {self.model.__name__} with ID {instance.id}")
        logger.info(f"Update data: {kwargs}")
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key)
                setattr(instance, key, value)
                logger.info(f"Updated {key}: {old_value} -> {value}")
        
        self.session.add(instance)
        await self.session.flush()
        logger.info("Session flushed successfully")
        
        await self.session.refresh(instance)
        logger.info("Instance refreshed successfully")
        
        await self.session.commit()
        logger.info("Transaction committed successfully")
        
        return instance
    
    async def delete(self, instance: ModelType) -> bool:
        """Delete a record."""
        await self.session.delete(instance)
        await self.session.flush()
        await self.session.commit()
        return True
    
    async def count(self) -> int:
        """Count total records."""
        stmt = select(func.count(self.model.id))
        result = await self.session.execute(stmt)
        return result.scalar()
    
    async def exists(self, id: UUID) -> bool:
        """Check if a record exists."""
        instance = await self.get_by_id(id)
        return instance is not None
    
    async def get_by_field(self, field: str, value) -> Optional[ModelType]:
        """Get a single record by a specific field."""
        stmt = select(self.model).where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_by_field(self, field: str, value, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records by a specific field with pagination."""
        stmt = select(self.model).where(getattr(self.model, field) == value).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()