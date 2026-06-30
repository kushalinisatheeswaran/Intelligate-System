import React from "react";
import { Tabs } from "expo-router";
import { Text, Platform } from "react-native";

function TabIcon({ icon }) {
  return <Text style={{ fontSize: 20 }}>{icon}</Text>;
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor   : "#1D4ED8",
        tabBarInactiveTintColor : "#9CA3AF",
        tabBarStyle             : {
          backgroundColor  : "#fff",
          borderTopColor   : "#E5E7EB",
          borderTopWidth   : 0.5,
          paddingBottom    : Platform.OS === "ios" ? 20 : 6,
          paddingTop       : 6,
          height           : Platform.OS === "ios" ? 80 : 60,
        },
        tabBarLabelStyle  : { fontSize: 11, fontWeight: "600" },
        headerStyle       : { backgroundColor: "#1D4ED8" },
        headerTintColor   : "#fff",
        headerTitleStyle  : { fontWeight: "700", fontSize: 17 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title       : "Live Feed",
          headerTitle : "IntelliGate — Live Feed",
          tabBarIcon  : () => <TabIcon icon="📡" />,
        }}
      />
      <Tabs.Screen
        name="pending"
        options={{
          title       : "Pending",
          headerTitle : "Pending Approvals",
          tabBarIcon  : () => <TabIcon icon="⏳" />,
        }}
      />
      <Tabs.Screen
        name="gate-status"
        options={{
          title       : "Gate",
          headerTitle : "Gate Status",
          tabBarIcon  : () => <TabIcon icon="🚪" />,
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title       : "Alerts",
          headerTitle : "Notification History",
          tabBarIcon  : () => <TabIcon icon="🔔" />,
        }}
      />
    </Tabs>
  );
}