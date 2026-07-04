import os
import time
import cv2
import requests
import socketio

from ocr import extract_plate_text, get_plate_region
from ocr_manager import OCRManager
from arduino_manager import ArduinoManager

# =========================
# CONFIG
# =========================
DEVICE_ID = "exit_cam_1"

BACKEND_URL = "http://10.34.13.95:5050"
VERIFY_URL = f"{BACKEND_URL}/api/verify"

HEADERS = {"Content-Type": "application/json"}

# =========================
# SOCKET.IO
# =========================
sio = socketio.Client()
arduino = ArduinoManager("/dev/cu.usbserial-120", 115200, sio)

@sio.event
def connect():
    print("📡 EXIT Connected to backend")

@sio.on("execute_gate_action")
def on_gate_action(data):
    action = data.get("action", "").upper()
    print(f"🚪 EXIT Gate action: {action}")
    arduino.send_command(action)

sio.connect(BACKEND_URL)

# =========================
# OCR
# =========================
ocr = OCRManager(confirm_threshold=3, history_window=6)

cap = cv2.VideoCapture(0)

last_plate = None
last_time = 0
COOLDOWN = 5

print("🚀 EXIT SYSTEM STARTED")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    roi, _ = get_plate_region(frame)
    if roi is None:
        roi = frame

    plate = extract_plate_text(roi)

    if plate:
        plate = ocr.stabilise(plate)
        formatted = ocr.format_plate(plate)

        final_plate = formatted or plate

        now = time.time()

        if final_plate != last_plate or (now - last_time > COOLDOWN):
            print(f"📸 EXIT sending: {final_plate}")

            payload = {
                "type": "plate",
                "value": final_plate,
                "direction": "exit",
                "device_id": DEVICE_ID
            }

            try:
                res = requests.post(VERIFY_URL, json=payload, headers=HEADERS)
                print("📡 RESPONSE:", res.status_code, res.text)
            except Exception as e:
                print("❌ API error:", e)

            last_plate = final_plate
            last_time = now

    cv2.imshow("EXIT CAM", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
sio.disconnect()