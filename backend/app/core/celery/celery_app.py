from celery import Celery
from kombu import Queue
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "soc_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.core.celery.tasks.scan_tasks",
        "app.core.celery.tasks.asset_tasks",
        "app.core.celery.tasks.vulnerability_tasks",
        "app.core.celery.tasks.report_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Task routing
    task_routes={
        "scan_tasks.*": {"queue": "scan_queue"},
        "asset_tasks.*": {"queue": "asset_queue"},
        "vulnerability_tasks.*": {"queue": "vuln_queue"},
        "report_tasks.*": {"queue": "report_queue"},
    },

    # Define queues
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("scan_queue", routing_key="scan_tasks"),
        Queue("asset_queue", routing_key="asset_tasks"),
        Queue("vuln_queue", routing_key="vulnerability_tasks"),
        Queue("report_queue", routing_key="report_tasks"),
    ),

    # Retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,

    # Worker configuration
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)