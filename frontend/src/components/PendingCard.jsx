import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";

export default function PendingCard({ item, onApprove, onReject }) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.icon}>⚠️</Text>
        <View style={styles.info}>
          <Text style={styles.identifier}>{item.identifier}</Text>
          <Text style={styles.meta}>
            {item.id_type === "plate" ? "🚗 Unknown Plate" : "🪪 Unknown Student ID"}
          </Text>
        </View>
        <View style={styles.pendingBadge}>
          <Text style={styles.pendingText}>PENDING</Text>
        </View>
      </View>

      <Text style={styles.time}>
        Detected: {new Date(item.created_at).toLocaleString()}
      </Text>

      <View style={styles.actions}>
        <TouchableOpacity style={styles.approveBtn} onPress={onApprove}>
          <Text style={styles.approveBtnText}>✓  Approve + Open Gate</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.rejectBtn} onPress={onReject}>
          <Text style={styles.rejectBtnText}>✗  Reject</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card          : { backgroundColor: "#fff", marginHorizontal: 14,
                    marginTop: 10, borderRadius: 12, padding: 14,
                    borderLeftWidth: 4, borderLeftColor: "#F59E0B" },
  header        : { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  icon          : { fontSize: 22, marginRight: 10 },
  info          : { flex: 1 },
  identifier    : { fontSize: 15, fontWeight: "700", color: "#111827" },
  meta          : { fontSize: 12, color: "#6B7280", marginTop: 2 },
  pendingBadge  : { backgroundColor: "#FEF3C7", borderRadius: 6,
                    paddingHorizontal: 8, paddingVertical: 2 },
  pendingText   : { fontSize: 10, fontWeight: "700", color: "#92400E" },
  time          : { fontSize: 11, color: "#9CA3AF", marginBottom: 12 },
  actions       : { flexDirection: "row", gap: 8 },
  approveBtn    : { flex: 1, backgroundColor: "#059669", borderRadius: 8,
                    paddingVertical: 10, alignItems: "center" },
  approveBtnText: { color: "#fff", fontWeight: "600", fontSize: 13 },
  rejectBtn     : { flex: 1, backgroundColor: "#DC2626", borderRadius: 8,
                    paddingVertical: 10, alignItems: "center" },
  rejectBtnText : { color: "#fff", fontWeight: "600", fontSize: 13 },
});