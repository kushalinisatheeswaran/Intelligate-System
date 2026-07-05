import eventlet
eventlet.monkey_patch()   # MUST be first — before any other imports

from app import create_app
from app.services.socket_service import socketio
from app.services.fcm_service import send_unknown_vehicle_alert
import os

app = create_app()

if __name__ == "__main__":
    print("=" * 50)
    print("  IntelliGate Backend — Starting")
    print(f"  Socket.IO: active (eventlet)")
    print(f"  Firebase:  {os.getenv('FIREBASE_ENABLED', 'false')}")
    print(f"  ESP32:     {os.getenv('ESP32_MODE', 'stub')}")
    print("=" * 50)

    socketio.run(
        app,
        host  = "0.0.0.0",   # accessible from phone on same WiFi
        port  = 5050,        # Changed from 5000 to bypass macOS Control Center
        debug = True
    )