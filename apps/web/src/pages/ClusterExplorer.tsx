import { useEffect, useState } from 'react';
import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Search, RotateCw } from 'lucide-react';

import { apiClient } from '@/services/api';
import { Cluster } from '@/types';
import ClusterCard from '@/components/ClusterCard';
import { FilterSidebar } from '@/components/FilterSidebar';
import { EmptyClusterList, EmptySearchResults } from '@/components/EmptyStates';
import { ExportButton } from '@/components/ExportButton';
import { FilterChips, useFilterChips, type FilterChip } from '@/components/FilterChips';
import { Button } from '@/components/ui/button';

export default function ClusterExplorer() {
  const queryClient = useQueryClient()
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');

  // Get filter params from URL
  const sortBy = searchParams.get('sort_by') || 'size';
  const order = searchParams.get('order') || 'desc';
  const minSize = searchParams.get('min_size') ? parseInt(searchParams.get('min_size')!) : undefined;
  const activeSearch = searchParams.get('search')?.trim() || '';
  const limit = 20;
  const offset = parseInt(searchParams.get('offset') || '0');

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await queryClient.invalidateQueries({ queryKey: ['clusters'] })
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  const updateParam = (
    key: string,
    value: string | undefined,
    options: { resetOffset?: boolean } = {}
  ) => {
    const { resetOffset = true } = options
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    if (resetOffset) {
      newParams.set('offset', '0');
    }
    setSearchParams(newParams);
  };

  const {
    data: clusters,
    isLoading,
    isFetching,
    isPlaceholderData,
    error,
  } = useQuery({
    queryKey: ['clusters', sortBy, order, minSize, activeSearch, offset],
    queryFn: async () => {
      const res = await apiClient.getClusters({
        sort_by: sortBy,
        order: order as 'asc' | 'desc',
        min_size: minSize,
        q: activeSearch || undefined,
        limit,
        offset,
      });
      return res.clusters;
    },
    placeholderData: keepPreviousData,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    updateParam('search', searchQuery || undefined);
  };

  const handleNextPage = () => {
    updateParam('offset', (offset + limit).toString(), { resetOffset: false });
  };

  const handlePrevPage = () => {
    updateParam('offset', Math.max(0, offset - limit).toString(), { resetOffset: false });
  };

  const hasPrevPage = offset > 0;
  const hasNextPage = Boolean(clusters && clusters.length === limit);
  const showInitialLoading = isLoading && !clusters;
  const showUpdating = isFetching && !showInitialLoading;

  useEffect(() => {
    setSearchQuery(activeSearch);
  }, [activeSearch]);

  const { buildChips } = useFilterChips()
  const activeFilters: FilterChip[] = buildChips(
    {
      sort_by: sortBy !== 'size' ? sortBy : undefined,
      order: order !== 'desc' ? order : undefined,
      min_size: minSize,
      search: searchParams.get('search'),
    },
    {
      sort_by: () => updateParam('sort_by', undefined),
      order: () => updateParam('order', undefined),
      min_size: () => updateParam('min_size', undefined),
      search: () => {
        setSearchQuery('')
        updateParam('search', undefined)
      },
    }
  )

  const clearAllFilters = () => {
    setSearchParams({})
    setSearchQuery('')
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Explore Clusters</h1>
          <p className="text-muted-foreground">
            Browse all opportunity clusters with advanced filtering and search
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RotateCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <ExportButton type="clusters" data={clusters} />
        </div>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="relative max-w-lg">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search clusters by keyword..."
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 pl-9 pr-28 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        />
        {searchQuery && (
          <button
            type="button"
            className="absolute right-16 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            onClick={() => {
              setSearchQuery('')
              updateParam('search', undefined)
            }}
          >
            Clear
          </button>
        )}
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
            onSortChange={(value: string) => updateParam('sort_by', value)}
            onOrderChange={(value: string) => updateParam('order', value)}
            minSize={minSize}
            onMinSizeChange={(value: number | undefined) => updateParam('min_size', value?.toString())}
          />
        </aside>

        {/* Cluster Grid */}
        <div className="flex-1 space-y-6">
          <FilterChips chips={activeFilters} onClearAll={clearAllFilters} />

          {showUpdating && (
            <div className="inline-flex items-center rounded-md border bg-muted/40 px-3 py-1 text-xs text-muted-foreground">
              Updating clusters...
            </div>
          )}

          {showInitialLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-64 rounded-xl border bg-muted/50 animate-pulse" />
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-destructive">
              Failed to load clusters. Please try again.
            </div>
          )}

          {clusters && clusters.length > 0 && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {clusters.map((cluster: Cluster) => (
                  <ClusterCard key={cluster.id} cluster={cluster} />
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between border-t pt-4">
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
          {clusters && clusters.length === 0 && (
            activeSearch || minSize ? (
              <EmptySearchResults
                onClearSearch={() => {
                  setSearchParams({});
                  setSearchQuery('');
                }}
              />
            ) : (
              <EmptyClusterList />
            )
          )}
        </div>
      </div>
    </div>
  );
}
