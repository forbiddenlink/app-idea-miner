import { useState, useEffect, useRef, useId } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import { Cluster, Idea } from '@/types';
import { apiClient } from '@/services/api';
import { cn } from '@/utils/cn';

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

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
      navigate(`/clusters?idea=${result.id}`);
    }
    setQuery('');
    setIsOpen(false);
    inputRef.current?.blur();
  };

  const getSentimentColor = (sentiment?: string) => {
    if (!sentiment) return 'text-muted-foreground';
    return sentiment === 'positive' ? 'text-success' : sentiment === 'negative' ? 'text-destructive' : 'text-muted-foreground';
  };

  return (
    <div ref={searchRef} className="relative w-full max-w-md" role="search">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
        <input
          ref={inputRef}
          type="search"
          placeholder="Search clusters, ideas…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          className="w-full rounded-md border border-border bg-background py-2 pl-9 pr-9 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
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
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            aria-label="Clear search query"
          >
            <XMarkIcon className="h-4 w-4" aria-hidden="true" />
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
            className="absolute top-full z-50 mt-2 max-h-96 w-full overflow-y-auto rounded-lg border border-border bg-popover shadow-lg"
          >
            {isLoading ? (
              <div className="px-4 py-3 text-sm text-muted-foreground" role="status" aria-live="polite">
                Searching...
              </div>
            ) : results.length === 0 ? (
              <div className="px-4 py-3 text-sm text-muted-foreground" role="status" aria-live="polite">
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
                    className={cn(
                      "w-full border-b border-border/50 px-4 py-3 text-left transition-colors last:border-b-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                      selectedIndex === index ? 'bg-muted' : 'hover:bg-muted/50'
                    )}
                    role="option"
                    aria-selected={selectedIndex === index}
                    aria-label={`${result.type}: ${result.title}`}
                  >
                    <div className="flex items-start gap-3">
                      <span
                        className={cn(
                          "rounded px-2 py-0.5 text-xs font-medium",
                          result.type === 'cluster'
                            ? 'bg-primary/10 text-primary'
                            : 'bg-secondary text-secondary-foreground'
                        )}
                        aria-hidden="true"
                      >
                        {result.type === 'cluster' ? 'Cluster' : 'Idea'}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium text-foreground">{result.title}</p>
                        <div className="mt-1 flex items-center gap-2">
                          <p className="truncate text-sm text-muted-foreground">{result.description}</p>
                          {result.idea_count && (
                            <span className="whitespace-nowrap text-xs text-muted-foreground">
                              {result.idea_count} ideas
                            </span>
                          )}
                          {result.sentiment && (
                            <span className={cn("text-xs font-medium", getSentimentColor(result.sentiment))}>
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
