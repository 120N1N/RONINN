from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import backend.db.models as models
import backend.db.database as database
import backend.db.schemas as schemas
from backend.core.orchestrator import Orchestrator
from backend.core import auth
from backend.core.limiter import limiter
import os
from datetime import datetime

router = APIRouter()
orchestrator = Orchestrator()

# --- AUTH ---
@router.post("/auth/register")
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user: raise HTTPException(status_code=400, detail="Username taken")
    hashed = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        email=user.email, 
        hashed_password=hashed,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add(new_user)
    db.commit()
    return {"status": "success"}

import time
from fastapi import Request
import redis
from backend.config import settings

# Attempt to connect to Redis for Rate Limiting
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None

login_attempts = {} # Fallback in-memory

@router.post("/auth/login")
def login(user: schemas.UserLogin, request: Request, db: Session = Depends(database.get_db)):
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.headers.get("x-real-ip", request.client.host if request.client else "unknown")
        
    current_time = time.time()
    
    # Check rate limit using Redis if available
    if redis_client:
        attempts_key = f"login_fail:{client_ip}"
        attempts = redis_client.get(attempts_key)
        if attempts and int(attempts) >= 5:
            ttl = redis_client.ttl(attempts_key)
            if ttl > 0:
                raise HTTPException(status_code=429, detail="Too many failed login attempts. Please try again later.")
    else:
        # Fallback to in-memory rate limiting
        if client_ip in login_attempts:
            attempts, lockout_time = login_attempts[client_ip]
            if lockout_time and current_time < lockout_time:
                raise HTTPException(status_code=429, detail="Too many failed login attempts. Please try again later.")
            elif lockout_time and current_time >= lockout_time:
                login_attempts[client_ip] = (0, None)

    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        if redis_client:
            attempts_key = f"login_fail:{client_ip}"
            current_attempts = redis_client.incr(attempts_key)
            if current_attempts == 1:
                redis_client.expire(attempts_key, 900) # Set TTL to 900 seconds (15 mins) on first fail
        else:
            attempts, _ = login_attempts.get(client_ip, (0, None))
            attempts += 1
            if attempts >= 5:
                login_attempts[client_ip] = (attempts, current_time + 900)
            else:
                login_attempts[client_ip] = (attempts, None)
            
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    # Reset attempts on successful login
    if redis_client:
        attempts_key = f"login_fail:{client_ip}"
        redis_client.delete(attempts_key)
    else:
        if client_ip in login_attempts:
            del login_attempts[client_ip]

    token = auth.create_access_token(data={"sub": db_user.username})
    
    # Cookie Security Flags
    response = JSONResponse(content={"access_token": token, "token_type": "bearer", "status": "success"})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=(settings.APP_ENV == "production"),
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response

@router.post("/auth/logout")
def logout(token: str = Depends(auth.oauth2_scheme)):
    # Blacklist token in Redis
    if redis_client:
        ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        redis_client.setex(f"blacklist_{token}", ttl, "true")
        
    response = JSONResponse(content={"status": "success", "message": "Berhasil logout."})
    response.delete_cookie("access_token", httponly=True, secure=(settings.APP_ENV == "production"), samesite="lax")
    return response

@router.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

import shutil

@router.put("/auth/profile")
def update_profile(profile_data: schemas.UserProfileUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Check if username is being changed and is already taken
    if profile_data.username != current_user.username:
        existing_user = db.query(models.User).filter(models.User.username == profile_data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username is already taken")
    
    current_user.username = profile_data.username
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
        
    if profile_data.password:
        current_user.hashed_password = auth.get_password_hash(profile_data.password)
        
    db.commit()
    
    # Issue a new token since username (subject) might have changed
    token = auth.create_access_token(data={"sub": current_user.username})
    return {"status": "success", "access_token": token, "token_type": "bearer"}

@router.post("/auth/photo")
def upload_profile_photo(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Allowed: JPG, PNG, WEBP, GIF.")
        
    # Generate unique filename
    import uuid
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs("uploads/avatars", exist_ok=True)
    file_path = os.path.join("uploads", "avatars", filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Delete old photo if exists
    if current_user.photo_url:
        old_filename = current_user.photo_url.split("/")[-1]
        old_path = os.path.join("uploads", "avatars", old_filename)
        if os.path.exists(old_path) and os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass
                
    photo_url = f"{settings.API_BASE_URL.rstrip('/api')}/static/avatars/{filename}"
    current_user.photo_url = photo_url
    db.commit()
    
    return {"status": "success", "photo_url": photo_url}

# --- SCAN CORE ---
@router.post("/scan")
@limiter.limit("2/minute")
def start_scan(request_obj: Request, request: schemas.ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    new_scan = models.Scan(target=request.target, mode=request.mode, status="PENDING", progress=0, user_id=current_user.id)
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    background_tasks.add_task(orchestrator.run_scan, new_scan.id, request.target, request.mode)
    return new_scan

@router.get("/scan/{scan_id}")
def get_scan(scan_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id).first()
    if not scan: raise HTTPException(status_code=404, detail="Not found")
    return scan

@router.get("/scans/{scan_id}/tools/{tool_name}/log")
def get_tool_log(scan_id: str, tool_name: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id).first()
    if not scan: raise HTTPException(status_code=404, detail="Scan not found")
    
    import os
    safe_scan_id = os.path.basename(str(scan_id))
    safe_tool_name = os.path.basename(str(tool_name))
    log_path = os.path.join("tools_output", safe_scan_id, f"{safe_tool_name}.txt")
    
    if not os.path.exists(log_path):
        return {"log": "No raw log available or tool did not generate output."}
        
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        return {"log": f.read()}

@router.get("/reports")
def list_reports(db: Session = Depends(database.get_db), offset: int = 0, limit: int = 10, current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Scan).filter(models.Scan.user_id == current_user.id).order_by(models.Scan.last_scan_at.desc()).offset(offset).limit(limit).all()

# --- EXPORTS ---
@router.get("/reports/{scan_id}/json")
def export_json(scan_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id).first()
    if not scan: raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content={"id": scan.id, "target": scan.target, "findings": scan.findings})

@router.delete("/reports/{scan_id}")
def delete_report(scan_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id).first()
    if not scan: raise HTTPException(status_code=404, detail="Not found")
    
    # Delete database record
    db.delete(scan)
    db.commit()
    
    # Optionally delete files in tools_output
    import shutil
    import os
    
    # Sanitize scan_id to prevent path traversal
    safe_scan_id = os.path.basename(str(scan_id))
    output_dir = os.path.join("tools_output", safe_scan_id)
    if os.path.exists(output_dir) and safe_scan_id:
        shutil.rmtree(output_dir)
        
    return {"status": "deleted"}

@router.get("/reports/{scan_id}/pdf")
def export_pdf(scan_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id).first()
    if not scan: raise HTTPException(status_code=404, detail="Not found")
    
    try:
        from backend.utils.pdf_generator import create_pdf_report
        pdf_path = create_pdf_report(scan)
        return FileResponse(path=pdf_path, filename=f"Corvus_Report_{scan.id}.pdf", media_type='application/pdf')
    except ImportError as e:
        return {"error": "ReportLab is not installed or PDF generation failed. Run pip install reportlab."}
    except Exception as e:
        return {"error": f"Failed to generate PDF: {str(e)}"}
