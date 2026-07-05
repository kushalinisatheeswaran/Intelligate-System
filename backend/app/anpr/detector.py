import os
import cv2
import logging
from typing import List, Dict, Any

logger = logging.getLogger("anpr.detector")

class PlateDetector:
    """
    Object detection wrapper for finding license plates in an image.
    Uses YOLOv8 if available, falling back to Haar cascades.
    """
    def __init__(self, model_path: str = None):
        self.yolo_model = None
        self.yolo_available = False
        self.plate_cascade = None
        
        self._init_yolo(model_path)
        self._init_haar()

    def _init_yolo(self, model_path):
        if not model_path:
            # Look in typical locations
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            model_path = os.path.join(base_dir, "numberplate", "models", "best.pt")
        
        if os.path.exists(model_path):
            try:
                from ultralytics import YOLO
                self.yolo_model = YOLO(model_path)
                self.yolo_available = True
                logger.info(f"YOLOv8 license-plate model loaded from: {model_path}")
            except ImportError:
                logger.warning("ultralytics not installed. Falling back to Haar cascade.")
            except Exception as e:
                logger.warning(f"Could not load YOLOv8 model ({e}). Falling back to Haar cascade.")
        else:
            logger.warning(f"YOLOv8 model not found at {model_path}. Falling back to Haar cascade.")

    def _init_haar(self):
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_russian_plate_number.xml")
        self.plate_cascade = cv2.CascadeClassifier(cascade_path)
        if self.plate_cascade.empty():
            logger.error("Haar cascade for plate detection failed to load!")

    def detect(self, frame) -> List[Dict[str, Any]]:
        """
        Detect license plates in a BGR frame.
        Returns a list of dicts: {'crop': np.ndarray, 'bbox': (x,y,w,h), 'conf': float}
        """
        if frame is None:
            return []
            
        if self.yolo_available:
            return self._detect_yolo(frame)
        return self._detect_haar(frame)

    def _detect_yolo(self, frame) -> List[Dict[str, Any]]:
        results = self.yolo_model.predict(frame, verbose=False, conf=0.25)
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                
                # Clamp coordinates
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
                
                crop = frame[y1:y2, x1:x2]
                if crop.size > 0:
                    detections.append({
                        "crop": crop,
                        "bbox": (x1, y1, x2 - x1, y2 - y1),
                        "conf": conf,
                    })
        return detections

    def _detect_haar(self, frame) -> List[Dict[str, Any]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        gray = cv2.equalizeHist(gray)

        rects = self.plate_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4, minSize=(80, 20), maxSize=(600, 200)
        )

        detections = []
        for (x, y, w, h) in rects:
            aspect = w / h if h > 0 else 0
            if 1.5 <= aspect <= 7.0:
                crop = frame[y:y+h, x:x+w]
                if crop.size > 0:
                    detections.append({
                        "crop": crop,
                        "bbox": (x, y, w, h),
                        "conf": 0.6,
                    })
        return detections
