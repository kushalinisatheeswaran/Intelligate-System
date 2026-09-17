import threading
import logging

logger = logging.getLogger(__name__)

class GateStateMachine:
    def __init__(self):
        self.state = "CLOSED"
        self.lock = threading.Lock()

    def transition_to(self, new_state: str) -> bool:
        new_state = new_state.upper()
        valid_states = {"CLOSED", "OPENING", "OPEN", "CLOSING", "ERROR"}
        if new_state not in valid_states:
            logger.error(f"[STATE] Invalid target state: {new_state}")
            return False

        with self.lock:
            if self.state == new_state:
                logger.debug(f"[STATE] Already in state: {new_state}. Ignoring transition.")
                return False

            logger.info(f"[STATE] Transition: {self.state} ➜ {new_state}")
            self.state = new_state
            
            # Broadcast state changes immediately to Mobile App
            try:
                from app.services.socket_service import emit_gate_status
                
                # Map to status strings used by React Native app: open | closed | unknown
                if new_state == "OPEN":
                    app_state = "open"
                elif new_state == "CLOSED":
                    app_state = "closed"
                elif new_state == "OPENING":
                    app_state = "opening"
                elif new_state == "CLOSING":
                    app_state = "closing"
                else:
                    app_state = "unknown"
                    
                emit_gate_status(app_state, triggered_by="Hardware Feedback")
            except Exception as e:
                logger.error(f"[STATE] Broadcast failed: {e}")
                
            return True

    def get_state(self) -> str:
        with self.lock:
            return self.state

gate_state_machine = GateStateMachine()
