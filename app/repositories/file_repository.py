"""File repository for data access operations."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models import ClaimFile, FileAccessLog, FileValidationRule
from app.repositories.base import BaseRepository


class FileRepository(BaseRepository[ClaimFile]):
    """Repository for ClaimFile model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ClaimFile, session)
    
    async def get_by_claim_id(self, claim_id: UUID, include_deleted: bool = False) -> List[ClaimFile]:
        """Get files by claim ID."""
        stmt = select(ClaimFile).where(ClaimFile.claim_id == claim_id)
        
        if not include_deleted:
            stmt = stmt.where(ClaimFile.is_deleted == 0)
        
        stmt = stmt.order_by(ClaimFile.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_customer_id(self, customer_id: UUID, include_deleted: bool = False) -> List[ClaimFile]:
        """Get files by customer ID."""
        stmt = select(ClaimFile).where(ClaimFile.customer_id == customer_id)
        
        if not include_deleted:
            stmt = stmt.where(ClaimFile.is_deleted == 0)
        
        stmt = stmt.order_by(ClaimFile.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_file_hash(self, file_hash: str) -> Optional[ClaimFile]:
        """Get file by hash (for duplicate detection)."""
        stmt = select(ClaimFile).where(
            and_(
                ClaimFile.file_hash == file_hash,
                ClaimFile.is_deleted == 0
            )
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_files_by_status(self, status: str, customer_id: Optional[UUID] = None) -> List[ClaimFile]:
        """Get files by status."""
        stmt = select(ClaimFile).where(
            and_(
                ClaimFile.status == status,
                ClaimFile.is_deleted == 0
            )
        )
        
        if customer_id:
            stmt = stmt.where(ClaimFile.customer_id == customer_id)
        
        stmt = stmt.order_by(ClaimFile.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_files_by_document_type(self, document_type: str, customer_id: Optional[UUID] = None) -> List[ClaimFile]:
        """Get files by document type."""
        stmt = select(ClaimFile).where(
            and_(
                ClaimFile.document_type == document_type,
                ClaimFile.is_deleted == 0
            )
        )
        
        if customer_id:
            stmt = stmt.where(ClaimFile.customer_id == customer_id)
        
        stmt = stmt.order_by(ClaimFile.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_expired_files(self, before_date: datetime) -> List[ClaimFile]:
        """Get files that have expired."""
        stmt = select(ClaimFile).where(
            and_(
                ClaimFile.expires_at < before_date,
                ClaimFile.is_deleted == 0
            )
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_files_summary(self, customer_id: UUID) -> Dict[str, Any]:
        """Get file statistics for a customer."""
        # Total files and size
        total_stmt = select(
            func.count(ClaimFile.id).label("total_files"),
            func.coalesce(func.sum(ClaimFile.file_size), 0).label("total_size")
        ).where(
            and_(
                ClaimFile.customer_id == customer_id,
                ClaimFile.is_deleted == 0
            )
        )
        
        total_result = await self.session.execute(total_stmt)
        total_data = total_result.one()
        
        # Files by document type
        by_type_stmt = select(
            ClaimFile.document_type,
            func.count(ClaimFile.id).label("count"),
            func.coalesce(func.sum(ClaimFile.file_size), 0).label("size")
        ).where(
            and_(
                ClaimFile.customer_id == customer_id,
                ClaimFile.is_deleted == 0
            )
        ).group_by(ClaimFile.document_type)
        
        by_type_result = await self.session.execute(by_type_stmt)
        by_type_data = by_type_result.all()
        
        # Recent files (last 5)
        recent_stmt = select(ClaimFile).where(
            and_(
                ClaimFile.customer_id == customer_id,
                ClaimFile.is_deleted == 0
            )
        ).order_by(ClaimFile.created_at.desc()).limit(5)
        
        recent_result = await self.session.execute(recent_stmt)
        recent_files = recent_result.scalars().all()
        
        return {
            "total_files": total_data.total_files or 0,
            "total_size": total_data.total_size or 0,
            "by_document_type": {
                row.document_type: {
                    "count": row.count,
                    "size": row.size
                }
                for row in by_type_data
            },
            "recent_files": recent_files
        }
    
    async def search_files(self, query: str, customer_id: Optional[UUID] = None,
                          document_type: Optional[str] = None,
                          date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None,
                          limit: int = 100, offset: int = 0) -> List[ClaimFile]:
        """Search files with various criteria."""
        stmt = select(ClaimFile).where(ClaimFile.is_deleted == 0)
        
        # Add search conditions
        if query:
            stmt = stmt.where(
                or_(
                    ClaimFile.filename.ilike(f"%{query}%"),
                    ClaimFile.original_filename.ilike(f"%{query}%"),
                    ClaimFile.description.ilike(f"%{query}%")
                )
            )
        
        if customer_id:
            stmt = stmt.where(ClaimFile.customer_id == customer_id)
        
        if document_type:
            stmt = stmt.where(ClaimFile.document_type == document_type)
        
        if date_from:
            stmt = stmt.where(ClaimFile.created_at >= date_from)
        
        if date_to:
            stmt = stmt.where(ClaimFile.created_at <= date_to)
        
        stmt = stmt.order_by(ClaimFile.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def increment_download_count(self, file_id: UUID) -> bool:
        """Increment download count for a file."""
        file_obj = await self.get_by_id(file_id)
        if file_obj:
            file_obj.download_count = (file_obj.download_count or 0) + 1
            await self.session.flush()
            return True
        return False


class FileAccessLogRepository(BaseRepository[FileAccessLog]):
    """Repository for FileAccessLog model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(FileAccessLog, session)
    
    async def log_access(self, file_id: UUID, user_id: Optional[UUID], access_type: str,
                        ip_address: Optional[str], user_agent: Optional[str],
                        access_status: str = "success", failure_reason: Optional[str] = None,
                        session_id: Optional[str] = None) -> FileAccessLog:
        """Log file access event."""
        access_log = FileAccessLog(
            file_id=file_id,
            user_id=user_id,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent,
            access_status=access_status,
            failure_reason=failure_reason,
            session_id=session_id
        )
        
        self.session.add(access_log)
        await self.session.flush()
        return access_log
    
    async def get_access_logs_by_file(self, file_id: UUID, limit: int = 100, offset: int = 0) -> List[FileAccessLog]:
        """Get access logs for a specific file."""
        stmt = select(FileAccessLog).where(FileAccessLog.file_id == file_id)
        stmt = stmt.order_by(FileAccessLog.access_time.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_access_logs_by_user(self, user_id: UUID, limit: int = 100, offset: int = 0) -> List[FileAccessLog]:
        """Get access logs for a specific user."""
        stmt = select(FileAccessLog).where(FileAccessLog.user_id == user_id)
        stmt = stmt.order_by(FileAccessLog.access_time.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_suspicious_activity(self, threshold: int = 10, time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """Get suspicious access activity."""
        from datetime import datetime, timedelta
        
        time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        # Get users with high access frequency
        stmt = select(
            FileAccessLog.user_id,
            FileAccessLog.ip_address,
            func.count(FileAccessLog.id).label("access_count")
        ).where(
            and_(
                FileAccessLog.access_time >= time_threshold,
                FileAccessLog.access_status == "success"
            )
        ).group_by(
            FileAccessLog.user_id,
            FileAccessLog.ip_address
        ).having(func.count(FileAccessLog.id) > threshold)
        
        result = await self.session.execute(stmt)
        return [
            {
                "user_id": row.user_id,
                "ip_address": row.ip_address,
                "access_count": row.access_count
            }
            for row in result.all()
        ]


class FileValidationRuleRepository(BaseRepository[FileValidationRule]):
    """Repository for FileValidationRule model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(FileValidationRule, session)
    
    async def get_by_document_type(self, document_type: str) -> Optional[FileValidationRule]:
        """Get validation rule by document type."""
        stmt = select(FileValidationRule).where(
            and_(
                FileValidationRule.document_type == document_type,
                FileValidationRule.is_active == 1
            )
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_active_rules(self) -> List[FileValidationRule]:
        """Get all active validation rules."""
        stmt = select(FileValidationRule).where(FileValidationRule.is_active == 1)
        stmt = stmt.order_by(FileValidationRule.priority.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()