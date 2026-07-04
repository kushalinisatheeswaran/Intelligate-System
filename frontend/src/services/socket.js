import { io } from "socket.io-client";
import { SOCKET_URL } from "../constants/config";

export const connectSocket = () => {
  if (global.socketInstance) return global.socketInstance;

  global.socketInstance = io(SOCKET_URL, {
    transports           : ["websocket"],
    reconnection         : true,
    reconnectionDelay    : 2000,
    reconnectionAttempts : 10,
    forceNew             : false,
  });

  global.socketInstance.on("connect", () => {
    console.log("[SOCKET] Connected:", global.socketInstance.id);
    // Join guards room — Flask targets this room for security events
    global.socketInstance.emit("join_room", { room: "guards" });
  });

  global.socketInstance.on("connect_error", (err) => {
    console.warn("[SOCKET] Connection error:", err.message);
  });

  global.socketInstance.on("disconnect", (reason) => {
    console.log("[SOCKET] Disconnected:", reason);
  });

  return global.socketInstance;
};

export const getSocket = () => {
  if (!global.socketInstance) {
    return connectSocket();
  }
  return global.socketInstance;
};

export const disconnectSocket = () => {
  if (global.socketInstance) {
    global.socketInstance.disconnect();
    global.socketInstance = null;
  }
};