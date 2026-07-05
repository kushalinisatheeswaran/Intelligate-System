import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  StatusBar,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter, useLocalSearchParams } from "expo-router";
import api from "../../../../src/services/api";

export default function StudentDetailsScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  const fetchDetails = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await api.get(`/users/${id}`);
      setStudent(response.data);
    } catch (err) {
      Alert.alert("Error", err.response?.data?.error || "Failed to load details");
      router.back();
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  useEffect(() => {
    fetchDetails();
  }, [fetchDetails]);

  const handleDelete = () => {
    Alert.alert(
      "Deactivate Student",
      `Are you sure you want to deactivate ${student?.name}? All their registered vehicles and student IDs will be revoked.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Confirm Deactivation",
          style: "destructive",
          onPress: async () => {
            setDeleting(true);
            try {
              await api.delete(`/users/${id}`);
              Alert.alert("Success", "Student deactivated successfully.", [
                {
                  text: "OK",
                  onPress: () => {
                    router.back();
                  },
                },
              ]);
            } catch (err) {
              Alert.alert(
                "Error",
                err.response?.data?.error || "Failed to deactivate student."
              );
            } finally {
              setDeleting(false);
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1D4ED8" />
      </SafeAreaView>
    );
  }

  const barcodeRec = student?.student_ids?.[0];
  const vehiclesList = student?.vehicles || [];

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
        <Text style={styles.headerTitle}>Student Details</Text>
        <TouchableOpacity
          onPress={() => router.push(`/admin/students/edit/${id}`)}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Text style={styles.backText}>✏️</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Profile Card */}
        <View style={styles.card}>
          <Text style={styles.cardHeader}>Personal Info</Text>
          <View style={styles.detailRow}>
            <Text style={styles.label}>Name</Text>
            <Text style={styles.value}>{student?.name}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.label}>Email</Text>
            <Text style={styles.value}>{student?.email || "N/A"}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.label}>Status</Text>
            <View
              style={[
                styles.statusPill,
                { backgroundColor: student?.is_active ? "#D1FAE5" : "#FEE2E2" },
              ]}
            >
              <Text
                style={[
                  styles.statusText,
                  { color: student?.is_active ? "#065F46" : "#991B1B" },
                ]}
              >
                {student?.is_active ? "ACTIVE" : "DEACTIVATED"}
              </Text>
            </View>
          </View>
        </View>

        {/* Student ID Card */}
        <View style={styles.card}>
          <Text style={styles.cardHeader}>Student ID Details</Text>
          <View style={styles.detailRow}>
            <Text style={styles.label}>Student Number</Text>
            <Text style={styles.value}>{barcodeRec?.student_number || "N/A"}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.label}>Faculty</Text>
            <Text style={styles.value}>{barcodeRec?.faculty || "N/A"}</Text>
          </View>
        </View>

        {/* Registered Vehicles */}
        <View style={styles.card}>
          <View style={styles.vehiclesHeaderRow}>
            <Text style={styles.cardHeader}>Registered Vehicles</Text>
            <TouchableOpacity
              style={styles.addVehicleBtn}
              onPress={() =>
                router.push({
                  pathname: "/admin/vehicles/add",
                  params: { userId: id },
                })
              }
              activeOpacity={0.7}
            >
              <Text style={styles.addVehicleText}>+ Add</Text>
            </TouchableOpacity>
          </View>

          {vehiclesList.length === 0 ? (
            <Text style={styles.emptyVehicles}>No vehicles registered.</Text>
          ) : (
            vehiclesList.map((v) => (
              <View key={v.id.toString()} style={styles.vehicleRow}>
                <View>
                  <Text style={styles.plateText}>{v.plate_number}</Text>
                  <Text style={styles.typeText}>{v.vehicle_type?.toUpperCase()}</Text>
                </View>
                <TouchableOpacity
                  style={styles.editVehicleBtn}
                  onPress={() =>
                    router.push({
                      pathname: `/admin/vehicles/edit/${v.id}`,
                      params: {
                        plate: v.plate_number,
                        type: v.vehicle_type,
                        isActive: v.is_active,
                      },
                    })
                  }
                  activeOpacity={0.7}
                >
                  <Text style={styles.editVehicleText}>Manage</Text>
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>

        {/* Deactivate/Delete Button */}
        {student?.is_active && (
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={handleDelete}
            disabled={deleting}
            activeOpacity={0.8}
          >
            {deleting ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.deleteButtonText}>Deactivate Student Access</Text>
            )}
          </TouchableOpacity>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F3F4F6",
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
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
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 15,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeader: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1D4ED8",
    marginBottom: 12,
    textTransform: "uppercase",
  },
  detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  label: {
    fontSize: 14,
    color: "#6B7280",
    fontWeight: "500",
  },
  value: {
    fontSize: 14,
    color: "#1F2937",
    fontWeight: "700",
  },
  statusPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 11,
    fontWeight: "700",
  },
  vehiclesHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  addVehicleBtn: {
    backgroundColor: "#1D4ED8",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  addVehicleText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
  },
  emptyVehicles: {
    color: "#9CA3AF",
    fontSize: 13,
    textAlign: "center",
    paddingVertical: 10,
  },
  vehicleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  plateText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1F2937",
  },
  typeText: {
    fontSize: 11,
    color: "#6B7280",
    marginTop: 2,
  },
  editVehicleBtn: {
    backgroundColor: "#F3F4F6",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  editVehicleText: {
    color: "#374151",
    fontSize: 12,
    fontWeight: "700",
  },
  deleteButton: {
    backgroundColor: "#DC2626",
    height: 48,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 10,
    marginBottom: 30,
  },
  deleteButtonText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "700",
  },
});
