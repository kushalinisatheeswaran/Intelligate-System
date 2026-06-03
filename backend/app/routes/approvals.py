from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database import db
from app.models.pending import PendingApproval
from app.models.vehicle import Vehicle
from app.models.user    import User
from app.utils.decorators import admin_required

approvals_bp = Blueprint("approvals", __name__)


@approvals_bp.route("/pending", methods=["GET"])
@jwt_required()
@admin_required
def get_pending():
    items = PendingApproval.query.filter_by(status="pending")\
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
    approval    = PendingApproval.query.get_or_404(approval_id)

    if approval.status != "pending":
        return jsonify({"error": "Already reviewed"}), 400

    approval.status      = "approved"
    approval.reviewed_by = reviewer_id
    approval.reviewed_at = datetime.utcnow()

    existing = Vehicle.query.filter_by(plate_number=approval.identifier).first()
    if not existing and approval.id_type == "plate":
        visitor = User(name=f"Visitor ({approval.identifier})", role="visitor")
        db.session.add(visitor)
        db.session.flush()
        vehicle = Vehicle(
            user_id      = visitor.id,
            plate_number = approval.identifier,
            vehicle_type = "unknown",
            is_active    = True
        )
        db.session.add(vehicle)

    db.session.commit()
    return jsonify({
        "message": "Approved. Vehicle registered.",
        "id":      approval_id,
        "status":  "approved"
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