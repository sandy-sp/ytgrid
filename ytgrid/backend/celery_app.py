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
