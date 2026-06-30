import cv2
import asyncio
import logging
from typing import Optional

logger = logging.getLogger("anpr.camera")

class AsyncCameraStream:
    """
    Dedicated worker for async video ingestion.
    Runs video capture in a non-blocking way, pushing frames to an asyncio.Queue.
    """
    def __init__(self, source=0, queue_size=5):
        self.source = source
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.is_running = False
        self._cap = None

    def start(self):
        """Starts the camera capture thread/task."""
        if self.is_running:
            return
        
        self.is_running = True
        self._cap = cv2.VideoCapture(self.source)
        
        if not self._cap.isOpened():
            logger.error(f"Failed to open video source: {self.source}")
            self.is_running = False
            raise ValueError(f"Cannot open video source: {self.source}")
        
        # Start a dedicated asyncio task for reading frames to avoid blocking
        asyncio.create_task(self._capture_loop())
        logger.info(f"Started camera stream from {self.source}")

    async def _capture_loop(self):
        """Continuously read frames and put them into the queue, dropping oldest if full."""
        while self.is_running and self._cap.isOpened():
            # cv2.read is blocking, so we offload it to a thread
            ret, frame = await asyncio.to_thread(self._cap.read)
            
            if not ret:
                logger.warning("Failed to read frame from camera. Reconnecting...")
                await asyncio.sleep(1)
                continue
            
            if self.queue.full():
                # Drop the oldest frame to prevent lagging behind real-time
                try:
                    self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            
            await self.queue.put(frame)
            # Small sleep to yield control
            await asyncio.sleep(0.01)

    async def get_frame(self):
        """Get the latest frame from the queue."""
        if not self.is_running:
            return None
        return await self.queue.get()

    def stop(self):
        """Stops the camera stream."""
        self.is_running = False
        if self._cap:
            self._cap.release()
        logger.info("Stopped camera stream.")
