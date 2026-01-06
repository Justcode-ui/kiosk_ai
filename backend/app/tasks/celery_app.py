"""
Celery Application Configuration
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "kioskai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.follow_up_tasks", "app.tasks.daily_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-inactive-customers": {
        "task": "app.tasks.follow_up_tasks.check_inactive_customers",
        "schedule": 3600.0,  # Run every hour
    },
    "daily-business-summary": {
        "task": "app.tasks.daily_tasks.send_all_daily_summaries",
        "schedule": 24 * 3600.0, # Run once a day (roughly)
        # For production use crontab for exact time
    },
}
