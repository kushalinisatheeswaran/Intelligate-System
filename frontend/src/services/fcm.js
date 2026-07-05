import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { Platform } from "react-native";
import api from "./api";

// How notifications behave when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert : true,
    shouldPlaySound : true,
    shouldSetBadge  : true,
  }),
});

export async function registerForPushNotifications() {
  if (!Device.isDevice) {
    console.log("[FCM] Push notifications require a physical device");
    return null;
  }

  // Request permission
  const { status: existingStatus } =
    await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    console.warn("[FCM] Notification permission not granted");
    return null;
  }

  // Android requires a notification channel
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("intelligate_alerts", {
      name             : "IntelliGate Alerts",
      importance       : Notifications.AndroidImportance.MAX,
      vibrationPattern : [0, 250, 250, 250],
      lightColor       : "#FF0000",
      sound            : "default",
    });
  }

  // Get Expo push token (works with FCM on Android)
  const tokenData = await Notifications.getExpoPushTokenAsync();
  const fcmToken  = tokenData.data;
  console.log("[FCM] Token obtained:", fcmToken.substring(0, 30) + "...");

  // Register with Flask backend — POST /api/devices/register
  try {
    await api.post("/devices/register", {
      fcm_token   : fcmToken,
      device_type : Platform.OS,
    });
    console.log("[FCM] Token registered with backend");
  } catch (err) {
    console.warn("[FCM] Token registration failed:", err.message);
  }

  return fcmToken;
}

export function setupNotificationListeners(navigationRef) {
  // Notification received while app is in foreground
  const foregroundSub = Notifications.addNotificationReceivedListener(
    (notification) => {
      // Socket.IO handles live UI updates — no extra action needed here
      console.log("[FCM] Foreground notification received");
    }
  );

  // Notification tapped — navigate to the correct screen
  const tapSub = Notifications.addNotificationResponseReceivedListener(
    (response) => {
      const data   = response.notification.request.content.data;
      const screen = data?.screen;
      if (screen && navigationRef?.current) {
        // Map Flask FCM data.screen values to Expo Router paths
        const routeMap = {
          PendingApprovals : "/(app)/(tabs)/pending",
          GateStatus       : "/(app)/(tabs)/gate-status",
        };
        const route = routeMap[screen];
        if (route) {
          navigationRef.current.navigate(route);
        }
      }
    }
  );

  // Return cleanup function to call on unmount
  return () => {
    foregroundSub.remove();
    tapSub.remove();
  };
}

export async function unregisterPushNotifications() {
  try {
    const tokenData = await Notifications.getExpoPushTokenAsync();
    await api.post("/devices/unregister", { fcm_token: tokenData.data });
    console.log("[FCM] Token unregistered from backend");
  } catch (err) {
    console.warn("[FCM] Unregister failed:", err.message);
  }
}