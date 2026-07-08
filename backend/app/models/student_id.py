from app.database import db
from datetime import datetime, timezone

class StudentID(db.Model):
    __tablename__ = "student_ids"

    id             = db.Column(db.Integer,    primary_key=True)
    user_id        = db.Column(db.Integer,    db.ForeignKey("users.id"), nullable=False)
    student_number = db.Column(db.String(30), unique=True, nullable=False)
    faculty        = db.Column(db.String(60), nullable=True)
    is_active      = db.Column(db.Boolean,    default=True)
    created_at     = db.Column(db.DateTime,   default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super(StudentID, self).__init__(**kwargs)

    def to_dict(self):
        return {
            "id":             self.id,
            "user_id":        self.user_id,
            "student_number": self.student_number,
            "faculty":        self.faculty,
            "is_active":      self.is_active
        }