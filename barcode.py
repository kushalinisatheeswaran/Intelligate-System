import cv2
from pyzbar.pyzbar import decode

# Initialize the camera feed (0 is usually the built-in webcam)
cap = cv2.VideoCapture(0)

print("Barcode scanner active. Hold a barcode up to the camera...")
print("Press 'q' on your keyboard to quit.")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame. Is your webcam open in another app?")
        break

    # Find and decode barcodes in the frame using pyzbar [cite: 12, 109]
    detected_barcodes = decode(frame)

    for barcode in detected_barcodes:
        # Extract the string data from the barcode 
        barcode_data = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        
        print(f"Found {barcode_type} Barcode! Data: {barcode_data}")
        
        # Draw a green bounding box around the detected barcode on screen
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, barcode_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the live video feed window
    cv2.imshow('Student ID Scanner', frame)

    # Break the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up and close windows
cap.release()
cv2.destroyAllWindows()