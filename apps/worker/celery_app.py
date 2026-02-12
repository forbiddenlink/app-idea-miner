"""
Celery Application Configuration
Main Celery instance with task routing and configuration.
"""

import os

from celery import Celery
from kombu import Exchange, Queue

# Load configuration from environment
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

# Create Celery application
celery_app = Celery(
    "app_idea_miner",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Celery Configuration
celery_app.conf.update(
    # Task Discovery
    imports=[
        "apps.worker.tasks.ingestion",
        "apps.worker.tasks.processing",
        "apps.worker.tasks.clustering",
    ],
    # Task Routing
    task_routes={
        "apps.worker.tasks.ingestion.*": {"queue": "ingestion"},
        "apps.worker.tasks.processing.*": {"queue": "processing"},
        "apps.worker.tasks.clustering.*": {"queue": "clustering"},
    },
    # Task Queues
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("ingestion", Exchange("ingestion"), routing_key="ingestion"),
        Queue("processing", Exchange("processing"), routing_key="processing"),
        Queue("clustering", Exchange("clustering"), routing_key="clustering"),
    ),
    # Task Execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # seconds
    task_max_retries=3,
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Results
    result_expires=3600,  # 1 hour
    result_extended=True,
    # Worker
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Beat (Scheduled Tasks)
    beat_schedule={
        "fetch-rss-feeds": {
            "task": "apps.worker.tasks.ingestion.fetch_rss_feeds",
            "schedule": 21600.0,  # Every 6 hours
        },
        # Add more scheduled tasks here as needed
    },
)


if __name__ == "__main__":
    celery_app.start()
