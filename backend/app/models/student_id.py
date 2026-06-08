from app.database import db
from datetime import datetime

class StudentID(db.Model):
    __tablename__ = "student_ids"

    id             = db.Column(db.Integer,    primary_key=True)
    user_id        = db.Column(db.Integer,    db.ForeignKey("users.id"), nullable=False)
    student_number = db.Column(db.String(30), unique=True, nullable=False)
    faculty        = db.Column(db.String(60), nullable=True)
    is_active      = db.Column(db.Boolean,    default=True)
    created_at     = db.Column(db.DateTime,   default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":             self.id,
            "user_id":        self.user_id,
            "student_number": self.student_number,
            "faculty":        self.faculty,
            "is_active":      self.is_active
        }