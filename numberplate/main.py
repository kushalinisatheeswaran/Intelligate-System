import os
import time
import cv2
import requests
import re
import serial
import socketio
from ocr import extract_plate_text

# =========================
# CONFIG
# =========================
BACKEND_API_URL = "http://127.0.0.1:5050/api/verify"

HEADERS = {
    "Content-Type": "application/json"
    # "Authorization": "Bearer YOUR_JWT_TOKEN"  # Un-comment if JWT is enabled
}

# =========================
# PLATE FORMATTER
# =========================
def format_plate(text: str):
    """
    Converts OCR output into strict format: ABC-1234
    """
    if not text:
        return None

    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())

    match = re.match(r'^([A-Z]{2,3})(\d{4})$', cleaned)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    return None


# =========================
# ARDUINO NANO SERIAL SETUP
# =========================
SERIAL_PORT = "/dev/cu.usbserial-120"  # Your active MacBook Air port
BAUD_RATE = 115200

try:
    nano_serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("🔌 Arduino Nano connected successfully!")
    time.sleep(2) # Allow Arduino bootloader auto-reset to settle securely
except Exception as e:
    print(f"⚠️ Arduino Nano not connected on {SERIAL_PORT}: {e}")
    nano_serial = None


# =========================
# SOCKET.IO CLIENT SETUP
# =========================
sio = socketio.Client()

@sio.event
def connect():
    print("📡 Connected to Socket.IO backend!")

@sio.event
def disconnect():
    print("📡 Disconnected from Socket.IO backend!")

@sio.on("execute_gate_action")
def on_execute_gate_action(data):
    action = data.get("action", "").upper()
    print(f"📡 Socket.IO execute_gate_action received: {action}")
    if action in ("OPEN", "CLOSE"):
        if nano_serial and nano_serial.is_open:
            nano_serial.reset_input_buffer()
            nano_serial.reset_output_buffer()
            nano_serial.write(f"{action}\n".encode("utf-8"))
            print(f"⚡ Gate {action} signal sent to Arduino Nano from Socket.IO override.")
        else:
            print("⚠️ Arduino Nano connection not open for manual override")

try:
    sio.connect("http://127.0.0.1:5050")
except Exception as e:
    print(f"⚠️ Failed to connect to Socket.IO backend: {e}")


# =========================
# CAMERA INIT
# =========================
cap = cv2.VideoCapture(0)

print("🚀 ANPR System Started. Press 'q' to quit.")

# =========================
# STATE CONTROL
# =========================
last_sent_plate = None
last_send_time = 0
SEND_COOLDOWN = 10.0

empty_counter = 0
empty_reset_time = 3.0


# =========================
# MAIN LOOP
# =========================
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    # D. OCR Optimization: Process every 5th frame to reduce CPU load, but display every frame smoothly
    if frame_count % 5 != 0:
        cv2.imshow("ANPR System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    plate = extract_plate_text(frame)

    if plate:
        raw = plate
        formatted = format_plate(raw)

        # If it fails format check, we still send the raw text to the backend so the backend
        # can log it as an UNKNOWN_VEHICLE and trigger appropriate alert events.
        plate_to_send = formatted if formatted else raw

        print(f"🔍 OCR: Raw={raw} | Formatted={formatted} | Target={plate_to_send}")
        empty_counter = 0

        current_time = time.time()

        is_new = plate_to_send != last_sent_plate
        cooldown_ok = (current_time - last_send_time) > SEND_COOLDOWN

        if is_new or cooldown_ok:
            print(f"📸 Sending plate to backend: {plate_to_send}")

            # Save image
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

                print(f"📡 Backend: {response.status_code} {response.text}")

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == "granted" or data.get("message") == "granted":
                        print("🚪 Access Granted!")

                        if nano_serial and nano_serial.is_open:
                            nano_serial.reset_input_buffer()
                            nano_serial.reset_output_buffer()
                            nano_serial.write(b"OPEN\n")
                            print("⚡ Gate OPEN signal sent to Arduino Nano. Waiting for hardware sequence...")
                            
                            while True:
                                line = nano_serial.readline().decode('utf-8').strip()
                                if "Gate Cycle Completed" in line:
                                    print("⚙️ Hardware Message: Gate cycle finished cleanly.")
                                    break
                                elif line:
                                    print(f"⚙️ Hardware Log: {line}")
                            
                            current_time = time.time()
                        else:
                            print("⚠️ Arduino Nano connection not open")
                    elif data.get("status") == "ignored":
                        print("ℹ️ Duplicate detection ignored by Backend.")
                    else:
                        print("🔒 Access Denied by Backend.")

            except Exception as e:
                print(f"⚠️ Request failed: {e}")

            last_sent_plate = plate_to_send
            last_send_time = current_time

    else:
        # Lane empty detection / exit event
        if last_sent_plate:
            empty_counter += 1

            if empty_counter > 6:  # Since we process every 5th frame, 6 * 5 = 30 frames (~1-2 seconds)
                print("🏁 Lane cleared")
                # Clear session in backend so the vehicle state is reset
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

    # Display camera view
    cv2.imshow("ANPR System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()