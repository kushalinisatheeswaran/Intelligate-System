from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.database import db
from app.models.user       import User
from app.models.vehicle    import Vehicle
from app.models.student_id import StudentID
from app.utils.decorators  import admin_required
from app.utils.validators  import validate_identifier

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def get_users():
    users = User.query.filter(User.role != "visitor")\
                .order_by(User.name).all()
    return jsonify({
        "total": len(users),
        "users": [u.to_dict() for u in users]
    }), 200


@users_bp.route("/users/register", methods=["POST"])
@jwt_required()
@admin_required
def register_user():
    """
    Register a new authorized user with their vehicle or student ID.
    Admin calls this to pre-authorize someone before they arrive.
    """
    data = request.get_json()

    required = ["name", "type", "identifier"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    name       = data["name"].strip()
    id_type    = data["type"].strip().lower()
    identifier = data["identifier"].strip().upper()

    is_valid, error = validate_identifier(id_type, identifier)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Check for duplicate
    if id_type == "plate":
        if Vehicle.query.filter_by(plate_number=identifier).first():
            return jsonify({"error": f"Plate {identifier} already registered"}), 409
    elif id_type == "barcode":
        if StudentID.query.filter_by(student_number=identifier).first():
            return jsonify({"error": f"Student ID {identifier} already registered"}), 409

    # Create user
    user = User(
        name  = name,
        email = data.get("email"),
        role  = data.get("role", "student")
    )
    db.session.add(user)
    db.session.flush()

    # Create vehicle or student ID
    if id_type == "plate":
        record = Vehicle(
            user_id      = user.id,
            plate_number = identifier,
            vehicle_type = data.get("vehicle_type", "car"),
            is_active    = True
        )
    else:
        record = StudentID(
            user_id        = user.id,
            student_number = identifier,
            faculty        = data.get("faculty", "Unknown"),
            is_active      = True
        )

    db.session.add(record)
    db.session.commit()

    return jsonify({
        "message":    "User registered successfully",
        "user":       user.to_dict(),
        "identifier": identifier,
        "type":       id_type
    }), 201


@users_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@jwt_required()
@admin_required
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)

    # Deactivate all their vehicles and student IDs
    Vehicle.query.filter_by(user_id=user_id).update({"is_active": False})
    StudentID.query.filter_by(user_id=user_id).update({"is_active": False})
    user.is_active = False

    db.session.commit()
    return jsonify({
        "message": f"User {user.name} deactivated. All identifiers revoked.",
        "user_id": user_id
    }), 200


@users_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@jwt_required()
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    Vehicle.query.filter_by(user_id=user_id).update({"is_active": True})
    StudentID.query.filter_by(user_id=user_id).update({"is_active": True})
    user.is_active = True

    db.session.commit()
    return jsonify({
        "message": f"User {user.name} reactivated.",
        "user_id": user_id
    }), 200