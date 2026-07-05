import cv2
import pytesseract
import re
import numpy as np
from collections import Counter

# =========================
# SINGLE FAST OCR CONFIG
# Only PSM 7 (single text line) — fastest and most accurate for plates
# =========================
OCR_CONFIG = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

# =========================
# TEMPORAL STABILISER
# Prevents flicker by requiring a plate to appear N times before reporting
# =========================
_plate_history = []
CONFIRM_THRESHOLD = 3   # plate must appear this many times in the window
HISTORY_WINDOW    = 6   # look at the last N detections

# =========================
# CLEAN RESULT
# =========================
def clean_plate(text: str):
    text = re.sub(r'[^A-Z0-9]', '', text.upper())

    # Length: real plates are 4–10 chars
    if len(text) < 4 or len(text) > 10:
        return None

    # Must contain at least one letter AND one digit
    if not re.search(r'[A-Z]', text) or not re.search(r'[0-9]', text):
        return None

    # Reject "all-same" noise like "AAAA1" or "11111A"
    if len(set(text)) < 3:
        return None

    return text


# =========================
# TEMPORAL STABILISER
# =========================
def stabilise(plate: str):
    """
    Add plate to rolling history. Return it only when it has been
    seen CONFIRM_THRESHOLD times in the last HISTORY_WINDOW frames.
    This eliminates single-frame noise detections completely.
    """
    global _plate_history
    _plate_history.append(plate)
    _plate_history = _plate_history[-HISTORY_WINDOW:]   # keep window

    counts = Counter(_plate_history)
    best, freq = counts.most_common(1)[0]
    if freq >= CONFIRM_THRESHOLD:
        return best
    return None


def reset_stabiliser():
    """Call this when switching to a new scan session."""
    global _plate_history
    _plate_history = []


# =========================
# PREPROCESS — ONE FAST PATH
# =========================
def preprocess_for_ocr(roi):
    """
    Single optimised preprocessing path.
    Fast enough for real-time; good enough for most lighting conditions.
    """
    # Upscale: Tesseract works best with ~60-80px tall characters
    h, w = roi.shape[:2]
    if h < 60:
        scale = 60 / h
        roi = cv2.resize(roi, None, fx=scale, fy=scale,
                         interpolation=cv2.INTER_CUBIC)

    # Grayscale
    if len(roi.shape) == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi.copy()

    # CLAHE → improves contrast in both bright and dark conditions
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Bilateral filter → smooth noise, preserve character edges
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    # Otsu threshold → binary image (black text on white background)
    _, binary = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # If plate is dark-background / white-text, invert so text is dark
    # Heuristic: if more white pixels than black, invert
    if np.mean(binary) > 127:
        binary = cv2.bitwise_not(binary)

    return binary


# =========================
# FIND PLATE REGION
# =========================
def get_plate_region(frame):
    """
    Find the most plate-like rectangular region in the frame.
    Uses morphological closing to group characters first,
    then scores contours by aspect ratio + area.

    Returns (roi_bgr, bbox) or (None, None).
    """
    h_f, w_f = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Blur → edge detect
    blur  = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 80, 200)

    # Morphological close: joins the gaps between characters
    # Wide kernel captures the full plate width
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    best_score = 0.0
    best_bbox  = None

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h

        # Hard filters — skip obvious non-plates
        if w < 80 or h < 20:           continue   # too small
        if w < h:                       continue   # taller than wide
        if area > 0.6 * h_f * w_f:     continue   # basically the whole frame

        aspect = w / float(h)
        if not (1.5 <= aspect <= 7.0):  continue   # implausible ratio

        # Score: ideal ratio 2.5–5.0, ideal area > 2000 px
        aspect_score = 1.0 if 2.5 <= aspect <= 5.0 else 0.5
        area_score   = 1.0 if area > 2000 else (area / 2000)
        score = aspect_score * area_score

        if score > best_score:
            best_score = score
            pad = 6
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(w_f, x + w + pad)
            y2 = min(h_f, y + h + pad)
            best_bbox = (x1, y1, x2 - x1, y2 - y1)

    if best_bbox is None:
        return None, None

    x, y, w, h = best_bbox
    return frame[y:y+h, x:x+w], best_bbox


# =========================
# MAIN FUNCTION  (drop-in replacement)
# =========================
def extract_plate_text(frame) -> str | None:
    """
    Accepts a BGR frame. Returns a confirmed plate string or None.

    The stabiliser means this returns None for the first few frames
    of a new plate, then returns the same string consistently once
    it is confident. This eliminates the noisy flicker you were seeing.
    """
    if frame is None or frame.size == 0:
        return None

    # 1. Locate the plate region
    roi, bbox = get_plate_region(frame)
    if roi is None:
        roi = frame   # fallback: use full frame

    # 2. Preprocess (single fast path)
    binary = preprocess_for_ocr(roi)

    # 3. OCR — single config call
    try:
        raw = pytesseract.image_to_string(binary, config=OCR_CONFIG)
    except Exception:
        return None

    # 4. Clean
    text  = re.sub(r'[\s\n\r]+', '', raw)
    plate = clean_plate(text)

    if plate is None:
        return None

    # 5. Temporal stabilisation — only return when confident
    return stabilise(plate)


# =========================
# DEBUG VERSION (shows bounding box on screen)
# =========================
def extract_plate_text_debug(frame):
    """
    Same logic as extract_plate_text but also returns an annotated frame.
    Use this during development; swap back to extract_plate_text for prod.
    """
    debug = frame.copy()
    roi, bbox = get_plate_region(frame)

    plate = None
    if roi is not None:
        binary = preprocess_for_ocr(roi)
        try:
            raw   = pytesseract.image_to_string(binary, config=OCR_CONFIG)
            text  = re.sub(r'[\s\n\r]+', '', raw)
            plate = clean_plate(text)
            if plate:
                plate = stabilise(plate)
        except Exception:
            pass

        if bbox:
            x, y, w, h = bbox
            color = (0, 255, 0) if plate else (0, 165, 255)
            cv2.rectangle(debug, (x, y), (x + w, y + h), color, 2)
            label = plate if plate else "detecting..."
            cv2.putText(debug, label, (x, max(y - 8, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)

    return plate, debug