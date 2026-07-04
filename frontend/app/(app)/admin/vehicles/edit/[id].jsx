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
import { useRouter, useLocalSearchParams } from "expo-router";
import api from "../../../../../src/services/api";

export default function EditVehicleScreen() {
  const router = useRouter();
  const { id, plate, type, isActive } = useLocalSearchParams();
  const [plateNumber, setPlateNumber] = useState(plate || "");
  const [vehicleType, setVehicleType] = useState(type || "car");
  const [isVehicleActive, setIsVehicleActive] = useState(
    isActive === "true" || isActive === true
  );
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!plateNumber.trim()) {
      Alert.alert("Required Fields", "License Plate Number is required.");
      return;
    }

    setSaving(true);
    try {
      await api.put(`/vehicles/${id}`, {
        plate_number: plateNumber.trim().toUpperCase(),
        vehicle_type: vehicleType.toLowerCase(),
        is_active: isVehicleActive,
      });

      Alert.alert("Success", "Vehicle updated successfully.", [
        {
          text: "OK",
          onPress: () => {
            router.back();
          },
        },
      ]);
    } catch (err) {
      Alert.alert("Error", err.response?.data?.error || "Failed to update vehicle.");
    } finally {
      setSaving(false);
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
        <Text style={styles.headerTitle}>Edit Vehicle</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.sectionTitle}>Modify Vehicle</Text>

        <View style={styles.formGroup}>
          <Text style={styles.label}>License Plate Number *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. ABC-1234"
            placeholderTextColor="#9CA3AF"
            value={plateNumber}
            onChangeText={setPlateNumber}
            autoCapitalize="characters"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Vehicle Type</Text>
          <View style={styles.toggleContainer}>
            {["car", "bike", "van"].map((t) => (
              <TouchableOpacity
                key={t}
                style={[
                  styles.toggleButton,
                  vehicleType === t ? styles.toggleActive : null,
                ]}
                onPress={() => setVehicleType(t)}
              >
                <Text
                  style={[
                    styles.toggleText,
                    vehicleType === t ? styles.toggleTextActive : null,
                  ]}
                >
                  {t.toUpperCase()}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Active Status</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                isVehicleActive ? styles.toggleActive : null,
              ]}
              onPress={() => setIsVehicleActive(true)}
            >
              <Text
                style={[
                  styles.toggleText,
                  isVehicleActive ? styles.toggleTextActive : null,
                ]}
              >
                ACTIVE
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                !isVehicleActive ? styles.toggleActive : null,
              ]}
              onPress={() => setIsVehicleActive(false)}
            >
              <Text
                style={[
                  styles.toggleText,
                  !isVehicleActive ? styles.toggleTextActive : null,
                ]}
              >
                INACTIVE
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity
          style={styles.submitButton}
          onPress={handleSave}
          disabled={saving}
          activeOpacity={0.8}
        >
          {saving ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.submitButtonText}>Save Changes</Text>
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
    fontSize: 12,
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
  },
  submitButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
  },
});
