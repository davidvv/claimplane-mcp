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

__all__ = [
    "send_claim_submitted_email",
    "send_status_update_email",
    "send_document_rejected_email",
]
