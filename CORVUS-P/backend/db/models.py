from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    hashed_password = Column(String)
    scans = relationship("Scan", back_populates="owner")

class Scan(Base):
    __tablename__ = "scans"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    target = Column(String)
    target_hash = Column(String, index=True, nullable=True)
    mode = Column(String)
    config_snapshot = Column(JSON, nullable=True)
    status = Column(String, default="PENDING")
    progress = Column(Integer, default=0)
    current_step = Column(String, default="INITIALIZING")
    findings = Column(JSON, default=[])
    tool_outputs = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scan_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    parent_scan_id = Column(String, ForeignKey("scans.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="scans")

class VulnerabilityFingerprint(Base):
    __tablename__ = "vulnerability_fingerprints"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint = Column(String(64), unique=True, index=True) # SHA256 of endpoint+vuln_type+parameter
    first_seen_scan_id = Column(String, ForeignKey("scans.id"))
    last_seen_scan_id = Column(String, ForeignKey("scans.id"))

class LLMApiKey(Base):
    __tablename__ = "llm_api_keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    name = Column(String(100), nullable=True)
    api_key = Column(String, nullable=False) # stored encrypted
    model = Column(String(100), nullable=True) # stored chosen model
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = relationship("User")

class PreprocessedDataset(Base):
    __tablename__ = "preprocessed_datasets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    rows = Column(Integer)
    features = Column(Integer)
    file_path = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User")

class TrainedModel(Base):
    __tablename__ = "trained_models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("preprocessed_datasets.id"), nullable=False)
    name = Column(String(255))
    params = Column(JSON)
    metrics = Column(JSON)
    model_path = Column(String(512))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User")
    dataset = relationship("PreprocessedDataset")

class DeepValidateLog(Base):
    __tablename__ = "deep_validate_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    target = Column(String(255), nullable=True) # Domain or IP
    endpoint = Column(String(512), nullable=False)
    status = Column(String(50), nullable=False) # e.g., 'success', 'timeout', 'rejected_private_ip'
    timestamp = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User")
