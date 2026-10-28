from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    photo_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ScanRequest(BaseModel):
    target: str
    mode: str = "core"

class Finding(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    cvss: float
    location: str
    description: str
    points: List[str]
    remediation: str

class ScanResponse(BaseModel):
    id: str
    target: str
    mode: str
    status: str
    progress: int
    current_step: str
    findings: List[Finding]
    recon: Optional[dict] = None
    ai_summary: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True
