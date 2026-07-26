import React, { useState, useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  StatusBar,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useAuth } from "../../src/context/AuthContext";

export default function SettingsScreen() {
  const { user, logout } = useAuth();
  const router = useRouter();

  // Snackbar State
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarType, setSnackbarType] = useState("success"); // success | error
  const fadeAnim = useMemo(() => new Animated.Value(0), []);

  const showSnackbar = (message, type = "success") => {
    setSnackbarMessage(message);
    setSnackbarType(type);
    Animated.sequence([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.delay(2500),
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const handleLogout = async () => {
    try {
      showSnackbar("Logging out...", "success");
      setTimeout(async () => {
        await logout();
        router.replace("/(auth)/login");
      }, 800);
    } catch (err) {
      showSnackbar("Failed to log out.", "error");
    }
  };

  const getRoleBadgeStyle = (role) => {
    if (role === "admin") {
      return { bg: "#FEE2E2", text: "#991B1B", border: "#FCA5A5" };
    }
    return { bg: "#FEF3C7", text: "#92400E", border: "#FCD34D" };
  };

  const badge = getRoleBadgeStyle(user?.role);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1D4ED8" />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Text style={styles.backText}>⬅️</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Settings</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Profile Card */}
      <View style={styles.profileCard}>
        <View style={styles.avatarContainer}>
          <Text style={styles.avatarText}>👤</Text>
        </View>
        <Text style={styles.userName}>{user?.name || "User Name"}</Text>
        <Text style={styles.userEmail}>{user?.email || "email@intelligate.com"}</Text>

        <View
          style={[
            styles.badge,
            {
              backgroundColor: badge.bg,
              borderColor: badge.border,
            },
          ]}
        >
          <Text style={[styles.badgeText, { color: badge.text }]}>
            {user?.role?.toUpperCase() || "GUARD"}
          </Text>
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionsContainer}>
        {user?.role === "admin" && (
          <TouchableOpacity
            style={styles.actionRow}
            onPress={() => router.push("/admin")}
            activeOpacity={0.7}
          >
            <View style={styles.actionLeft}>
              <Text style={styles.actionIcon}>🛡️</Text>
              <Text style={styles.actionText}>Admin Control Panel</Text>
            </View>
            <Text style={styles.arrowIcon}>➡️</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity
          style={[styles.actionRow, styles.logoutRow]}
          onPress={handleLogout}
          activeOpacity={0.7}
        >
          <View style={styles.actionLeft}>
            <Text style={styles.actionIcon}>🚪</Text>
            <Text style={[styles.actionText, styles.logoutText]}>Log Out</Text>
          </View>
          <Text style={styles.arrowIcon}>➡️</Text>
        </TouchableOpacity>
      </View>

      {/* Animated Snackbar */}
      {snackbarMessage ? (
        <Animated.View
          style={[
            styles.snackbar,
            {
              opacity: fadeAnim,
              backgroundColor: snackbarType === "success" ? "#10B981" : "#EF4444",
            },
          ]}
        >
          <Text style={styles.snackbarText}>{snackbarMessage}</Text>
        </Animated.View>
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F3F4F6",
  },
  header: {
    backgroundColor: "#1D4ED8",
    height: 60,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 15,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: "center",
    alignItems: "center",
  },
  backText: {
    fontSize: 20,
    color: "#fff",
  },
  headerTitle: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "700",
  },
  profileCard: {
    backgroundColor: "#fff",
    margin: 20,
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3,
  },
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#EFF6FF",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#DBEAFE",
  },
  avatarText: {
    fontSize: 38,
  },
  userName: {
    fontSize: 22,
    fontWeight: "800",
    color: "#1F2937",
    marginBottom: 6,
  },
  userEmail: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 16,
    fontWeight: "500",
  },
  badge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: "800",
  },
  actionsContainer: {
    backgroundColor: "#fff",
    marginHorizontal: 20,
    borderRadius: 16,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3,
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  actionLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  actionIcon: {
    fontSize: 20,
    marginRight: 16,
  },
  actionText: {
    fontSize: 16,
    color: "#374151",
    fontWeight: "600",
  },
  arrowIcon: {
    fontSize: 14,
    color: "#9CA3AF",
  },
  logoutRow: {
    borderBottomWidth: 0,
  },
  logoutText: {
    color: "#EF4444",
  },
  snackbar: {
    position: "absolute",
    bottom: 40,
    left: 20,
    right: 20,
    padding: 16,
    borderRadius: 12,
    flexDirection: "row",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 5,
    elevation: 4,
  },
  snackbarText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "700",
  },
});
