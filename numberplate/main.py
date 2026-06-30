import os
import time
import cv2
import requests
import re
import serial  # 🔌 Added for USB communication to the ESP32
from ocr import extract_plate_text

def format_plate(text: str):
    """
    Normalizes OCR plate text.
    Returns cleaned alphanumeric string or None if empty.
    """
    if not text:
        return None
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
    if len(cleaned) >= 4:
        return cleaned
    return None

# 💡 Target the production API route exposed by verify.py
BACKEND_API_URL = "http://127.0.0.1:5050/api/verify"

# Token placeholder since your blueprint uses @jwt_required()
HEADERS = {
    "Content-Type": "application/json"
    # "Authorization": "Bearer YOUR_JWT_TOKEN_HERE" # Add if required
}

# 🔌 Initialize Serial Link to ESP32 board
try:
    # Matches the exact USB serial port configuration on your Mac
    esp32_serial = serial.Serial('/dev/cu.usbserial-0001', 115200, timeout=1)
    print("🔌 Hardware Serial Link to ESP32 established successfully!")
except Exception as e:
    print(f"⚠️ Could not open USB Serial Port: {e}. Running pipeline in standalone simulation mode.")
    esp32_serial = None

cap = cv2.VideoCapture(0)
print("🚀 Production HTTP-Driven ANPR Pipeline Active. Press 'q' to quit.")

# --- Dynamic Throttling Parameters ---
last_sent_plate = None
last_send_time = 0
SEND_COOLDOWN = 4.0        # Seconds before checking the same car again
NO_PLATE_RESET_TIME = 3.0  # Seconds of empty lane before resetting state memory

empty_frame_counter = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    plate = extract_plate_text(frame)

    if plate:
        raw_ocr = plate
        cleaned_str = re.sub(r'[^A-Z0-9]', '', raw_ocr.upper())
        formatted_plate = format_plate(raw_ocr)

        if formatted_plate:
            print(f"🔍 OCR Log: Raw='{raw_ocr}' | Cleaned='{cleaned_str}' | Formatted='{formatted_plate}'")
            plate = formatted_plate
            empty_frame_counter = 0 
        else:
            print(f"❌ OCR Log: Raw='{raw_ocr}' | Cleaned='{cleaned_str}' | Status=INVALID (Must be 2-3 letters + 4 digits)")
            continue

        current_time = time.time()
        is_new_vehicle = plate != last_sent_plate
        cooldown_expired = (current_time - last_send_time) > SEND_COOLDOWN

        if is_new_vehicle or cooldown_expired:
            print(f"📸 Camera Node captured: {plate} -> Sending POST request...")
            
            # Save the image
            os.makedirs("unknown_plates", exist_ok=True)
            image_path = f"unknown_plates/unknown_{plate}.jpg"
            cv2.imwrite(image_path, frame)
            
            payload = {
                "type": "plate",
                "value": plate,
                "direction": "entry",
                "image_path": f"numberplate/{image_path}"
            }
            
            try:
                # Fire standard synchronous HTTP payload to Flask
                response = requests.post(BACKEND_API_URL, json=payload, headers=HEADERS, timeout=3)
                print(f"📡 Backend Response ({response.status_code}): {response.text}")
                
                # 🎯 THE HARDWARE BRIDGE TRIGGER
                if response.status_code == 200:
                    res_json = response.json()
                    
                    # Match against the exact successful payload key found in your database logs
                    if res_json.get("status") == "granted":
                        if esp32_serial and esp32_serial.is_open:
                            print("⚡ Access Granted! Sending physical open signal via USB...")
                            esp32_serial.write(b'O')  # Write data byte 'O' to open the servo gate
                        else:
                            print("⚠️ Serial target unavailable. Physical actuation command dropped.")
                            
            except Exception as e:
                print(f"⚠️ Transmission delay or serialization fault: {e}")
                
            last_sent_plate = plate
            last_send_time = current_time
    else:
        # Monitor if vehicle has completely exited the checkpoint lane
        if last_sent_plate is not None:
            if empty_frame_counter == 0:
                empty_reset_start = time.time()
            
            empty_frame_counter += 1
            
            if (time.time() - empty_reset_start) > NO_PLATE_RESET_TIME:
                print("🏁 Checkpoint lane cleared. Ready for next vehicle approach.")
                last_sent_plate = None

    cv2.imshow("ANPR Gate System Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()