from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime
from app.database import db
from app.models.administrator import Administrator

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    email    = data["email"].strip().lower()
    password = data["password"]

    # Find admin account by email via relationship
    admin = Administrator.query.join(Administrator.user)\
                .filter_by(email=email).first()

    if not admin or not admin.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not admin.user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    # Update last login timestamp
    admin.last_login = datetime.utcnow()
    db.session.commit()

    # Create JWT with custom claims
    # identity = admin user id (string required by flask-jwt-extended)
    # additional_claims = role, name, email embedded in token
    access_token = create_access_token(
        identity=str(admin.user_id),
        additional_claims={
            "role":     admin.role,
            "name":     admin.user.name,
            "email":    admin.user.email,
            "admin_id": admin.id
        }
    )

    return jsonify({
        "message":      "Login successful",
        "access_token": access_token,
        "token_type":   "Bearer",
        "user": {
            "id":    admin.user_id,
            "name":  admin.user.name,
            "email": admin.user.email,
            "role":  admin.role
        }
    }), 200


@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    """
    Returns the currently logged-in user's profile.
    Frontend calls this on page load to verify token is still valid.
    """
    claims = get_jwt()
    return jsonify({
        "id":    get_jwt_identity(),
        "name":  claims.get("name"),
        "email": claims.get("email"),
        "role":  claims.get("role")
    }), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Client-side logout — frontend deletes the token.
    Phase 3 uses stateless JWT so no server-side blacklist yet.
    If needed in production, use flask-jwt-extended's token blocklist.
    """
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/auth/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data    = request.get_json()

    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "old_password and new_password required"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    admin = Administrator.query.filter_by(user_id=int(user_id)).first()

    if not admin or not admin.check_password(old_password):
        return jsonify({"error": "Current password is incorrect"}), 401

    admin.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200