from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database import db
from app.models.pending    import PendingApproval
from app.models.vehicle    import Vehicle
from app.models.student_id import StudentID
from app.models.user       import User
from app.models.access_log import AccessLog
from app.services.gate_service import open_gate
from app.utils.decorators  import admin_required

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
    """
    Admin approves an unknown vehicle.
    Steps:
      1. Mark pending as approved
      2. Register vehicle/student in authorized table
      3. Optionally open gate immediately (if vehicle is still at gate)
    """
    reviewer_id = int(get_jwt_identity())
    approval    = PendingApproval.query.get_or_404(approval_id)
    data        = request.get_json() or {}
    open_now    = data.get("open_gate", False)  # optional: open gate immediately

    if approval.status != "pending":
        return jsonify({"error": "Already reviewed"}), 400

    approval.status      = "approved"
    approval.reviewed_by = reviewer_id
    approval.reviewed_at = datetime.utcnow()

    new_user    = None
    registered  = False

    # Register as authorized vehicle
    if approval.id_type == "plate":
        existing = Vehicle.query.filter_by(
            plate_number=approval.identifier
        ).first()
        if not existing:
            new_user = User(
                name  = data.get("name", f"Visitor ({approval.identifier})"),
                email = data.get("email"),
                role  = data.get("role", "visitor")
            )
            db.session.add(new_user)
            db.session.flush()
            vehicle = Vehicle(
                user_id      = new_user.id,
                plate_number = approval.identifier,
                vehicle_type = data.get("vehicle_type", "car"),
                is_active    = True
            )
            db.session.add(vehicle)
            registered = True
        else:
            # Reactivate if was deactivated
            existing.is_active = True
            registered = True

    # Register as authorized student
    elif approval.id_type == "barcode":
        existing = StudentID.query.filter_by(
            student_number=approval.identifier
        ).first()
        if not existing:
            new_user = User(
                name   = data.get("name", f"Student ({approval.identifier})"),
                email  = data.get("email"),
                role   = "student"
            )
            db.session.add(new_user)
            db.session.flush()
            student = StudentID(
                user_id        = new_user.id,
                student_number = approval.identifier,
                faculty        = data.get("faculty", "Unknown"),
                is_active      = True
            )
            db.session.add(student)
            registered = True

    # Log this approval as a granted entry
    log = AccessLog(
        user_id    = new_user.id if new_user else None,
        identifier = approval.identifier,
        id_type    = approval.id_type,
        direction  = "entry",
        status     = "granted",
        timestamp  = datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    gate_result = None
    if open_now:
        gate_result = open_gate()

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
    return jsonify({
        "message": "Rejected.",
        "id":      approval_id,
        "status":  "rejected",
        "reason":  reason
    }), 200