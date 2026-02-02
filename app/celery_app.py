"""
Celery application configuration for async task processing.

This file sets up Celery to handle background tasks like sending emails.
Celery uses Redis as a message broker - tasks go into Redis, and workers pick them up.
"""
import logging
from celery import Celery
from celery.schedules import crontab
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
        'app.tasks.draft_tasks.*': {'queue': 'notifications'},
        'app.tasks.gdpr_retention_task.*': {'queue': 'notifications'},
    },

    # Default queue name
    task_default_queue='notifications',

    # Result expiration - how long to keep task results (1 hour)
    result_expires=3600,

    # Celery Beat schedule for periodic tasks (draft reminders and cleanup)
    beat_schedule={
        # Check for 30-min inactive drafts every 5 minutes
        'send-draft-reminder-30min': {
            'task': 'send_draft_reminder_30min',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
        # Send day-5 reminders once per day at 10:00 UTC
        'send-draft-reminder-day5': {
            'task': 'send_draft_reminder_day5',
            'schedule': crontab(hour=10, minute=0),  # Daily at 10:00
        },
        # Send day-8 reminders once per day at 10:00 UTC
        'send-draft-reminder-day8': {
            'task': 'send_draft_reminder_day8',
            'schedule': crontab(hour=10, minute=15),  # Daily at 10:15
        },
        # Cleanup expired drafts (day 11) once per day at 03:00 UTC
        'cleanup-expired-drafts': {
            'task': 'cleanup_expired_drafts',
            'schedule': crontab(hour=3, minute=0),  # Daily at 03:00
        },
        # Send final reminders (day 45) once per day at 10:30 UTC
        'send-final-reminder': {
            'task': 'send_final_reminder',
            'schedule': crontab(hour=10, minute=30),  # Daily at 10:30
        },
        # Cleanup orphan files (24h+) every hour
        'cleanup-orphan-files': {
            'task': 'cleanup_orphan_files',
            'schedule': crontab(minute=0),  # Every hour at :00
        },
        # GDPR 7-year data retention purge (1st of every month at 02:00)
        'run-gdpr-retention-purge': {
            'task': 'run_retention_purge',
            'schedule': crontab(day_of_month=1, hour=2, minute=0),
        },
    },
)

# Auto-discover tasks from the tasks package
# This tells Celery to look for @celery_app.task decorators in these modules
celery_app.autodiscover_tasks(['app.tasks'])

logger.info("Celery app initialized successfully")
logger.info(f"Broker URL: {config.CELERY_BROKER_URL}")
logger.info(f"Result Backend: {config.CELERY_RESULT_BACKEND}")
