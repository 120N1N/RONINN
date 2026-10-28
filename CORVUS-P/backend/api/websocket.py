from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
try:
    import redis.asyncio as aioredis
    import redis
except ImportError:
    aioredis = None
    redis = None
from backend.config import settings

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                continue

manager = ConnectionManager()

class ScanLogManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, scan_id: str, websocket: WebSocket):
        await websocket.accept()
        if scan_id not in self.connections:
            self.connections[scan_id] = []
        self.connections[scan_id].append(websocket)

    def disconnect(self, scan_id: str, websocket: WebSocket):
        if scan_id in self.connections:
            if websocket in self.connections[scan_id]:
                self.connections[scan_id].remove(websocket)
            if not self.connections[scan_id]:
                del self.connections[scan_id]

    async def broadcast(self, scan_id: str, message: str):
        if scan_id in self.connections:
            for ws in list(self.connections[scan_id]):
                try:
                    await ws.send_text(message)
                except Exception:
                    self.disconnect(scan_id, ws)

log_manager = ScanLogManager()

# Global event loop tracking for thread-safe broadcast
_server_loop = None

def set_server_loop(loop):
    global _server_loop
    _server_loop = loop

def broadcast_scan_log_sync(scan_id: str, message: str):
    """
    Called synchronously from background tasks (e.g. Orchestrator)
    to broadcast live log lines to connected clients.
    """
    global _server_loop
    if _server_loop and _server_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(log_manager.broadcast(scan_id, message), _server_loop)
        except Exception:
            pass

    # Also broadcast via Redis if redis is running
    try:
        import redis
        rc = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        rc.publish(f"scan_logs:{scan_id}", message)
    except Exception:
        pass

@router.websocket("/ws/progress/{scan_id}")
async def websocket_progress(websocket: WebSocket, scan_id: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/ws/scans/{scan_id}/log")
async def websocket_logs(websocket: WebSocket, scan_id: str, token: str = None):
    # Verifikasi token autentikasi (mencegah unauthenticated connection membaca log)
    if not token:
        token = websocket.query_params.get("token")
        
    authenticated = False
    if token:
        try:
            from jose import jwt
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
            if payload.get("sub"):
                authenticated = True
        except Exception:
            authenticated = False

    if not authenticated:
        await websocket.close(code=1008)
        return

    global _server_loop
    _server_loop = asyncio.get_running_loop()
    
    await log_manager.connect(scan_id, websocket)
    
    # Send existing logs from DB on connect
    try:
        from backend.db.database import SessionLocal
        from backend.db import models
        db = SessionLocal()
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if scan and scan.logs:
            for log_line in scan.logs:
                await websocket.send_text(log_line)
        db.close()
    except Exception:
        pass
        
    # Also listen to Redis if available
    redis_task = None
    if aioredis is not None:
        try:
            redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(f"scan_logs:{scan_id}")
            
            async def redis_reader():
                try:
                    async for message in pubsub.listen():
                        if message["type"] == "message":
                            try:
                                await websocket.send_text(message["data"])
                            except Exception:
                                break
                except Exception:
                    pass
            
            redis_task = asyncio.create_task(redis_reader())
        except Exception:
            redis_task = None

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        log_manager.disconnect(scan_id, websocket)
        if redis_task:
            redis_task.cancel()
