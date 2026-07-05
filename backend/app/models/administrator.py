from app.database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Administrator(db.Model):
    __tablename__ = "administrators"

    id            = db.Column(db.Integer,    primary_key=True)
    user_id       = db.Column(db.Integer,    db.ForeignKey("users.id"), nullable=False)
    password_hash = db.Column(db.String(255),nullable=False)
    role          = db.Column(db.String(20), default="guard")  # admin | guard
    last_login    = db.Column(db.DateTime,   nullable=True)
    created_at    = db.Column(db.DateTime,   default=datetime.utcnow)

    user = db.relationship("User", backref="admin_profile", lazy=True)

    def __init__(self, **kwargs):
        super(Administrator, self).__init__(**kwargs)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id":         self.id,
            "user_id":    self.user_id,
            "role":       self.role,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "name":       self.user.name if self.user else None,
            "email":      self.user.email if self.user else None
        }