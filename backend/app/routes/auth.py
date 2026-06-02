from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email    = data.get("email")
    password = data.get("password")

    # DUMMY — Phase 3 adds real JWT
    DUMMY_USERS = {
        "admin@intelligate.com":  {"password": "admin123",  "role": "admin"},
        "guard@intelligate.com":  {"password": "guard123",  "role": "guard"},
    }

    user = DUMMY_USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful (dummy token)",
        "token": "dummy-jwt-token-replace-in-phase-3",
        "role": user["role"],
        "email": email
    }), 200