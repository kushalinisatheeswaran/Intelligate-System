from flask import Blueprint, jsonify, request

approvals_bp = Blueprint("approvals", __name__)

DUMMY_PENDING = [
    {"id": 1, "identifier": "XYZ-9988", "type": "plate",  "image_path": None, "status": "pending", "created_at": "2025-05-21T14:19:03"},
    {"id": 2, "identifier": "QRS-4421", "type": "plate",  "image_path": None, "status": "pending", "created_at": "2025-05-21T13:55:22"},
]

@approvals_bp.route("/pending", methods=["GET"])
def get_pending():
    pending = [p for p in DUMMY_PENDING if p["status"] == "pending"]
    return jsonify({"total": len(pending), "pending": pending}), 200


@approvals_bp.route("/approve/<int:approval_id>", methods=["POST"])
def approve(approval_id):
    # Phase 2: will update DB and add to authorized list
    return jsonify({
        "message": f"Approval {approval_id} approved (dummy)",
        "id": approval_id,
        "status": "approved"
    }), 200


@approvals_bp.route("/reject/<int:approval_id>", methods=["POST"])
def reject(approval_id):
    data = request.get_json() or {}
    reason = data.get("reason", "No reason provided")
    return jsonify({
        "message": f"Approval {approval_id} rejected (dummy)",
        "id": approval_id,
        "status": "rejected",
        "reason": reason
    }), 200