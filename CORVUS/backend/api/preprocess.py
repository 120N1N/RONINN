import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

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
        
    # Validate file extension to prevent insecure uploads (e.g. .exe, .sh)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".txt", ".json", ".parquet", ".pq"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV, JSON, TXT, or Parquet datasets are allowed.")

    # Ensure temporary upload folder exists
    os.makedirs("uploads", exist_ok=True)
    temp_path = f"uploads/{uuid_filename(file.filename)}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 1. Load Data
        df = DatasetPreprocessor.load_data(temp_path)
        
        # 2. Impute NaNs / Handle Missing values
        df = DatasetPreprocessor.handle_missing(df)
        
        # 3. Normalize & map Label Target
        df = DatasetPreprocessor.map_labels(df, label_col)
        
        # 4. Feature Extraction & Engineering
        df_featured = DatasetPreprocessor.extract_features(df)
        
        # 5. Split train/test (80/20)
        X_train, X_test, y_train, y_test = DatasetPreprocessor.split_data(df_featured)
        
        # 6. Save preprocessed CSVs & Commit to DB
        name_clean = dataset_name or file.filename
        dataset_id = DatasetPreprocessor.save_preprocessed(
            X_train, X_test, y_train, y_test, name_clean, current_user.id
        )
        
        # Query created record
        dataset_record = db.query(models.PreprocessedDataset).filter(models.PreprocessedDataset.id == dataset_id).first()
        return dataset_record
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preprocessing failed: {str(e)}")
    finally:
        # Clean up temporary raw upload file
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
        
    # Check both train and test paths
    train_path = dataset.file_path
    if not os.path.exists(train_path):
        raise HTTPException(status_code=404, detail="Preprocessed dataset file is missing from disk.")
        
    filename = os.path.basename(train_path)
    return FileResponse(
        train_path,
        media_type="text/csv",
        filename=f"preprocessed_{dataset.name.replace(' ', '_')}_{filename}"
    )

def uuid_filename(orig: str) -> str:
    import uuid
    ext = os.path.splitext(orig)[1]
    return f"{uuid.uuid4().hex}{ext}"
