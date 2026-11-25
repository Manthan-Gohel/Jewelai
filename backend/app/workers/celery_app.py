import os
import sys
from celery import Celery
from app.core.config import settings

# In test/dev environment or when Redis is not configured, run in-process with memory broker
is_dev_or_test = (
    os.environ.get("TESTING") == "True" or
    settings.ENVIRONMENT in ["test", "development"] or
    any("pytest" in arg for arg in sys.argv)
)

broker_url = "memory://" if is_dev_or_test else settings.REDIS_URL
backend_url = None if is_dev_or_test else settings.REDIS_URL

celery_app = Celery(
    "jewelai_tasks",
    broker=broker_url,
    backend=backend_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_always_eager=is_dev_or_test,
    task_eager_propagates=is_dev_or_test,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.process_incoming_webhook_event": {"queue": "instagram_webhooks"},
    },
    task_default_retry_delay=5,
    task_max_retries=3,
)
