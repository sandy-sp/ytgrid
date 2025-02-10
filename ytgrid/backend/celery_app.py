import os
from celery import Celery
from ytgrid.utils.config import config

broker_url = config.CELERY_BROKER_URL
result_backend = config.CELERY_RESULT_BACKEND

celery_app = Celery('ytgrid', broker=broker_url, backend=result_backend)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Ensure that the tasks module is imported so that tasks are registered.
import ytgrid.backend.tasks  # This line forces registration of tasks like "ytgrid.tasks.run_automation"

# Optionally, you can autodiscover tasks:
# celery_app.autodiscover_tasks(['ytgrid.backend.tasks'])