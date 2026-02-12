// Advanced Search with Autocomplete
// Real-time suggestions, recent searches, keyboard navigation

import { useState, useEffect, useRef } from 'react';
import { MagnifyingGlassIcon, ClockIcon, FireIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'router-dom';

interface SearchResult {
  type: 'cluster' | 'idea' | 'keyword';
  id: string;
  label: string;
  description?: string;
  count?: number;
}

interface AdvancedSearchProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  showSuggestions?: boolean;
}

export const AdvancedSearch = ({
  onSearch,
  placeholder = 'Search clusters, ideas, keywords...',
  showSuggestions = true,
}: AdvancedSearchProps) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [popularKeywords, setPopularKeywords] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Load recent searches from localStorage
  useEffect(() => {
    const recent = JSON.parse(localStorage.getItem('recentSearches') || '[]');
    setRecentSearches(recent.slice(0, 5));

    // TODO: Fetch popular keywords from API
    setPopularKeywords(['budget tracking', 'fitness app', 'productivity', 'AI assistant', 'health']);
  }, []);

  // Fetch suggestions as user types (debounced)
  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        // TODO: Replace with actual API call
        const mockSuggestions: SearchResult[] = [
          { type: 'cluster', id: '1', label: 'Budget Tracking Apps', count: 12 },
          { type: 'keyword', id: 'budget', label: 'budget', count: 24 },
          { type: 'idea', id: '2', label: 'AI-powered budget tracking with bank sync', description: 'Positive sentiment' },
        ];
        setSuggestions(mockSuggestions.filter(s =>
          s.label.toLowerCase().includes(query.toLowerCase())
        ));
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev =>
            Math.min(prev + 1, suggestions.length + recentSearches.length + popularKeywords.length - 1)
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, -1));
          break;
        case 'Enter':
          e.preventDefault();
          if (selectedIndex >= 0) {
            handleSelect(selectedIndex);
          } else {
            handleSubmit();
          }
          break;
        case 'Escape':
          setIsOpen(false);
          setSelectedIndex(-1);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, suggestions, recentSearches, popularKeywords]);

  const handleSubmit = () => {
    if (!query.trim()) return;

    // Save to recent searches
    const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 10);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));

    onSearch(query);
    setIsOpen(false);
  };

  const handleSelect = (index: number) => {
    const allItems = [
      ...suggestions,
      ...recentSearches.map(s => ({ type: 'recent' as const, id: s, label: s })),
      ...popularKeywords.map(k => ({ type: 'popular' as const, id: k, label: k })),
    ];

    const item = allItems[index];
    if (!item) return;

    if (item.type === 'cluster') {
      navigate(`/clusters/${item.id}`);
    } else {
      setQuery(item.label);
      onSearch(item.label);
    }

    setIsOpen(false);
  };

  const renderSuggestion = (item: SearchResult | { type: 'recent' | 'popular'; label: string }, index: number) => {
    const isSelected = index === selectedIndex;

    return (
      <button
        key={`${item.type}-${item.label}`}
        onClick={() => handleSelect(index)}
        className={`
          w-full px-4 py-2 text-left hover:bg-slate-700 transition-colors
          ${isSelected ? 'bg-slate-700' : ''}
          flex items-center gap-3
        `}
      >
        {item.type === 'cluster' && <div className="w-2 h-2 bg-indigo-500 rounded-full" />}
        {item.type === 'recent' && <ClockIcon className="h-4 w-4 text-slate-400" />}
        {item.type === 'popular' && <FireIcon className="h-4 w-4 text-amber-500" />}
        {item.type === 'keyword' && <MagnifyingGlassIcon className="h-4 w-4 text-slate-400" />}

        <div className="flex-1">
          <div className="text-slate-200">{item.label}</div>
          {(item as SearchResult).description && (
            <div className="text-xs text-slate-400">{(item as SearchResult).description}</div>
          )}
        </div>

        {(item as SearchResult).count && (
          <span className="text-xs text-slate-400">{(item as SearchResult).count} results</span>
        )}
      </button>
    );
  };

  return (
    <div className="relative">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          placeholder={placeholder}
          className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg
                     text-slate-200 placeholder-slate-400
                     focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          aria-label="Search"
          aria-autocomplete="list"
          aria-controls="search-suggestions"
          aria-expanded={isOpen}
        />
        {query && (
          <button
            onClick={() => setQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
            aria-label="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      {showSuggestions && isOpen && (
        <div
          id="search-suggestions"
          className="absolute top-full mt-2 w-full bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto"
          role="listbox"
        >
          {suggestions.length > 0 && (
            <div>
              <div className="px-4 py-2 text-xs uppercase text-slate-400 font-semibold">Suggestions</div>
              {suggestions.map((item, i) => renderSuggestion(item, i))}
            </div>
          )}

          {recentSearches.length > 0 && query.length === 0 && (
            <div>
              <div className="px-4 py-2 text-xs uppercase text-slate-400 font-semibold">Recent Searches</div>
              {recentSearches.map((search, i) => renderSuggestion({ type: 'recent', label: search }, suggestions.length + i))}
            </div>
          )}

          {popularKeywords.length > 0 && query.length === 0 && (
            <div>
              <div className="px-4 py-2 text-xs uppercase text-slate-400 font-semibold">Popular Keywords</div>
              {popularKeywords.map((keyword, i) =>
                renderSuggestion(
                  { type: 'popular', label: keyword },
                  suggestions.length + recentSearches.length + i
                )
              )}
            </div>
          )}

          {query.length > 0 && suggestions.length === 0 && (
            <div className="px-4 py-8 text-center text-slate-400">
              No results found for "{query}"
            </div>
          )}
        </div>
      )}
    </div>
  );
};
