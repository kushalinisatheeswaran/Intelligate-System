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
import api from "../../../../../src/services/api";

export default function EditStudentScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [studentId, setStudentId] = useState("");
  const [faculty, setFaculty] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchDetails = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await api.get(`/users/${id}`);
      const data = response.data;
      setName(data.name || "");
      setEmail(data.email || "");
      const barcodeRec = data.student_ids?.[0];
      setStudentId(barcodeRec?.student_number || "");
      setFaculty(barcodeRec?.faculty || "");
    } catch (err) {
      Alert.alert("Error", err.response?.data?.error || "Failed to load student details");
      router.back();
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  useEffect(() => {
    fetchDetails();
  }, [fetchDetails]);

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert("Required Fields", "Name is required.");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        email: email.trim() || null,
      };

      if (studentId.trim()) {
        payload.student_number = studentId.trim().toUpperCase();
        payload.faculty = faculty.trim() || "Unknown";
      }

      await api.put(`/users/${id}`, payload);

      Alert.alert("Success", "Student updated successfully.", [
        {
          text: "OK",
          onPress: () => {
            router.back();
          },
        },
      ]);
    } catch (err) {
      Alert.alert("Error", err.response?.data?.error || "Failed to update student.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
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
        <Text style={styles.headerTitle}>Edit Student</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.sectionTitle}>Student Details</Text>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Full Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. John Doe"
            placeholderTextColor="#9CA3AF"
            value={name}
            onChangeText={setName}
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Email Address</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. john.doe@university.edu"
            placeholderTextColor="#9CA3AF"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Student ID / Barcode</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. 113113"
            placeholderTextColor="#9CA3AF"
            value={studentId}
            onChangeText={setStudentId}
            autoCapitalize="characters"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Faculty / Department</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. Engineering"
            placeholderTextColor="#9CA3AF"
            value={faculty}
            onChangeText={setFaculty}
          />
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
    fontSize: 14,
    fontWeight: "600",
    color: "#6B7280",
    textTransform: "uppercase",
    marginBottom: 20,
  },
  formGroup: {
    marginBottom: 16,
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
