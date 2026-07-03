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
  Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import api from "../../../../src/services/api";

const PAGE_SIZE = 5;

export default function GuardListScreen() {
  const router = useRouter();
  const [guards, setGuards] = useState([]);
  const [filteredGuards, setFilteredGuards] = useState([]);
  const [paginatedGuards, setPaginatedGuards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deactivatingId, setDeactivatingId] = useState(null);

  // Search State
  const [searchQuery, setSearchQuery] = useState("");

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);

  // Snackbar State
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarType, setSnackbarType] = useState("success"); // success | error
  const fadeAnim = useRef(new Animated.Value(0)).current;

  // Skeleton Animation
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

  const fetchGuards = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const response = await api.get("/admin/guards");
      const list = response.data?.guards || [];
      setGuards(list);
      if (isRefresh) {
        showSnackbar("Guards directory updated successfully.");
      }
    } catch (err) {
      showSnackbar("Failed to load guards.", "error");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchGuards();
  }, [fetchGuards]);

  // Search filtering
  useEffect(() => {
    let result = [...guards];
    const query = searchQuery.trim().toLowerCase();
    if (query) {
      result = result.filter(
        (g) =>
          g.name?.toLowerCase().includes(query) ||
          g.email?.toLowerCase().includes(query)
      );
    }

    setFilteredGuardsList(result);
  }, [searchQuery, guards]);

  const setFilteredGuardsList = (result) => {
    setFilteredGuards(result);
    setCurrentPage(1);
  };

  // Pagination
  useEffect(() => {
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    const paginated = filteredGuards.slice(startIndex, startIndex + PAGE_SIZE);
    setPaginatedGuards(paginated);
  }, [filteredGuards, currentPage]);

  const totalPages = Math.max(1, Math.ceil(filteredGuards.length / PAGE_SIZE));

  const handleDeactivate = (guard) => {
    Alert.alert(
      "Deactivate Guard",
      `Are you sure you want to deactivate guard ${guard.name}? They will no longer be able to log in.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Deactivate",
          style: "destructive",
          onPress: async () => {
            setDeactivatingId(guard.id);
            try {
              await api.delete(`/admin/guards/${guard.id}`);
              showSnackbar(`Guard ${guard.name} deactivated.`);
              fetchGuards();
            } catch (err) {
              showSnackbar("Failed to deactivate guard.", "error");
            } finally {
              setDeactivatingId(null);
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

  const renderItem = ({ item }) => {
    const isWorking = deactivatingId === item.id;
    return (
      <View style={styles.guardCard}>
        <View style={styles.cardInfo}>
          <Text style={styles.guardName}>{item.name}</Text>
          <Text style={styles.guardEmail}>{item.email || "No email"}</Text>
          <Text style={styles.lastLogin}>
            Last Login: {item.last_login ? new Date(item.last_login).toLocaleString() : "Never"}
          </Text>
        </View>
        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.actionBtn, styles.editBtn]}
            onPress={() =>
              router.push({
                pathname: `/admin/guards/edit/${item.id}`,
                params: { name: item.name, email: item.email },
              })
            }
            activeOpacity={0.7}
          >
            <Text style={styles.editBtnText}>Edit</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionBtn, styles.deactivateBtn]}
            onPress={() => handleDeactivate(item)}
            disabled={isWorking}
            activeOpacity={0.7}
          >
            {isWorking ? (
              <ActivityIndicator size="small" color="#991B1B" />
            ) : (
              <Text style={styles.deactivateBtnText}>Deactivate</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    );
  };

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
        <Text style={styles.headerTitle}>Guards</Text>
        <TouchableOpacity
          onPress={() => router.push("/admin/guards/add")}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Text style={styles.backText}>➕</Text>
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search by guard name or email..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor="#9CA3AF"
        />
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
            data={paginatedGuards}
            keyExtractor={(item) => item.id.toString()}
            renderItem={renderItem}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => fetchGuards(true)}
                colors={["#1D4ED8"]}
              />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyIcon}>👮</Text>
                <Text style={styles.emptyText}>No guards found.</Text>
              </View>
            }
          />

          {/* Pagination UI */}
          {filteredGuards.length > PAGE_SIZE && (
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
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
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
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  listContent: {
    padding: 16,
  },
  guardCard: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 18,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  cardInfo: {
    marginBottom: 12,
  },
  guardName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 4,
  },
  guardEmail: {
    fontSize: 13,
    color: "#6B7280",
    marginBottom: 8,
  },
  lastLogin: {
    fontSize: 11,
    color: "#9CA3AF",
    fontWeight: "500",
  },
  actions: {
    flexDirection: "row",
    justifyContent: "flex-end",
  },
  actionBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginLeft: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  editBtn: {
    backgroundColor: "#E5E7EB",
  },
  editBtnText: {
    color: "#374151",
    fontSize: 12,
    fontWeight: "700",
  },
  deactivateBtn: {
    backgroundColor: "#FEE2E2",
  },
  deactivateBtnText: {
    color: "#DC2626",
    fontSize: 12,
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
    width: "55%",
    marginBottom: 8,
  },
  skeletonLineSmall: {
    height: 12,
    backgroundColor: "#E5E7EB",
    borderRadius: 4,
    width: "35%",
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
