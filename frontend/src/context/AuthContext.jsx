import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import * as SecureStore from "expo-secure-store";
import api, { registerUnauthorizedCallback, setAuthToken } from "../services/api";
import { connectSocket, disconnectSocket } from "../services/socket";
import {
  registerForPushNotifications,
  unregisterPushNotifications,
} from "../services/fcm";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null);
  const [loading, setLoading] = useState(true);

  const handleUnauthorized = useCallback(async () => {
    try {
      await SecureStore.deleteItemAsync("jwt_token");
    } catch {
      // SecureStore issue
    }
    disconnectSocket();
    setUser(null);
  }, []);

  useEffect(() => {
    registerUnauthorizedCallback(handleUnauthorized);
  }, [handleUnauthorized]);

  // On app start — restore session if token exists and is valid
  useEffect(() => {
    (async () => {
      try {
        const token = await SecureStore.getItemAsync("jwt_token");
        if (token) {
          setAuthToken(token);
          const res = await api.get("/auth/me");
          setUser(res.data);
          connectSocket();
        }
      } catch {
        // Token expired or invalid — clear it
        try {
          await SecureStore.deleteItemAsync("jwt_token");
        } catch {
          // SecureStore issue
        }
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await api.post("/auth/login", {
      email    : email.trim().toLowerCase(),
      password,
    });

    const { access_token, user: userData } = res.data;

    // Persist JWT securely on device
    await SecureStore.setItemAsync("jwt_token", access_token);
    setAuthToken(access_token);
    setUser(userData);

    // Start Socket.IO connection
    connectSocket();

    // Register this device for FCM push notifications
    await registerForPushNotifications();

    return userData;
  }, []);

  const logout = useCallback(async () => {
    try {
      await unregisterPushNotifications();
      await api.post("/auth/logout");
    } catch {
      // Ignore errors on logout — proceed regardless
    } finally {
      await SecureStore.deleteItemAsync("jwt_token");
      setAuthToken(null);
      disconnectSocket();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
};