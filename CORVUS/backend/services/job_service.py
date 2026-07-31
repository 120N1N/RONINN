# backend/services/job_service.py
from backend.queue.celery_app import celery_app
from backend.db import models

class JobService:
    @staticmethod
    def cancel_job(job_id: str):
        """Cancels a running Celery job (Point #21)."""
        celery_app.control.revoke(job_id, terminate=True)

    @staticmethod
    def get_job_status(job_id: str):
        """Gets status of a Celery job."""
        return celery_app.AsyncResult(job_id).status
