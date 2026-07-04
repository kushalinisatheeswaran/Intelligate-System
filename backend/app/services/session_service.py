import time
import logging

logger = logging.getLogger(__name__)

class VehicleSessionManager:
    def __init__(self):
        # Maps plate -> { "state": str, "start_time": float, "last_seen": float }
        self.active_sessions = {}
        self.last_detected_plate = None
        self.last_event_timestamp = 0.0
        self.debounce_window = 20.0  # seconds

    def can_process_plate(self, plate: str) -> bool:
        """
        Determines whether a plate detection event should be processed.
        Transitions state to ACTIVE_SESSION and ignores duplicates.
        """
        current_time = time.time()
        clean_plate = plate.strip().upper().replace(" ", "").replace("-", "")

        # 1. Check debounce window
        if clean_plate == self.last_detected_plate:
            time_since_last = current_time - self.last_event_timestamp
            if time_since_last < self.debounce_window:
                logger.info(f"[SESSION] Ignoring duplicate plate {clean_plate} (debounce: {time_since_last:.1f}s)")
                return False

        # Update last seen tracking
        self.last_detected_plate = clean_plate
        self.last_event_timestamp = current_time

        # 2. State Machine Lifecycle check
        session = self.active_sessions.get(clean_plate)
        if session:
            session["last_seen"] = current_time
            if session["state"] == "ACTIVE_SESSION":
                logger.info(f"[SESSION] Plate {clean_plate} is already in ACTIVE_SESSION. Skipping verification.")
                return False
            session["state"] = "ACTIVE_SESSION"
            return True
        else:
            # IDLE -> VEHICLE_DETECTED -> ACTIVE_SESSION
            logger.info(f"[SESSION] Creating new ACTIVE_SESSION for plate: {clean_plate}")
            self.active_sessions[clean_plate] = {
                "state": "ACTIVE_SESSION",
                "start_time": current_time,
                "last_seen": current_time
            }
            return True

    def clear_session(self, plate: str):
        """
        Resets/clears the active session for a plate when exit/lane cleared is triggered.
        """
        clean_plate = plate.strip().upper().replace(" ", "").replace("-", "")
        if clean_plate in self.active_sessions:
            logger.info(f"[SESSION] Resetting session for plate: {clean_plate}")
            del self.active_sessions[clean_plate]
        if self.last_detected_plate == clean_plate:
            self.last_detected_plate = None

session_manager = VehicleSessionManager()
