from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class ScanCreate(BaseModel):
    target: str
    mode: str = "normal" # quick, normal, deep
    enable_fuzz: bool = True
    include_subdomain: bool = True

class ScanResponse(BaseModel):
    id: str
    target: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FindingSchema(BaseModel):
    type: str
    severity: str
    source: str
    endpoint: str
    confidence: float
    
    class Config:
        from_attributes = True

class ScanDetail(ScanResponse):
    progress: int
    findings: List[FindingSchema]
    last_scan_at: datetime
    
    class Config:
        from_attributes = True
