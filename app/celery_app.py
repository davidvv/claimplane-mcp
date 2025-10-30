"""
Celery application configuration for async task processing.

This file sets up Celery to handle background tasks like sending emails.
Celery uses Redis as a message broker - tasks go into Redis, and workers pick them up.
"""
import logging
from celery import Celery
from app.config import config

# Set up logging
logger = logging.getLogger(__name__)

# Create Celery app instance
# The name 'flight_claim_worker' is just for identification in logs
celery_app = Celery(
    'flight_claim_worker',
    broker=config.CELERY_BROKER_URL,  # Where tasks are queued (Redis)
    backend=config.CELERY_RESULT_BACKEND  # Where results are stored (Redis)
)

# Configure Celery with our settings from config.py
celery_app.conf.update(
    # Serialization - how tasks are converted to/from JSON
    task_serializer=config.CELERY_TASK_SERIALIZER,
    result_serializer=config.CELERY_RESULT_SERIALIZER,
    accept_content=config.CELERY_ACCEPT_CONTENT,

    # Timezone settings
    timezone=config.CELERY_TIMEZONE,
    enable_utc=config.CELERY_ENABLE_UTC,

    # Task tracking - lets us see task status while it's running
    task_track_started=config.CELERY_TASK_TRACK_STARTED,

    # Time limit - kill tasks that take too long (30 minutes)
    task_time_limit=config.CELERY_TASK_TIME_LIMIT,

    # Retry settings - if a task fails, retry it automatically
    task_acks_late=True,  # Only mark task as done AFTER it completes successfully
    task_reject_on_worker_lost=True,  # Retry if worker crashes

    # Task routing - send all tasks to the 'notifications' queue
    task_routes={
        'app.tasks.claim_tasks.*': {'queue': 'notifications'},
    },

    # Default queue name
    task_default_queue='notifications',

    # Result expiration - how long to keep task results (1 hour)
    result_expires=3600,
)

# Auto-discover tasks from the tasks package
# This tells Celery to look for @celery_app.task decorators in these modules
celery_app.autodiscover_tasks(['app.tasks'])

logger.info("Celery app initialized successfully")
logger.info(f"Broker URL: {config.CELERY_BROKER_URL}")
logger.info(f"Result Backend: {config.CELERY_RESULT_BACKEND}")
