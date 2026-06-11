import os
import sys
import json
import logging
from datetime import datetime
import shutil
import threading
import time
import cv2

# Import modular components
from detector import detect_plate, preprocess_frame
from ocr import extract_plate_text
from db_check import get_owner_details
from gate_controller import control_gate
import cv2
from ocr import extract_plate_text

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    plate = extract_plate_text(frame)

    if plate:
        print("Detected Plate:", plate)

    cv2.imshow("ANPR", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()