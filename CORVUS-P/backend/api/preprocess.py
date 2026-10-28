import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from backend.db.database import get_db
from backend.db import models
from backend.core import auth
from backend.core.preprocess import DatasetPreprocessor

router = APIRouter(prefix="/preprocess", tags=["Dataset Preprocessing"])

class PreprocessedDatasetResponse(BaseModel):
    id: int
    name: str
    rows: int
    features: int
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True

def uuid_filename(orig: str) -> str:
    ext = os.path.splitext(orig)[1]
    return f"{uuid.uuid4().hex}{ext}"

@router.post("/upload", response_model=PreprocessedDatasetResponse)
async def upload_and_preprocess_dataset(
    file: UploadFile = File(...),
    label_col: str = Form(...),
    dataset_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Only Admin can access Dataset Upload.")
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".txt", ".json", ".parquet", ".pq"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV, JSON, TXT, or Parquet datasets are allowed.")

    os.makedirs("uploads", exist_ok=True)
    temp_path = f"uploads/{uuid_filename(file.filename)}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        name_clean = dataset_name or file.filename
        
        # Eksekusi pipeline secara end-to-end dengan chunking untuk menghemat RAM
        dataset_id = DatasetPreprocessor.process_end_to_end(
            file_path=temp_path,
            label_col=label_col,
            dataset_name=name_clean,
            user_id=current_user.id
        )
        
        dataset_record = db.query(models.PreprocessedDataset).filter(models.PreprocessedDataset.id == dataset_id).first()
        return dataset_record
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preprocessing failed: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/datasets", response_model=List[PreprocessedDatasetResponse])
def list_preprocessed_datasets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.PreprocessedDataset).filter(
        models.PreprocessedDataset.user_id == current_user.id
    ).all()

@router.get("/datasets/{dataset_id}")
def download_preprocessed_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    dataset = db.query(models.PreprocessedDataset).filter(
        models.PreprocessedDataset.id == dataset_id,
        models.PreprocessedDataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset record not found.")
        
    train_path = dataset.file_path
    if not os.path.exists(train_path):
        raise HTTPException(status_code=404, detail="Preprocessed dataset file is missing from disk.")
        
    filename = os.path.basename(train_path)
    return FileResponse(
        train_path,
        media_type="text/csv",
        filename=f"preprocessed_{dataset.name.replace(' ', '_')}_{filename}"
    )
