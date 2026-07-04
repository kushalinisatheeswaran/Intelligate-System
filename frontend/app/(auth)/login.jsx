import React, { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, Alert, ActivityIndicator,
  KeyboardAvoidingView, Platform, ScrollView,
} from "react-native";
import { useAuth } from "../../src/context/AuthContext";

export default function LoginScreen() {
  const { login }              = useAuth();
  const [email,    setEmail]   = useState("");
  const [password, setPassword]= useState("");
  const [loading,  setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Missing Fields", "Please enter your email and password.");
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      // AuthContext sets user → (app)/_layout.jsx redirect fires automatically
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        err.response?.data?.message ||
        "Login failed. Check your credentials and try again.";
      Alert.alert("Login Failed", msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.card}>
          <Text style={styles.logo}>🚪</Text>
          <Text style={styles.title}>IntelliGate</Text>
          <Text style={styles.subtitle}>Security Management System</Text>

          <TextInput
            style={styles.input}
            placeholder="Email address"
            placeholderTextColor="#9CA3AF"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            returnKeyType="next"
            editable={!loading}
          />

          <TextInput
            style={styles.input}
            placeholder="Password"
            placeholderTextColor="#9CA3AF"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            returnKeyType="done"
            onSubmitEditing={handleLogin}
            editable={!loading}
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.buttonText}>Sign In</Text>
            }
          </TouchableOpacity>

          <Text style={styles.hint}>
            Admin: admin@intelligate.com{"\n"}
            Guard: guard@intelligate.com
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container      : { flex: 1, backgroundColor: "#1D4ED8" },
  scroll         : { flexGrow: 1, justifyContent: "center", padding: 24 },
  card           : { backgroundColor: "#fff", borderRadius: 20,
                     padding: 32, alignItems: "center",
                     shadowColor: "#000", shadowOffset: { width: 0, height: 4 },
                     shadowOpacity: 0.15, shadowRadius: 12, elevation: 8 },
  logo           : { fontSize: 56, marginBottom: 8 },
  title          : { fontSize: 28, fontWeight: "800",
                     color: "#1D4ED8", marginBottom: 4 },
  subtitle       : { fontSize: 13, color: "#6B7280", marginBottom: 32,
                     textAlign: "center" },
  input          : { width: "100%", height: 52, borderWidth: 1.5,
                     borderColor: "#E5E7EB", borderRadius: 10,
                     paddingHorizontal: 16, fontSize: 15,
                     color: "#111827", marginBottom: 14,
                     backgroundColor: "#F9FAFB" },
  button         : { width: "100%", height: 52, backgroundColor: "#1D4ED8",
                     borderRadius: 10, justifyContent: "center",
                     alignItems: "center", marginTop: 8 },
  buttonDisabled : { opacity: 0.6 },
  buttonText     : { color: "#fff", fontSize: 16, fontWeight: "700" },
  hint           : { marginTop: 20, fontSize: 11, color: "#9CA3AF",
                     textAlign: "center", lineHeight: 18 },
});