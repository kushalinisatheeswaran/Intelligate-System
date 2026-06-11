from app.database import db
from datetime import datetime

class PendingApproval(db.Model):
    __tablename__ = "pending_approvals"

    id          = db.Column(db.Integer,     primary_key=True)
    log_id      = db.Column(db.Integer,     db.ForeignKey("access_logs.id"), nullable=False)
    identifier  = db.Column(db.String(50),  nullable=False)
    id_type     = db.Column(db.String(10),  nullable=False)
    image_path  = db.Column(db.String(255), nullable=True)
    status      = db.Column(db.String(10),  default="pending") # pending | approved | rejected
    reviewed_by = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=True)
    reason      = db.Column(db.String(255), nullable=True)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime,    nullable=True)

    log = db.relationship("AccessLog", backref="pending_approval", lazy=True)

    def to_dict(self):
        return {
            "id":          self.id,
            "log_id":      self.log_id,
            "identifier":  self.identifier,
            "id_type":     self.id_type,
            "image_path":  self.image_path,
            "status":      self.status,
            "reason":      self.reason,
            "created_at":  self.created_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None
        }