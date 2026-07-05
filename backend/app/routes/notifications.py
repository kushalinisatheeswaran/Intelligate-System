from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.notification import Notification
from app.utils.decorators import guard_or_admin_required, admin_required

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications", methods=["GET"])
@jwt_required()
@guard_or_admin_required
def get_notifications():
    """
    Returns notification history.
    Dashboard notification panel calls this.
    """
    limit  = min(int(request.args.get("limit", 50)), 200)
    status = request.args.get("status")

    query = Notification.query.order_by(Notification.sent_at.desc())

    if status:
        query = query.filter_by(status=status)

    total = query.count()
    items = query.limit(limit).all()

    return jsonify({
        "total":         total,
        "notifications": [n.to_dict() for n in items]
    }), 200


@notifications_bp.route("/notifications/test", methods=["POST"])
@jwt_required()
@admin_required
def test_notification():
    """
    Sends a test Telegram message.
    Admin calls this from dashboard to verify bot is working.
    """
    result = send_test_message()
    return jsonify({
        "message": "Test alert sent" if result.get("sent") else "Test failed",
        "result":  result
    }), 200


@notifications_bp.route("/notifications/stats", methods=["GET"])
@jwt_required()
@guard_or_admin_required
def notification_stats():
    """Summary counts for dashboard notification panel."""
    total  = Notification.query.count()
    sent   = Notification.query.filter_by(status="sent").count()
    failed = Notification.query.filter_by(status="failed").count()

    return jsonify({
        "total":  total,
        "sent":   sent,
        "failed": failed
    }), 200