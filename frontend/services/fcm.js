import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import api from "./api";

export async function registerForPushNotifications() {
  if (!Device.isDevice) {
    console.log("[FCM] Must use physical device for notifications");
    return null;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    console.log("[FCM] Notification permission denied");
    return null;
  }

  // Get Expo push token (works with FCM on Android)
  const token = (await Notifications.getExpoPushTokenAsync()).data;
  console.log("[FCM] Push token:", token);

  // Register token with Flask backend
  try {
    await api.post("/devices/register", {
      fcm_token:   token,
      device_type: Platform.OS  // "android" | "ios"
    });
    console.log("[FCM] Token registered with backend");
  } catch (err) {
    console.error("[FCM] Token registration failed:", err.message);
  }

  return token;
}

// Handle notification tap — navigate to correct screen
export function setupNotificationHandler(navigationRef) {
  Notifications.addNotificationResponseReceivedListener((response) => {
    const data   = response.notification.request.content.data;
    const screen = data?.screen;

    if (screen && navigationRef.current) {
      navigationRef.current.navigate(screen);
    }
  });
}