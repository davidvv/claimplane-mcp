"""
Tasks package for async background processing.

This package contains Celery tasks that run in the background.
Tasks are picked up by Celery workers and executed asynchronously.
"""

# Import tasks so Celery can discover them
from app.tasks.claim_tasks import (
    send_claim_submitted_email,
    send_status_update_email,
    send_document_rejected_email,
)

from app.tasks.draft_tasks import (
    send_draft_reminder_30min,
    send_draft_reminder_day5,
    send_draft_reminder_day8,
    cleanup_expired_drafts,
    send_final_reminder,
)

from app.tasks.file_cleanup_tasks import cleanup_orphan_files

__all__ = [
    # Claim notification tasks
    "send_claim_submitted_email",
    "send_status_update_email",
    "send_document_rejected_email",
    # Draft reminder tasks (Celery Beat)
    "send_draft_reminder_30min",
    "send_draft_reminder_day5",
    "send_draft_reminder_day8",
    "cleanup_expired_drafts",
    "send_final_reminder",
    # File cleanup tasks (Celery Beat)
    "cleanup_orphan_files",
]
