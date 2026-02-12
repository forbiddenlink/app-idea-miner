import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Download, Filter, Search, Sparkles, X } from 'lucide-react';

import { Idea, IdeaQueryParams } from '@/types';
import { apiClient as api } from '../services/api';
import { IdeaCard } from '../components/IdeaCard';
import { IdeaCardSkeleton as LoadingSkeleton } from '../components/LoadingSkeleton';
import { useDebounce } from '@/hooks/useDebounce';
import { Button } from '@/components/ui/button';

const sentimentOptions = ['positive', 'neutral', 'negative'];
const domainOptions = [
  'productivity',
  'health',
  'finance',
  'social',
  'education',
  'entertainment',
  'other',
];

type SortBy = 'quality' | 'date' | 'sentiment';
type SortOrder = 'asc' | 'desc';

export default function Ideas() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(true);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  const limit = 20;
  const activeSearch = searchParams.get('search')?.trim() || '';
  const selectedSentiment = searchParams.get('sentiment') || '';
  const selectedDomain = searchParams.get('domain') || '';
  const minQuality = searchParams.get('min_quality')
    ? parseFloat(searchParams.get('min_quality')!)
    : 0;
  const sortByRaw = searchParams.get('sort_by');
  const sortOrderRaw = searchParams.get('order');
  const sortBy: SortBy =
    sortByRaw === 'date' || sortByRaw === 'sentiment' || sortByRaw === 'quality'
      ? sortByRaw
      : 'quality';
  const sortOrder: SortOrder = sortOrderRaw === 'asc' || sortOrderRaw === 'desc' ? sortOrderRaw : 'desc';
  const offset = parseInt(searchParams.get('offset') || '0', 10);

  const [searchQuery, setSearchQuery] = useState(activeSearch);
  const debouncedSearch = useDebounce(searchQuery, 350);

  const updateParam = useCallback((
    key: string,
    value: string | undefined,
    options: { resetOffset?: boolean } = {}
  ) => {
    const { resetOffset = true } = options;
    const next = new URLSearchParams(searchParams);
    if (value && value.trim()) {
      next.set(key, value.trim());
    } else {
      next.delete(key);
    }
    if (resetOffset) {
      next.set('offset', '0');
    }
    setSearchParams(next);
  }, [searchParams, setSearchParams]);

  const clearAllFilters = () => {
    setSearchParams({});
    setSearchQuery('');
  };

  useEffect(() => {
    setSearchQuery(activeSearch);
  }, [activeSearch]);

  useEffect(() => {
    if (debouncedSearch === activeSearch) return;
    updateParam('search', debouncedSearch || undefined);
  }, [debouncedSearch, activeSearch, updateParam]);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (!exportMenuRef.current?.contains(event.target as Node)) {
        setExportMenuOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setExportMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const {
    data: ideasResponse,
    isLoading,
    isFetching,
    isPlaceholderData,
    error,
  } = useQuery({
    queryKey: [
      'ideas',
      activeSearch,
      selectedSentiment,
      selectedDomain,
      minQuality,
      sortBy,
      sortOrder,
      offset,
      limit,
    ],
    queryFn: async () => {
      const params: IdeaQueryParams = {
        limit,
        offset,
        sort_by: sortBy,
        order: sortOrder,
      };
      if (activeSearch) params.q = activeSearch;
      if (selectedSentiment) params.sentiment = selectedSentiment;
      if (selectedDomain) params.domain = selectedDomain;
      if (minQuality > 0) params.min_quality = minQuality;

      return await api.getIdeas(params);
    },
    placeholderData: keepPreviousData,
    staleTime: 60000,
  });

  const ideas = useMemo(() => ideasResponse?.ideas ?? [], [ideasResponse]);
  const totalIdeas = ideasResponse?.pagination?.total ?? 0;
  const hasPrevPage = offset > 0;
  const hasNextPage = Boolean(ideasResponse?.pagination?.has_more);
  const startItem = ideas.length ? offset + 1 : 0;
  const endItem = offset + ideas.length;

  const hasActiveFilters =
    !!activeSearch ||
    !!selectedSentiment ||
    !!selectedDomain ||
    minQuality > 0 ||
    sortBy !== 'quality' ||
    sortOrder !== 'desc';
  const showInitialLoading = isLoading && !ideasResponse;
  const showUpdating = isFetching && !showInitialLoading;

  const handleExport = (format: 'json' | 'csv') => {
    if (!ideas.length) return;
    setExportMenuOpen(false);

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(ideas, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ideas-page-${Math.floor(offset / limit) + 1}-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }

    const headers = ['Problem Statement', 'Sentiment', 'Quality Score', 'Domain', 'Date'];
    const rows = ideas.map((idea: Idea) => [
      idea.problem_statement || '',
      idea.sentiment || '',
      idea.quality_score || 0,
      idea.domain || '',
      new Date(idea.extracted_at).toLocaleDateString(),
    ]);

    const csv = [
      headers.join(','),
      ...rows.map((row: (string | number)[]) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ideas-page-${Math.floor(offset / limit) + 1}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container py-8 space-y-8 min-h-screen">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ideas Browser</h1>
          <p className="text-muted-foreground">Explore extracted app ideas with server-side search and filters</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setShowFilters((prev) => !prev)}>
            <Filter className="mr-2 h-4 w-4" />
            {showFilters ? 'Hide' : 'Show'} Filters
          </Button>

          <div ref={exportMenuRef} className="relative">
            <Button
              type="button"
              variant="outline"
              onClick={() => setExportMenuOpen((open) => !open)}
              aria-expanded={exportMenuOpen}
              aria-controls="ideas-export-menu"
              aria-haspopup="menu"
            >
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <div
              id="ideas-export-menu"
              role="menu"
              className={`absolute right-0 z-20 mt-2 w-40 rounded-md border bg-popover text-popover-foreground shadow-md transition-all duration-150 ${
                exportMenuOpen ? 'visible opacity-100' : 'invisible opacity-0'
              }`}
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => handleExport('json')}
                className="w-full px-4 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground transition-colors rounded-t-md"
              >
                Export Page (JSON)
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => handleExport('csv')}
                className="w-full px-4 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground transition-colors rounded-b-md"
              >
                Export Page (CSV)
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-6 xl:flex-row xl:items-start">
        {showFilters && (
          <motion.aside
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-full xl:w-72 xl:sticky xl:top-4"
          >
            <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Filters</h3>
                <Button variant="ghost" size="sm" className="h-auto p-0" onClick={clearAllFilters}>
                  Clear
                </Button>
              </div>

              <div className="space-y-2">
                <label
                  htmlFor="search-input"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Search
                </label>
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    id="search-input"
                    type="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search ideas..."
                    className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 pl-9 pr-10 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={() => {
                        setSearchQuery('');
                        updateParam('search', undefined);
                      }}
                      className="absolute right-2 top-1.5 rounded p-1 text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      aria-label="Clear search"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="sentiment-select" className="text-sm font-medium leading-none">
                  Sentiment
                </label>
                <select
                  id="sentiment-select"
                  value={selectedSentiment}
                  onChange={(e) => updateParam('sentiment', e.target.value || undefined)}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">All Sentiments</option>
                  {sentimentOptions.map((sentiment) => (
                    <option key={sentiment} value={sentiment}>
                      {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label htmlFor="domain-select" className="text-sm font-medium leading-none">
                  Domain
                </label>
                <select
                  id="domain-select"
                  value={selectedDomain}
                  onChange={(e) => updateParam('domain', e.target.value || undefined)}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">All Domains</option>
                  {domainOptions.map((domain) => (
                    <option key={domain} value={domain}>
                      {domain.charAt(0).toUpperCase() + domain.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <label htmlFor="quality-range" className="text-sm font-medium leading-none">
                    Min Quality
                  </label>
                  <span className="text-xs text-muted-foreground">{minQuality.toFixed(1)}</span>
                </div>
                <input
                  id="quality-range"
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={minQuality}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value);
                    updateParam('min_quality', value > 0 ? value.toString() : undefined);
                  }}
                  className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0.0</span>
                  <span>1.0</span>
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="sort-select" className="text-sm font-medium leading-none">
                  Sort By
                </label>
                <select
                  id="sort-select"
                  value={sortBy}
                  onChange={(e) => updateParam('sort_by', e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="quality">Quality Score</option>
                  <option value="date">Date (Newest by default)</option>
                  <option value="sentiment">Sentiment Score</option>
                </select>
              </div>

              <div className="space-y-2">
                <label htmlFor="order-select" className="text-sm font-medium leading-none">
                  Sort Order
                </label>
                <select
                  id="order-select"
                  value={sortOrder}
                  onChange={(e) => updateParam('order', e.target.value as SortOrder)}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
          </motion.aside>
        )}

        <div className="flex-1 space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground mb-4">
            <div className="flex items-center gap-1.5 bg-muted/50 px-2.5 py-1 rounded-md">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              <span className="font-medium text-foreground">
                {startItem}-{endItem}
              </span>
              <span>of {totalIdeas} ideas</span>
            </div>
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={clearAllFilters}>
                <X className="mr-1 h-3 w-3" />
                Clear Filters
              </Button>
            )}
          </div>

          {showUpdating && (
            <div
              data-testid="ideas-updating-indicator"
              className="inline-flex items-center rounded-md border bg-muted/40 px-3 py-1 text-xs text-muted-foreground"
              role="status"
              aria-live="polite"
            >
              Updating results...
            </div>
          )}

          {showInitialLoading ? (
            <div className="grid grid-cols-1 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <LoadingSkeleton key={i} />
              ))}
            </div>
          ) : error ? (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-8 text-center text-destructive">
              <p className="font-medium mb-1">Failed to load ideas</p>
              <p className="text-sm opacity-90">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
          ) : ideas.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="rounded-xl border bg-card text-card-foreground shadow-sm p-12 text-center"
            >
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <Search className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="mt-4 text-lg font-semibold">No ideas found</h3>
              <p className="mt-2 text-muted-foreground">
                Try adjusting your filters or search query to find what you are looking for.
              </p>
              <Button variant="outline" className="mt-4" onClick={clearAllFilters}>
                Clear Filters
              </Button>
            </motion.div>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4">
                {ideas.map((idea: Idea) => (
                  <IdeaCard key={idea.id} idea={idea} />
                ))}
              </div>

              <div className="flex items-center justify-between border-t pt-4">
                <Button
                  variant="outline"
                  onClick={() => updateParam('offset', Math.max(0, offset - limit).toString(), { resetOffset: false })}
                  disabled={!hasPrevPage || isFetching}
                >
                  Previous
                </Button>

                <span className="text-sm text-muted-foreground">
                  Page {Math.floor(offset / limit) + 1}
                </span>

                <Button
                  variant="outline"
                  onClick={() => updateParam('offset', (offset + limit).toString(), { resetOffset: false })}
                  disabled={!hasNextPage || isPlaceholderData || isFetching}
                >
                  Next
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
