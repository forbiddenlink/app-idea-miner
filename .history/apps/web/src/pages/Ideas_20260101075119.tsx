import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { api } from '../services/api';
import IdeaCard from '../components/IdeaCard';
import LoadingSkeleton from '../components/LoadingSkeleton';
import { useDebounce } from '../hooks/useDebounce';

const sentimentOptions = ['positive', 'neutral', 'negative'];
const domainOptions = ['productivity', 'health', 'finance', 'social', 'education', 'entertainment', 'other'];

export default function Ideas() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSentiment, setSelectedSentiment] = useState<string>('');
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [minQuality, setMinQuality] = useState<number>(0);
  const [sortBy, setSortBy] = useState<'quality' | 'date' | 'sentiment'>('quality');
  const [showFilters, setShowFilters] = useState(true);

  const debouncedSearch = useDebounce(searchQuery, 300);

  // Fetch all ideas
  const { data: ideasData, isLoading, error } = useQuery({
    queryKey: ['ideas', selectedSentiment, selectedDomain],
    queryFn: async () => {
      const params: any = {};
      if (selectedSentiment) params.sentiment = selectedSentiment;
      if (selectedDomain) params.domain = selectedDomain;

      const response = await api.get('/ideas', { params });
      return response.data.ideas || [];
    },
    staleTime: 60000,
  });

  // Client-side filtering and sorting
  const filteredIdeas = useMemo(() => {
    if (!ideasData) return [];

    let filtered = [...ideasData];

    // Search filter
    if (debouncedSearch) {
      const query = debouncedSearch.toLowerCase();
      filtered = filtered.filter((idea: any) =>
        idea.problem_statement?.toLowerCase().includes(query) ||
        idea.context?.toLowerCase().includes(query)
      );
    }

    // Quality filter
    if (minQuality > 0) {
      filtered = filtered.filter((idea: any) => idea.quality_score >= minQuality);
    }

    // Sort
    filtered.sort((a: any, b: any) => {
      switch (sortBy) {
        case 'quality':
          return (b.quality_score || 0) - (a.quality_score || 0);
        case 'date':
          return new Date(b.extracted_at).getTime() - new Date(a.extracted_at).getTime();
        case 'sentiment':
          return (b.sentiment_score || 0) - (a.sentiment_score || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [ideasData, debouncedSearch, minQuality, sortBy]);

  // Export functionality
  const handleExport = (format: 'json' | 'csv') => {
    if (!filteredIdeas.length) return;

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(filteredIdeas, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ideas-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      // CSV export
      const headers = ['Problem Statement', 'Sentiment', 'Quality Score', 'Domain', 'Date'];
      const rows = filteredIdeas.map((idea: any) => [
        idea.problem_statement || '',
        idea.sentiment || '',
        idea.quality_score || 0,
        idea.domain || '',
        new Date(idea.extracted_at).toLocaleDateString(),
      ]);

      const csv = [
        headers.join(','),
        ...rows.map((row: any[]) => row.map((cell: any) => `"${cell}"`).join(',')),
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ideas-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Ideas Browser
            </h1>
            <p className="text-slate-400">
              Explore all extracted app ideas with advanced filtering
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 transition-all duration-200 flex items-center gap-2"
            >
              <FunnelIcon className="w-5 h-5" />
              {showFilters ? 'Hide' : 'Show'} Filters
            </button>
            <div className="relative group">
              <button className="px-4 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 transition-all duration-200 flex items-center gap-2">
                <ArrowDownTrayIcon className="w-5 h-5" />
                Export
              </button>
              <div className="absolute right-0 mt-2 w-32 bg-slate-800 border border-slate-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                <button
                  onClick={() => handleExport('json')}
                  className="w-full px-4 py-2 text-left hover:bg-slate-700 rounded-t-lg transition-colors"
                >
                  JSON
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full px-4 py-2 text-left hover:bg-slate-700 rounded-b-lg transition-colors"
                >
                  CSV
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-slate-400">
          <span className="flex items-center gap-2">
            <SparklesIcon className="w-4 h-4 text-indigo-400" />
            {filteredIdeas.length} ideas found
          </span>
          {debouncedSearch && (
            <span>• Searching for "{debouncedSearch}"</span>
          )}
          {selectedSentiment && (
            <span>• Sentiment: {selectedSentiment}</span>
          )}
          {selectedDomain && (
            <span>• Domain: {selectedDomain}</span>
          )}
        </div>
      </motion.div>

      <div className="flex gap-6">
        {/* Filters Sidebar */}
        {showFilters && (
          <motion.aside
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-64 flex-shrink-0"
          >
            <div className="card sticky top-8 space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  Filters
                </h3>

                {/* Search */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Search
                  </label>
                  <div className="relative">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search ideas..."
                      className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                    />
                  </div>
                </div>

                {/* Sentiment Filter */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Sentiment
                  </label>
                  <select
                    value={selectedSentiment}
                    onChange={(e) => setSelectedSentiment(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  >
                    <option value="">All</option>
                    {sentimentOptions.map((sentiment) => (
                      <option key={sentiment} value={sentiment}>
                        {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Domain Filter */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Domain
                  </label>
                  <select
                    value={selectedDomain}
                    onChange={(e) => setSelectedDomain(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  >
                    <option value="">All</option>
                    {domainOptions.map((domain) => (
                      <option key={domain} value={domain}>
                        {domain.charAt(0).toUpperCase() + domain.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Quality Filter */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Min Quality Score: {minQuality.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={minQuality}
                    onChange={(e) => setMinQuality(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>0.0</span>
                    <span>1.0</span>
                  </div>
                </div>

                {/* Sort By */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Sort By
                  </label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                  >
                    <option value="quality">Quality Score</option>
                    <option value="date">Date (Newest)</option>
                    <option value="sentiment">Sentiment Score</option>
                  </select>
                </div>

                {/* Clear Filters */}
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedSentiment('');
                    setSelectedDomain('');
                    setMinQuality(0);
                    setSortBy('quality');
                  }}
                  className="w-full mt-4 px-4 py-2 text-sm bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 rounded-lg transition-all duration-200"
                >
                  Clear All Filters
                </button>
              </div>
            </div>
          </motion.aside>
        )}

        {/* Ideas Grid */}
        <div className="flex-1">
          {isLoading ? (
            <div className="grid grid-cols-1 gap-4">
              {[...Array(6)].map((_, i) => (
                <LoadingSkeleton key={i} type="idea" />
              ))}
            </div>
          ) : error ? (
            <div className="card text-center py-12">
              <p className="text-red-400 mb-2">Failed to load ideas</p>
              <p className="text-slate-400 text-sm">
                {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          ) : filteredIdeas.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="card text-center py-12"
            >
              <SparklesIcon className="w-16 h-16 mx-auto mb-4 text-slate-600" />
              <h3 className="text-xl font-semibold mb-2">No ideas found</h3>
              <p className="text-slate-400">
                Try adjusting your filters or search query
              </p>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid grid-cols-1 gap-4"
            >
              {filteredIdeas.map((idea: any, index: number) => (
                <motion.div
                  key={idea.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <IdeaCard idea={idea} />
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
