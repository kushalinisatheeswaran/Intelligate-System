import asyncio
import logging
import cv2
from typing import Optional, Callable
from app.anpr.camera import AsyncCameraStream
from app.anpr.detector import PlateDetector
from app.anpr.preprocessor import ImagePreprocessor
from app.anpr.ocr_engine import OCREngine
from app.anpr.postprocessor import PlatePostprocessor
from app.anpr.decision import DecisionEngine

logger = logging.getLogger("anpr.pipeline")

class ANPRPipeline:
    """
    Orchestrates the asynchronous execution of the ANPR process.
    """
    def __init__(self, camera_source=0, db_session_func=None, gate_callback: Callable = None, alert_callback: Callable = None):
        self.camera = AsyncCameraStream(source=camera_source)
        self.detector = PlateDetector()
        self.preprocessor = ImagePreprocessor()
        self.ocr = OCREngine()
        self.postprocessor = PlatePostprocessor()
        self.decision = DecisionEngine(get_db_session_func=db_session_func)
        
        self.gate_callback = gate_callback
        self.alert_callback = alert_callback
        self.is_running = False

    async def start(self):
        """Starts the pipeline workers."""
        if self.is_running:
            return
        
        self.is_running = True
        self.camera.start()
        
        # Start the processing worker loop
        asyncio.create_task(self._processing_loop())
        logger.info("ANPR Pipeline started.")

    async def stop(self):
        """Stops the pipeline workers."""
        self.is_running = False
        self.camera.stop()
        logger.info("ANPR Pipeline stopped.")

    async def _processing_loop(self):
        """Main loop that pulls frames and processes them asynchronously."""
        while self.is_running:
            frame = await self.camera.get_frame()
            if frame is None:
                await asyncio.sleep(0.1)
                continue

            # Run CPU-intensive detection in a thread
            detections = await asyncio.to_thread(self.detector.detect, frame)
            
            for det in detections:
                crop = det['crop']
                # Preprocess
                binary = self.preprocessor.preprocess_for_ocr(crop)
                
                # OCR
                raw_text = await asyncio.to_thread(self.ocr.extract_text, binary)
                
                # Postprocess
                clean_text = self.postprocessor.clean(raw_text)
                final_plate = self.postprocessor.stabilize(clean_text)

                if final_plate:
                    # Evaluate decision
                    decision_result = await self.decision.evaluate(final_plate)
                    
                    if decision_result["granted"] and self.gate_callback:
                        # Async callback to open gate (e.g. over MQTT/HTTP)
                        await self.gate_callback(final_plate)
                    elif not decision_result["granted"] and self.alert_callback:
                        # Async callback to send alerts
                        await self.alert_callback(final_plate, crop)

            # Prevent busy looping
            await asyncio.sleep(0.01)
