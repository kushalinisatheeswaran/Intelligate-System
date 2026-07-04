from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app.services.gate_service import open_gate, close_gate
from app.services import socket_service

gate_bp = Blueprint("gate", __name__)

@gate_bp.route("/gate/open", methods=["POST"])
@jwt_required()
def trigger_open():
    """
    API endpoint that receives network instructions and pushes them 
    directly to open the physical gate.
    """
    result = open_gate()
    if result.get("status") == "error":
        return jsonify(result), 500
        
    claims = get_jwt()
    username = claims.get("name", "admin")
    socket_service.emit_gate_status("open", triggered_by=username)
    return jsonify(result), 200

@gate_bp.route("/gate/close", methods=["POST"])
@jwt_required()
def trigger_close():
    """
    API endpoint that receives network instructions and pushes them 
    directly to close the physical gate.
    """
    result = close_gate()
    if result.get("status") == "error":
        return jsonify(result), 500
        
    claims = get_jwt()
    username = claims.get("name", "admin")
    socket_service.emit_gate_status("closed", triggered_by=username)
    return jsonify(result), 200