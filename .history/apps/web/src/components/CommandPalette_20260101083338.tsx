// Command Palette Component
// Universal search with Cmd+K shortcut (Cmd/Ctrl+K)

import { useState, useEffect, useCallback, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, ClockIcon, StarIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  type: 'cluster' | 'idea' | 'page' | 'action';
  action: () => void;
  icon?: React.ComponentType<any>;
  keywords?: string[];
}

export const CommandPalette = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const navigate = useNavigate();

  // Fetch data for search
  const { data: clusters } = useQuery({
    queryKey: ['clusters', { limit: 50 }],
    queryFn: () => apiClient.getClusters({ limit: 50 }),
    enabled: isOpen,
  });

  const { data: ideas } = useQuery({
    queryKey: ['ideas'],
    queryFn: async () => {
      const response = await apiClient.getIdeas();
      return response.ideas || [];
    },
    enabled: isOpen,
  });

  // Load recent searches
  useEffect(() => {
    const stored = localStorage.getItem('app-idea-miner-recent-searches');
    if (stored) {
      try {
        setRecentSearches(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to load recent searches:', e);
      }
    }
  }, []);

  // Keyboard shortcut: Cmd+K or Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const saveRecentSearch = (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    const updated = [searchQuery, ...recentSearches.filter((s) => s !== searchQuery)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('app-idea-miner-recent-searches', JSON.stringify(updated));
  };

  // Build command items
  const buildCommands = useCallback((): CommandItem[] => {
    const commands: CommandItem[] = [];

    // Pages
    commands.push(
      {
        id: 'page-dashboard',
        title: 'Dashboard',
        subtitle: 'View overview and stats',
        type: 'page',
        action: () => navigate('/'),
        keywords: ['home', 'overview', 'stats'],
      },
      {
        id: 'page-clusters',
        title: 'Explore Clusters',
        subtitle: 'Browse all opportunity clusters',
        type: 'page',
        action: () => navigate('/clusters'),
        keywords: ['browse', 'opportunities'],
      },
      {
        id: 'page-ideas',
        title: 'Ideas Browser',
        subtitle: 'View all extracted ideas',
        type: 'page',
        action: () => navigate('/ideas'),
        keywords: ['browse', 'search'],
      },
      {
        id: 'page-analytics',
        title: 'Analytics',
        subtitle: 'View trends and insights',
        type: 'page',
        action: () => navigate('/analytics'),
        keywords: ['charts', 'graphs', 'trends'],
      }
    );

    // Clusters
    if (clusters) {
      clusters.forEach((cluster: any) => {
        commands.push({
          id: `cluster-${cluster.id}`,
          title: cluster.label,
          subtitle: `${cluster.idea_count} ideas · ${cluster.keywords?.slice(0, 3).join(', ')}`,
          type: 'cluster',
          action: () => {
            navigate(`/clusters/${cluster.id}`);
            setIsOpen(false);
          },
          keywords: cluster.keywords || [],
        });
      });
    }

    // Ideas
    if (ideas && ideas.length > 0) {
      ideas.slice(0, 20).forEach((idea: any) => {
        commands.push({
          id: `idea-${idea.id}`,
          title: idea.problem_statement,
          subtitle: `${idea.sentiment} · Quality: ${(idea.quality_score * 100).toFixed(0)}%`,
          type: 'idea',
          action: () => {
            // Could navigate to idea detail page if we add one
            navigate(`/ideas?search=${encodeURIComponent(idea.problem_statement)}`);
            setIsOpen(false);
          },
        });
      });
    }

    return commands;
  }, [clusters, ideas, navigate]);

  // Filter commands based on query
  const filteredCommands = useCallback(() => {
    if (!query.trim()) return buildCommands().slice(0, 10);

    const searchLower = query.toLowerCase();
    return buildCommands().filter((cmd) => {
      const titleMatch = cmd.title.toLowerCase().includes(searchLower);
      const subtitleMatch = cmd.subtitle?.toLowerCase().includes(searchLower);
      const keywordMatch = cmd.keywords?.some((k) => k.toLowerCase().includes(searchLower));
      return titleMatch || subtitleMatch || keywordMatch;
    });
  }, [query, buildCommands]);

  const handleSelect = (command: CommandItem) => {
    saveRecentSearch(query);
    command.action();
    setIsOpen(false);
    setQuery('');
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={() => setIsOpen(false)}>
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-start justify-center p-4 pt-[15vh]">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-xl backdrop-blur-xl bg-slate-800/90 border border-slate-700/50 shadow-2xl transition-all">
                {/* Search Input */}
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-4 top-4 w-5 h-5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search clusters, ideas, or pages..."
                    className="w-full pl-12 pr-4 py-4 bg-transparent border-none focus:outline-none text-white placeholder-slate-400 text-lg"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    autoFocus
                  />
                  <div className="absolute right-4 top-4 text-xs text-slate-500 px-2 py-1 bg-slate-700/50 rounded">
                    ⌘K
                  </div>
                </div>

                {/* Results */}
                <div className="border-t border-slate-700/50 max-h-[60vh] overflow-y-auto">
                  {!query && recentSearches.length > 0 && (
                    <div className="p-2">
                      <div className="px-3 py-2 text-xs text-slate-400 font-medium flex items-center gap-2">
                        <ClockIcon className="w-4 h-4" />
                        Recent Searches
                      </div>
                      {recentSearches.map((search, idx) => (
                        <button
                          key={idx}
                          onClick={() => setQuery(search)}
                          className="w-full text-left px-3 py-2 hover:bg-slate-700/50 rounded text-slate-300 text-sm"
                        >
                          {search}
                        </button>
                      ))}
                    </div>
                  )}

                  {filteredCommands().length === 0 ? (
                    <div className="p-8 text-center text-slate-400">
                      <p>No results found</p>
                      <p className="text-sm mt-1">Try a different search term</p>
                    </div>
                  ) : (
                    <div className="p-2">
                      {filteredCommands().map((cmd) => (
                        <button
                          key={cmd.id}
                          onClick={() => handleSelect(cmd)}
                          className="w-full text-left px-3 py-3 hover:bg-slate-700/50 rounded transition-colors group"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600/20 to-purple-600/20 flex items-center justify-center">
                              {cmd.type === 'cluster' && (
                                <div className="w-2 h-2 rounded-full bg-indigo-400" />
                              )}
                              {cmd.type === 'idea' && (
                                <div className="w-2 h-2 rounded-full bg-green-400" />
                              )}
                              {cmd.type === 'page' && (
                                <div className="w-2 h-2 rounded-full bg-purple-400" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-white font-medium truncate group-hover:text-indigo-300 transition-colors">
                                {cmd.title}
                              </div>
                              {cmd.subtitle && (
                                <div className="text-sm text-slate-400 truncate">{cmd.subtitle}</div>
                              )}
                            </div>
                            <div className="flex-shrink-0 text-xs text-slate-500 uppercase px-2 py-1 bg-slate-700/30 rounded">
                              {cmd.type}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="border-t border-slate-700/50 px-4 py-2 flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-slate-700/50 rounded">↑↓</kbd> Navigate
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-slate-700/50 rounded">↵</kbd> Select
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-slate-700/50 rounded">esc</kbd> Close
                    </span>
                  </div>
                  <span>{filteredCommands().length} results</span>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};
