from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app.utils.decorators import admin_required
from app.services.gate_service   import open_gate, close_gate

from app.services import socket_service
from app.services.fcm_service    import send_gate_alert

from app.models.vehicle import Vehicle
from app.models.access_log import AccessLog
from app.database import db  # Assume the db comes from extensions based on typical flask structure

gate_bp = Blueprint("gate", __name__)

@gate_bp.route("/gate/open", methods=["POST"])
@jwt_required()
@admin_required
def gate_open():
    claims = get_jwt()
    name   = claims.get("name", "admin")
    result = open_gate()
    
    socket_service.emit_gate_status("open", triggered_by=name)
    send_gate_alert("open", triggered_by=name)
    return jsonify(result), 200

@gate_bp.route("/gate/close", methods=["POST"])
@jwt_required()
@admin_required
def gate_close():
    claims = get_jwt()
    name   = claims.get("name", "admin")
    result = close_gate()
    
    socket_service.emit_gate_status("closed", triggered_by=name)
    return jsonify(result), 200

@gate_bp.route("/gate/check-plate", methods=["POST"])
def check_plate():
    """
    M2M Endpoint for the IntelliGate automated system
    Expected Payload: {"plate": "ABC1234"}
    """
    data = request.get_json()
    if not data or "plate" not in data:
        return jsonify({"allowed": False, "error": "Missing plate data"}), 400
        
    detected_plate = data.get("plate").strip().upper()
    
    # 1. Look up the plate in your registered vehicles model
    vehicle = Vehicle.query.filter_by(plate_number=detected_plate).first()
    
    if vehicle and vehicle.is_approved: # Customize based on your model attributes
        # Plate matches an active user!
        # Trigger your existing hardware/socket logic
        open_gate() 
        socket_service.emit_gate_status("open", triggered_by=f"ANPR: {detected_plate}")
        send_gate_alert("open", triggered_by=f"ANPR: {detected_plate}")
        
        # Log successful entry to database
        log = AccessLog(plate_number=detected_plate, status="ALLOWED", remarks="Automated verification successful")
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"allowed": True, "message": "Access Granted"}), 200
    
    else:
        # Plate is unknown or unauthorized
        # Log unauthorized attempt to entry_attempts log / database
        log = AccessLog(plate_number=detected_plate, status="DENIED", remarks="Unknown or unapproved plate")
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"allowed": False, "message": "Access Denied"}), 200