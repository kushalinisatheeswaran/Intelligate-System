import React, { useState, useEffect, useCallback } from "react";
import {
  View, FlatList, StyleSheet, Text,
  Alert, RefreshControl, ActivityIndicator,
} from "react-native";
import { getSocket } from "../../../src/services/socket";
import { SOCKET_EVENTS } from "../../../src/constants/config";
import api from "../../../src/services/api";
import PendingCard from "../../../src/components/PendingCard";

export default function PendingScreen() {
  const [items,      setItems]      = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadPending = useCallback(async () => {
    try {
      const res = await api.get("/pending");
      setItems(res.data.pending || []);
    } catch (err) {
      const msg = err.response?.data?.error || "Failed to load pending approvals";
      Alert.alert("Error", msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadPending();
    setRefreshing(false);
  }, [loadPending]);

  useEffect(() => {
    loadPending();
  }, [loadPending]);

  // Socket.IO listeners
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    // New unknown vehicle detected — add to top of list instantly
    const onUnknownVehicle = (data) => {
      setItems((prev) => {
        const exists = prev.find((p) => p.id === data.pending_id);
        if (exists) return prev;
        return [
          {
            id         : data.pending_id,
            identifier : data.identifier,
            id_type    : data.id_type,
            image_path : data.image_path,
            status     : "pending",
            created_at : data.timestamp,
          },
          ...prev,
        ];
      });
    };

    // Admin approved or rejected — remove from list instantly
    const onApprovalUpdate = (data) => {
      setItems((prev) => prev.filter((p) => p.id !== data.pending_id));
    };

    socket.on(SOCKET_EVENTS.UNKNOWN_VEHICLE,  onUnknownVehicle);
    socket.on(SOCKET_EVENTS.APPROVAL_UPDATE,  onApprovalUpdate);

    return () => {
      socket.off(SOCKET_EVENTS.UNKNOWN_VEHICLE, onUnknownVehicle);
      socket.off(SOCKET_EVENTS.APPROVAL_UPDATE, onApprovalUpdate);
    };
  }, []);

  const handleApprove = useCallback((item) => {
    Alert.alert(
      "Approve Entry",
      `Allow ${item.identifier} to enter?\n\nThis will register the vehicle and open the gate.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text    : "Approve + Open Gate",
          onPress : async () => {
            try {
              await api.post(`/approve/${item.id}`, { open_gate: true });
              // Socket.IO approval_update removes it from list automatically
              // Fallback: remove locally if socket event is delayed
              setItems((prev) => prev.filter((p) => p.id !== item.id));
            } catch (err) {
              Alert.alert("Error", err.response?.data?.error || "Approval failed");
            }
          },
        },
      ]
    );
  }, []);

  const handleReject = useCallback((item) => {
    Alert.alert(
      "Reject Entry",
      `Deny access for ${item.identifier}?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text    : "Reject",
          style   : "destructive",
          onPress : async () => {
            try {
              await api.post(`/reject/${item.id}`, {
                reason: "Rejected by security guard",
              });
              setItems((prev) => prev.filter((p) => p.id !== item.id));
            } catch (err) {
              Alert.alert("Error", err.response?.data?.error || "Rejection failed");
            }
          },
        },
      ]
    );
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1D4ED8" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>
          {items.length} pending {items.length === 1 ? "approval" : "approvals"}
        </Text>
      </View>

      <FlatList
        data={items}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <PendingCard
            item={item}
            onApprove={() => handleApprove(item)}
            onReject={()  => handleReject(item)}
          />
        )}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh}
                          tintColor="#1D4ED8" />
        }
        contentContainerStyle={
          items.length === 0 ? styles.emptyContainer : styles.listContent
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>✅</Text>
            <Text style={styles.emptyTitle}>All clear</Text>
            <Text style={styles.emptySubtitle}>
              Unknown vehicles will appear here instantly
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container      : { flex: 1, backgroundColor: "#F3F4F6" },
  center         : { flex: 1, justifyContent: "center", alignItems: "center" },
  header         : { paddingVertical: 10, paddingHorizontal: 16,
                     backgroundColor: "#fff",
                     borderBottomWidth: 0.5, borderColor: "#E5E7EB" },
  headerText     : { fontSize: 13, color: "#6B7280", fontWeight: "500" },
  listContent    : { paddingBottom: 20 },
  emptyContainer : { flex: 1, justifyContent: "center" },
  empty          : { alignItems: "center", paddingTop: 60 },
  emptyIcon      : { fontSize: 48, marginBottom: 12 },
  emptyTitle     : { fontSize: 18, fontWeight: "600", color: "#6B7280" },
  emptySubtitle  : { fontSize: 13, color: "#9CA3AF", marginTop: 8,
                     textAlign: "center", paddingHorizontal: 40 },
});