import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  ActivityIndicator,
  StatusBar,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import api from "../../../src/services/api";

export default function RegisterVehicleScreen() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [plateNumber, setPlateNumber] = useState("");
  const [vehicleType, setVehicleType] = useState("car"); // car | bike
  const [role, setRole] = useState("student"); // student | staff
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name.trim() || !plateNumber.trim()) {
      Alert.alert("Required Fields", "Name and License Plate Number are required.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/users/register", {
        name: name.trim(),
        email: email.trim() || null,
        type: "plate",
        identifier: plateNumber.trim().toUpperCase(),
        role: role,
        vehicle_type: vehicleType.toLowerCase(),
      });

      Alert.alert(
        "Registration Successful",
        `${name} has been pre-authorized with Plate Number ${plateNumber}.`,
        [
          {
            text: "OK",
            onPress: () => {
              router.back();
            },
          },
        ]
      );
    } catch (err) {
      Alert.alert(
        "Registration Failed",
        err.response?.data?.error || "An error occurred during registration."
      );
    } finally {
      setLoading(false);
    }
  };

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
        <Text style={styles.headerTitle}>Register Vehicle User</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.sectionTitle}>User & Vehicle Details</Text>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Owner Full Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. Jane Smith"
            placeholderTextColor="#9CA3AF"
            value={name}
            onChangeText={setName}
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Email Address</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. jane.smith@university.edu"
            placeholderTextColor="#9CA3AF"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>License Plate Number *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. WP-ABC-1234"
            placeholderTextColor="#9CA3AF"
            value={plateNumber}
            onChangeText={setPlateNumber}
            autoCapitalize="characters"
          />
        </View>

        {/* Role Selector */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Owner Role</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                role === "student" ? styles.toggleActive : null,
              ]}
              onPress={() => setRole("student")}
            >
              <Text
                style={[
                  styles.toggleText,
                  role === "student" ? styles.toggleTextActive : null,
                ]}
              >
                Student
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                role === "staff" ? styles.toggleActive : null,
              ]}
              onPress={() => setRole("staff")}
            >
              <Text
                style={[
                  styles.toggleText,
                  role === "staff" ? styles.toggleTextActive : null,
                ]}
              >
                Staff
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Vehicle Type Selector */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Vehicle Type</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                vehicleType === "car" ? styles.toggleActive : null,
              ]}
              onPress={() => setVehicleType("car")}
            >
              <Text
                style={[
                  styles.toggleText,
                  vehicleType === "car" ? styles.toggleTextActive : null,
                ]}
              >
                🚗 Car
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                vehicleType === "bike" ? styles.toggleActive : null,
              ]}
              onPress={() => setVehicleType("bike")}
            >
              <Text
                style={[
                  styles.toggleText,
                  vehicleType === "bike" ? styles.toggleTextActive : null,
                ]}
              >
                🏍️ Bike / Cycle
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity
          style={styles.submitButton}
          onPress={handleRegister}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.submitButtonText}>Authorize Vehicle User</Text>
          )}
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
    padding: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#6B7280",
    textTransform: "uppercase",
    marginBottom: 20,
  },
  formGroup: {
    marginBottom: 18,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: "#374151",
    marginBottom: 6,
  },
  input: {
    backgroundColor: "#fff",
    height: 48,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    paddingHorizontal: 12,
    fontSize: 14,
    color: "#1F2937",
  },
  toggleContainer: {
    flexDirection: "row",
    backgroundColor: "#E5E7EB",
    borderRadius: 8,
    padding: 3,
  },
  toggleButton: {
    flex: 1,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 6,
  },
  toggleActive: {
    backgroundColor: "#fff",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  toggleText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#4B5563",
  },
  toggleTextActive: {
    fontWeight: "700",
    color: "#1D4ED8",
  },
  submitButton: {
    backgroundColor: "#1D4ED8",
    height: 48,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  submitButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
  },
});
