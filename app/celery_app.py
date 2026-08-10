from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "my_app",
    broker=settings.REDIS_URL,
    backend=settings.CELERY_BACKEND,
    include=["app.tasks"]
)

celery_app.conf.update(
    result_expires=3600,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_max_tasks_per_child=30,
    task_soft_time_limit=300,
    task_time_limit=330,
)

celery_app.conf.beat_schedule = {
    "delete_expired_links": {
        "task": "app.tasks.delete_expired_links",
        "schedule": crontab(hour=3),
    }
}
