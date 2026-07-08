# app/models/notification.py
# NOTE: filename is notification.py (no 's') — matches import below

from app.database import db
from datetime import datetime, timezone

class Notification(db.Model):
    __tablename__ = "notifications"

    id          = db.Column(db.Integer,     primary_key=True)
    log_id      = db.Column(db.Integer,     db.ForeignKey("access_logs.id"), nullable=True)
    identifier  = db.Column(db.String(50),  nullable=False)
    id_type     = db.Column(db.String(10),  nullable=False)
    channel     = db.Column(db.String(20),  default="fcm")   # fcm | socketio
    recipient   = db.Column(db.String(50),  nullable=True)
    message     = db.Column(db.Text,        nullable=False)
    image_path  = db.Column(db.String(255), nullable=True)
    status      = db.Column(db.String(10),  default="sent")  # sent | failed
    error       = db.Column(db.String(255), nullable=True)
    sent_at     = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":         self.id,
            "log_id":     self.log_id,
            "identifier": self.identifier,
            "id_type":    self.id_type,
            "channel":    self.channel,
            "recipient":  self.recipient,
            "message":    self.message,
            "image_path": self.image_path,
            "status":     self.status,
            "error":      self.error,
            "sent_at":    self.sent_at.isoformat()
        }