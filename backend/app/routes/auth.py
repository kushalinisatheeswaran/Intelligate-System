from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime, timezone

from app.database import db
from app.models.administrator import Administrator
from app.models.user import User   # IMPORTANT FIX

auth_bp = Blueprint("auth", __name__)


# ======================================================
# LOGIN
# ======================================================
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    print("\n" + "=" * 60)
    print("LOGIN ATTEMPT")
    print("EMAIL:", email)

    admin = (
        Administrator.query
        .join(User, Administrator.user_id == User.id)
        .filter(User.email == email)
        .first()
    )

    print("ADMIN FOUND:", admin)

    if not admin:
        print("RESULT: USER NOT FOUND")
        print("=" * 60)
        return jsonify({"error": "Invalid email or password"}), 401

    password_ok = admin.check_password(password)

    print("PASSWORD MATCH:", password_ok)

    if not password_ok:
        print("RESULT: PASSWORD INCORRECT")
        print("=" * 60)
        return jsonify({"error": "Invalid email or password"}), 401

    if hasattr(admin.user, "is_active") and not admin.user.is_active:
        print("RESULT: ACCOUNT DEACTIVATED")
        print("=" * 60)
        return jsonify({"error": "Account is deactivated"}), 403

    admin.last_login = datetime.now(timezone.utc)
    db.session.commit()

    access_token = create_access_token(
        identity=str(admin.user_id),
        additional_claims={
            "role": admin.role,
            "name": admin.user.name,
            "email": admin.user.email,
            "admin_id": admin.id,
        },
    )

    print("RESULT: LOGIN SUCCESS")
    print("=" * 60)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "Bearer",
        "user": {
            "id": admin.user_id,
            "name": admin.user.name,
            "email": admin.user.email,
            "role": admin.role,
        },
    }), 200
# ======================================================
# GET CURRENT USER
# ======================================================
@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    claims = get_jwt()

    return jsonify({
        "id": get_jwt_identity(),
        "name": claims.get("name"),
        "email": claims.get("email"),
        "role": claims.get("role")
    }), 200


# ======================================================
# LOGOUT (CLIENT SIDE JWT)
# ======================================================
@auth_bp.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully"}), 200


# ======================================================
# CHANGE PASSWORD
# ======================================================
@auth_bp.route("/auth/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()

    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "old_password and new_password required"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    admin = Administrator.query.filter_by(user_id=int(user_id)).first()

    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    if not admin.check_password(old_password):
        return jsonify({"error": "Current password is incorrect"}), 401

    admin.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200