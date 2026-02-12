import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { apiClient } from '@/services/api';
import { ClusterCard } from '@/components/ClusterCard';
import { FilterSidebar } from '@/components/FilterSidebar';

export const ClusterExplorer: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');

  // Get filter params from URL
  const sortBy = searchParams.get('sort_by') || 'size';
  const order = searchParams.get('order') || 'desc';
  const minSize = searchParams.get('min_size') ? parseInt(searchParams.get('min_size')!) : undefined;
  const limit = 20;
  const offset = parseInt(searchParams.get('offset') || '0');

  // Update URL params helper
  const updateParam = (key: string, value: string | undefined) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    newParams.set('offset', '0'); // Reset pagination on filter change
    setSearchParams(newParams);
  };

  // Fetch clusters with filters
  const { data: clusters, isLoading, error } = useQuery({
    queryKey: ['clusters', sortBy, order, minSize, offset],
    queryFn: () =>
      apiClient.getClusters({
        sort_by: sortBy,
        order: order as 'asc' | 'desc',
        min_size: minSize,
        limit,
        offset,
      }),
  });

  // Handle search submit
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    updateParam('search', searchQuery || undefined);
  };

  // Pagination handlers
  const handleNextPage = () => {
    updateParam('offset', (offset + limit).toString());
  };

  const handlePrevPage = () => {
    updateParam('offset', Math.max(0, offset - limit).toString());
  };

  const hasPrevPage = offset > 0;
  const hasNextPage = clusters && clusters.length === limit;

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">Explore Clusters</h1>
        <p className="text-slate-400">
          Browse all opportunity clusters with advanced filtering and search
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search clusters by keyword..."
            className="w-full bg-slate-800 text-white rounded-lg pl-12 pr-4 py-3 border border-slate-700 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          />
        </div>
      </form>

      {/* Main Content */}
      <div className="flex gap-8">
        {/* Sidebar */}
        <FilterSidebar
          sortBy={sortBy}
          order={order}
          onSortChange={(value) => updateParam('sort_by', value)}
          onOrderChange={(value) => updateParam('order', value)}
          minSize={minSize}
          onMinSizeChange={(value) => updateParam('min_size', value?.toString())}
        />

        {/* Cluster Grid */}
        <div className="flex-1">
          {/* Loading State */}
          {isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="card animate-pulse h-64"
                >
                  <div className="h-6 bg-slate-700 rounded mb-4 w-3/4"></div>
                  <div className="h-4 bg-slate-700 rounded mb-2 w-full"></div>
                  <div className="h-4 bg-slate-700 rounded mb-4 w-5/6"></div>
                  <div className="flex gap-2 mb-4">
                    <div className="h-6 bg-slate-700 rounded w-16"></div>
                    <div className="h-6 bg-slate-700 rounded w-16"></div>
                    <div className="h-6 bg-slate-700 rounded w-16"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="card bg-danger-500/10 border border-danger-500/20">
              <p className="text-danger-400">
                Failed to load clusters. Please try again.
              </p>
            </div>
          )}

          {/* Clusters Grid */}
          {clusters && clusters.length > 0 && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {clusters.map((cluster: any) => (
                  <ClusterCard key={cluster.id} cluster={cluster} />
                ))}
              </div>

              {/* Pagination */}
              <div className="flex justify-between items-center">
                <button
                  onClick={handlePrevPage}
                  disabled={!hasPrevPage}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    hasPrevPage
                      ? 'bg-primary-500 text-white hover:bg-primary-600'
                      : 'bg-slate-700 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  Previous
                </button>

                <span className="text-slate-400">
                  Showing {offset + 1} - {offset + clusters.length}
                </span>

                <button
                  onClick={handleNextPage}
                  disabled={!hasNextPage}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    hasNextPage
                      ? 'bg-primary-500 text-white hover:bg-primary-600'
                      : 'bg-slate-700 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  Next
                </button>
              </div>
            </>
          )}

          {/* Empty State */}
          {clusters && clusters.length === 0 && (
            <div className="card text-center py-12">
              <p className="text-slate-400 text-lg">
                No clusters found matching your filters.
              </p>
              <button
                onClick={() => {
                  setSearchParams({});
                  setSearchQuery('');
                }}
                className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              >
                Clear All Filters
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
