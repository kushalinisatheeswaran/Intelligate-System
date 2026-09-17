# IntelliGate – Smart University Gate Automation System

IntelliGate is a **Smart University Gate Automation System** developed to automate and improve vehicle and student access management at a university entrance.

The system combines **vehicle number plate recognition, student barcode identification, backend verification, access logging, occupancy tracking, real-time monitoring, human approval for unauthorized vehicles, and physical gate automation** in a single integrated prototype.

---

## 1. Problem & Motivation

Traditional university gate management often depends on manual verification by security personnel. This can result in:

- Human errors during verification
- Longer access times
- Limited real-time monitoring
- Difficulty maintaining entry and exit records
- Weak occupancy tracking
- Difficulty handling unauthorized vehicles efficiently

IntelliGate addresses these limitations by introducing an automated access-control and monitoring system.

---

## 2. Main Features

### Vehicle Access Control

- USB camera for vehicle entry
- Raspberry Pi camera for vehicle exit
- Vehicle number plate recognition using OpenCV and OCR
- Vehicle authorization through the backend
- Entry/exit state checking
- Anti-passback control
- Automatic access logging
- Physical gate control

### Student Access Control

- MacBook camera for student barcode capture
- Code 39 barcode identification
- Six-digit student ID extraction
- Backend student verification
- Student entry/exit tracking
- Access logging
- Student occupancy tracking
- Physical gate activation for valid access

### Unauthorized Vehicle Handling

- Unknown vehicle detection
- Automatic access denial
- Pending approval request creation
- Guard/Admin review
- Approve or reject workflow
- Traceable access decisions
- Gate remains closed when access is rejected

### Mobile Monitoring

- React Native mobile application
- Admin and Guard access
- Access monitoring
- Occupancy monitoring
- Pending approval management
- Vehicle and student management
- Real-time event updates using Socket.IO

### Security

- JWT-based authentication
- Role-Based Access Control (RBAC)
- Admin and Guard roles
- Password hashing
- Protected backend APIs
- Generic invalid-login responses
- Input validation
- Failed-login attempt detection
- Temporary account lockout after repeated failed login attempts

---

## 3. System Architecture

```text
             INPUT / SENSING
                    |
       +------------+-------------+
       |            |             |
 USB Entry      Pi Exit       MacBook Camera
  Camera         Camera       Student Barcode
       |            |             |
       +------------+-------------+
                    |
                    v
             RECOGNITION
        OpenCV / OCR / Barcode
               Decoding
                    |
                    v
              FLASK BACKEND
        REST API / JWT / RBAC
                    |
             +------+------+
             |             |
             v             v
        PostgreSQL     Access Decision
             |             |
             |       +-----+------+
             |       |            |
             |    Granted       Denied
             |       |            |
             |       v            v
             |   Gate Control   Pending
             |                 Approval
             |
             v
        Access Logs
        User / Vehicle Data
        Occupancy State

                    |
              Socket.IO
                    |
                    v
          React Native Mobile App
                    |
              Guard / Admin

                    +
             Arduino Nano
                    |
               Servo Motor
                    |
              Physical Gate
```

---

## 4. Technology Stack

### Backend

- Python
- Flask
- Flask-SocketIO
- Flask-JWT-Extended
- SQLAlchemy
- PostgreSQL

### Computer Vision & Recognition

- OpenCV
- Tesseract OCR
- Barcode decoding
- Code 39 barcode format

### Frontend / Mobile Application

- React Native
- Expo
- REST API communication
- Socket.IO

### Hardware

- Raspberry Pi
- USB Camera – Vehicle Entry
- Pi Camera – Vehicle Exit
- MacBook Camera – Student Code 39 Barcode Scanning
- Arduino Nano
- Servo Motor

### Real-Time Communication

- Socket.IO
- Firebase / FCM support

---

## 5. Vehicle Access Workflow

```text
Vehicle Approaches
        |
        v
Camera Captures Plate
        |
        v
OpenCV + OCR
        |
        v
Extract Plate Number
        |
        v
Flask Backend
        |
        v
Database Verification
        |
        v
Entry / Exit State Check
        |
   +----+----+
   |         |
 Valid     Invalid
   |         |
   v         v
Access     Access
Granted    Denied
   |         |
   v         v
Access    Pending Approval
Log       (if unknown)
   |
   v
Physical Gate Opens
```

An authorized vehicle is allowed only when its requested direction is valid.

For example:

- Vehicle outside + ENTRY → Allowed
- Vehicle inside + ENTRY → Denied
- Vehicle inside + EXIT → Allowed
- Vehicle outside + EXIT → Denied

This prevents invalid repeated entry or exit.

---

## 6. Student Access Workflow

```text
Student Approaches
        |
        v
MacBook Camera
        |
        v
Capture Code 39 Barcode
        |
        v
Extract Student ID
        |
        v
Flask Backend Verification
        |
        v
Entry / Exit State Check
        |
        v
Create Access Log
        |
        v
Update Occupancy
        |
        v
Open Physical Gate
```

The student's latest successful access state is used to determine whether the student is currently inside or outside.

Successful student entry and exit events contribute to the **Currently Inside / Occupancy** monitoring functionality.

---

## 7. Anti-Passback

IntelliGate includes entry/exit state checking to prevent invalid repeated access.

```text
Outside
   |
 ENTRY
   |
   v
Inside
   |
 EXIT
   |
   v
Outside
```

Examples:

```text
Outside → ENTRY → Granted
Inside  → ENTRY → Denied

Inside  → EXIT  → Granted
Outside → EXIT  → Denied
```

This helps maintain a more accurate representation of the current access state.

---

## 8. Unauthorized Vehicle Approval

Unknown vehicles are not automatically granted access.

```text
Unknown Vehicle
       |
       v
Access Denied
       |
       v
Pending Approval Created
       |
       v
Guard / Admin Reviews
       |
   +---+---+
   |       |
Approve  Reject
   |       |
   v       v
Gate     Gate
Access   Closed
```

The approval/rejection decision is recorded so that the event remains traceable.

---

## 9. Database

IntelliGate uses **PostgreSQL** as its relational database and **SQLAlchemy** as the ORM.

Main data entities include:

- Users
- Vehicles
- Student IDs
- Administrators
- Access Logs
- Pending Approvals
- Notifications
- Device Tokens

Access logs are particularly important because they maintain historical entry/exit information and support occupancy/state tracking.

---

## 10. Backend API

The backend is developed using **Flask** and provides REST APIs for:

- Authentication
- User management
- Vehicle management
- Student verification
- Vehicle verification
- Access logs
- Pending approvals
- Approval/rejection
- Gate control
- Occupancy-related information
- Device registration
- Notifications

The backend acts as the central decision-making component of IntelliGate.

---

## 11. Authentication & Security

IntelliGate includes several backend security mechanisms.

### JWT Authentication

After successful login, the backend issues a JSON Web Token (JWT). Protected API requests require a valid token.

### Role-Based Access Control

The system supports roles such as:

- Admin
- Guard

Permissions can be restricted according to the authenticated user's role.

### Password Security

Passwords are stored using secure password hashing rather than plain text.

### Login Protection

The system detects repeated incorrect password attempts.

After **three consecutive incorrect password attempts**, login is temporarily locked for **60 seconds**.

> Note: The current prototype stores login-attempt state in backend memory. Restarting the backend clears this temporary state. A production deployment could persist lockout information using PostgreSQL or Redis.

---

## 12. Real-Time Monitoring

IntelliGate uses **Socket.IO** for real-time communication between the backend and the mobile application.

This allows important events, such as access events and unauthorized vehicle activity, to be communicated to the application without requiring continuous manual refresh.

REST APIs are used primarily for request-response operations, while Socket.IO supports real-time event delivery.

---

## 13. Physical Gate Control

A major feature of IntelliGate is the integration between software decisions and physical gate operation.

```text
Recognition
     |
     v
Flask Backend
     |
     v
Access Decision
     |
     v
Gate Command
     |
     v
Arduino Nano
     |
     v
Servo Motor
     |
     v
Physical Gate
```

When valid access is granted, the gate-control mechanism can activate the servo motor to open the physical prototype gate.

---

## 14. Testing & Results

The integrated system was tested using major end-to-end workflows.

| Test | Result |
|---|---|
| Authorized vehicle entry | PASS |
| Vehicle number plate identification | PASS |
| Student barcode identification | PASS |
| Student entry logging | PASS |
| Student occupancy tracking | PASS |
| Physical gate opening | PASS |
| Unknown vehicle detection | PASS |
| Pending approval creation | PASS |
| Approve / Reject workflow | PASS |

The final integration testing demonstrated communication between recognition, backend verification, database operations, mobile monitoring, and physical gate control.

---

## 15. Engineering Challenges

During development, several engineering challenges were addressed:

### OCR Under Varying Conditions

Number plate recognition can be affected by:

- Lighting
- Camera angle
- Distance
- Image quality
- Glare

### Multiple Camera Integration

Different camera sources were integrated for entry and exit monitoring.

### Entry / Exit State Management

The system must not only recognize an identifier but also determine whether the requested entry or exit action is valid.

### Hardware–Software Integration

Backend access decisions must be correctly translated into physical gate actions through the hardware control system.

### Real-Time Synchronization

Access events, database state, occupancy information, pending approvals, and the mobile application need to remain synchronized.

---

## 16. Current Prototype Limitations

The current IntelliGate implementation is a university project prototype.

Some current limitations include:

- OCR accuracy depends on camera and lighting conditions.
- Night-time operation requires adequate gate-area illumination.
- The prototype operates over HTTP on the local network.
- Temporary login lockout state is stored in backend memory.
- Production deployment would require additional infrastructure and security hardening.

---

## 17. Future Improvements

Possible future improvements include:

- HTTPS/TLS communication
- Improved low-light/night-time number plate recognition
- More robust ANPR models
- Persistent login-attempt and account-lockout storage
- Enhanced security-event auditing
- Improved camera hardware
- Larger-scale deployment testing
- Cloud-based monitoring and backup
- Additional analytics and reporting
- More advanced occupancy monitoring

---

## 18. Project Structure

A simplified project structure is:

```text
IntelliGate/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   └── database/
│   └── run.py
│
├── numberplate/
│   ├── main.py
│   ├── ocr.py
│   └── camera / recognition modules
│
├── frontend/
│   ├── app/
│   ├── src/
│   └── components/
│
├── hardware/
│   └── Arduino / gate-control components
│
└── README.md
```

> The exact directory structure may vary depending on the deployment environment.

---

## 19. System Requirements

Typical prototype requirements include:

### Raspberry Pi

- Python 3
- OpenCV
- Flask backend dependencies
- Camera support
- Network connection

### Backend

- Python 3
- PostgreSQL
- Required Python packages from the project environment

### Mobile Application

- Node.js
- npm
- Expo / React Native environment

### Hardware

- Arduino Nano
- Servo motor
- USB camera
- Raspberry Pi camera

---

## 20. Running the System

The complete IntelliGate prototype consists of multiple components that should be started according to the deployment environment:

1. PostgreSQL database
2. Flask backend
3. Vehicle recognition/camera service
4. Student barcode scanning component
5. Arduino/servo gate-control component
6. React Native mobile application

Network addresses must match the current local-network configuration.

> Do not hard-code an example Raspberry Pi IP from this README into a new environment. Verify the Raspberry Pi's current local IP address before starting the client applications.

---

## 21. Conclusion

IntelliGate demonstrates an integrated approach to smart university gate management by combining:

- Automated vehicle number plate recognition
- Student barcode identification
- Backend access verification
- Entry/exit state management
- Occupancy tracking
- Unauthorized vehicle approval
- Real-time monitoring
- Access logging
- Mobile application management
- Physical gate automation

The project integrates **computer vision, backend development, relational database management, real-time communication, mobile application development, embedded hardware, and physical gate control** into a single working prototype.

---

## IntelliGate

**Smart University Gate Automation System**

Developed as an engineering project demonstrating the integration of software, database, computer vision, networking, mobile application development, and hardware automation.
