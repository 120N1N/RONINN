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

@router.delete("/models/{model_id}")
def delete_trained_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    model = db.query(models.TrainedModel).filter(
        models.TrainedModel.id == model_id,
        models.TrainedModel.user_id == current_user.id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.model_path and os.path.exists(model.model_path):
        try:
            os.remove(model.model_path)
        except Exception:
            pass
    db.delete(model)
    db.commit()
    return {"status": "success", "message": f"Model {model_id} deleted"}


# --- Confidence Score Analysis Routes ---

class ConfidenceAnalysisRequest(BaseModel):
    scan_id: Optional[str] = None  # None or "all"
    high_threshold: Optional[float] = 80.0
    medium_threshold: Optional[float] = 50.0

@router.get("/scan-reports")
def list_scan_reports_for_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Query reports matching exactly the reports presented in the Reports page (10 reports)
    scans = db.query(models.Scan).filter(
        models.Scan.user_id == current_user.id
    ).order_by(models.Scan.last_scan_at.desc()).limit(10).all()
    
    total_findings_all = 0
    items = []
    for s in scans:
        findings = s.findings or []
        count = len(findings)
        total_findings_all += count
        items.append({
            "id": s.id,
            "target": s.target,
            "mode": s.mode,
            "status": s.status,
            "findings_count": count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "last_scan_at": s.last_scan_at.isoformat() if s.last_scan_at else None
        })
    return {
        "scans": items,
        "total_scans": len(items),
        "total_findings": total_findings_all
    }

@router.post("/confidence-analysis")
def perform_confidence_analysis(
    req: ConfidenceAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    from backend.core.confidence import get_active_rf_model, analyze_findings
    import logging
    _logger = logging.getLogger("corvus.confidence")

    # 1. Load active Random Forest model
    model, model_meta = get_active_rf_model(db)
    if model is None:
        raise HTTPException(
            status_code=400,
            detail="Random Forest model belum dilatih. Silakan lakukan training model terlebih dahulu pada section Random Forest Training."
        )

    # 2. Gather findings from database scan history
    target_findings = []
    selected_scan = None
    if req.scan_id and req.scan_id.strip() not in ["", "all"]:
        selected_scan = db.query(models.Scan).filter(
            models.Scan.id == req.scan_id,
            models.Scan.user_id == current_user.id
        ).first()
        if not selected_scan:
            raise HTTPException(status_code=404, detail="Scan history report tidak ditemukan.")
        for f in (selected_scan.findings or []):
            f_copy = dict(f)
            f_copy["_scan_id"] = selected_scan.id
            f_copy["_target"] = selected_scan.target
            target_findings.append(f_copy)
    else:
        # Match exactly the reports displayed in Reports page (10 reports)
        all_scans = db.query(models.Scan).filter(
            models.Scan.user_id == current_user.id
        ).order_by(models.Scan.last_scan_at.desc()).limit(10).all()
        for s in all_scans:
            for f in (s.findings or []):
                f_copy = dict(f)
                f_copy["_scan_id"] = s.id
                f_copy["_target"] = s.target
                target_findings.append(f_copy)

    # 3. Analyze findings
    result = analyze_findings(
        raw_findings=target_findings,
        model=model,
        model_meta=model_meta,
        high_threshold=req.high_threshold or 80.0,
        medium_threshold=req.medium_threshold or 50.0
    )

    # 4. Save analysis record if single scan
    if selected_scan is not None:
        try:
            tool_outputs = dict(selected_scan.tool_outputs or {})
            tool_outputs["confidence_analysis"] = {
                "analyzed_at": result["analyzed_at"],
                "model_name": model_meta.get("name"),
                "avg_confidence": result["avg_confidence"],
                "total_findings": result["total_findings"],
                "high_count": result["high_confidence_count"],
                "med_count": result["medium_confidence_count"],
                "low_count": result["low_confidence_count"]
            }
            selected_scan.tool_outputs = tool_outputs
            db.commit()
        except Exception as e:
            _logger.warning(f"Failed to persist confidence analysis snapshot to scan: {e}")

    return result


