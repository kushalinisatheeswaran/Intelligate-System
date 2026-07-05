from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.database import db
from app.models.user       import User
from app.models.vehicle    import Vehicle
from app.models.student_id import StudentID
from app.models.administrator import Administrator
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


# ======================================================
# STUDENT CRUD APIs (EXTENDED USER INFO)
# ======================================================

@users_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    user_dict = user.to_dict()
    user_dict["vehicles"] = [v.to_dict() for v in user.vehicles]
    user_dict["student_ids"] = [s.to_dict() for s in user.student_ids]
    return jsonify(user_dict), 200


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400
        user.name = name

    if "email" in data:
        email = data["email"].strip().lower() if data["email"] else None
        if email:
            existing = User.query.filter(User.email == email, User.id != user_id).first()
            if existing:
                return jsonify({"error": f"Email {email} is already in use"}), 409
        user.email = email



    # Also allow updating student ID details if role is student/staff
    if "student_number" in data or "faculty" in data:
        student_id_rec = StudentID.query.filter_by(user_id=user_id).first()
        if student_id_rec:
            if "student_number" in data:
                student_num = data["student_number"].strip().upper()
                is_valid, err = validate_identifier("barcode", student_num)
                if not is_valid:
                    return jsonify({"error": err}), 400
                dup = StudentID.query.filter(StudentID.student_number == student_num, StudentID.user_id != user_id).first()
                if dup:
                    return jsonify({"error": f"Student number {student_num} already registered"}), 409
                student_id_rec.student_number = student_num
            if "faculty" in data:
                student_id_rec.faculty = data["faculty"].strip()
        else:
            if "student_number" in data:
                student_num = data["student_number"].strip().upper()
                is_valid, err = validate_identifier("barcode", student_num)
                if not is_valid:
                    return jsonify({"error": err}), 400
                dup = StudentID.query.filter_by(student_number=student_num).first()
                if dup:
                    return jsonify({"error": f"Student number {student_num} already registered"}), 409
                student_id_rec = StudentID(
                    user_id=user_id,
                    student_number=student_num,
                    faculty=data.get("faculty", "Unknown").strip(),
                    is_active=True
                )
                db.session.add(student_id_rec)

    db.session.commit()
    
    # Return user details
    user_dict = user.to_dict()
    user_dict["vehicles"] = [v.to_dict() for v in user.vehicles]
    user_dict["student_ids"] = [s.to_dict() for s in user.student_ids]
    return jsonify({
        "message": "User updated successfully",
        "user": user_dict
    }), 200


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    Vehicle.query.filter_by(user_id=user_id).update({"is_active": False})
    StudentID.query.filter_by(user_id=user_id).update({"is_active": False})
    user.is_active = False
    db.session.commit()
    return jsonify({
        "message": f"User {user.name} soft-deleted successfully",
        "user_id": user_id
    }), 200


# ======================================================
# VEHICLE CRUD APIs
# ======================================================

@users_bp.route("/users/<int:user_id>/vehicles", methods=["POST"])
@jwt_required()
@admin_required
def add_user_vehicle(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data or not data.get("plate_number"):
        return jsonify({"error": "Missing required field: plate_number"}), 400

    plate_number = data["plate_number"].strip().upper()
    is_valid, error = validate_identifier("plate", plate_number)
    if not is_valid:
        return jsonify({"error": error}), 400

    existing = Vehicle.query.filter_by(plate_number=plate_number).first()
    if existing:
        return jsonify({"error": f"Plate {plate_number} already registered"}), 409

    vehicle = Vehicle(
        user_id=user_id,
        plate_number=plate_number,
        vehicle_type=data.get("vehicle_type", "car"),
        is_active=True
    )
    db.session.add(vehicle)
    db.session.commit()

    return jsonify({
        "message": "Vehicle attached successfully",
        "vehicle": vehicle.to_dict()
    }), 201


@users_bp.route("/users/<int:user_id>/vehicles", methods=["GET"])
@jwt_required()
@admin_required
def get_user_vehicles(user_id):
    user = User.query.get_or_404(user_id)
    vehicles = Vehicle.query.filter_by(user_id=user_id).all()
    return jsonify({
        "total": len(vehicles),
        "vehicles": [v.to_dict() for v in vehicles]
    }), 200


@users_bp.route("/vehicles/<int:vehicle_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.get_json() or {}

    if "plate_number" in data:
        plate_number = data["plate_number"].strip().upper()
        is_valid, error = validate_identifier("plate", plate_number)
        if not is_valid:
            return jsonify({"error": error}), 400

        existing = Vehicle.query.filter(Vehicle.plate_number == plate_number, Vehicle.id != vehicle_id).first()
        if existing:
            return jsonify({"error": f"Plate {plate_number} already registered"}), 409
        vehicle.plate_number = plate_number

    if "vehicle_type" in data:
        vehicle.vehicle_type = data["vehicle_type"].strip().lower()

    if "is_active" in data:
        vehicle.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({
        "message": "Vehicle updated successfully",
        "vehicle": vehicle.to_dict()
    }), 200


@users_bp.route("/vehicles/<int:vehicle_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({
        "message": "Vehicle deleted successfully",
        "vehicle_id": vehicle_id
    }), 200


# ======================================================
# GUARD CRUD APIs
# ======================================================

@users_bp.route("/admin/guards", methods=["GET"])
@jwt_required()
@admin_required
def get_guards():
    guards = Administrator.query.filter_by(role="guard").all()
    return jsonify({
        "total": len(guards),
        "guards": [g.to_dict() for g in guards]
    }), 200


@users_bp.route("/admin/guards", methods=["POST"])
@jwt_required()
@admin_required
def create_guard():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Name, email, and password required"}), 400

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    if User.query.filter_by(email=email).first():
        return jsonify({"error": f"Email {email} is already in use"}), 409

    user = User(
        name=name,
        email=email,
        role="staff"
    )
    db.session.add(user)
    db.session.flush()

    admin_profile = Administrator(
        user_id=user.id,
        role="guard"
    )
    admin_profile.set_password(password)
    db.session.add(admin_profile)
    db.session.commit()

    return jsonify({
        "message": "Guard account created successfully",
        "guard": admin_profile.to_dict()
    }), 201


@users_bp.route("/admin/guards/<int:admin_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_guard(admin_id):
    admin = Administrator.query.filter_by(id=admin_id, role="guard").first_or_404()
    data = request.get_json() or {}

    user = admin.user
    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400
        user.name = name

    if "email" in data:
        email = data["email"].strip().lower()
        if email:
            existing = User.query.filter(User.email == email, User.id != user.id).first()
            if existing:
                return jsonify({"error": f"Email {email} is already in use"}), 409
        user.email = email

    if "password" in data:
        password = data["password"]
        if password:
            admin.set_password(password)

    db.session.commit()
    return jsonify({
        "message": "Guard updated successfully",
        "guard": admin.to_dict()
    }), 200


@users_bp.route("/admin/guards/<int:admin_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def deactivate_guard(admin_id):
    admin = Administrator.query.filter_by(id=admin_id, role="guard").first_or_404()
    admin.user.is_active = False
    db.session.commit()
    return jsonify({
        "message": f"Guard {admin.user.name} deactivated successfully",
        "admin_id": admin_id
    }), 200