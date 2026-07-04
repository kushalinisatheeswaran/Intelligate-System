import axios from "axios";
import * as SecureStore from "expo-secure-store";
import { API_BASE_URL } from "../constants/config";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * 🔥 IMPORTANT:
 * This ensures token is applied instantly after login
 * (prevents FEED / logs 401 race condition)
 */
export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
};

// Attach JWT automatically for every request
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await SecureStore.getItemAsync("jwt_token");

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (err) {
      console.log("SecureStore error:", err);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Handle global 401 (token expired / invalid)
 */
let onUnauthorized = null;

export const registerUnauthorizedCallback = (cb) => {
  onUnauthorized = cb;
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status;

    if (status === 401) {
      try {
        await SecureStore.deleteItemAsync("jwt_token");
      } catch (err) {
        console.log("SecureStore delete error:", err);
      }

      // clear axios header immediately
      setAuthToken(null);

      if (onUnauthorized) {
        onUnauthorized();
      }
    }

    return Promise.reject(error);
  }
);

export default api;