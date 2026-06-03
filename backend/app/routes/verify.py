from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
from app.database import db
from app.models.vehicle    import Vehicle
from app.models.student_id import StudentID
from app.models.access_log import AccessLog
from app.models.pending    import PendingApproval
from app.services.gate_service     import open_gate
from app.services.telegram_service import send_denial_alert
from app.utils.validators  import validate_identifier

verify_bp = Blueprint("verify", __name__)


@verify_bp.route("/verify", methods=["POST"])
@jwt_required()
def verify():
    """
    Core verification endpoint — called by CV engine on every detection.

    Full workflow:
      1. Validate input format
      2. Check DB for authorized plate or student ID
      3. Write access log
      4. GRANTED  → open gate, return success
      5. DENIED   → create pending approval, send Telegram alert, return denied
    """
    data = request.get_json()

    # --- Input validation ---
    if not data or "type" not in data or "value" not in data:
        return jsonify({"error": "Missing required fields: type, value"}), 400

    id_type    = data["type"].strip().lower()
    value      = data["value"].strip().upper()
    direction  = data.get("direction", "entry").strip().lower()
    image_path = data.get("image_path")

    if direction not in ("entry", "exit"):
        return jsonify({"error": "direction must be 'entry' or 'exit'"}), 400

    is_valid, error_msg = validate_identifier(id_type, value)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # --- Authorization check ---
    user       = None
    authorized = False

    if id_type == "plate":
        vehicle = Vehicle.query.filter_by(
            plate_number=value, is_active=True
        ).first()
        if vehicle:
            authorized = True
            user = vehicle.user

    elif id_type == "barcode":
        student = StudentID.query.filter_by(
            student_number=value, is_active=True
        ).first()
        if student:
            authorized = True
            user = student.user

    # --- Check if already denied and still pending (avoid duplicate pending entries) ---
    if not authorized:
        existing_pending = PendingApproval.query.filter_by(
            identifier=value, status="pending"
        ).first()
        if existing_pending:
            return jsonify({
                "status":    "denied",
                "identifier": value,
                "type":       id_type,
                "reason":    "already_pending",
                "pending_id": existing_pending.id,
                "timestamp":  datetime.utcnow().isoformat(),
                "message":   "Already in pending review queue"
            }), 200

    # --- Write access log ---
    log = AccessLog(
        user_id    = user.id if user else None,
        identifier = value,
        id_type    = id_type,
        direction  = direction,
        status     = "granted" if authorized else "denied",
        image_path = image_path,
        timestamp  = datetime.utcnow()
    )
    db.session.add(log)
    db.session.flush()

    # --- DENIED flow ---
    if not authorized:
        pending = PendingApproval(
            log_id     = log.id,
            identifier = value,
            id_type    = id_type,
            image_path = image_path,
            status     = "pending"
        )
        db.session.add(pending)
        db.session.commit()

        # Send Telegram alert with image
        send_denial_alert(
            identifier = value,
            id_type    = id_type,
            timestamp  = log.timestamp.isoformat(),
            image_path = image_path
        )

        return jsonify({
            "status":     "denied",
            "identifier": value,
            "type":       id_type,
            "direction":  direction,
            "reason":     "not_in_database",
            "pending_id": pending.id,
            "timestamp":  log.timestamp.isoformat(),
            "message":    "Access denied. Added to pending review."
        }), 200

    # --- GRANTED flow ---
    db.session.commit()
    gate_result = open_gate()

    return jsonify({
        "status":     "granted",
        "identifier": value,
        "type":       id_type,
        "direction":  direction,
        "name":       user.name,
        "user_id":    user.id,
        "timestamp":  log.timestamp.isoformat(),
        "gate":       gate_result,
        "message":    "Access granted. Gate opening."
    }), 200


@verify_bp.route("/verify/status/<string:identifier>", methods=["GET"])
@jwt_required()
def check_status(identifier):
    """
    Check if a plate or student ID is currently authorized.
    Useful for the dashboard to quickly look up a specific identifier.
    """
    identifier = identifier.strip().upper()

    vehicle = Vehicle.query.filter_by(
        plate_number=identifier, is_active=True
    ).first()
    if vehicle:
        return jsonify({
            "identifier": identifier,
            "type":       "plate",
            "authorized": True,
            "user":       vehicle.user.to_dict()
        }), 200

    student = StudentID.query.filter_by(
        student_number=identifier, is_active=True
    ).first()
    if student:
        return jsonify({
            "identifier": identifier,
            "type":       "barcode",
            "authorized": True,
            "user":       student.user.to_dict()
        }), 200

    # Check if pending
    pending = PendingApproval.query.filter_by(
        identifier=identifier, status="pending"
    ).first()

    return jsonify({
        "identifier": identifier,
        "authorized": False,
        "pending":    pending is not None,
        "pending_id": pending.id if pending else None
    }), 200