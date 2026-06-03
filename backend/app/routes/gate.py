from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import admin_required
from app.services.gate_service import open_gate, close_gate

gate_bp = Blueprint("gate", __name__)

@gate_bp.route("/gate/open", methods=["POST"])
@jwt_required()
@admin_required
def gate_open():
    result = open_gate()
    return jsonify(result), 200

@gate_bp.route("/gate/close", methods=["POST"])
@jwt_required()
@admin_required
def gate_close():
    result = close_gate()
    return jsonify(result), 200