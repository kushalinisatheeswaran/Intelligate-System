import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  TextInput,
  ActivityIndicator,
  Animated,
  RefreshControl,
  StatusBar,
  Alert,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import api from "../../../../src/services/api";

const PAGE_SIZE = 5;

export default function VehicleDirectoryScreen() {
  const router = useRouter();
  const [vehicles, setVehicles] = useState([]);
  const [filteredVehicles, setFilteredVehicles] = useState([]);
  const [paginatedVehicles, setPaginatedVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all"); // all | car | bike | van
  const [statusFilter, setStatusFilter] = useState("all"); // all | active | inactive

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);

  // Snackbar State
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarType, setSnackbarType] = useState("success"); // success | error
  const fadeAnim = useMemo(() => new Animated.Value(0), []);

  // Skeleton Animation
  const skeletonAlpha = useMemo(() => new Animated.Value(0.3), []);

  const showSnackbar = (message, type = "success") => {
    setSnackbarMessage(message);
    setSnackbarType(type);
    Animated.sequence([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.delay(2000),
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  };

  useEffect(() => {
    if (loading) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(skeletonAlpha, {
            toValue: 0.7,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(skeletonAlpha, {
            toValue: 0.3,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [loading]);

  const fetchAllVehicles = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      // Step A: Fetch all users
      const usersRes = await api.get("/users");
      const list = usersRes.data?.users || [];
      const staffOrStudents = list.filter((u) => u.role !== "visitor");

      // Step B: Batch fetch vehicles for all users
      const promises = staffOrStudents.map(async (u) => {
        try {
          const vRes = await api.get(`/users/${u.id}/vehicles`);
          const userV = vRes.data?.vehicles || [];
          return userV.map((v) => ({
            ...v,
            ownerName: u.name,
            ownerEmail: u.email,
            ownerId: u.id,
          }));
        } catch {
          return []; // Fail-safe for individual fetch issues
        }
      });

      const results = await Promise.all(promises);
      // Step C: Flatten all results into a single flat list
      const flattened = results.flat();
      setVehicles(flattened);

      if (isRefresh) {
        showSnackbar("Vehicle directory updated successfully.");
      }
    } catch (err) {
      showSnackbar("Failed to load vehicle directory.", "error");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAllVehicles();
  }, [fetchAllVehicles]);

  // Search & Filtering
  useEffect(() => {
    let result = [...vehicles];

    // Search Query (by plate number or owner name)
    const query = searchQuery.trim().toLowerCase();
    if (query) {
      result = result.filter(
        (v) =>
          v.plate_number?.toLowerCase().includes(query) ||
          v.ownerName?.toLowerCase().includes(query)
      );
    }

    // Vehicle Type Filter
    if (typeFilter !== "all") {
      result = result.filter((v) => v.vehicle_type?.toLowerCase() === typeFilter);
    }

    // Active Status Filter
    if (statusFilter === "active") {
      result = result.filter((v) => v.is_active);
    } else if (statusFilter === "inactive") {
      result = result.filter((v) => !v.is_active);
    }

    setFilteredVehicles(result);
    setCurrentPage(1);
  }, [searchQuery, typeFilter, statusFilter, vehicles]);

  // Pagination
  useEffect(() => {
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    const paginated = filteredVehicles.slice(startIndex, startIndex + PAGE_SIZE);
    setPaginatedVehicles(paginated);
  }, [filteredVehicles, currentPage]);

  const totalPages = Math.max(1, Math.ceil(filteredVehicles.length / PAGE_SIZE));

  const handleDeleteVehicle = (vehicle) => {
    Alert.alert(
      "Delete Vehicle",
      `Are you sure you want to delete vehicle ${vehicle.plate_number}?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await api.delete(`/vehicles/${vehicle.id}`);
              showSnackbar("Vehicle deleted successfully.");
              fetchAllVehicles();
            } catch (err) {
              showSnackbar("Failed to delete vehicle.", "error");
            }
          },
        },
      ]
    );
  };

  const renderSkeletonItem = () => (
    <Animated.View style={[styles.skeletonCard, { opacity: skeletonAlpha }]}>
      <View style={styles.skeletonLeft}>
        <View style={styles.skeletonLineLarge} />
        <View style={styles.skeletonLineSmall} />
      </View>
      <View style={styles.skeletonRight} />
    </Animated.View>
  );

  const renderItem = ({ item }) => (
    <View style={styles.vehicleCard}>
      <View style={styles.cardInfo}>
        <View style={styles.plateRow}>
          <Text style={styles.plateNumber}>{item.plate_number}</Text>
          <View
            style={[
              styles.statusPill,
              { backgroundColor: item.is_active ? "#D1FAE5" : "#FEE2E2" },
            ]}
          >
            <Text
              style={[
                styles.statusText,
                { color: item.is_active ? "#065F46" : "#991B1B" },
              ]}
            >
              {item.is_active ? "ACTIVE" : "INACTIVE"}
            </Text>
          </View>
        </View>
        <Text style={styles.vehicleType}>Type: {item.vehicle_type?.toUpperCase()}</Text>
        <Text style={styles.ownerText}>
          Owner: {item.ownerName} ({item.ownerEmail || "No email"})
        </Text>
      </View>
      <View style={styles.actionColumn}>
        <TouchableOpacity
          style={[styles.actionBtn, styles.editBtn]}
          onPress={() =>
            router.push({
              pathname: `/admin/vehicles/edit/${item.id}`,
              params: {
                plate: item.plate_number,
                type: item.vehicle_type,
                isActive: item.is_active,
              },
            })
          }
          activeOpacity={0.7}
        >
          <Text style={styles.editBtnText}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionBtn, styles.deleteBtn]}
          onPress={() => handleDeleteVehicle(item)}
          activeOpacity={0.7}
        >
          <Text style={styles.deleteBtnText}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

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
        <Text style={styles.headerTitle}>Vehicle Directory</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search by plate number or owner..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor="#9CA3AF"
        />
      </View>

      {/* Type Filter Tabs */}
      <View style={styles.filterRow}>
        <Text style={styles.filterLabel}>Type:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {["all", "car", "bike", "van"].map((t) => (
            <TouchableOpacity
              key={t}
              style={[
                styles.filterTab,
                typeFilter === t ? styles.filterTabActive : null,
              ]}
              onPress={() => setTypeFilter(t)}
            >
              <Text
                style={[
                  styles.filterTabText,
                  typeFilter === t ? styles.filterTabTextActive : null,
                ]}
              >
                {t.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Status Filter Tabs */}
      <View style={styles.filterRow}>
        <Text style={styles.filterLabel}>Status:</Text>
        {["all", "active", "inactive"].map((s) => (
          <TouchableOpacity
            key={s}
            style={[
              styles.filterTab,
              statusFilter === s ? styles.filterTabActive : null,
            ]}
            onPress={() => setStatusFilter(s)}
          >
            <Text
              style={[
                styles.filterTabText,
                statusFilter === s ? styles.filterTabTextActive : null,
              ]}
            >
              {s.toUpperCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.listContent}>
          {renderSkeletonItem()}
          {renderSkeletonItem()}
          {renderSkeletonItem()}
        </View>
      ) : (
        <View style={{ flex: 1 }}>
          <FlatList
            data={paginatedVehicles}
            keyExtractor={(item) => item.id.toString()}
            renderItem={renderItem}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => fetchAllVehicles(true)}
                colors={["#1D4ED8"]}
              />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyIcon}>🚗</Text>
                <Text style={styles.emptyText}>No vehicles matching criteria.</Text>
              </View>
            }
          />

          {/* Pagination UI */}
          {filteredVehicles.length > PAGE_SIZE && (
            <View style={styles.paginationRow}>
              <TouchableOpacity
                style={[styles.pageBtn, currentPage === 1 ? styles.pageBtnDisabled : null]}
                onPress={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <Text style={styles.pageBtnText}>Prev</Text>
              </TouchableOpacity>
              <Text style={styles.pageInfo}>
                Page {currentPage} of {totalPages}
              </Text>
              <TouchableOpacity
                style={[
                  styles.pageBtn,
                  currentPage === totalPages ? styles.pageBtnDisabled : null,
                ]}
                onPress={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                <Text style={styles.pageBtnText}>Next</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      )}

      {/* Animated Snackbar */}
      {snackbarMessage ? (
        <Animated.View
          style={[
            styles.snackbar,
            {
              opacity: fadeAnim,
              backgroundColor: snackbarType === "success" ? "#10B981" : "#EF4444",
            },
          ]}
        >
          <Text style={styles.snackbarText}>{snackbarMessage}</Text>
        </Animated.View>
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
    fontSize: 18,
    color: "#fff",
  },
  headerTitle: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "700",
  },
  searchContainer: {
    padding: 12,
    backgroundColor: "#fff",
  },
  searchInput: {
    height: 44,
    backgroundColor: "#F3F4F6",
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 14,
    color: "#1F2937",
    fontWeight: "500",
  },
  filterRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    paddingBottom: 8,
    paddingHorizontal: 12,
  },
  filterLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: "#4B5563",
    width: 55,
  },
  filterTab: {
    paddingVertical: 5,
    paddingHorizontal: 12,
    borderRadius: 20,
    marginRight: 8,
    backgroundColor: "#F3F4F6",
  },
  filterTabActive: {
    backgroundColor: "#1D4ED8",
  },
  filterTabText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#4B5563",
  },
  filterTabTextActive: {
    color: "#fff",
  },
  listContent: {
    padding: 16,
  },
  vehicleCard: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 18,
    marginBottom: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  cardInfo: {
    flex: 1,
    marginRight: 10,
  },
  plateRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  plateNumber: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1F2937",
    marginRight: 10,
  },
  statusPill: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  statusText: {
    fontSize: 9,
    fontWeight: "800",
  },
  vehicleType: {
    fontSize: 12,
    color: "#4B5563",
    fontWeight: "600",
    marginBottom: 3,
  },
  ownerText: {
    fontSize: 12,
    color: "#6B7280",
    fontWeight: "500",
  },
  actionColumn: {
    justifyContent: "center",
  },
  actionBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    marginBottom: 6,
    alignItems: "center",
  },
  editBtn: {
    backgroundColor: "#E5E7EB",
  },
  editBtnText: {
    color: "#374151",
    fontSize: 11,
    fontWeight: "700",
  },
  deleteBtn: {
    backgroundColor: "#FEE2E2",
  },
  deleteBtnText: {
    color: "#DC2626",
    fontSize: 11,
    fontWeight: "700",
  },
  skeletonCard: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 18,
    marginBottom: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  skeletonLeft: {
    flex: 1,
  },
  skeletonLineLarge: {
    height: 16,
    backgroundColor: "#E5E7EB",
    borderRadius: 4,
    width: "45%",
    marginBottom: 8,
  },
  skeletonLineSmall: {
    height: 12,
    backgroundColor: "#E5E7EB",
    borderRadius: 4,
    width: "65%",
  },
  skeletonRight: {
    width: 24,
    height: 24,
    backgroundColor: "#E5E7EB",
    borderRadius: 4,
  },
  emptyContainer: {
    paddingVertical: 60,
    alignItems: "center",
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyText: {
    color: "#6B7280",
    fontSize: 14,
    fontWeight: "600",
  },
  paginationRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
  pageBtn: {
    backgroundColor: "#1D4ED8",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  pageBtnDisabled: {
    backgroundColor: "#9CA3AF",
  },
  pageBtnText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 13,
  },
  pageInfo: {
    fontSize: 13,
    fontWeight: "600",
    color: "#374151",
  },
  snackbar: {
    position: "absolute",
    bottom: 80,
    left: 20,
    right: 20,
    padding: 16,
    borderRadius: 12,
    flexDirection: "row",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 5,
    elevation: 4,
  },
  snackbarText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "700",
  },
});
