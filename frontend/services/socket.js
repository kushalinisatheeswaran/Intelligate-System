import { io } from "socket.io-client";

const SOCKET_URL = "http://192.168.1.X:5000";

let socket = null;

export const connectSocket = () => {
  if (socket?.connected) return socket;

  socket = io(SOCKET_URL, {
    transports:         ["websocket"],
    reconnection:       true,
    reconnectionDelay:  2000,
    reconnectionAttempts: 10,
  });

  socket.on("connect", () => {
    console.log("[SOCKET] Connected to IntelliGate");
    // Join guard room to receive targeted events
    socket.emit("join_room", { room: "guards" });
  });

  socket.on("disconnect", () => {
    console.log("[SOCKET] Disconnected");
  });

  return socket;
};

export const getSocket = () => socket;
export const disconnectSocket = () => socket?.disconnect();