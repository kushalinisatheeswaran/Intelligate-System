from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import guard_or_admin_required
from app.models.access_log import AccessLog
from sqlalchemy import func
from datetime import datetime, date
from app.database import db

logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/logs", methods=["GET"])
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