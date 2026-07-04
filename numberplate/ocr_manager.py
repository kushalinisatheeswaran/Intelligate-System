import re
from collections import Counter

class OCRManager:
    def __init__(self, confirm_threshold=3, history_window=6):
        self.confirm_threshold = confirm_threshold
        self.history_window = history_window
        self.history = []

    def clean_plate(self, text: str) -> str | None:
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        if len(text) < 4 or len(text) > 10:
            return None
        # Must contain at least one letter and one digit
        if not re.search(r'[A-Z]', text) or not re.search(r'[0-9]', text):
            return None
        # Reject noise like all same chars
        if len(set(text)) < 3:
            return None
        return text

    def format_plate(self, text: str) -> str | None:
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

    def stabilise(self, raw_plate: str) -> str | None:
        """
        Require identical plate reads for multiple consecutive frames (confirm_threshold).
        """
        cleaned = self.clean_plate(raw_plate)
        if not cleaned:
            return None

        self.history.append(cleaned)
        self.history = self.history[-self.history_window:]

        counts = Counter(self.history)
        best, freq = counts.most_common(1)[0]
        if freq >= self.confirm_threshold:
            return best
        return None

    def reset(self):
        self.history = []
