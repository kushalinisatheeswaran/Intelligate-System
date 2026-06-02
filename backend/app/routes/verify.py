from flask import Blueprint, request, jsonify
from datetime import datetime

verify_bp = Blueprint("verify", __name__)

@verify_bp.route("/verify", methods=["POST"])
def verify():
    data = request.get_json()

    if not data or "type" not in data or "value" not in data:
        return jsonify({"error": "Missing required fields: type, value"}), 400

    id_type  = data["type"]       # "plate" or "barcode"
    value    = data["value"]      # "ABC-1234" or "23/ENG/062"
    direction = data.get("direction", "entry")

    # --- DUMMY LOGIC (replaced in Phase 2) ---
    AUTHORIZED = ["ABC-1234", "XYZ-5678", "23/ENG/062", "23/ENG/070"]

    if value in AUTHORIZED:
        return jsonify({
            "status": "granted",
            "identifier": value,
            "type": id_type,
            "direction": direction,
            "name": "Authorized User",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Gate opening"
        }), 200
    else:
        return jsonify({
            "status": "denied",
            "identifier": value,
            "type": id_type,
            "direction": direction,
            "reason": "not_in_database",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Access denied. Pending review."
        }), 200