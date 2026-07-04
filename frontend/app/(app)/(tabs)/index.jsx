import React, { useState, useEffect, useCallback } from "react";
import {
  View, FlatList, StyleSheet, Text,
  RefreshControl,
} from "react-native";
import { getSocket } from "../../../src/services/socket";
import { SOCKET_EVENTS } from "../../../src/constants/config";
import api from "../../../src/services/api";
import VehicleCard from "../../../src/components/VehicleCard";

export default function LiveFeedScreen() {
  const [events,     setEvents]     = useState([]);
  const [connected,  setConnected]  = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadRecentLogs = useCallback(async () => {
    try {
      const res       = await api.get("/logs?limit=30");
      const formatted = (res.data.logs || []).map((log) => ({
        id         : String(log.id),
        identifier : log.identifier,
        id_type    : log.id_type,
        direction  : log.direction,
        status     : log.status,
        name       : log.name,
        timestamp  : log.timestamp,
        isLive     : false,
      }));
      setEvents(formatted);
    } catch (err) {
      console.error("[FEED] Failed to load logs:", err.message);
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadRecentLogs();
    setRefreshing(false);
  }, [loadRecentLogs]);

  // Load recent logs from REST API on mount
  useEffect(() => {
    loadRecentLogs();
  }, [loadRecentLogs]);

  // Listen to Socket.IO vehicle_detected event
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const onConnect    = () => setConnected(true);
    const onDisconnect = () => setConnected(false);

    const onVehicleDetected = (data) => {
      const event = {
        id         : `live-${Date.now()}-${Math.random()}`,
        identifier : data.identifier,
        id_type    : data.id_type,
        direction  : data.direction,
        status     : data.status,
        name       : data.name,
        timestamp  : data.timestamp,
        isLive     : true,
      };
      // Prepend newest event to top, keep list capped at 50
      setEvents((prev) => [event, ...prev.slice(0, 49)]);
    };

    socket.on("connect",                     onConnect);
    socket.on("disconnect",                  onDisconnect);
    socket.on(SOCKET_EVENTS.VEHICLE_DETECTED, onVehicleDetected);

    // Sync current connection state
    setConnected(socket.connected);

    return () => {
      socket.off("connect",                     onConnect);
      socket.off("disconnect",                  onDisconnect);
      socket.off(SOCKET_EVENTS.VEHICLE_DETECTED, onVehicleDetected);
    };
  }, []);

  return (
    <View style={styles.container}>
      {/* Live connection status banner */}
      <View style={[
        styles.statusBar,
        connected ? styles.statusOnline : styles.statusOffline,
      ]}>
        <Text style={[
          styles.statusText,
          connected ? styles.statusTextOnline : styles.statusTextOffline,
        ]}>
          {connected
            ? "🟢  Connected — updates are live"
            : "🔴  Disconnected — pull down to refresh"}
        </Text>
      </View>

      <FlatList
        data={events}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <VehicleCard event={item} />}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh}
                          tintColor="#1D4ED8" />
        }
        contentContainerStyle={
          events.length === 0 ? styles.emptyContainer : styles.listContent
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>📡</Text>
            <Text style={styles.emptyTitle}>No events yet</Text>
            <Text style={styles.emptySubtitle}>
              Vehicle detections appear here in real time
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container          : { flex: 1, backgroundColor: "#F3F4F6" },
  statusBar          : { paddingVertical: 8, paddingHorizontal: 16 },
  statusOnline       : { backgroundColor: "#D1FAE5" },
  statusOffline      : { backgroundColor: "#FEE2E2" },
  statusText         : { fontSize: 12, fontWeight: "600", textAlign: "center" },
  statusTextOnline   : { color: "#065F46" },
  statusTextOffline  : { color: "#991B1B" },
  listContent        : { paddingBottom: 20 },
  emptyContainer     : { flex: 1, justifyContent: "center" },
  empty              : { alignItems: "center", paddingTop: 60 },
  emptyIcon          : { fontSize: 48, marginBottom: 12 },
  emptyTitle         : { fontSize: 18, fontWeight: "600", color: "#6B7280" },
  emptySubtitle      : { fontSize: 13, color: "#9CA3AF", marginTop: 8,
                         textAlign: "center", paddingHorizontal: 40 },
});