import os
import time
import cv2
import requests
import socketio

from ocr import extract_plate_text
from ocr_manager import OCRManager
from arduino_manager import ArduinoManager

# =========================
# CONFIG
# =========================
BACKEND_API_URL = "http://127.0.0.1:5050/api/verify"
HEADERS = {
    "Content-Type": "application/json"
}

# =========================
# SOCKET.IO CLIENT SETUP
# =========================
sio = socketio.Client()
arduino = None

@sio.event
def connect():
    print("📡 Connected to Socket.IO backend!")

@sio.event
def disconnect():
    print("📡 Disconnected from Socket.IO backend!")

@sio.on("execute_gate_action")
def on_execute_gate_action(data):
    action = data.get("action", "").upper()
    print(f"📡 Socket.IO execute_gate_action: {action}")
    if arduino:
        arduino.send_command(action)

# Try connection to Socket.IO backend
try:
    sio.connect("http://127.0.0.1:5050")
except Exception as e:
    print(f"⚠️ Failed to connect to Socket.IO backend: {e}")

# =========================
# ARDUINO MANAGER INIT
# =========================
SERIAL_PORT = "/dev/cu.usbserial-120"
arduino = ArduinoManager(port=SERIAL_PORT, baud=115200, socket_client=sio)
arduino.connect()

# =========================
# OCR & SESSION CONTROL
# =========================
ocr = OCRManager(confirm_threshold=3, history_window=6)
cap = cv2.VideoCapture(0)

last_sent_plate = None
last_send_time = 0.0
SEND_COOLDOWN = 10.0  # seconds debounce window
empty_counter = 0

print("🚀 ANPR System Started. Press 'q' to quit.")
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    # Process every 5th frame to reduce load while keeping rendering smooth
    if frame_count % 5 != 0:
        cv2.imshow("ANPR System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Use standard ROI detection from ocr.py
    from ocr import get_plate_region
    roi, bbox = get_plate_region(frame)
    if roi is None:
        roi = frame

    # 1. OCR Preprocess and Read
    from ocr import preprocess_for_ocr, OCR_CONFIG
    import pytesseract
    binary = preprocess_for_ocr(roi)
    try:
        raw_text = pytesseract.image_to_string(binary, config=OCR_CONFIG)
        raw_text = raw_text.strip().replace("\n", "").replace("\r", "")
    except Exception:
        raw_text = None

    # 2. OCR Stabilization
    stabilized_plate = ocr.stabilise(raw_text) if raw_text else None

    if stabilized_plate:
        # 3. OCR Format Verification
        formatted = ocr.format_plate(stabilized_plate)
        plate_to_send = formatted if formatted else stabilized_plate

        print(f"🔍 Stabilized OCR: Raw={raw_text} | Formatted={formatted} | Target={plate_to_send}")
        empty_counter = 0

        # Debouncing
        current_time = time.time()
        is_new = plate_to_send != last_sent_plate
        cooldown_ok = (current_time - last_send_time) > SEND_COOLDOWN

        if is_new or cooldown_ok:
            print(f"📸 Sending plate to backend: {plate_to_send}")

            os.makedirs("unknown_plates", exist_ok=True)
            image_path = f"unknown_plates/{plate_to_send}_{int(current_time)}.jpg"
            cv2.imwrite(image_path, frame)

            payload = {
                "type": "plate",
                "value": plate_to_send,
                "direction": "entry",
                "image_path": image_path
            }

            try:
                response = requests.post(
                    BACKEND_API_URL,
                    json=payload,
                    headers=HEADERS,
                    timeout=3
                )
                print(f"📡 Backend Response: {response.status_code} {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    if status == "granted" or data.get("message") == "granted":
                        print("🚪 Access Granted! Backend triggers gate opening sequence.")
                    elif status == "ignored":
                        print("ℹ️ Duplicate detection ignored by Backend.")
                    else:
                        print("🔒 Access Denied by Backend.")
            except Exception as e:
                print(f"⚠️ Verification request failed: {e}")

            last_sent_plate = plate_to_send
            last_send_time = current_time

    else:
        # Lane empty detection
        if last_sent_plate:
            empty_counter += 1
            if empty_counter > 6:  # ~1.5 - 2 seconds (6 * 5 = 30 frames)
                print("🏁 Lane cleared")
                # Clear session on backend
                try:
                    clear_url = BACKEND_API_URL.replace("/verify", "/lane/clear")
                    requests.post(
                        clear_url,
                        json={"plate": last_sent_plate},
                        headers=HEADERS,
                        timeout=3
                    )
                except Exception as e:
                    print(f"⚠️ Failed to clear lane on backend: {e}")

                last_sent_plate = None
                empty_counter = 0
                ocr.reset()

    # Display video feed
    cv2.imshow("ANPR System", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
arduino.close()
sio.disconnect()