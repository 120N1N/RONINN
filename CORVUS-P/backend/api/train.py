from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from celery.result import AsyncResult

from backend.db.database import get_db
from backend.db import models
from backend.core import auth
from backend.queue.celery_app import celery_app
from backend.core.train import RandomForestTrainer
import os
import uuid
import threading

local_jobs = {}

router = APIRouter(prefix="/train", tags=["Random Forest Training"])

# --- schemas ---
class TrainParams(BaseModel):
    n_estimators: Optional[int] = 100
    max_depth: Optional[int] = None

class TrainRequest(BaseModel):
    dataset_id: int
    params: TrainParams

class TrainedModelResponse(BaseModel):
    id: int
    dataset_id: int
    name: str
    params: dict
    metrics: dict
    model_path: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }

# --- routes ---

@router.post("")
def start_model_training(
    req: TrainRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Only Admin can access ML Training.")
        
    # Verify dataset exists and belongs to user
    dataset = db.query(models.PreprocessedDataset).filter(
        models.PreprocessedDataset.id == req.dataset_id,
        models.PreprocessedDataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
        
    if os.getenv("USE_LOCAL_TASK_RUNNER") == "true":
        job_id = str(uuid.uuid4())
        local_jobs[job_id] = {"status": "training", "progress": 20, "model_id": None, "error": None}
        
        def run_local_train(jid, did, params, uid):
            try:
                local_jobs[jid]["progress"] = 60
                model_id = RandomForestTrainer.train(did, params, uid)
                local_jobs[jid]["status"] = "completed"
                local_jobs[jid]["progress"] = 100
                local_jobs[jid]["model_id"] = model_id
            except Exception as e:
                local_jobs[jid]["status"] = "failed"
                local_jobs[jid]["error"] = str(e)
                
        threading.Thread(target=run_local_train, args=(job_id, req.dataset_id, req.params.model_dump(), current_user.id)).start()
        return {"job_id": job_id, "status": "PENDING"}
    else:
        # Trigger Celery background task
        task = celery_app.send_task(
            "train_model_task",
            args=[req.dataset_id, req.params.model_dump(), current_user.id]
        )
        return {"job_id": task.id, "status": "PENDING"}

@router.get("/status/{job_id}")
def check_training_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if os.getenv("USE_LOCAL_TASK_RUNNER") == "true":
        if job_id in local_jobs:
            job = local_jobs[job_id]
            if job["status"] == "completed":
                model_record = db.query(models.TrainedModel).filter(models.TrainedModel.id == job["model_id"]).first()
                if model_record:
                    return {
                        "status": "completed",
                        "progress": 100,
                        "metrics": model_record.metrics,
                        "model_id": job["model_id"]
                    }
            return job
        return {"status": "failed", "error": "Job not found in local runner memory"}

    res = AsyncResult(job_id, app=celery_app)
    
    if res.state == "PENDING":
        return {"status": "training", "progress": 20}
    elif res.state == "STARTED":
        return {"status": "training", "progress": 60}
    elif res.state == "FAILURE":
        return {"status": "failed", "error": str(res.result)}
    elif res.state == "SUCCESS":
        # Extract model ID returned by Celery task
        task_result = res.result
        model_id = task_result.get("model_id")
        
        # Query metrics from DB
        model_record = db.query(models.TrainedModel).filter(models.TrainedModel.id == model_id).first()
        if model_record:
            return {
                "status": "completed",
                "progress": 100,
                "metrics": model_record.metrics,
                "model_id": model_id
            }
        return {"status": "completed", "progress": 100}
        
    return {"status": res.state.lower()}

@router.get("/models", response_model=List[TrainedModelResponse])
def list_trained_models(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.TrainedModel).filter(
        models.TrainedModel.user_id == current_user.id
    ).all()

