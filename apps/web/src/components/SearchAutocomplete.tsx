import { useState, useEffect, useRef, useId } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import { Cluster, Idea } from '@/types';
import { apiClient } from '@/services/api';

interface SearchResult {
  type: 'cluster' | 'idea';
  id: string;
  title: string;
  description: string;
  sentiment?: string;
  idea_count?: number;
}

export const SearchAutocomplete = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxId = useId();
  const navigate = useNavigate();

  // Debounced search
  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setIsOpen(false);
      setSelectedIndex(-1);
      return;
    }

    setIsLoading(true);
    const timer = setTimeout(async () => {
      try {
        const [clusterRes, ideaRes] = await Promise.all([
          apiClient.getClusters({ limit: 100 }),
          apiClient.searchIdeas(query, 5),
        ]);

        // Search clusters client-side over the fetched page
        const clusters: SearchResult[] = clusterRes.clusters
          .filter((c: Cluster) =>
            c.label.toLowerCase().includes(query.toLowerCase()) ||
            c.keywords.some((k: string) => k.toLowerCase().includes(query.toLowerCase()))
          )
          .slice(0, 5)
          .map((c: Cluster) => ({
            type: 'cluster' as const,
            id: c.id,
            title: c.label,
            description: c.keywords.slice(0, 3).join(', '),
            idea_count: c.idea_count,
          }));

        // Search ideas via API search endpoint
        const ideas: SearchResult[] = ideaRes.results.map((i: Idea) => ({
          type: 'idea' as const,
          id: i.id,
          title: i.problem_statement.substring(0, 80) + (i.problem_statement.length > 80 ? '...' : ''),
          description: i.domain || 'Idea',
          sentiment: i.sentiment,
        }));

        setResults([...clusters, ...ideas]);
        setIsOpen(true);
      } catch (error) {
        console.error('Search error:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    setSelectedIndex(-1);
  }, [query]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : prev));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      handleSelect(results[selectedIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  const handleSelect = (result: SearchResult) => {
    if (result.type === 'cluster') {
      navigate(`/clusters/${result.id}`);
    } else {
      // Navigate to cluster that contains this idea
      navigate(`/clusters?idea=${result.id}`);
    }
    setQuery('');
    setIsOpen(false);
    inputRef.current?.blur();
  };

  const getSentimentColor = (sentiment?: string) => {
    if (!sentiment) return 'text-slate-400';
    return sentiment === 'positive' ? 'text-green-400' : sentiment === 'negative' ? 'text-red-400' : 'text-slate-400';
  };

  return (
    <div ref={searchRef} className="relative w-full max-w-md" role="search">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" aria-hidden="true" />
        <input
          ref={inputRef}
          type="search"
          placeholder="Search clusters, ideas… (Ctrl + /)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          className="w-full pl-10 pr-10 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          aria-label="Search clusters and ideas"
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-expanded={isOpen}
          role="combobox"
          aria-activedescendant={selectedIndex >= 0 ? `search-result-${selectedIndex}` : undefined}
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setResults([]);
              setIsOpen(false);
              setSelectedIndex(-1);
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded"
            aria-label="Clear search query"
          >
            <XMarkIcon className="w-5 h-5" aria-hidden="true" />
          </button>
        )}
      </div>

      <AnimatePresence>
        {isOpen && query.length >= 2 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            id={listboxId}
            role="listbox"
            aria-label="Search results"
            aria-live="polite"
            className="absolute top-full mt-2 w-full bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-h-96 overflow-y-auto z-50"
          >
            {isLoading ? (
              <div className="px-4 py-3 text-slate-400 text-sm" role="status" aria-live="polite">
                Searching...
              </div>
            ) : results.length === 0 ? (
              <div className="px-4 py-3 text-slate-400 text-sm" role="status" aria-live="polite">
                No results found
              </div>
            ) : (
              <>
                {results.map((result, index) => (
                  <button
                    type="button"
                    key={`${result.type}-${result.id}`}
                    id={`search-result-${index}`}
                    onClick={() => handleSelect(result)}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`w-full text-left px-4 py-3 hover:bg-slate-700/50 transition-colors border-b border-slate-700/50 last:border-b-0 ${selectedIndex === index ? 'bg-slate-700/50' : ''
                      } focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500`}
                    role="option"
                    aria-selected={selectedIndex === index}
                    aria-label={`${result.type}: ${result.title}`}
                  >
                    <div className="flex items-start gap-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${result.type === 'cluster'
                          ? 'bg-primary-500/20 text-primary-400'
                          : 'bg-purple-500/20 text-purple-400'
                          }`}
                        aria-hidden="true"
                      >
                        {result.type === 'cluster' ? 'Cluster' : 'Idea'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-slate-200 font-medium truncate">{result.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <p className="text-slate-400 text-sm truncate">{result.description}</p>
                          {result.idea_count && (
                            <span className="text-slate-500 text-xs whitespace-nowrap">
                              {result.idea_count} ideas
                            </span>
                          )}
                          {result.sentiment && (
                            <span className={`text-xs font-medium ${getSentimentColor(result.sentiment)}`}>
                              {result.sentiment}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
