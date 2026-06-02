# Phase 4 will add real ESP32 serial communication
def open_gate():
    print("[GATE SERVICE] OPEN command sent (stub)")
    return {"gate": "open", "status": "ok", "note": "stub - ESP32 not connected"}

def close_gate():
    print("[GATE SERVICE] CLOSE command sent (stub)")
    return {"gate": "closed", "status": "ok", "note": "stub - ESP32 not connected"}