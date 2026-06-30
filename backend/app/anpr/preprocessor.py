import cv2
import numpy as np

class ImagePreprocessor:
    """
    Adaptive image preprocessing pipeline for OCR optimization.
    """
    @staticmethod
    def preprocess_for_ocr(roi: np.ndarray) -> np.ndarray:
        """
        Enhances the plate crop for optimal OCR extraction.
        Applies grayscale, resizing, CLAHE, bilateral filtering, and adaptive thresholding.
        """
        if roi is None or roi.size == 0:
            return roi
            
        # Upscale: Tesseract works best with ~60-80px tall characters
        h, w = roi.shape[:2]
        if h < 60 and h > 0:
            scale = 60 / h
            roi = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Grayscale
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi.copy()

        # CLAHE -> improves contrast in both bright and dark conditions
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Bilateral filter -> smooth noise, preserve character edges
        gray = cv2.bilateralFilter(gray, 9, 75, 75)

        # Otsu threshold -> binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Invert if text is white on dark background (most plates are black text on white)
        # Heuristic: if more white pixels than black, invert
        if np.mean(binary) > 127:
            binary = cv2.bitwise_not(binary)

        return binary
