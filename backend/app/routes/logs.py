from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import guard_or_admin_required
from app.models.access_log import AccessLog
from sqlalchemy import func
from datetime import datetime, date
from app.database import db
from app.models.vehicle import Vehicle
from app.models.pending import PendingApproval
from app.services.socket_service import socketio  # or wherever your socketio instance is imported from


logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/logs", methods=["GET","POST"])
@jwt_required()
@guard_or_admin_required
def get_logs():
    status   = request.args.get("status")
    search   = request.args.get("search", "").strip().upper()
    limit    = min(int(request.args.get("limit", 50)), 200)
    log_date = request.args.get("date")

    query = AccessLog.query.order_by(AccessLog.timestamp.desc())

    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(AccessLog.identifier.ilike(f"%{search}%"))
    if log_date:
        try:
            target = datetime.strptime(log_date, "%Y-%m-%d").date()
            query  = query.filter(func.date(AccessLog.timestamp) == target)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    total = query.count()
    logs  = query.limit(limit).all()

    return jsonify({"total": total, "logs": [l.to_dict() for l in logs]}), 200


@logs_bp.route("/stats", methods=["GET"])
@jwt_required()
@guard_or_admin_required
def get_stats():
    today = date.today()

    total   = AccessLog.query.filter(func.date(AccessLog.timestamp) == today).count()
    granted = AccessLog.query.filter(
        func.date(AccessLog.timestamp) == today,
        AccessLog.status == "granted"
    ).count()
    denied = total - granted

    hourly = db_hourly_stats(today)

    plate_count   = AccessLog.query.filter(
        func.date(AccessLog.timestamp) == today,
        AccessLog.id_type == "plate"
    ).count()
    barcode_count = AccessLog.query.filter(
        func.date(AccessLog.timestamp) == today,
        AccessLog.id_type == "barcode"
    ).count()

    return jsonify({
        "today":   {"total": total, "granted": granted, "denied": denied},
        "by_hour": hourly,
        "by_type": {"plate": plate_count, "barcode": barcode_count}
    }), 200


def db_hourly_stats(target_date):
    results = db.session.query(
        func.extract("hour", AccessLog.timestamp).label("hour"),
        func.count(AccessLog.id).label("count")
    ).filter(
        func.date(AccessLog.timestamp) == target_date
    ).group_by("hour").order_by("hour").all()
    return [{"hour": f"{int(r.hour):02d}:00", "count": r.count} for r in results]

@logs_bp.route("/logs/detect", methods=["POST"])
# Note: Do not add @jwt_required() here so your teammate's camera scripts can access it easily without needing to manage authentication tokens.
def handle_camera_detection():
    pending_entry = None
    data = request.json
    if not data:
        return jsonify({"error": "Missing payload"}), 400

    identifier = data.get("identifier")
    id_type = data.get("id_type", "plate")
    direction = data.get("direction", "entry")

    if not identifier:
        return jsonify({"error": "Missing identifier"}), 400

    # 1. Query your single PostgreSQL database to check if the vehicle is active
    vehicle = Vehicle.query.filter_by(plate_number=identifier).first()

    if vehicle and vehicle.is_active:
        # It's a registered, active vehicle -> GRANT ACCESS
        status = "granted"
        open_gate = True
        user_id = vehicle.user_id
    else:
        # It's an unknown vehicle -> DENY & SEND TO PENDING QUEUE
        status = "denied"
        open_gate = False
        user_id = None

        # Add a record to your temporary PendingApproval queue
        pending_entry = PendingApproval(
            identifier=identifier,
            id_type=id_type,
            status="pending"
        )
        db.session.add(pending_entry)

    # 2. Log every single try permanently into your AccessLog table
    new_log = AccessLog(
        user_id=user_id,
        identifier=identifier,
        id_type=id_type,
        direction=direction,
        status=status,
        timestamp=datetime.utcnow()
    )
    db.session.add(new_log)
    db.session.commit()

    # 3. Broadcast real-time alerts across your network to update the mobile app screens instantly
    if status == "granted":
        socketio.emit("vehicle_detected", {
            "identifier": identifier,
            "id_type": id_type,
            "direction": direction,
            "status": status,
            "timestamp": new_log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }, to="guards")
        socketio.emit("gate_status", {"status": "open", "triggered_by": "system"}, to="guards")
    else:
        socketio.emit("unknown_vehicle", {
            "pending_id": pending_entry.id,
            "identifier": identifier,
            "id_type": id_type,
            "timestamp": pending_entry.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }, to="guards")

    return jsonify({
        "status": status,
        "open_gate": open_gate,
        "message": f"Detection successfully processed as {status}"
    }), 201