from app.database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer,     primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=True)
    role       = db.Column(db.String(20),  default="student")  # student | staff
    is_active  = db.Column(db.Boolean,     default=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    # Relationships
    vehicles    = db.relationship("Vehicle",   backref="user", lazy=True)
    student_ids = db.relationship("StudentID", backref="user", lazy=True)
    access_logs = db.relationship("AccessLog", backref="user", lazy=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "role":       self.role,
            "is_active":  self.is_active,
            "created_at": self.created_at.isoformat()
        }