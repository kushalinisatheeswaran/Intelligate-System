# Phase 5 will add real Telegram bot
def send_denial_alert(identifier, id_type, timestamp, image_path=None):
    print(f"[TELEGRAM STUB] DENIED — {id_type}: {identifier} at {timestamp}")
    return {"sent": False, "note": "stub - Telegram not configured yet"}