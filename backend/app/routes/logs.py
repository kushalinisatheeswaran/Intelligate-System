from flask import Blueprint, request, jsonify
from datetime import datetime

logs_bp = Blueprint("logs", __name__)

DUMMY_LOGS = [
    {"id": 1, "identifier": "ABC-1234", "type": "plate",   "direction": "entry", "status": "granted", "name": "B. Karthigan",  "timestamp": "2025-05-21T14:32:05"},
    {"id": 2, "identifier": "23/ENG/070","type": "barcode","direction": "entry", "status": "granted", "name": "S. Kushalini",  "timestamp": "2025-05-21T14:28:41"},
    {"id": 3, "identifier": "XYZ-9988", "type": "plate",   "direction": "entry", "status": "denied",  "name": None,           "timestamp": "2025-05-21T14:19:03"},
    {"id": 4, "identifier": "23/ENG/138","type": "barcode","direction": "entry", "status": "granted", "name": "M. Sulaksan",   "timestamp": "2025-05-21T14:11:50"},
    {"id": 5, "identifier": "QRS-4421", "type": "plate",   "direction": "entry", "status": "denied",  "name": None,           "timestamp": "2025-05-21T13:55:22"},
]

@logs_bp.route("/logs", methods=["GET"])
def get_logs():
    status  = request.args.get("status")
    search  = request.args.get("search", "").lower()
    limit   = int(request.args.get("limit", 50))

    logs = DUMMY_LOGS
    if status:
        logs = [l for l in logs if l["status"] == status]
    if search:
        logs = [l for l in logs if search in l["identifier"].lower()]

    return jsonify({"total": len(logs), "logs": logs[:limit]}), 200


@logs_bp.route("/stats", methods=["GET"])
def get_stats():
    return jsonify({
        "today": {"total": 47, "granted": 41, "denied": 6},
        "by_hour": [
            {"hour": "08:00", "count": 8},
            {"hour": "09:00", "count": 15},
            {"hour": "10:00", "count": 12},
            {"hour": "11:00", "count": 7},
            {"hour": "12:00", "count": 5},
        ],
        "by_type": {"plate": 30, "barcode": 17}
    }), 200