from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.utils.decorators import admin_required
from app.services.gate_service   import open_gate, close_gate

# 💡 SAFE UNIFIED MODULE IMPORT:
# This untangles the startup compile chain by treating the socket file as a module namespace.
from app.services import socket_service

from app.services.fcm_service    import send_gate_alert

gate_bp = Blueprint("gate", __name__)

@gate_bp.route("/gate/open", methods=["POST"])
@jwt_required()
@admin_required
def gate_open():
    claims = get_jwt()
    name   = claims.get("name", "admin")
    result = open_gate()
    
    # Updated to use module namespace prefixes
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
    
    # Updated to use module namespace prefixes
    socket_service.emit_gate_status("closed", triggered_by=name)
    return jsonify(result), 200