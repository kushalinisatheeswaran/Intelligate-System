from app.models.device_token import DeviceToken
from app import create_app
from app.database import db
from app.models.user          import User
from app.models.vehicle       import Vehicle
from app.models.student_id    import StudentID
from app.models.administrator import Administrator
from app.models.access_log    import AccessLog
from app.models.pending import PendingApproval
from app.models.device_token import DeviceToken
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    print("Clearing existing data...")
    DeviceToken.query.delete()
    PendingApproval.query.delete()
    AccessLog.query.delete()
    Administrator.query.delete()
    StudentID.query.delete()
    Vehicle.query.delete()

    # PARENT LAST
    User.query.delete()

    db.session.commit()
    print("Creating users...")
    users = [
        User(name="B. Karthigan",  email="karthigan@uni.edu",  role="student"),
        User(name="S. Kushalini",  email="kushalini@uni.edu",  role="student"),
        User(name="M. Sulaksan",   email="sulaksan@uni.edu",   role="student"),
        User(name="Dr. Fernando",  email="fernando@uni.edu",   role="staff"),
        User(name="Admin User",    email="admin@intelligate.com", role="admin"),
        User(name="Guard Rajan",   email="guard@intelligate.com", role="staff"),
    ]
    for u in users:
        db.session.add(u)
    db.session.flush()

    print("Creating vehicles...")
    vehicles = [
        Vehicle(user_id=users[0].id, plate_number="ABC-1234", vehicle_type="car"),
        Vehicle(user_id=users[1].id, plate_number="XYZ-5678", vehicle_type="car"),
        Vehicle(user_id=users[3].id, plate_number="STF-0011", vehicle_type="car"),
    ]
    for v in vehicles:
        db.session.add(v)

    print("Creating student IDs...")
    student_ids = [
        StudentID(user_id=users[0].id, student_number="23/ENG/062", faculty="Engineering"),
        StudentID(user_id=users[1].id, student_number="23/ENG/070", faculty="Engineering"),
        StudentID(user_id=users[2].id, student_number="23/ENG/138", faculty="Engineering"),
    ]
    for s in student_ids:
        db.session.add(s)

    print("Creating admin accounts...")
    admin = Administrator(user_id=users[4].id, role="admin")
    admin.set_password("admin123")
    guard = Administrator(user_id=users[5].id, role="guard")
    guard.set_password("guard123")
    db.session.add(admin)
    db.session.add(guard)

    print("Creating sample access logs...")
    identifiers = [
        ("ABC-1234", "plate",   "granted", users[0].id),
        ("XYZ-5678", "plate",   "granted", users[1].id),
        ("23/ENG/062","barcode","granted", users[0].id),
        ("23/ENG/070","barcode","granted", users[1].id),
        ("UNKNOWN-1", "plate",  "denied",  None),
        ("UNKNOWN-2", "plate",  "denied",  None),
    ]
    for i in range(30):
        pick = random.choice(identifiers)
        log = AccessLog(
            user_id    = pick[3],
            identifier = pick[0],
            id_type    = pick[1],
            direction  = "entry",
            status     = pick[2],
            timestamp  = datetime.utcnow() - timedelta(hours=random.randint(0, 23),
                                                        minutes=random.randint(0, 59))
        )
        db.session.add(log)

    db.session.commit()
    print("Seed complete. Database ready.")