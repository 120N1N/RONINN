from sqlalchemy.orm import Session
from backend.db import models
from backend.queue.tasks import run_orchestrator_task
import re
import socket
import hashlib
import json
from datetime import datetime, timedelta
from backend.config import settings

def normalize_target(target: str) -> str:
    """ Normalizes target to a consistent format. """
    return target.lower().strip().replace("https://", "").replace("http://", "").split("/")[0]

def is_valid_target(target: str) -> bool:
    """ Validates target and checks for restricted IPs. """
    # 1. Clean target
    target = normalize_target(target)
    
    # 2. Check if valid hostname or IP
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        return False
        
    # 3. Block private IPs
    private_patterns = [
        r"^127\.", r"^10\.", r"^172\.(1[6-9]|2[0-9]|3[0-1])\.", r"^192\.168\.",
        r"^169\.254\.", r"^0\.", r"^localhost$"
    ]
    
    for pattern in private_patterns:
        if re.match(pattern, ip) or re.match(pattern, target):
            return False
            
    return True

def get_or_create_scan(db: Session, target: str, mode: str, config_snapshot: dict = None, user_id: str = None, parent_scan_id: str = None):
    normalized_target = normalize_target(target)
    
    # Calculate target_hash
    config_str = json.dumps(config_snapshot, sort_keys=True) if config_snapshot else "{}"
    target_hash_data = f"{normalized_target}:{mode}:{config_str}"
    target_hash = hashlib.sha256(target_hash_data.encode()).hexdigest()
    
    # TTL Check
    cache_threshold = datetime.utcnow() - timedelta(seconds=settings.SCAN_CACHE_TTL)
    
    existing_scan = db.query(models.Scan).filter(
        models.Scan.target_hash == target_hash,
        models.Scan.status == "COMPLETED",
        models.Scan.finished_at > cache_threshold
    ).order_by(models.Scan.created_at.desc()).first()
    
    if existing_scan:
        return existing_scan, True # Return existing scan and 'is_cached' flag
    
    # Create new scan
    new_scan = models.Scan(
        target=target,
        target_hash=target_hash,
        mode=mode,
        config_snapshot=config_snapshot,
        user_id=user_id,
        parent_scan_id=parent_scan_id
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    return new_scan, False

def get_active_scans_count(db: Session) -> int:
    return db.query(models.Scan).filter(models.Scan.status == "RUNNING").count()

import os
import threading
from backend.core.orchestrator import Orchestrator

def enqueue_scan(scan_id: str, target: str, mode: str):
    """ Enqueue task to Celery or run locally. """
    if os.getenv("USE_LOCAL_TASK_RUNNER") == "true":
        print(f"[!] Running scan {scan_id} in Local Mode...")
        # Jalankan di thread terpisah agar tidak memblock API
        thread = threading.Thread(target=Orchestrator().run_scan, args=(scan_id, target, mode))
        thread.start()
    else:
        run_orchestrator_task.delay(scan_id, target, mode)
