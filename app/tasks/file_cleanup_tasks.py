"""Celery tasks for file cleanup operations."""
import asyncio
import logging
from datetime import datetime, timedelta

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper function to run async code in Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
        asyncio.set_event_loop(None)


async def _cleanup_orphan_files():
    """
    Delete orphan files older than 24 hours.
    
    Orphan files are files that were uploaded during OCR processing but never
    linked to a claim. These files are stored in temp_uploads/ and should be
    linked to a claim within 24 hours, otherwise they will be cleaned up.
    
    Returns:
        Dictionary with cleanup statistics
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, and_
    from app.config import config
    from app.models import ClaimFile
    from app.services.nextcloud_service import nextcloud_service
    
    # Create fresh engine for this event loop
    engine = create_async_engine(config.DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    session = SessionLocal()
    deleted_count = 0
    error_count = 0
    
    try:
        # Find orphan files older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        stmt = select(ClaimFile).where(
            and_(
                ClaimFile.claim_id == None,  # Orphan (no claim linked)
                ClaimFile.uploaded_at < cutoff_time,
                ClaimFile.is_deleted == 0
            )
        )
        
        result = await session.execute(stmt)
        orphan_files = result.scalars().all()
        
        logger.info(f"[cleanup_orphan_files] Found {len(orphan_files)} orphan file(s) to clean up")
        
        for file in orphan_files:
            try:
                # Delete from Nextcloud
                await nextcloud_service.delete_file(file.storage_path)
                
                # Soft delete in database
                file.is_deleted = 1
                file.deleted_at = datetime.utcnow()
                deleted_count += 1
                
                logger.info(f"[cleanup_orphan_files] Deleted orphan file: {file.id} ({file.original_filename})")
                
            except Exception as e:
                error_count += 1
                logger.error(f"[cleanup_orphan_files] Failed to delete orphan file {file.id}: {e}")
        
        await session.commit()
        
        result = {
            "deleted": deleted_count,
            "errors": error_count,
            "found": len(orphan_files)
        }
        
        logger.info(f"[cleanup_orphan_files] Cleanup complete: {result}")
        return result
        
    finally:
        await session.close()
        await engine.dispose()


@celery_app.task(
    name="cleanup_orphan_files",
    bind=True,
    max_retries=2,
    default_retry_delay=3600  # 1 hour retry delay
)
def cleanup_orphan_files(self):
    """
    Task: Clean up orphan files older than 24 hours.
    
    This task runs every hour and deletes files that were uploaded during OCR
    processing but never linked to a claim within 24 hours.
    """
    logger.info("[cleanup_orphan_files] Starting orphan file cleanup task")
    try:
        result = run_async(_cleanup_orphan_files())
        logger.info(f"[cleanup_orphan_files] Task completed: {result}")
        return result
    except Exception as e:
        logger.error(f"[cleanup_orphan_files] Task failed: {e}", exc_info=True)
        raise self.retry(exc=e)
