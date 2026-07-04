import React, { useState, useEffect, useCallback } from "react";
import {
  View, Text, TouchableOpacity, StyleSheet,
  Alert, ActivityIndicator, ScrollView,
} from "react-native";
import { getSocket } from "../../../src/services/socket";
import { SOCKET_EVENTS } from "../../../src/constants/config";
import { useAuth } from "../../../src/context/AuthContext";
import api from "../../../src/services/api";

const STATUS_CONFIG = {
  open    : { bg: "#D1FAE5", textColor: "#065F46", icon: "🔓", label: "OPEN"    },
  closed  : { bg: "#FEE2E2", textColor: "#991B1B", icon: "🔒", label: "CLOSED"  },
  unknown : { bg: "#F3F4F6", textColor: "#6B7280", icon: "❓", label: "UNKNOWN" },
};

export default function GateStatusScreen() {
  const { user }                      = useAuth();
  const [gateStatus,  setGateStatus]  = useState("unknown");
  const [lastUpdate,  setLastUpdate]  = useState(null);
  const [loading,     setLoading]     = useState(false);

  const isAdmin = user?.role === "admin";
  const config  = STATUS_CONFIG[gateStatus] ?? STATUS_CONFIG.unknown;

  // Listen to Socket.IO gate_status events
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const onGateStatus = (data) => {
      setGateStatus(data.status);
      setLastUpdate({
        time         : new Date().toLocaleTimeString(),
        triggered_by : data.triggered_by || "system",
      });
    };

    socket.on(SOCKET_EVENTS.GATE_STATUS, onGateStatus);
    return () => socket.off(SOCKET_EVENTS.GATE_STATUS, onGateStatus);
  }, []);

  const handleGateAction = useCallback((action) => {
    if (!isAdmin) {
      Alert.alert(
        "Access Denied",
        "Only administrators can manually control the gate."
      );
      return;
    }

    Alert.alert(
      `${action === "open" ? "Open" : "Close"} Gate`,
      `Manually ${action} the main gate?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text    : "Confirm",
          style   : action === "close" ? "destructive" : "default",
          onPress : async () => {
            setLoading(true);
            try {
              const socket = getSocket();
              if (socket && socket.connected) {
                socket.emit("gate_command", { command: action.toUpperCase() });
              } else {
                await api.post(`/gate/${action}`);
              }
            } catch (err) {
              Alert.alert(
                "Error",
                err.response?.data?.error || `Failed to ${action} gate`
              );
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  }, [isAdmin]);

  return (
    <ScrollView style={styles.container}
                contentContainerStyle={styles.content}>

      {/* Gate status indicator */}
      <View style={[styles.statusCard, { backgroundColor: config.bg }]}>
        <Text style={styles.statusIcon}>{config.icon}</Text>
        <Text style={[styles.statusLabel, { color: config.textColor }]}>
          Gate is {config.label}
        </Text>
        {lastUpdate ? (
          <Text style={styles.lastUpdate}>
            {lastUpdate.time} — triggered by {lastUpdate.triggered_by}
          </Text>
        ) : (
          <Text style={styles.lastUpdate}>
            Waiting for gate event via Socket.IO...
          </Text>
        )}
      </View>

      {/* Admin manual controls */}
      {isAdmin ? (
        <View style={styles.controlsCard}>
          <Text style={styles.controlsTitle}>Manual Override</Text>
          <Text style={styles.controlsSubtitle}>Admin use only</Text>

          <TouchableOpacity
            style={[styles.controlBtn, styles.openBtn,
                    loading && styles.btnDisabled]}
            onPress={() => handleGateAction("open")}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.controlBtnText}>🔓  Open Gate</Text>
            }
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.controlBtn, styles.closeBtn,
                    loading && styles.btnDisabled]}
            onPress={() => handleGateAction("close")}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.controlBtnText}>🔒  Close Gate</Text>
            }
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.guardNote}>
          <Text style={styles.guardNoteIcon}>👮</Text>
          <Text style={styles.guardNoteText}>
            Guard view — the gate opens automatically when an authorized
            vehicle or student ID is verified. Contact an administrator
            for manual override.
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container       : { flex: 1, backgroundColor: "#F3F4F6" },
  content         : { padding: 20, paddingBottom: 40 },
  statusCard      : { borderRadius: 16, padding: 32,
                      alignItems: "center", marginBottom: 20 },
  statusIcon      : { fontSize: 64, marginBottom: 12 },
  statusLabel     : { fontSize: 28, fontWeight: "800", letterSpacing: 1 },
  lastUpdate      : { fontSize: 12, color: "#6B7280", marginTop: 8,
                      textAlign: "center" },
  controlsCard    : { backgroundColor: "#fff", borderRadius: 16,
                      padding: 20, marginBottom: 16 },
  controlsTitle   : { fontSize: 17, fontWeight: "700", color: "#111827",
                      textAlign: "center" },
  controlsSubtitle: { fontSize: 12, color: "#9CA3AF", textAlign: "center",
                      marginBottom: 16 },
  controlBtn      : { height: 54, borderRadius: 12, justifyContent: "center",
                      alignItems: "center", marginBottom: 12 },
  openBtn         : { backgroundColor: "#059669" },
  closeBtn        : { backgroundColor: "#DC2626" },
  btnDisabled     : { opacity: 0.5 },
  controlBtnText  : { color: "#fff", fontSize: 16, fontWeight: "700" },
  guardNote       : { backgroundColor: "#EFF6FF", borderRadius: 14,
                      padding: 20, alignItems: "center" },
  guardNoteIcon   : { fontSize: 32, marginBottom: 10 },
  guardNoteText   : { fontSize: 13, color: "#1D4ED8", lineHeight: 20,
                      textAlign: "center" },
});