import axios from "axios";
import * as SecureStore from "expo-secure-store";

// Update this to your machine's local IP when testing on device
const BASE_URL = "http://192.168.1.X:5000/api";

const api = axios.create({ baseURL: BASE_URL });

// Attach JWT to every request automatically
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync("jwt_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;