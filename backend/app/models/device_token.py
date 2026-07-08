from app.database import db
from datetime import datetime, timezone

class DeviceToken(db.Model):
    __tablename__ = "device_tokens"

    id            = db.Column(db.Integer,     primary_key=True)
    user_id       = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=False)
    fcm_token     = db.Column(db.Text,        nullable=False, unique=True)
    device_type   = db.Column(db.String(10),  default="android") # android | ios
    is_active     = db.Column(db.Boolean,     default=True)
    registered_at = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref="device_tokens", lazy=True)

    def to_dict(self):
        return {
            "id":            self.id,
            "user_id":       self.user_id,
            "device_type":   self.device_type,
            "is_active":     self.is_active,
            "registered_at": self.registered_at.isoformat()
            # never return fcm_token to client
        }