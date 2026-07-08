from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from typing import List

logger = logging.getLogger("anpr.websockets")

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Admin dashboard connected via WebSocket.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("Admin dashboard disconnected.")

    async def broadcast_alert(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/anpr-events")
async def anpr_events_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time ANPR events.
    The ANPR Pipeline uses `manager.broadcast_alert` to push events here.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open, wait for client messages if any
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def alert_callback(plate_number: str, crop_image=None):
    """
    Callback function injected into the ANPRPipeline.
    Triggered when an unknown vehicle is detected.
    """
    # In production, crop_image should be uploaded to S3 and the URL sent here.
    # We will send a basic event structure for now.
    event_data = {
        "event_type": "unknown_vehicle",
        "plate_number": plate_number,
        "message": f"Alert: Unregistered plate {plate_number} detected at gate.",
    }
    await manager.broadcast_alert(event_data)

async def gate_callback(plate_number: str):
    """
    Callback function injected into the ANPRPipeline.
    Triggered when a registered vehicle is detected.
    """
    event_data = {
        "event_type": "access_granted",
        "plate_number": plate_number,
        "message": f"Access granted for registered plate {plate_number}.",
    }
    await manager.broadcast_alert(event_data)
