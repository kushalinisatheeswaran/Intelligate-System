from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from app.database import db
from app.models.vehicle    import Vehicle
from app.models.student_id import StudentID
from app.models.access_log import AccessLog
from app.models.pending    import PendingApproval
from app.services.gate_service     import open_gate
from app.services.telegram_service import send_denial_alert

verify_bp = Blueprint("verify", __name__)

@verify_bp.route("/verify", methods=["POST"])
@jwt_required()
def verify():
    """
    Called by CV engine (Karthigan/Sulaksan) with a valid JWT.
    They get a token by calling POST /api/auth/login first.
    Role: guard or admin can call this.
    """
    data = request.get_json()

    if not data or "type" not in data or "value" not in data:
        return jsonify({"error": "Missing required fields: type, value"}), 400

    id_type    = data["type"]
    value      = data["value"].strip().upper()
    direction  = data.get("direction", "entry")
    image_path = data.get("image_path")

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

    else:
        return jsonify({"error": "Invalid type. Use 'plate' or 'barcode'"}), 400

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
            "reason":     "not_in_database",
            "timestamp":  log.timestamp.isoformat(),
            "message":    "Access denied. Added to pending review."
        }), 200

    db.session.commit()
    open_gate()

    return jsonify({
        "status":     "granted",
        "identifier": value,
        "type":       id_type,
        "direction":  direction,
        "name":       user.name,
        "timestamp":  log.timestamp.isoformat(),
        "message":    "Gate opening"
    }), 200