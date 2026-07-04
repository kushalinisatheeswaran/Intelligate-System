import logging
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)


def register_socket_events(socketio):

    @socketio.on("connect")
    def on_connect():
        logger.info(f"[SOCKET] Client connected")
        emit("connected", {
            "message": "Connected to IntelliGate real-time server",
            "status":  "ok"
        })

    @socketio.on("disconnect")
    def on_disconnect():
        logger.info(f"[SOCKET] Client disconnected")

    @socketio.on("join_room")
    def on_join(data):
        """
        React Native app joins a room after login.
        Allows sending events to specific roles only.
        data = {"room": "guards"} or {"room": "admins"}
        """
        room = data.get("room")
        if room in ("guards", "admins"):
            join_room(room)
            logger.info(f"[SOCKET] Client joined room: {room}")
            emit("room_joined", {"room": room})

    @socketio.on("ping_gate")
    def on_ping_gate(data):
        """
        React Native app pings to check if gate system is online.
        """
        emit("pong_gate", {"status": "online", "system": "IntelliGate"})

    @socketio.on("gate_command")
    def on_gate_command(data):
        """
        Manually trigger gate open or close from the frontend.
        """
        command = data.get("command", "").upper()
        logger.info(f"[SOCKET] Received gate_command: {command}")

        from app.services.gate_service import open_gate, close_gate
        from app.services.socket_service import emit_gate_status

        if command == "OPEN":
            open_gate()
            emit_gate_status("open", triggered_by="Admin Manual Control")
        elif command == "CLOSE":
            close_gate()
            emit_gate_status("closed", triggered_by="Admin Manual Control")
        else:
            logger.warning(f"[SOCKET] Invalid gate_command received: {command}")