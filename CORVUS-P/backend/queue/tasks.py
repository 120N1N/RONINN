from .celery_app import celery_app
from backend.core.orchestrator import Orchestrator
from backend.db.database import SessionLocal
from backend.db import models
import asyncio
import logging

logger = logging.getLogger("corvus.tasks")

@celery_app.task(bind=True, name="run_orchestrator_task")
def run_orchestrator_task(self, scan_id: str, target: str, mode: str):
    """
    Celery task that runs the Orchestrator.
    """
    db = SessionLocal()
    try:
        # Update status to RUNNING
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if not scan: return
        scan.status = "RUNNING"
        db.commit()

        # Progress callback for WebSocket (simplified for task)
        async def progress_callback(percentage: int, message: str):
            # Update DB
            db_inner = SessionLocal()
            s = db_inner.query(models.Scan).filter(models.Scan.id == scan_id).first()
            if s:
                s.progress = percentage
                db_inner.commit()
            db_inner.close()
            # Here we would also push to Redis for WebSocket bridge

        # Run Orchestrator
        orchestrator = Orchestrator()
        orchestrator.run_scan(scan_id, target, mode)

        # Re-fetch the scan from DB to ensure it was marked COMPLETED by orchestrator
        db_final = SessionLocal()
        final_scan = db_final.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if final_scan and final_scan.status != "FAILED":
            final_scan.status = "COMPLETED"
            final_scan.progress = 100
            db_final.commit()
        db_final.close()

    except Exception as e:
        logger.error(f"Task failed for scan {scan_id}: {str(e)}")
        if scan:
            scan.status = "FAILED"
            db.commit()
    finally:
        db.close()

@celery_app.task(bind=True, name="train_model_task")
def train_model_task(self, dataset_id: int, params: dict, user_id: str):
    """
    Celery task that executes RandomForest model training in the background.
    """
    from backend.core.train import RandomForestTrainer
    logger.info(f"Starting Random Forest training task for dataset {dataset_id}")
    try:
        model_id = RandomForestTrainer.train(dataset_id, params, user_id)
        logger.info(f"Finished training task for dataset {dataset_id}. Model ID: {model_id}")
        return {"status": "completed", "model_id": model_id}
    except Exception as e:
        logger.error(f"Training task failed for dataset {dataset_id}: {str(e)}")
        raise e
