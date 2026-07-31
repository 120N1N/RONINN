# backend/services/progress_service.py
import json
from backend.api.websocket import manager

class ProgressService:
    @staticmethod
    async def send_update(scan_id: str, percentage: int, message: str):
        """Sends real-time progress to frontend (Point #8, #35)."""
        payload = {
            "scan_id": scan_id,
            "progress": percentage,
            "message": message
        }
        await manager.broadcast(json.dumps(payload))
