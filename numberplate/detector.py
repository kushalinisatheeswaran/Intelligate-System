"""
License Plate Detector Module
==============================
Uses a two-tier detection strategy:
  1. YOLOv8 (if ultralytics + a custom license plate .pt model are available)
  2. OpenCV Haar Cascade fallback (ships with opencv-python, no download needed)

Both backends return a list of cropped plate images with bounding box coords.
"""

import cv2
import os
import logging
import numpy as np

logger = logging.getLogger("anpr_system")

# ---------------------------------------------------------------------------
# Tier 1: Try loading YOLOv8 licence-plate model
# ---------------------------------------------------------------------------
_yolo_model = None
_yolo_available = False

def _try_load_yolo():
    """Attempt to load a YOLOv8 licence-plate detection model once."""
    global _yolo_model, _yolo_available
    model_path = os.path.join(os.path.dirname(__file__), "models", "best.pt")
    if not os.path.exists(model_path):
        model_path = os.path.join(os.path.dirname(__file__), "license_plate_detector.pt")
    if not os.path.exists(model_path):
        return
    try:
        from ultralytics import YOLO
        _yolo_model = YOLO(model_path)
        _yolo_available = True
        logger.info(f"YOLOv8 license-plate model loaded from: {model_path}")
    except Exception as e:
        logger.warning(f"Could not load YOLOv8 model ({e}). Falling back to Haar cascade.")

_try_load_yolo()

# ---------------------------------------------------------------------------
# Tier 2: OpenCV Haar Cascade (always available)
# ---------------------------------------------------------------------------
_cascade_path = os.path.join(
    cv2.data.haarcascades, "haarcascade_russian_plate_number.xml"
)
_plate_cascade = cv2.CascadeClassifier(_cascade_path)
if _plate_cascade.empty():
    logger.warning("Haar cascade for plate detection failed to load!")


# ===========================  PUBLIC API  ==================================

def detect_plates_in_frame(frame):
    """
    Detect licence plates in a BGR frame.

    Returns:
        list[dict]: Each dict has:
            - 'crop'  : numpy.ndarray – cropped plate image (BGR)
            - 'bbox'  : tuple (x, y, w, h) relative to the input frame
            - 'conf'  : float – detection confidence (0-1)
    """
    if frame is None:
        return []

    if _yolo_available:
        return _detect_yolo(frame)
    return _detect_haar(frame)


def detect_plate(image_path: str):
    """
    Backwards-compatible API: accept an image path and return
    the best cropped plate image (preprocessed for OCR), or the
    full preprocessed image if no plate region is found.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    plates = detect_plates_in_frame(img)
    if plates:
        # Return the highest-confidence crop
        best = max(plates, key=lambda p: p["conf"])
        return preprocess_for_ocr(best["crop"])
    # Fallback: preprocess full image
    return preprocess_for_ocr(img)


def preprocess_frame(frame):
    """Legacy wrapper used by main.py — kept for compatibility."""
    return preprocess_for_ocr(frame)


def preprocess_for_ocr(image):
    """
    Full OCR-optimised preprocessing pipeline:
      1. Grayscale
      2. Resize (normalise height to ~60 px for Tesseract sweet-spot)
      3. Bilateral filter (denoise while keeping edges)
      4. Adaptive threshold (binarise)
    Returns the processed grayscale image.
    """
    if image is None:
        return None

    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Resize: Tesseract works best with character height ~30-50 px.
    # Normalise the plate image to height = 80 px.
    h, w = gray.shape[:2]
    if h > 0:
        target_h = 80
        scale = target_h / h
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Bilateral filter — removes noise but keeps edges
    denoised = cv2.bilateralFilter(gray, 11, 17, 17)

    # CLAHE — adaptive histogram equalisation for contrast boost
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Otsu thresholding — automatic optimal binary split
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh


# ===========================  PRIVATE BACKENDS  ============================

def _detect_yolo(frame):
    """Run YOLOv8 inference and return plate crops."""
    results = _yolo_model.predict(frame, verbose=False, conf=0.25)
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            # Clamp coordinates
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)
            crop = frame[y1:y2, x1:x2]
            if crop.size > 0:
                detections.append({
                    "crop": crop,
                    "bbox": (x1, y1, x2 - x1, y2 - y1),
                    "conf": conf,
                })
    return detections


def _detect_haar(frame):
    """
    Haar cascade detection — good at finding rectangular plate-like regions.
    Returns the same structure as _detect_yolo.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    # Equalise histogram so cascade works in varying light
    gray = cv2.equalizeHist(gray)

    rects = _plate_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(80, 20),
        maxSize=(600, 200),
    )

    detections = []
    for (x, y, w, h) in rects:
        # Filter by aspect ratio — plates are wide rectangles (ratio 2:1 – 6:1)
        aspect = w / h if h > 0 else 0
        if 1.5 <= aspect <= 7.0:
            crop = frame[y:y+h, x:x+w]
            if crop.size > 0:
                detections.append({
                    "crop": crop,
                    "bbox": (x, y, w, h),
                    "conf": 0.6,   # Haar doesn't give confidence; use fixed value
                })
    return detections
