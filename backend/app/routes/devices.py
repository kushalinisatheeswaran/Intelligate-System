from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models.device_token import DeviceToken

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("/devices/register", methods=["POST"])
@jwt_required()
def register_device():
    """
    React Native app calls this on login to register FCM token.
    If token already exists, updates it to active.
    """
    user_id = int(get_jwt_identity())
    data    = request.get_json()

    if not data or not data.get("fcm_token"):
        return jsonify({"error": "fcm_token is required"}), 400

    fcm_token   = data["fcm_token"]
    device_type = data.get("device_type", "android")

    # Upsert — update if exists, insert if new
    existing = DeviceToken.query.filter_by(fcm_token=fcm_token).first()
    if existing:
        existing.user_id     = user_id
        existing.device_type = device_type
        existing.is_active   = True
    else:
        token = DeviceToken(
            user_id     = user_id,
            fcm_token   = fcm_token,
            device_type = device_type,
            is_active   = True
        )
        db.session.add(token)

    db.session.commit()
    return jsonify({"message": "Device token registered"}), 200


@devices_bp.route("/devices/unregister", methods=["POST"])
@jwt_required()
def unregister_device():
    """
    Called on logout — deactivates FCM token so guard
    stops receiving alerts after signing out.
    """
    user_id = int(get_jwt_identity())
    data    = request.get_json()
    token   = data.get("fcm_token") if data else None

    if token:
        DeviceToken.query.filter_by(
            fcm_token=token, user_id=user_id
        ).update({"is_active": False})
    else:
        # Deactivate ALL tokens for this user
        DeviceToken.query.filter_by(
            user_id=user_id
        ).update({"is_active": False})

    db.session.commit()
    return jsonify({"message": "Device token unregistered"}), 200
