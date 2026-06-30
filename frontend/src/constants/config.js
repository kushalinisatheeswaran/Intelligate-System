// ─── Update FLASK_HOST to your machine's local IP address ───
// Find it with: ipconfig (Windows) or ifconfig (Mac/Linux)
// Your phone and laptop must be on the same WiFi network

export const FLASK_HOST = "10.184.145.175";      // ← change this
export const FLASK_PORT = "5000";
export const API_BASE_URL = `http://${FLASK_HOST}:${FLASK_PORT}/api`;
export const SOCKET_URL = `http://${FLASK_HOST}:${FLASK_PORT}`;

// Must match exactly what Flask emits in Phase 5
export const SOCKET_EVENTS = {
  VEHICLE_DETECTED: "vehicle_detected",
  UNKNOWN_VEHICLE: "unknown_vehicle",
  ACCESS_GRANTED: "access_granted",
  ACCESS_DENIED: "access_denied",
  GATE_STATUS: "gate_status",
  APPROVAL_UPDATE: "approval_update",
};

export const ROLES = {
  ADMIN: "admin",
  GUARD: "guard",
};