from app.database import db
from datetime import datetime

class AccessLog(db.Model):
    __tablename__ = "access_logs"

    id               = db.Column(db.Integer,     primary_key=True)
    user_id          = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=True)
    camera_id        = db.Column(db.String(50),  nullable=True)
    identifier       = db.Column(db.String(50),  nullable=True)  # plate or student number
    id_type          = db.Column(db.String(10),  nullable=False)  # plate | barcode
    direction        = db.Column(db.String(5),   default="entry") # entry | exit
    status           = db.Column(db.String(10),  nullable=False)  # granted | denied
    reason           = db.Column(db.String(255), nullable=True)
    confidence_score = db.Column(db.Float,       nullable=True)
    image_path       = db.Column(db.String(255), nullable=True)
    timestamp        = db.Column(db.DateTime,    default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(AccessLog, self).__init__(**kwargs)

    def to_dict(self):
        return {
            "id":               self.id,
            "user_id":          self.user_id,
            "camera_id":        self.camera_id,
            "identifier":       self.identifier,
            "id_type":          self.id_type,
            "direction":        self.direction,
            "status":           self.status,
            "reason":           self.reason,
            "confidence_score": self.confidence_score,
            "image_path":       self.image_path,
            "timestamp":        self.timestamp.isoformat(),
            "name":             self.user.name if self.user else None
        }