import React, { useState, useEffect, useCallback } from "react";
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
import api from "../../../../src/services/api";

export default function AddVehicleScreen() {
  const router = useRouter();
  const { userId } = useLocalSearchParams();
  const [owner, setOwner] = useState(null);
  const [plateNumber, setPlateNumber] = useState("");
  const [vehicleType, setVehicleType] = useState("car"); // car | bike | van
  const [loadingOwner, setLoadingOwner] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchOwner = useCallback(async () => {
    if (!userId) {
      setLoadingOwner(false);
      return;
    }
    setLoadingOwner(true);
    try {
      const res = await api.get(`/users/${userId}`);
      setOwner(res.data);
    } catch (err) {
      Alert.alert("Error", "Failed to load owner information.");
    } finally {
      setLoadingOwner(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchOwner();
  }, [fetchOwner]);

  const handleSave = async () => {
    if (!plateNumber.trim()) {
      Alert.alert("Required Fields", "License Plate Number is required.");
      return;
    }

    setSaving(true);
    try {
      await api.post(`/users/${userId}/vehicles`, {
        plate_number: plateNumber.trim().toUpperCase(),
        vehicle_type: vehicleType.toLowerCase(),
      });

      Alert.alert("Success", `Vehicle ${plateNumber} added successfully.`, [
        {
          text: "OK",
          onPress: () => {
            router.back();
          },
        },
      ]);
    } catch (err) {
      Alert.alert("Error", err.response?.data?.error || "Failed to add vehicle.");
    } finally {
      setSaving(false);
    }
  };

  if (loadingOwner) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1D4ED8" />
      </SafeAreaView>
    );
  }

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
        <Text style={styles.headerTitle}>Add Vehicle</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.sectionTitle}>Owner Information</Text>
        <View style={styles.ownerCard}>
          <Text style={styles.ownerName}>{owner?.name || "Unknown Owner"}</Text>
          <Text style={styles.ownerEmail}>{owner?.email || "No email"}</Text>
        </View>

        <Text style={styles.sectionTitle}>Vehicle Details</Text>

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

        <TouchableOpacity
          style={styles.submitButton}
          onPress={handleSave}
          disabled={saving}
          activeOpacity={0.8}
        >
          {saving ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.submitButtonText}>Add Vehicle</Text>
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
    padding: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#6B7280",
    textTransform: "uppercase",
    marginBottom: 10,
    marginTop: 10,
  },
  ownerCard: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  ownerName: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1F2937",
  },
  ownerEmail: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 3,
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
