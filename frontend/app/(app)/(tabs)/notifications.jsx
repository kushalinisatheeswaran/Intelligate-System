import React, { useState, useEffect, useCallback } from "react";
import {
  View, FlatList, StyleSheet, Text,
  RefreshControl, ActivityIndicator,
} from "react-native";
import api from "../../../src/services/api";

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState([]);
  const [loading,       setLoading]       = useState(true);
  const [refreshing,    setRefreshing]    = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await api.get("/notifications?limit=50");
      setNotifications(res.data.notifications || []);
    } catch (err) {
      console.error("[NOTIF] Load failed:", err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1D4ED8" />
      </View>
    );
  }

  const renderItem = ({ item }) => (
    <View style={[
      styles.item,
      item.status === "failed" && styles.itemFailed,
    ]}>
      <View style={styles.itemHeader}>
        <Text style={styles.identifier}>{item.identifier}</Text>
        <View style={[
          styles.statusBadge,
          item.status === "sent" ? styles.badgeSent : styles.badgeFailed,
        ]}>
          <Text style={[
            styles.statusText,
            item.status === "sent" ? styles.textSent : styles.textFailed,
          ]}>
            {item.status === "sent" ? "✓ Sent" : "✗ Failed"}
          </Text>
        </View>
      </View>

      <Text style={styles.type}>
        {item.id_type === "plate" ? "🚗 Plate" : "🪪 Student ID"}
        {"  ·  "}
        {item.channel?.toUpperCase() || "FCM"}
      </Text>

      <Text style={styles.message} numberOfLines={2}>
        {item.message}
      </Text>

      <Text style={styles.time}>
        {new Date(item.sent_at).toLocaleString()}
      </Text>

      {item.status === "failed" && item.error && (
        <Text style={styles.error} numberOfLines={1}>
          Error: {item.error}
        </Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={notifications}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh}
                          tintColor="#1D4ED8" />
        }
        contentContainerStyle={
          notifications.length === 0 ? styles.emptyContainer : styles.listContent
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>🔔</Text>
            <Text style={styles.emptyTitle}>No notifications yet</Text>
            <Text style={styles.emptySubtitle}>
              FCM alerts sent to this device will appear here
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
  listContent    : { paddingBottom: 20 },
  item           : { backgroundColor: "#fff", marginHorizontal: 14,
                     marginTop: 10, borderRadius: 12, padding: 14,
                     borderLeftWidth: 3, borderLeftColor: "#1D4ED8" },
  itemFailed     : { borderLeftColor: "#DC2626" },
  itemHeader     : { flexDirection: "row", justifyContent: "space-between",
                     alignItems: "center", marginBottom: 4 },
  identifier     : { fontSize: 15, fontWeight: "700", color: "#111827" },
  statusBadge    : { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 99 },
  badgeSent      : { backgroundColor: "#D1FAE5" },
  badgeFailed    : { backgroundColor: "#FEE2E2" },
  statusText     : { fontSize: 11, fontWeight: "600" },
  textSent       : { color: "#065F46" },
  textFailed     : { color: "#991B1B" },
  type           : { fontSize: 11, color: "#9CA3AF", marginBottom: 4 },
  message        : { fontSize: 12, color: "#6B7280", lineHeight: 18,
                     marginBottom: 6 },
  time           : { fontSize: 11, color: "#9CA3AF" },
  error          : { fontSize: 11, color: "#DC2626", marginTop: 4 },
  emptyContainer : { flex: 1, justifyContent: "center" },
  empty          : { alignItems: "center", paddingTop: 60 },
  emptyIcon      : { fontSize: 48, marginBottom: 12 },
  emptyTitle     : { fontSize: 18, fontWeight: "600", color: "#6B7280" },
  emptySubtitle  : { fontSize: 13, color: "#9CA3AF", marginTop: 8,
                     textAlign: "center", paddingHorizontal: 40 },
});