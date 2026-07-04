import os
from app import create_app
from app.services.fcm_service import send_gate_alert

app = create_app()
with app.app_context():
    print("Triggering single test push notification...")
    result = send_gate_alert("open", triggered_by="Test Runner")
    print("Result:", result)
