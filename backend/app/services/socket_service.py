import logging
from datetime import datetime, timezone
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)
socketio = SocketIO()

@socketio.on("plate_detected")
def handle_incoming_plate(data):
    """
    Production Database-driven access control.
    All permissions and metadata are read dynamically from PostgreSQL.
    """
    from app.models.vehicle import Vehicle
    from app.models.user import User
    from app.models.access_log import AccessLog
    from app import db

    raw_plate = data.get("plate", "").strip().upper().replace(" ", "").replace("-", "")
    if not raw_plate:
        return

    logger.info(f"[ANPR INBOUND] Processing lookup for clean string: {raw_plate}")
    timestamp_dt = datetime.now(timezone.utc)
    timestamp_iso = timestamp_dt.isoformat()

    try:
        # 1. Query DB ignoring hyphens and spaces inside the PostgreSQL column
        vehicle = Vehicle.query.filter(
            db.func.replace(db.func.replace(Vehicle.plate_number, '-', ''), ' ', '') == raw_plate
        ).first()

        if vehicle:
            # 2. Fetch the linked User profile from the DB using the foreign key relationship
            user_profile = User.query.get(vehicle.user_id)
            
            if user_profile:
                owner_name = user_profile.name
                user_role = user_profile.role  # 'student', 'staff', etc.
                
                # Check status flags dynamically from your DB schema properties
                # (Fallback to 'allowed' if column doesn't exist yet)
                is_active = getattr(vehicle, 'is_active', True) 
                
                if is_active:
                    logger.info(f"[ACCESS GRANTED] {vehicle.plate_number} verified. Owner: {owner_name} ({user_role})")
                    
                    payload = {
                        "identifier": vehicle.plate_number,
                        "id_type": "plate",
                        "direction": "entry",
                        "status": "granted",
                        "name": owner_name,
                        "timestamp": timestamp_iso
                    }
                    
                    # Broadcast to React Native Frontend
                    socketio.emit("vehicle_detected", payload)
                    socketio.emit("access_granted", payload)
                    socketio.emit("gate_status", {"status": "open", "triggered_by": "ANPR System"})
                    
                    # 3. Log the successful entry into your live AccessLog table
                    log_entry = AccessLog(
                        user_id=user_profile.id,
                        identifier=vehicle.plate_number,
                        id_type="plate",
                        direction="entry",
                        status="granted",
                        timestamp=timestamp_dt
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                    return

        # 4. ACCESS DENIED: Execution lands here if vehicle is missing or inactive
        logger.warning(f"[ACCESS DENIED] Unrecognized vehicle context for text: {raw_plate}")
        
        payload_denied = {
            "identifier": raw_plate,
            "id_type": "plate",
            "direction": "entry",
            "status": "denied",
            "name": "Unknown Vehicle",
            "timestamp": timestamp_iso
        }
        socketio.emit("vehicle_detected", payload_denied)
        socketio.emit("access_denied", payload_denied)
        
        # Log the violation into your live AccessLog table for security audits
        violation_log = AccessLog(
            user_id=None,
            identifier=raw_plate,
            id_type="plate",
            direction="entry",
            status="denied",
            timestamp=timestamp_dt
        )
        db.session.add(violation_log)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error(f"[SYSTEM DATABASE CRASH] Validation process failed: {e}")

# Restored Helper Functions for API Routes

def emit_vehicle_detected(data: dict):
    logger.info(f"[SOCKET] vehicle_detected -> {data.get('identifier')}")
    socketio.emit("vehicle_detected", data)

def emit_unknown_vehicle(data: dict):
    logger.info(f"[SOCKET] unknown_vehicle -> {data.get('identifier')}")
    socketio.emit("unknown_vehicle", data)

def emit_access_granted(data: dict):
    socketio.emit("access_granted", data)

def emit_access_denied(data: dict):
    socketio.emit("access_denied", data)

def emit_gate_status(status: str, triggered_by: str = "system"):
    data = {"status": status, "triggered_by": triggered_by}
    logger.info(f"[SOCKET] gate_status -> {status}")
    socketio.emit("gate_status", data)

def emit_approval_update(data: dict):
    logger.info(f"[SOCKET] approval_update -> pending#{data.get('pending_id')} {data.get('status')}")
    socketio.emit("approval_update", data)