import React, { useState, useEffect, useCallback, useRef } from "react";
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
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import api from "../../../../src/services/api";

const PAGE_SIZE = 5;

export default function StudentListScreen() {
  const router = useRouter();
  const [students, setStudents] = useState([]);
  const [filteredStudents, setFilteredStudents] = useState([]);
  const [paginatedStudents, setPaginatedStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all"); // all | active | inactive

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);

  // Snackbar State
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarType, setSnackbarType] = useState("success"); // success | error
  const fadeAnim = useRef(new Animated.Value(0)).current;

  // Skeleton Loader Animation
  const skeletonAlpha = useRef(new Animated.Value(0.3)).current;

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

  const fetchStudents = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const response = await api.get("/users");
      const allUsers = response.data?.users || [];
      const studentUsers = allUsers.filter((u) => u.role === "student");
      setStudents(studentUsers);
      if (isRefresh) {
        showSnackbar("Students list updated successfully.");
      }
    } catch (err) {
      showSnackbar(err.response?.data?.error || "Failed to load students.", "error");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  // Handle Search, Filtering, and resetting page
  useEffect(() => {
    let result = [...students];

    // 1. Search Query
    const query = searchQuery.trim().toLowerCase();
    if (query) {
      result = result.filter(
        (s) =>
          s.name?.toLowerCase().includes(query) ||
          s.email?.toLowerCase().includes(query)
      );
    }

    // 2. Status Filter
    if (statusFilter === "active") {
      result = result.filter((s) => s.is_active);
    } else if (statusFilter === "inactive") {
      result = result.filter((s) => !s.is_active);
    }

    setFilteredUsers(result);
  }, [searchQuery, statusFilter, students]);

  const setFilteredUsers = (result) => {
    setFilteredStudents(result);
    setCurrentPage(1);
  };

  // Handle Pagination
  useEffect(() => {
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    const paginated = filteredStudents.slice(startIndex, startIndex + PAGE_SIZE);
    setPaginatedStudents(paginated);
  }, [filteredStudents, currentPage]);

  const totalPages = Math.max(1, Math.ceil(filteredStudents.length / PAGE_SIZE));

  const renderSkeletonItem = () => (
    <Animated.View style={[styles.skeletonCard, { opacity: skeletonAlpha }]}>
      <View style={styles.skeletonLeft}>
        <View style={styles.skeletonLineLarge} />
        <View style={styles.skeletonLineSmall} />
        <View style={styles.skeletonPill} />
      </View>
      <View style={styles.skeletonRight} />
    </Animated.View>
  );

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.studentCard}
      onPress={() => router.push(`/admin/students/${item.id}`)}
      activeOpacity={0.7}
    >
      <View style={styles.cardInfo}>
        <Text style={styles.studentName}>{item.name}</Text>
        <Text style={styles.studentEmail}>{item.email || "No email"}</Text>
        <View style={styles.metaRow}>
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
              {item.is_active ? "ACTIVE" : "DEACTIVATED"}
            </Text>
          </View>
          <Text style={styles.createdDate}>
            Joined: {new Date(item.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>
      <Text style={styles.arrowIcon}>➡️</Text>
    </TouchableOpacity>
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
        <Text style={styles.headerTitle}>Students</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name or email..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor="#9CA3AF"
        />
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterContainer}>
        {["all", "active", "inactive"].map((f) => (
          <TouchableOpacity
            key={f}
            style={[
              styles.filterTab,
              statusFilter === f ? styles.filterTabActive : null,
            ]}
            onPress={() => setStatusFilter(f)}
          >
            <Text
              style={[
                styles.filterTabText,
                statusFilter === f ? styles.filterTabTextActive : null,
              ]}
            >
              {f.toUpperCase()}
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
            data={paginatedStudents}
            keyExtractor={(item) => item.id.toString()}
            renderItem={renderItem}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => fetchStudents(true)}
                colors={["#1D4ED8"]}
              />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyIcon}>👥</Text>
                <Text style={styles.emptyText}>No students matching criteria.</Text>
              </View>
            }
          />

          {/* Pagination UI */}
          {filteredStudents.length > PAGE_SIZE && (
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
  filterContainer: {
    flexDirection: "row",
    backgroundColor: "#fff",
    paddingBottom: 10,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  filterTab: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    marginRight: 8,
    backgroundColor: "#F3F4F6",
  },
  filterTabActive: {
    backgroundColor: "#1D4ED8",
  },
  filterTabText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#4B5563",
  },
  filterTabTextActive: {
    color: "#fff",
  },
  listContent: {
    padding: 16,
  },
  studentCard: {
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
  studentName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 4,
  },
  studentEmail: {
    fontSize: 13,
    color: "#6B7280",
    marginBottom: 10,
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  statusPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    marginRight: 10,
  },
  statusText: {
    fontSize: 10,
    fontWeight: "800",
  },
  createdDate: {
    fontSize: 11,
    color: "#9CA3AF",
    fontWeight: "500",
  },
  arrowIcon: {
    fontSize: 14,
    color: "#9CA3AF",
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
    width: "60%",
    marginBottom: 8,
  },
  skeletonLineSmall: {
    height: 12,
    backgroundColor: "#E5E7EB",
    borderRadius: 4,
    width: "40%",
    marginBottom: 12,
  },
  skeletonPill: {
    height: 18,
    backgroundColor: "#E5E7EB",
    borderRadius: 9,
    width: 70,
  },
  skeletonRight: {
    width: 20,
    height: 20,
    backgroundColor: "#E5E7EB",
    borderRadius: 4,
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
