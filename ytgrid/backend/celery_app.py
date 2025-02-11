"""
Celery App Initialization for YTGrid (Version 3)

This module configures and initializes the Celery application using broker and result backend
settings from the configuration. It also ensures that the tasks module is imported so that
tasks (such as "ytgrid.tasks.run_automation") are registered.
"""

import os
from celery import Celery
from ytgrid.utils.config import config

# Retrieve broker and result backend URLs from configuration
broker_url = config.CELERY_BROKER_URL
result_backend = config.CELERY_RESULT_BACKEND

# Initialize the Celery application for YTGrid
celery_app = Celery('ytgrid', broker=broker_url, backend=result_backend)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Ensure that the tasks module is imported so that tasks are registered.
import ytgrid.backend.tasks  # noqa: F401

# Optionally, you can autodiscover tasks:
# celery_app.autodiscover_tasks(['ytgrid.backend.tasks'])
