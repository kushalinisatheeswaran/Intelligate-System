import os
import time
import cv2
import requests
import re
import serial
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
while True:
    ret, frame = cap.read()
    if not ret:
        break

    plate = extract_plate_text(frame)

    if plate:
        raw = plate
        formatted = format_plate(raw)

        if not formatted:
            print(f"❌ Invalid plate: {raw}")
            continue

        print(f"🔍 OCR: Raw={raw} | Formatted={formatted}")
        plate = formatted
        empty_counter = 0

        current_time = time.time()

        is_new = plate != last_sent_plate
        cooldown_ok = (current_time - last_send_time) > SEND_COOLDOWN

        if is_new or cooldown_ok:

            print(f"📸 Sending plate: {plate}")

            # Save image
            os.makedirs("unknown_plates", exist_ok=True)
            image_path = f"unknown_plates/{plate}_{int(current_time)}.jpg"
            cv2.imwrite(image_path, frame)

            payload = {
                "type": "plate",
                "value": plate,
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

                # =========================
                # SUCCESS → OPEN GATE (SYNCHRONIZED)
                # =========================
                if response.status_code == 200:
                    data = response.json()

                    # Checks if the backend verification status is granted
                    if data.get("status") == "granted" or data.get("message") == "granted":
                        print("🚪 Access Granted!")

                        if nano_serial and nano_serial.is_open:
                            # 1. Clear out any background buffer clutter
                            nano_serial.reset_input_buffer()
                            nano_serial.reset_output_buffer()
                            
                            # 2. Send the execution string
                            nano_serial.write(b"OPEN\n")
                            print("⚡ Gate OPEN signal sent to Arduino Nano. Waiting for hardware sequence...")
                            
                            # 3. Synchronous loop: Block Python frames until Nano reports completion
                            while True:
                                line = nano_serial.readline().decode('utf-8').strip()
                                if "Gate Cycle Completed" in line:
                                    print("⚙️ Hardware Message: Gate cycle finished cleanly.")
                                    break
                                elif line:
                                    print(f"⚙️ Hardware Log: {line}")
                            
                            # 4. Refresh timestamp AFTER gate fully closes so cooldown starts now
                            current_time = time.time()
                        else:
                            print("⚠️ Arduino Nano connection not open")
                    else:
                        print("🔒 Access Denied by Backend.")

            except Exception as e:
                print(f"⚠️ Request failed: {e}")

            last_sent_plate = plate
            last_send_time = current_time

    else:
        # Lane empty detection
        if last_sent_plate:
            empty_counter += 1

            if empty_counter > 30:  # ~3 seconds depending on FPS
                print("🏁 Lane cleared")
                last_sent_plate = None
                empty_counter = 0

    # Display camera view
    cv2.imshow("ANPR System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()