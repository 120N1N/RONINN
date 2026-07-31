from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
import redis.asyncio as aioredis
from backend.config import settings

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                continue

manager = ConnectionManager()

@router.websocket("/ws/progress/{scan_id}")
async def websocket_progress(websocket: WebSocket, scan_id: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/ws/scans/{scan_id}/log")
async def websocket_logs(websocket: WebSocket, scan_id: str):
    await websocket.accept()
    
    redis_url = settings.REDIS_URL
    try:
        redis_client = aioredis.from_url(redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"scan_logs:{scan_id}")
        
        async def reader(ws: WebSocket):
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        await ws.send_text(message["data"])
                    except Exception:
                        break
                        
        task = asyncio.create_task(reader(websocket))
        
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            task.cancel()
            await pubsub.unsubscribe(f"scan_logs:{scan_id}")
            await redis_client.close()
    except Exception as e:
        await websocket.close()
