from app.database import db
from datetime import datetime

class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id           = db.Column(db.Integer,    primary_key=True)
    user_id      = db.Column(db.Integer,    db.ForeignKey("users.id"), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(30), default="car")  # car | bike | van
    is_active    = db.Column(db.Boolean,    default=True)
    created_at   = db.Column(db.DateTime,   default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":           self.id,
            "user_id":      self.user_id,
            "plate_number": self.plate_number,
            "vehicle_type": self.vehicle_type,
            "is_active":    self.is_active
        }