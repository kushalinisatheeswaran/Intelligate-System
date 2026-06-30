import { io } from "socket.io-client";
import { SOCKET_URL } from "../constants/config";

let socket = null;

export const connectSocket = () => {
  if (socket) return socket;

  socket = io(SOCKET_URL, {
    transports           : ["websocket"],
    reconnection         : true,
    reconnectionDelay    : 2000,
    reconnectionAttempts : 10,
    forceNew             : false,
  });

  socket.on("connect", () => {
    console.log("[SOCKET] Connected:", socket.id);
    // Join guards room — Flask targets this room for security events
    socket.emit("join_room", { room: "guards" });
  });

  socket.on("connect_error", (err) => {
    console.warn("[SOCKET] Connection error:", err.message);
  });

  socket.on("disconnect", (reason) => {
    console.log("[SOCKET] Disconnected:", reason);
  });

  return socket;
};

export const getSocket = () => {
  if (!socket) {
    return connectSocket();
  }
  return socket;
};

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};