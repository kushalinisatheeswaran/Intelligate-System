import React, { useState, useEffect, useCallback } from "react";
import {
  View, FlatList, StyleSheet, Text,
  TouchableOpacity, RefreshControl, ActivityIndicator,
} from "react-native";
import { getSocket } from "../../../src/services/socket";
import { SOCKET_EVENTS } from "../../../src/constants/config";
import api from "../../../src/services/api";

export default function OccupancyScreen() {
  const [occupancy,  setOccupancy]  = useState({
    vehicles_inside: 0,
    students_inside: 0,
    total_inside: 0,
    vehicles: [],
    students: [],
  });
  const [activeTab,  setActiveTab]  = useState("vehicles"); // 'vehicles' | 'students'
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchOccupancy = useCallback(async () => {
    try {
      const res = await api.get("/occupancy");
      setOccupancy(res.data);
    } catch (err) {
      console.error("[OCCUPANCY] Failed to fetch occupancy:", err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchOccupancy();
    setRefreshing(false);
  }, [fetchOccupancy]);

  useEffect(() => {
    fetchOccupancy();
  }, [fetchOccupancy]);

  // Socket.IO live updates
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    // Refresh ONLY on access_granted or approval_update resulting in granted access
    const onAccessGranted = () => {
      fetchOccupancy();
    };

    const onApprovalUpdate = (data) => {
      if (data && (data.status === "approved" || data.action === "approved")) {
        fetchOccupancy();
      } else {
        // Safe fallback for approval update
        fetchOccupancy();
      }
    };

    socket.on(SOCKET_EVENTS.ACCESS_GRANTED,  onAccessGranted);
    socket.on(SOCKET_EVENTS.APPROVAL_UPDATE, onApprovalUpdate);

    return () => {
      socket.off(SOCKET_EVENTS.ACCESS_GRANTED,  onAccessGranted);
      socket.off(SOCKET_EVENTS.APPROVAL_UPDATE, onApprovalUpdate);
    };
  }, [fetchOccupancy]);

  const listData = activeTab === "vehicles" ? occupancy.vehicles : occupancy.students;

  const renderCard = ({ item }) => {
    const isVehicle = activeTab === "vehicles";
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.identifierText}>
            {isVehicle ? "🚗 " : "🎓 "}
            {item.identifier}
          </Text>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>INSIDE</Text>
          </View>
        </View>

        <View style={styles.cardDetails}>
          <Text style={styles.detailLabel}>
            {isVehicle ? "Owner Name:" : "Student Name:"}
          </Text>
          <Text style={styles.detailValue}>
            {item.name ? item.name : "N/A"}
          </Text>
        </View>

        <View style={styles.cardDetails}>
          <Text style={styles.detailLabel}>Entry Time:</Text>
          <Text style={styles.detailValue}>
            {item.entry_time ? item.entry_time : "Unknown"}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Summary Cards */}
      <View style={styles.statsContainer}>
        <View style={[styles.statBox, styles.statBoxVehicles]}>
          <Text style={styles.statNumber}>{occupancy.vehicles_inside}</Text>
          <Text style={styles.statLabel}>Vehicles Inside</Text>
        </View>
        <View style={[styles.statBox, styles.statBoxStudents]}>
          <Text style={styles.statNumber}>{occupancy.students_inside}</Text>
          <Text style={styles.statLabel}>Students Inside</Text>
        </View>
        <View style={[styles.statBox, styles.statBoxTotal]}>
          <Text style={styles.statNumber}>{occupancy.total_inside}</Text>
          <Text style={styles.statLabel}>Total Inside</Text>
        </View>
      </View>

      {/* Tab Selectors */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === "vehicles" && styles.tabButtonActive]}
          onPress={() => setActiveTab("vehicles")}
          activeOpacity={0.7}
        >
          <Text style={[styles.tabText, activeTab === "vehicles" && styles.tabTextActive]}>
            VEHICLES INSIDE ({occupancy.vehicles_inside})
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabButton, activeTab === "students" && styles.tabButtonActive]}
          onPress={() => setActiveTab("students")}
          activeOpacity={0.7}
        >
          <Text style={[styles.tabText, activeTab === "students" && styles.tabTextActive]}>
            STUDENTS INSIDE ({occupancy.students_inside})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1D4ED8" />
        </View>
      ) : (
        <FlatList
          data={listData}
          keyExtractor={(item, index) => item.identifier + "-" + index}
          renderItem={renderCard}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#1D4ED8" />
          }
          contentContainerStyle={
            listData.length === 0 ? styles.emptyContainer : styles.listContent
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>🏛️</Text>
              <Text style={styles.emptyTitle}>
                {activeTab === "vehicles" ? "No Vehicles Inside" : "No Students Inside"}
              </Text>
              <Text style={styles.emptySubtitle}>
                Currently no {activeTab === "vehicles" ? "vehicles" : "students"} are logged inside campus.
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F3F4F6" },
  statsContainer: {
    flexDirection: "row",
    padding: 12,
    justifyContent: "space-between",
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  statBox: {
    flex: 1,
    paddingVertical: 10,
    marginHorizontal: 4,
    borderRadius: 8,
    alignItems: "center",
  },
  statBoxVehicles: { backgroundColor: "#EFF6FF" },
  statBoxStudents: { backgroundColor: "#ECFDF5" },
  statBoxTotal:    { backgroundColor: "#F3E8FF" },
  statNumber: { fontSize: 18, fontWeight: "700", color: "#1E293B" },
  statLabel:  { fontSize: 10, fontWeight: "600", color: "#64748B", marginTop: 2 },
  tabContainer: {
    flexDirection: "row",
    backgroundColor: "#fff",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  tabButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: "center",
    backgroundColor: "#F3F4F6",
    marginHorizontal: 4,
  },
  tabButtonActive: { backgroundColor: "#1D4ED8" },
  tabText: { fontSize: 11, fontWeight: "700", color: "#6B7280" },
  tabTextActive: { color: "#ffffff" },
  loadingContainer: { flex: 1, justifyContent: "center", alignItems: "center" },
  listContent: { padding: 12 },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  identifierText: { fontSize: 16, fontWeight: "700", color: "#111827" },
  badge: {
    backgroundColor: "#D1FAE5",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: { color: "#065F46", fontSize: 11, fontWeight: "700" },
  cardDetails: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 4,
  },
  detailLabel: { fontSize: 13, color: "#6B7280" },
  detailValue: { fontSize: 13, fontWeight: "600", color: "#1F2937" },
  emptyContainer: { flex: 1, justifyContent: "center" },
  empty: { alignItems: "center", paddingTop: 60 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 18, fontWeight: "600", color: "#6B7280" },
  emptySubtitle: {
    fontSize: 13, color: "#9CA3AF", marginTop: 8,
    textAlign: "center", paddingHorizontal: 40
  },
});
