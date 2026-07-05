import re
from collections import Counter, deque
import time

class PlatePostprocessor:
    """
    Cleans up OCR strings and provides per-camera temporal stabilization
    to prevent flickering or single-frame false positives.
    """
    def __init__(self, history_window=6, confirm_threshold=3, ttl=5.0):
        self.history_window = history_window
        self.confirm_threshold = confirm_threshold
        # Stores tuples of (timestamp, plate_string)
        self.history = deque(maxlen=history_window)
        self.ttl = ttl

    def clean(self, raw_text: str) -> str:
        """Applies regex and heuristics to clean the plate string."""
        text = re.sub(r'[^A-Z0-9]', '', raw_text.upper())

        # Real plates are usually 4-10 characters
        if len(text) < 4 or len(text) > 10:
            return None

        # Must contain at least one letter AND one digit
        if not re.search(r'[A-Z]', text) or not re.search(r'[0-9]', text):
            return None

        # Reject "all-same" noise
        if len(set(text)) < 3:
            return None

        return text

    def stabilize(self, plate: str) -> str:
        """
        Maintains a rolling window of recent plates. 
        Returns the plate only if it occurs enough times in the window.
        """
        now = time.time()
        
        # Remove stale entries
        while self.history and (now - self.history[0][0]) > self.ttl:
            self.history.popleft()

        if plate:
            self.history.append((now, plate))

        if not self.history:
            return None

        # Count frequencies
        plates_only = [p[1] for p in self.history]
        counts = Counter(plates_only)
        best, freq = counts.most_common(1)[0]

        if freq >= self.confirm_threshold:
            return best
        return None
