import re
import logging

logger = logging.getLogger("anpr.ocr")

class OCREngine:
    """
    OCR wrapper for extracting text from binary images.
    Defaults to PyTesseract but easily extensible for EasyOCR.
    """
    def __init__(self, engine_type="tesseract"):
        self.engine_type = engine_type
        if self.engine_type == "tesseract":
            try:
                import pytesseract
                self.pytesseract = pytesseract
                self.config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            except ImportError:
                logger.error("pytesseract is not installed!")
                self.pytesseract = None
        elif self.engine_type == "easyocr":
            try:
                import easyocr
                self.reader = easyocr.Reader(['en'], gpu=True)
            except ImportError:
                logger.error("easyocr is not installed!")
                self.reader = None

    def extract_text(self, binary_image) -> str:
        """Runs the OCR engine on the provided image."""
        if binary_image is None or binary_image.size == 0:
            return ""

        raw_text = ""
        try:
            if self.engine_type == "tesseract" and self.pytesseract:
                raw_text = self.pytesseract.image_to_string(binary_image, config=self.config)
            elif self.engine_type == "easyocr" and hasattr(self, 'reader') and self.reader:
                results = self.reader.readtext(binary_image, detail=0)
                raw_text = "".join(results)
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return ""

        # Clean whitespace
        return re.sub(r'[\s\n\r]+', '', raw_text)
