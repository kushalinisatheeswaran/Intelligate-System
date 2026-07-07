from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from app.database import db
from app.models.vehicle     import Vehicle
from app.models.student_id import StudentID
from app.models.access_log import AccessLog
from app.models.pending    import PendingApproval
from app.services.gate_service import open_gate

# 💡 SAFE UNIFIED MODULE IMPORT: 
# Instead of pulling specific named emitter functions at startup, we import 
# the service as a whole to clear up the Flask initialization chain.
from app.services import socket_service

from app.services.fcm_service import send_unknown_vehicle_alert
from app.utils.validators import validate_identifier

verify_bp = Blueprint("verify", __name__)


@verify_bp.route("/verify", methods=["POST"])
def verify():
    data = request.get_json()

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

    # --- Anti-Passback check for authorized credentials ---
    if authorized:
        last_log = AccessLog.query.filter_by(identifier=value, status="granted")\
                                  .order_by(AccessLog.timestamp.desc())\
                                  .first()
        
        if direction == "entry" and last_log and last_log.direction == "entry":
            timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            # Broadcast the blocked tailgating/passback attempt to the UI dashboard
            socket_service.emit_access_denied({
                "identifier": value,
                "id_type":    id_type,
                "reason":     "already_inside",
                "timestamp":  timestamp_str
            })
            
            return jsonify({
                "status":     "denied",
                "identifier": value,
                "type":       id_type,
                "direction":  direction,
                "reason":     "already_inside",
                "timestamp":  datetime.utcnow().isoformat(),
                "message":    "Access denied. Vehicle/User is already logged inside the premises."
            }), 200

    # --- Duplicate pending check ---
    if not authorized:
        existing_pending = PendingApproval.query.filter_by(
            identifier=value, status="pending"
        ).first()
        if existing_pending:
            return jsonify({
                "status":     "denied",
                "identifier": value,
                "type":       id_type,
                "reason":     "already_pending",
                "pending_id": existing_pending.id,
                "timestamp":  datetime.utcnow().isoformat(),
                "message":    "Already in pending review queue"
            }), 200

    # --- Write access log ---
    log = AccessLog()
    log.user_id    = user.id if user else None
    log.identifier = value
    log.id_type    = id_type
    log.direction  = direction
    log.status     = "granted" if authorized else "denied"
    log.image_path = image_path
    log.timestamp  = datetime.utcnow()
    db.session.add(log)
    db.session.flush()

    timestamp_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # --- DENIED flow ---
    if not authorized:
        pending = PendingApproval()
        pending.log_id     = log.id
        pending.identifier = value
        pending.id_type    = id_type
        pending.image_path = image_path
        pending.status     = "pending"
        db.session.add(pending)
        db.session.commit()

        # 1. Socket.IO — Using prefixed object routes now
        socket_service.emit_vehicle_detected({
            "identifier": value,
            "id_type":    id_type,
            "direction":  direction,
            "status":     "denied",
            "name":       None,
            "timestamp":  timestamp_str
        })
        socket_service.emit_unknown_vehicle({
            "identifier": value,
            "id_type":    id_type,
            "image_path": image_path,
            "pending_id": pending.id,
            "timestamp":  timestamp_str
        })
        socket_service.emit_access_denied({
            "identifier": value,
            "id_type":    id_type,
            "reason":     "not_in_database",
            "timestamp":  timestamp_str
        })

        # 2. FCM — push notification if app is closed
        send_unknown_vehicle_alert(
            identifier = value,
            id_type    = id_type,
            pending_id = pending.id,
            timestamp  = timestamp_str,
            image_url  = image_path
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

    # Socket.IO — Using prefixed object routes now
    socket_service.emit_vehicle_detected({
        "identifier": value,
        "id_type":    id_type,
        "direction":  direction,
        "status":     "granted",
        "name":       user.name,
        "timestamp":  timestamp_str
    })
    socket_service.emit_access_granted({
        "identifier": value,
        "id_type":    id_type,
        "name":       user.name,
        "direction":  direction,
        "timestamp":  timestamp_str
    })
    socket_service.emit_gate_status("open", triggered_by="auto_verify")

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

    pending = PendingApproval.query.filter_by(
        identifier=identifier, status="pending"
    ).first()
    return jsonify({
        "identifier": identifier,
        "authorized": False,
        "pending":    pending is not None,
        "pending_id": pending.id if pending else None
    }), 200