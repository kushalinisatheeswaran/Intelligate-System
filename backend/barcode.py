import sys
import time
import cv2
import requests

try:
    import zxingcpp
except ImportError:
    print("\n[ERROR] zxing-cpp is missing.")
    sys.exit(1)

# Configuration: Replace with your actual backend API URL
BACKEND_URL = "http://127.0.0.1:5050/api/scan"  # Adjust port/path to match your backend route

# Debounce settings to prevent spamming duplicate requests
last_scanned_data = None
last_scanned_time = 0
COOLDOWN_SECONDS = 3  # Wait 3 seconds before allowing the same ID to scan again

cap = cv2.VideoCapture(0)
print("Barcode scanner active and linked to API backend. Scan an ID...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    detected_barcodes = zxingcpp.read_barcodes(frame)

    for barcode in detected_barcodes:
        barcode_data = barcode.text
        barcode_format = str(barcode.format)
        current_time = time.time()
        
        # Check if it's a new barcode or if the cooldown period has passed
        if barcode_data != last_scanned_data or (current_time - last_scanned_time) > COOLDOWN_SECONDS:
            last_scanned_data = barcode_data
            last_scanned_time = current_time
            
            print(f"Sending to backend -> {barcode_format}: {barcode_data}")
            
            # Send data directly to your backend service
            try:
                payload = {"barcode": barcode_data, "type": barcode_format}
                response = requests.post(BACKEND_URL, json=payload, timeout=5)
                print(f"Backend response status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"[Network Error] Could not connect to backend server: {e}")

        # Position box drawing logic
        if hasattr(barcode, 'position') and barcode.position:
            pos = barcode.position
            try:
                top_left = (int(pos.top_left.x), int(pos.top_left.y))
                bottom_right = (int(pos.bottom_right.x), int(pos.bottom_right.y))
                cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
                cv2.putText(frame, barcode_data, (top_left[0], top_left[1] - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            except AttributeError:
                pass

    cv2.imshow('Student ID Scanner', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()