from flask import Flask
from flask_cors import CORS
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=["http://localhost:3000"])

    # Register all route blueprints
    from app.routes.verify import verify_bp
    from app.routes.logs import logs_bp
    from app.routes.approvals import approvals_bp
    from app.routes.gate import gate_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(verify_bp,    url_prefix="/api")
    app.register_blueprint(logs_bp,      url_prefix="/api")
    app.register_blueprint(approvals_bp, url_prefix="/api")
    app.register_blueprint(gate_bp,      url_prefix="/api")
    app.register_blueprint(auth_bp,      url_prefix="/api")

    @app.route("/api/health")
    def health():
        return {"status": "ok", "project": "IntelliGate"}, 200

    return app