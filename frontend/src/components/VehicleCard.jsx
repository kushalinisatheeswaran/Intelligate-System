import React from "react";
import { View, Text, StyleSheet } from "react-native";

export default function VehicleCard({ event }) {
  const isGranted = event.status === "granted";

  return (
    <View style={[styles.card, isGranted ? styles.granted : styles.denied]}>
      <View style={styles.row}>
        <Text style={styles.icon}>{isGranted ? "✅" : "🚨"}</Text>
        <View style={styles.info}>
          <Text style={styles.identifier}>{event.identifier}</Text>
          <Text style={styles.meta}>
            {event.id_type === "plate" ? "🚗 Plate" : "🪪 Student ID"}
            {event.name ? `  ·  ${event.name}` : "  ·  Unknown"}
          </Text>
        </View>
        {event.isLive && (
          <View style={styles.liveBadge}>
            <Text style={styles.liveText}>LIVE</Text>
          </View>
        )}
      </View>
      <Text style={styles.time}>
        {event.direction?.toUpperCase()}  ·  {event.timestamp}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card       : { marginHorizontal: 14, marginTop: 10, borderRadius: 12,
                 padding: 14, borderLeftWidth: 4, backgroundColor: "#fff" },
  granted    : { borderLeftColor: "#059669" },
  denied     : { borderLeftColor: "#DC2626", backgroundColor: "#FFF5F5" },
  row        : { flexDirection: "row", alignItems: "center", marginBottom: 6 },
  icon       : { fontSize: 22, marginRight: 10 },
  info       : { flex: 1 },
  identifier : { fontSize: 15, fontWeight: "700", color: "#111827" },
  meta       : { fontSize: 12, color: "#6B7280", marginTop: 2 },
  liveBadge  : { backgroundColor: "#FBBF24", borderRadius: 6,
                 paddingHorizontal: 8, paddingVertical: 2 },
  liveText   : { fontSize: 10, fontWeight: "700", color: "#78350F" },
  time       : { fontSize: 11, color: "#9CA3AF" },
});