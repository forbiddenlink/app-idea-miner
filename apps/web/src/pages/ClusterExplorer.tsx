import {
  keepPreviousData,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { RotateCw, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import ClusterCard from "@/components/ClusterCard";
import DataFreshness from "@/components/DataFreshness";
import {
  EmptyClusterList,
  EmptySearchResults,
  ErrorState,
} from "@/components/EmptyStates";
import { ExportButton } from "@/components/ExportButton";
import {
  FilterChips,
  useFilterChips,
  type FilterChip,
} from "@/components/FilterChips";
import { FilterSidebar } from "@/components/FilterSidebar";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api";
import { Cluster } from "@/types";
import { useRefreshSettings } from "./Settings";

const validSortBy = new Set([
  "size",
  "quality",
  "sentiment",
  "trend",
  "created_at",
]);
const validOrder = new Set(["asc", "desc"]);

const parsePositiveInt = (value: string | null): number | undefined => {
  if (!value) return undefined;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
};

const parseNonNegativeInt = (value: string | null, fallback = 0): number => {
  const parsed = Number.parseInt(value || "", 10);
  if (!Number.isFinite(parsed) || parsed < 0) return fallback;
  return parsed;
};

export default function ClusterExplorer() {
  const { enabled: autoRefresh, interval: refreshInterval } =
    useRefreshSettings();
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(
    searchParams.get("search") || "",
  );

  // Get filter params from URL
  const sortByRaw = searchParams.get("sort_by");
  const orderRaw = searchParams.get("order");
  const sortBy = sortByRaw && validSortBy.has(sortByRaw) ? sortByRaw : "size";
  const order = orderRaw && validOrder.has(orderRaw) ? orderRaw : "desc";
  const minSize = parsePositiveInt(searchParams.get("min_size"));
  const activeSearch = searchParams.get("search")?.trim() || "";
  const limit = 20;
  const offset = parseNonNegativeInt(searchParams.get("offset"));

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await queryClient.invalidateQueries({ queryKey: ["clusters"] });
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const updateParam = (
    key: string,
    value: string | undefined,
    options: { resetOffset?: boolean } = {},
  ) => {
    const { resetOffset = true } = options;
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    if (resetOffset) {
      newParams.set("offset", "0");
    }
    setSearchParams(newParams);
  };

  const {
    data: clustersResponse,
    isLoading,
    isFetching,
    isPlaceholderData,
    error,
    dataUpdatedAt,
    isRefetching,
  } = useQuery({
    queryKey: ["clusters", sortBy, order, minSize, activeSearch, offset],
    queryFn: async () => {
      const res = await apiClient.getClusters({
        sort_by: sortBy,
        order: order as "asc" | "desc",
        min_size: minSize,
        q: activeSearch || undefined,
        limit,
        offset,
      });
      return res;
    },
    placeholderData: keepPreviousData,
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    updateParam("search", searchQuery || undefined);
  };

  const handleNextPage = () => {
    updateParam("offset", (offset + limit).toString(), { resetOffset: false });
  };

  const handlePrevPage = () => {
    updateParam("offset", Math.max(0, offset - limit).toString(), {
      resetOffset: false,
    });
  };

  const hasPrevPage = offset > 0;
  const clusters = clustersResponse?.clusters || [];
  const pagination = clustersResponse?.pagination;
  const hasNextPage = Boolean(pagination?.has_more);
  const showInitialLoading = isLoading && !clustersResponse;
  const showUpdating = isFetching && !showInitialLoading;

  useEffect(() => {
    setSearchQuery(activeSearch);
  }, [activeSearch]);

  const { buildChips } = useFilterChips();
  const activeFilters: FilterChip[] = buildChips(
    {
      sort_by: sortBy === "size" ? undefined : sortBy,
      order: order === "desc" ? undefined : order,
      min_size: minSize,
      search: searchParams.get("search"),
    },
    {
      sort_by: () => updateParam("sort_by", undefined),
      order: () => updateParam("order", undefined),
      min_size: () => updateParam("min_size", undefined),
      search: () => {
        setSearchQuery("");
        updateParam("search", undefined);
      },
    },
  );

  const clearAllFilters = () => {
    setSearchParams({});
    setSearchQuery("");
  };

  return (
    <div className="app-page">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="section-kicker">Clusters</p>
          <h1 className="mt-1 text-2xl sm:text-3xl font-bold">
            Explore Clusters
          </h1>
          <p className="mt-1 text-muted-foreground">
            Browse all opportunity clusters with advanced filtering and search
          </p>
        </div>
        <div className="flex items-center gap-3">
          {dataUpdatedAt > 0 && (
            <DataFreshness
              dataUpdatedAt={dataUpdatedAt}
              isRefetching={isRefetching}
            />
          )}
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RotateCw
              className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <ExportButton type="clusters" data={clusters} />
        </div>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="relative max-w-xl">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search clusters by keyword…"
          aria-label="Search clusters by keyword"
          className="field-control pl-9 pr-28"
        />
        {searchQuery && (
          <button
            type="button"
            className="focus-ring absolute right-16 top-1/2 -translate-y-1/2 rounded-lg px-2 py-1 text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground"
            onClick={() => {
              setSearchQuery("");
              updateParam("search", undefined);
            }}
          >
            Clear
          </button>
        )}
        <button
          type="submit"
          className="focus-ring absolute right-2 top-1/2 -translate-y-1/2 rounded-lg bg-primary px-2.5 py-1 text-xs font-semibold text-primary-foreground shadow-raised transition-colors hover:bg-primary/90"
        >
          Go
        </button>
      </form>

      {/* Main Content */}
      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar */}
        <aside className="w-full md:w-64 shrink-0">
          <FilterSidebar
            sortBy={sortBy}
            order={order}
            onSortChange={(value: string) => updateParam("sort_by", value)}
            onOrderChange={(value: string) => updateParam("order", value)}
            minSize={minSize}
            onMinSizeChange={(value: number | undefined) =>
              updateParam("min_size", value?.toString())
            }
          />
        </aside>

        {/* Cluster Grid */}
        <div className="flex-1 space-y-6">
          <FilterChips chips={activeFilters} onClearAll={clearAllFilters} />

          {showUpdating && (
            <output
              aria-live="polite"
              className="inline-flex items-center rounded-xl border border-border/70 bg-card px-3 py-1 text-xs font-medium text-muted-foreground"
            >
              Updating clusters…
            </output>
          )}

          {showInitialLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={`skeleton-cluster-${i}`}
                  className="card h-64 animate-pulse bg-muted/45"
                />
              ))}
            </div>
          )}

          {error && (
            <ErrorState
              error="Failed to load clusters. Please try again."
              onRetry={handleRefresh}
            />
          )}

          {clusters.length > 0 && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {clusters.map((cluster: Cluster) => (
                  <ClusterCard key={cluster.id} cluster={cluster} />
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between border-t border-border/70 pt-4">
                <Button
                  variant="outline"
                  onClick={handlePrevPage}
                  disabled={!hasPrevPage || isFetching}
                >
                  Previous
                </Button>

                <span className="text-sm text-muted-foreground">
                  Showing {offset + 1} - {offset + clusters.length}
                </span>

                <Button
                  variant="outline"
                  onClick={handleNextPage}
                  disabled={!hasNextPage || isPlaceholderData || isFetching}
                >
                  Next
                </Button>
              </div>
            </>
          )}

          {/* Empty State */}
          {clusters.length === 0 &&
            (activeSearch || minSize ? (
              <EmptySearchResults
                onClearSearch={() => {
                  setSearchParams({});
                  setSearchQuery("");
                }}
              />
            ) : (
              <EmptyClusterList />
            ))}
        </div>
      </div>
    </div>
  );
}
