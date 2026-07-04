import os
import time
import threading
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ESP32_MODE     = os.getenv("ESP32_MODE", "stub")
ESP32_PORT     = os.getenv("ESP32_PORT", "/dev/ttyUSB0")
ESP32_BAUD     = int(os.getenv("ESP32_BAUD", 115200))
ESP32_TIMEOUT  = int(os.getenv("ESP32_TIMEOUT", 3))
ESP32_HTTP_URL = os.getenv("ESP32_HTTP_URL", "http://192.168.1.100")
GATE_OPEN_DURATION = int(os.getenv("GATE_OPEN_DURATION", 5))

# Serial connection — singleton, opened once at startup
_serial_conn = None


def get_serial_connection():
    """Returns existing serial connection or creates a new one."""
    global _serial_conn
    if _serial_conn and _serial_conn.is_open:
        return _serial_conn
    try:
        import serial
        _serial_conn = serial.Serial(
            port     = ESP32_PORT,
            baudrate = ESP32_BAUD,
            timeout  = ESP32_TIMEOUT
        )
        time.sleep(2)  # ESP32 needs 2s after serial connect to initialise
        logger.info(f"[GATE] Serial connected on {ESP32_PORT}")
        return _serial_conn
    except Exception as e:
        logger.error(f"[GATE] Serial connection failed: {e}")
        return None


def _send_serial_command(command: str) -> dict:
    """Send a raw command string to ESP32 over serial."""
    conn = get_serial_connection()
    if not conn:
        return {"status": "error", "message": "Serial connection unavailable"}

    try:
        conn.write(f"{command}\n".encode("utf-8"))
        conn.flush()

        # Read ESP32 response (it should reply OK or ERROR)
        response = conn.readline().decode("utf-8").strip()
        logger.info(f"[GATE] Serial sent: {command} | ESP32 replied: {response}")
        return {"status": "ok", "command": command, "esp32_response": response}

    except Exception as e:
        logger.error(f"[GATE] Serial write failed: {e}")
        return {"status": "error", "message": str(e)}


def _send_http_command(command: str) -> dict:
    """Send command to ESP32 over WiFi HTTP (alternative to serial)."""
    try:
        import requests
        endpoint = f"{ESP32_HTTP_URL}/gate/{command.lower()}"
        response = requests.post(endpoint, timeout=ESP32_TIMEOUT)
        logger.info(f"[GATE] HTTP sent to {endpoint} | Status: {response.status_code}")
        return {"status": "ok", "command": command, "http_status": response.status_code}
    except Exception as e:
        logger.error(f"[GATE] HTTP command failed: {e}")
        return {"status": "error", "message": str(e)}


def _auto_close_gate():
    """
    Closes the gate automatically after GATE_OPEN_DURATION seconds.
    Runs in a background thread so Flask is not blocked.
    """
    time.sleep(GATE_OPEN_DURATION)
    logger.info(f"[GATE] Auto-closing after {GATE_OPEN_DURATION}s")
    close_gate()


def open_gate() -> dict:
    """
    Opens the gate and schedules auto-close.
    Called by /api/verify on granted access and /api/gate/open for manual override.
    """
    from app.services.state_machine import gate_state_machine
    current_state = gate_state_machine.get_state()
    if current_state in ("OPEN", "OPENING"):
        logger.info(f"[GATE] Ignoring OPEN command. Gate is already {current_state}")
        return {"status": "ignored", "message": f"Gate is already {current_state}", "gate": current_state.lower()}

    logger.info("[GATE] OPEN command triggered")
    gate_state_machine.transition_to("OPENING")

    result = {}
    if ESP32_MODE == "serial":
        result = _send_serial_command("OPEN")
    elif ESP32_MODE == "http":
        result = _send_http_command("OPEN")
    else:
        # Stub mode — for development without hardware
        logger.info("[GATE STUB] OPEN — simulating opening sequence")
        result = {"status": "ok", "gate": "opening", "mode": "stub"}
        
        # Simulate hardware ACK transitions for stub mode
        def simulate_stub_open():
            time.sleep(1.5)
            gate_state_machine.transition_to("OPEN")
        threading.Thread(target=simulate_stub_open, daemon=True).start()

    # Broadcast execute_gate_action via Socket.IO
    try:
        from app.services.socket_service import socketio
        socketio.emit("execute_gate_action", {"action": "OPEN"})
    except Exception as e:
        logger.error(f"[GATE] Failed to emit execute_gate_action OPEN: {e}")

    # Schedule auto-close in background thread
    thread = threading.Thread(target=_auto_close_gate, daemon=True)
    thread.start()

    result["gate"]            = "opening"
    result["auto_close_in"]   = f"{GATE_OPEN_DURATION}s"
    return result


def close_gate() -> dict:
    """
    Closes the gate.
    Called automatically after open duration or manually via /api/gate/close.
    """
    from app.services.state_machine import gate_state_machine
    current_state = gate_state_machine.get_state()
    if current_state in ("CLOSED", "CLOSING"):
        logger.info(f"[GATE] Ignoring CLOSE command. Gate is already {current_state}")
        return {"status": "ignored", "message": f"Gate is already {current_state}", "gate": current_state.lower()}

    logger.info("[GATE] CLOSE command triggered")
    gate_state_machine.transition_to("CLOSING")

    result = {}
    if ESP32_MODE == "serial":
        result = _send_serial_command("CLOSE")
    elif ESP32_MODE == "http":
        result = _send_http_command("CLOSE")
    else:
        logger.info("[GATE STUB] CLOSE — simulating closing sequence")
        result = {"status": "ok", "gate": "closing", "mode": "stub"}

        # Simulate hardware ACK transitions for stub mode
        def simulate_stub_close():
            time.sleep(1.5)
            gate_state_machine.transition_to("CLOSED")
        threading.Thread(target=simulate_stub_close, daemon=True).start()

    # Broadcast execute_gate_action via Socket.IO
    try:
        from app.services.socket_service import socketio
        socketio.emit("execute_gate_action", {"action": "CLOSE"})
    except Exception as e:
        logger.error(f"[GATE] Failed to emit execute_gate_action CLOSE: {e}")

    result["gate"] = "closing"
    return result