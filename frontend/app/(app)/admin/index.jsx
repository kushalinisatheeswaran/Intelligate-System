import React from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  StatusBar,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";

export default function AdminDashboard() {
  const router = useRouter();

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
        <Text style={styles.headerTitle}>Admin Control Panel</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.sectionTitle}>Supported Admin Modules</Text>

        {/* Students List */}
        <TouchableOpacity
          style={styles.menuCard}
          onPress={() => router.push("/admin/students")}
          activeOpacity={0.7}
        >
          <View style={styles.menuLeft}>
            <Text style={styles.menuIcon}>👥</Text>
            <View>
              <Text style={styles.menuTitle}>Student Directory</Text>
              <Text style={styles.menuDesc}>View students and manage gate access</Text>
            </View>
          </View>
          <Text style={styles.arrowIcon}>➡️</Text>
        </TouchableOpacity>

        {/* Vehicle Directory */}
        <TouchableOpacity
          style={styles.menuCard}
          onPress={() => router.push("/admin/vehicles")}
          activeOpacity={0.7}
        >
          <View style={styles.menuLeft}>
            <Text style={styles.menuIcon}>🚘</Text>
            <View>
              <Text style={styles.menuTitle}>Vehicle Directory</Text>
              <Text style={styles.menuDesc}>View and manage all registered vehicles</Text>
            </View>
          </View>
          <Text style={styles.arrowIcon}>➡️</Text>
        </TouchableOpacity>

        {/* Guard Directory */}
        <TouchableOpacity
          style={styles.menuCard}
          onPress={() => router.push("/admin/guards")}
          activeOpacity={0.7}
        >
          <View style={styles.menuLeft}>
            <Text style={styles.menuIcon}>👮</Text>
            <View>
              <Text style={styles.menuTitle}>Guard Directory</Text>
              <Text style={styles.menuDesc}>View, authorize and manage guards</Text>
            </View>
          </View>
          <Text style={styles.arrowIcon}>➡️</Text>
        </TouchableOpacity>

        <Text style={[styles.sectionTitle, { marginTop: 15 }]}>Quick Authorizations</Text>

        {/* Add Student */}
        <TouchableOpacity
          style={styles.menuCard}
          onPress={() => router.push("/admin/add-student")}
          activeOpacity={0.7}
        >
          <View style={styles.menuLeft}>
            <Text style={styles.menuIcon}>➕</Text>
            <View>
              <Text style={styles.menuTitle}>Add Student</Text>
              <Text style={styles.menuDesc}>Pre-authorize new student with ID</Text>
            </View>
          </View>
          <Text style={styles.arrowIcon}>➡️</Text>
        </TouchableOpacity>

        {/* Register Vehicle User */}
        <TouchableOpacity
          style={styles.menuCard}
          onPress={() => router.push("/admin/register-vehicle")}
          activeOpacity={0.7}
        >
          <View style={styles.menuLeft}>
            <Text style={styles.menuIcon}>🚗</Text>
            <View>
              <Text style={styles.menuTitle}>Register Vehicle User</Text>
              <Text style={styles.menuDesc}>Pre-authorize new user with license plate</Text>
            </View>
          </View>
          <Text style={styles.arrowIcon}>➡️</Text>
        </TouchableOpacity>
      </ScrollView>
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
  content: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: "#6B7280",
    textTransform: "uppercase",
    marginBottom: 10,
    marginLeft: 5,
  },
  menuCard: {
    backgroundColor: "#fff",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 2,
  },
  menuLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  menuIcon: {
    fontSize: 24,
    marginRight: 15,
  },
  menuTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 2,
  },
  menuDesc: {
    fontSize: 12,
    color: "#6B7280",
  },
  arrowIcon: {
    fontSize: 14,
    color: "#9CA3AF",
  },
});
