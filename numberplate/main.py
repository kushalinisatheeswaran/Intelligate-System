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
SERVER_URL = "http://10.34.9.39:5050"  # Target Raspberry Pi 4 backend
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
barcode_detector = cv2.barcode.BarcodeDetector()
qr_detector = cv2.QRCodeDetector()

cap = cv2.VideoCapture(0)

last_plate = None
last_time = 0
COOLDOWN = 5

print("🚀 ENTRY SYSTEM STARTED")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to grab frame, retrying...")
        time.sleep(0.1)
        continue

    # Try detecting Barcodes or QR codes first
    scanned_id = None
    try:
        retval, points, straight_code = barcode_detector.detectAndDecode(frame)
        if retval:
            if isinstance(retval, (list, tuple)):
                retval = retval[0]
            val = str(retval).strip()
            if val and val.isdigit():
                scanned_id = val
    except Exception:
        pass

    if not scanned_id:
        try:
            retval, points, straight_code = qr_detector.detectAndDecode(frame)
            if retval:
                val = str(retval).strip()
                if val and val.isdigit():
                    scanned_id = val
        except Exception:
            pass

    if scanned_id:
        current_time = time.time()
        if scanned_id != last_plate or (current_time - last_time) > COOLDOWN:
            print("📸 ENTRY Scanned Student ID / Barcode:", scanned_id)
            payload = {
                "type": "barcode",
                "value": scanned_id,
                "direction": "entry",
                "device_id": DEVICE_ID
            }
            try:
                res = requests.post(BACKEND_API_URL, json=payload, timeout=3)
                print("📡 Response:", res.status_code, res.text)
            except Exception as e:
                print("Backend error:", e)
            last_plate = scanned_id
            last_time = current_time

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