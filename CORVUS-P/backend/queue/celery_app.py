from celery import Celery
from backend.config import settings

celery_app = Celery(
    "corvus_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=settings.MAX_CONCURRENT_SCAN
)

# Priority Queues
celery_app.conf.task_routes = {
    "run_orchestrator_task": {"queue": "high_priority"}
}
