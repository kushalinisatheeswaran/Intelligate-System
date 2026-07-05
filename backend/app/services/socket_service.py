import logging
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

# Single SocketIO instance — imported everywhere
# Initialised in create_app(), used in routes and services
socketio = SocketIO()


def emit_vehicle_detected(data: dict):
    """
    Emitted on EVERY detection — granted or denied.
    React Native live feed screen listens to this.

    data = {
        identifier, id_type, direction,
        status, name, timestamp
    }
    """
    logger.info(f"[SOCKET] vehicle_detected → {data.get('identifier')}")
    socketio.emit("vehicle_detected", data)


def emit_unknown_vehicle(data: dict):
    """
    Emitted ONLY when a denied entry creates a pending approval.
    React Native alert banner listens to this.

    data = {
        identifier, id_type, image_path,
        pending_id, timestamp
    }
    """
    logger.info(f"[SOCKET] unknown_vehicle → {data.get('identifier')}")
    socketio.emit("unknown_vehicle", data)


def emit_access_granted(data: dict):
    """
    Emitted when access is granted.
    React Native shows green confirmation card.
    """
    socketio.emit("access_granted", data)


def emit_access_denied(data: dict):
    """
    Emitted when access is denied.
    React Native shows red denial card.
    """
    socketio.emit("access_denied", data)


def emit_gate_status(status: str, triggered_by: str = "system"):
    """
    Emitted after every gate open or close.
    React Native gate status indicator listens to this.

    status = "open" | "closed"
    """
    data = {"status": status, "triggered_by": triggered_by}
    logger.info(f"[SOCKET] gate_status → {status}")
    socketio.emit("gate_status", data)


def emit_approval_update(data: dict):
    """
    Emitted when admin approves or rejects a pending entry.
    React Native pending screen removes/updates the item live.

    data = {
        pending_id, identifier, status,
        reviewed_by, timestamp
    }
    """
    logger.info(
        f"[SOCKET] approval_update → "
        f"pending#{data.get('pending_id')} {data.get('status')}"
    )
    socketio.emit("approval_update", data)