from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.config import Config
from app.database import db, migrate
from app.services.socket_service import socketio


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    CORS(app, resources={
        r"/api/*": {"origins": app.config["SOCKETIO_CORS_ORIGINS"]},
        r"/socket.io/*": {"origins": app.config["SOCKETIO_CORS_ORIGINS"]}
    })

    # ✅ SocketIO init (FIXED)
    socketio.init_app(
        app,
        cors_allowed_origins=app.config["SOCKETIO_CORS_ORIGINS"],
        async_mode="eventlet"   # OR remove this line completely (recommended)
    )

    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return {"error": "Missing token"}, 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {"error": "Token expired"}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {"error": "Invalid token"}, 401

    # Import models
    from app.models import (
        user, vehicle, student_id, access_log,
        pending, administrator, notification, device_token
    )

    # Blueprints
    from app.routes.verify import verify_bp
    from app.routes.logs import logs_bp
    from app.routes.approvals import approvals_bp
    from app.routes.gate import gate_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.notifications import notifications_bp
    from app.routes.devices import devices_bp

    app.register_blueprint(verify_bp, url_prefix="/api")
    app.register_blueprint(logs_bp, url_prefix="/api")
    app.register_blueprint(approvals_bp, url_prefix="/api")
    app.register_blueprint(gate_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api")
    app.register_blueprint(devices_bp, url_prefix="/api")

    # Socket events
    from app.socket_events import register_socket_events
    register_socket_events(socketio)

    # Firebase
    from app.services.fcm_service import init_firebase
    init_firebase()

    @app.route("/api/health")
    def health():
        return {
            "status": "ok",
            "project": "IntelliGate"
        }, 200

    return app