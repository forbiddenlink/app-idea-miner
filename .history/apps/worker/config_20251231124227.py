"""
Worker Configuration
Environment-based configuration for Celery workers.
"""

import os


def get_worker_config():
    """
    Get worker configuration from environment variables.
    """
    return {
        "broker_url": os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
        "result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
        "worker_count": int(os.getenv("CELERY_WORKERS", "2")),
        "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
    }
