from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from app.database import db
from app.models.pending    import PendingApproval
from app.models.vehicle    import Vehicle
from app.models.student_id import StudentID
from app.models.user       import User
from app.models.access_log import AccessLog
from app.services.gate_service    import open_gate

# 💡 SAFE UNIFIED MODULE IMPORT:
# Replaces individual function extraction to bypass compile-time circular locks during app init
from app.services import socket_service

from app.utils.decorators import admin_required

approvals_bp = Blueprint("approvals", __name__)


@approvals_bp.route("/pending", methods=["GET"])
@jwt_required()
@admin_required
def get_pending():
    status_filter = request.args.get("status", "pending")
    items = PendingApproval.query\
                .filter_by(status=status_filter)\
                .order_by(PendingApproval.created_at.desc()).all()
    return jsonify({
        "total":   len(items),
        "pending": [p.to_dict() for p in items]
    }), 200


@approvals_bp.route("/approve/<int:approval_id>", methods=["POST"])
@jwt_required()
@admin_required
def approve(approval_id):
    reviewer_id = int(get_jwt_identity())
    claims      = get_jwt()
    approval    = PendingApproval.query.get_or_404(approval_id)
    data        = request.get_json() or {}
    open_now    = data.get("open_gate", False)

    if approval.status != "pending":
        return jsonify({"error": "Already reviewed"}), 400

    approval.status      = "approved"
    approval.reviewed_by = reviewer_id
    approval.reviewed_at = datetime.utcnow()

    new_user   = None
    registered = False

    if approval.id_type == "plate":
        normalized_id = approval.identifier.replace("-", "").replace(" ", "")
        existing = Vehicle.query.filter(
            db.func.replace(db.func.replace(Vehicle.plate_number, '-', ''), ' ', '') == normalized_id
        ).first()
        if not existing:
            new_user = User()
            new_user.name  = data.get("name", f"Visitor ({approval.identifier})")
            new_user.email = data.get("email")
            new_user.role  = data.get("role", "visitor")
            db.session.add(new_user)
            db.session.flush()
            vehicle = Vehicle()
            vehicle.user_id      = new_user.id
            vehicle.plate_number = approval.identifier
            vehicle.vehicle_type = data.get("vehicle_type", "car")
            vehicle.is_active    = True
            db.session.add(vehicle)
            registered = True
        else:
            existing.is_active = True
            registered = True

    elif approval.id_type == "barcode":
        existing = StudentID.query.filter_by(
            student_number=approval.identifier
        ).first()
        if not existing:
            new_user = User()
            new_user.name  = data.get("name", f"Student ({approval.identifier})")
            new_user.email = data.get("email")
            new_user.role  = "student"
            db.session.add(new_user)
            db.session.flush()
            student = StudentID()
            student.user_id        = new_user.id
            student.student_number = approval.identifier
            student.faculty        = data.get("faculty", "Unknown")
            student.is_active      = True
            db.session.add(student)
            registered = True

    log = AccessLog()
    log.user_id    = new_user.id if new_user else None
    log.identifier = approval.identifier
    log.id_type    = approval.id_type
    log.direction  = "entry"
    log.status     = "granted"
    log.timestamp  = datetime.utcnow()
    db.session.add(log)
    db.session.commit()

    # 💡 Socket.IO — Updated via module namespace reference
    socket_service.emit_approval_update({
        "pending_id":   approval_id,
        "identifier":   approval.identifier,
        "status":       "approved",
        "reviewed_by":  claims.get("name", "Admin"),
        "timestamp":    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })

    gate_result = None
    if open_now:
        gate_result = open_gate()
        socket_service.emit_gate_status("open", triggered_by=claims.get("name", "admin"))

    return jsonify({
        "message":    "Approved. Entry authorized.",
        "id":         approval_id,
        "status":     "approved",
        "registered": registered,
        "gate":       gate_result
    }), 200


@approvals_bp.route("/reject/<int:approval_id>", methods=["POST"])
@jwt_required()
@admin_required
def reject(approval_id):
    reviewer_id = int(get_jwt_identity())
    claims      = get_jwt()
    approval    = PendingApproval.query.get_or_404(approval_id)

    if approval.status != "pending":
        return jsonify({"error": "Already reviewed"}), 400

    data   = request.get_json() or {}
    reason = data.get("reason", "Rejected by admin")

    approval.status      = "rejected"
    approval.reason      = reason
    approval.reviewed_by = reviewer_id
    approval.reviewed_at = datetime.utcnow()

    db.session.commit()

    # 💡 Socket.IO — Updated via module namespace reference
    socket_service.emit_approval_update({
        "pending_id":  approval_id,
        "identifier":  approval.identifier,
        "status":      "rejected",
        "reason":      reason,
        "reviewed_by": claims.get("name", "Admin"),
        "timestamp":   datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "message": "Rejected.",
        "id":      approval_id,
        "status":  "rejected",
        "reason":  reason
    }), 200