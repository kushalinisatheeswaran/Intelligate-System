import time
import cv2
import requests
import re
from ocr import extract_plate_text

def format_plate(text: str):
    """
    Normalizes and validates OCR plate text.
    Rules: Remove spaces/specials, uppercase, exactly 2-3 letters followed by 4 digits.
    Returns formatted plate (e.g., AB-1234) or None if invalid.
    """
    if not text:
        return None
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
    match = re.fullmatch(r'([A-Z]{2,3})([0-9]{4})', cleaned)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None

# 💡 Target the production API route exposed by verify.py
BACKEND_API_URL = "http://127.0.0.1:5050/api/verify"

# Token placeholder since your blueprint uses @jwt_required()
# If you don't use authentication checks for local nodes yet, you can temporarily disable @jwt_required() in verify.py
HEADERS = {
    "Content-Type": "application/json"
    # "Authorization": "Bearer YOUR_JWT_TOKEN_HERE" # Add if required
}

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
            
            payload = {
                "type": "plate",
                "value": plate,
                "direction": "entry",
                "image_path": f"numberplate/unknown_plates/unknown_{plate}.jpg"
            }
            
            try:
                # Fire standard synchronous HTTP payload
                response = requests.post(BACKEND_API_URL, json=payload, headers=HEADERS, timeout=3)
                print(f"📡 Backend Response ({response.status_code}): {response.text}")
            except Exception as e:
                print(f"⚠️ Network transmission delay: {e}")
                
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