import os
import time
import cv2
import requests
import socketio

from ocr import extract_plate_text, get_plate_region, preprocess_for_ocr, OCR_CONFIG
from ocr_manager import OCRManager
from arduino_manager import ArduinoManager
import pytesseract

# =========================
# CONFIG
# =========================
DEVICE_ID = "entry_cam_1"
SERVER_URL = "http://10.34.13.95:5050"  # CHANGE THIS
BACKEND_API_URL = f"{SERVER_URL}/api/verify"

HEADERS = {"Content-Type": "application/json"}

# =========================
# SOCKET.IO
# =========================
sio = socketio.Client()
arduino = None

@sio.event
def connect():
    print("📡 ENTRY Connected to backend!")

@sio.event
def disconnect():
    print("📡 ENTRY Disconnected")

@sio.on("execute_gate_action")
def gate_action(data):
    action = data.get("action", "").upper()
    print(f"📡 Gate Action: {action}")
    if arduino:
        arduino.send_command(action)

try:
    sio.connect(SERVER_URL)
except Exception as e:
    print("Socket error:", e)

# =========================
# ARDUINO
# =========================
arduino = ArduinoManager("/dev/cu.usbserial-120", 115200, sio)
arduino.connect()

# =========================
# OCR
# =========================
ocr = OCRManager(confirm_threshold=3, history_window=6)

cap = cv2.VideoCapture(0)

last_plate = None
last_time = 0
COOLDOWN = 5

print("🚀 ENTRY SYSTEM STARTED")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    roi, _ = get_plate_region(frame)
    if roi is None:
        roi = frame

    binary = preprocess_for_ocr(roi)

    try:
        raw = pytesseract.image_to_string(binary, config=OCR_CONFIG).strip()
    except:
        raw = None

    plate = ocr.stabilise(raw) if raw else None

    if plate:
        formatted = ocr.format_plate(plate)
        final_plate = formatted or plate
        current_time = time.time()

        if final_plate != last_plate or (current_time - last_time) > COOLDOWN:
            print("📸 ENTRY Plate:", final_plate)

            payload = {
                "type": "plate",
                "value": final_plate,
                "direction": "entry",
                "device_id": DEVICE_ID
            }

            try:
                res = requests.post(BACKEND_API_URL, json=payload, timeout=3)
                print("📡 Response:", res.status_code, res.text)

            except Exception as e:
                print("Backend error:", e)

            last_plate = final_plate
            last_time = current_time

    cv2.imshow("ENTRY CAMERA", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
sio.disconnect()