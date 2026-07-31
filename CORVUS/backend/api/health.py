from fastapi import APIRouter
from backend.db.database import engine
import redis
from backend.config import settings
import subprocess

router = APIRouter()

@router.get("/health")
def health_check():
    health_status = {
        "status": "healthy",
        "database": "ok",
        "redis": "ok",
        "tools": "ok"
    }
    
    # Check DB
    try:
        with engine.connect() as connection:
            pass
    except Exception:
        health_status["database"] = "error"
        health_status["status"] = "unhealthy"
        
    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
    except Exception:
        health_status["redis"] = "error"
        health_status["status"] = "unhealthy"
        
    # Check essential tools (e.g. nuclei)
    try:
        subprocess.run(["nuclei", "-version"], capture_output=True, check=True)
    except Exception:
        health_status["tools"] = "partial" # Not critical but tool layer is affected
        
    return health_status
