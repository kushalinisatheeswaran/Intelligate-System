from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.utils.decorators import admin_required
from app.services.gate_service   import open_gate, close_gate
from app.services.socket_service import emit_gate_status
from app.services.fcm_service    import send_gate_alert

gate_bp = Blueprint("gate", __name__)

@gate_bp.route("/gate/open", methods=["POST"])
@jwt_required()
@admin_required
def gate_open():
    claims = get_jwt()
    name   = claims.get("name", "admin")
    result = open_gate()
    emit_gate_status("open", triggered_by=name)
    send_gate_alert("open", triggered_by=name)
    return jsonify(result), 200

@gate_bp.route("/gate/close", methods=["POST"])
@jwt_required()
@admin_required
def gate_close():
    claims = get_jwt()
    name   = claims.get("name", "admin")
    result = close_gate()
    emit_gate_status("closed", triggered_by=name)
    return jsonify(result), 200