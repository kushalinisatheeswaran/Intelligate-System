import React, { useRef, useEffect } from "react";
import { Slot, useNavigationContainerRef, useRouter, useSegments } from "expo-router";
import { View, ActivityIndicator } from "react-native";
import { AuthProvider, useAuth } from "../src/context/AuthContext";
import { setupNotificationListeners } from "../src/services/fcm";

function InitialLayout() {
  const { user, loading } = useAuth();
  const router            = useRouter();
  const segments          = useSegments();

  useEffect(() => {
    if (loading) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!user && !inAuthGroup) {
      // Not logged in — redirect to login
      router.replace("/(auth)/login");
    } else if (user && inAuthGroup) {
      // Already logged in — redirect to main tabs
      router.replace("/(app)/(tabs)/");
    }
  }, [user, loading, segments]);

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center",
                     backgroundColor: "#F3F4F6" }}>
        <ActivityIndicator size="large" color="#1D4ED8" />
      </View>
    );
  }

  const inAuthGroup = segments[0] === "(auth)";
  if (!user && !inAuthGroup) {
    return null;
  }

  return <Slot />;
}

export default function RootLayout() {
  const navigationRef = useNavigationContainerRef();

  useEffect(() => {
    // Wire FCM notification tap → navigate to correct screen
    const cleanup = setupNotificationListeners(navigationRef);
    return cleanup;
  }, []);

  return (
    <AuthProvider>
      <InitialLayout />
    </AuthProvider>
  );
}