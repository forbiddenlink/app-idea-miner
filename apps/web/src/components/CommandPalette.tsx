// Command Palette Component
// Universal search with Cmd+K shortcut (Cmd/Ctrl+K)

import { useState, useEffect, useCallback, useMemo, useRef, useId, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, ClockIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import { Cluster, Idea } from '@/types';
import { cn } from '@/utils/cn';

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  type: 'cluster' | 'idea' | 'page' | 'action';
  action: () => void;
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  keywords?: string[];
}

export const CommandPalette = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxId = useId();
  const navigate = useNavigate();

  const openPalette = useCallback(() => {
    setIsOpen(true);
    setSelectedIndex(0);
  }, []);

  const { data: clusters } = useQuery({
    queryKey: ['clusters', { limit: 50 }],
    queryFn: async () => {
      const res = await apiClient.getClusters({ limit: 50 });
      return res.clusters;
    },
    enabled: isOpen,
  });

  const { data: ideas } = useQuery({
    queryKey: ['ideas', { limit: 100, source: 'command-palette' }],
    queryFn: async () => {
      const response = await apiClient.getIdeas({ limit: 100 });
      return response.ideas || [];
    },
    enabled: isOpen,
  });

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

  const saveRecentSearch = (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    const updated = [searchQuery, ...recentSearches.filter((s) => s !== searchQuery)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('app-idea-miner-recent-searches', JSON.stringify(updated));
  };

  const buildCommands = useCallback((): CommandItem[] => {
    const commands: CommandItem[] = [];

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

    if (clusters) {
      clusters.forEach((cluster: Cluster) => {
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

    if (ideas && ideas.length > 0) {
      ideas.slice(0, 20).forEach((idea: Idea) => {
        commands.push({
          id: `idea-${idea.id}`,
          title: idea.problem_statement,
          subtitle: `${idea.sentiment} · Quality: ${(idea.quality_score * 100).toFixed(0)}%`,
          type: 'idea',
          action: () => {
            navigate(`/ideas?search=${encodeURIComponent(idea.problem_statement)}`);
            setIsOpen(false);
          },
        });
      });
    }

    return commands;
  }, [clusters, ideas, navigate]);

  const filteredCommands = useMemo(() => {
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
    setSelectedIndex(0);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openPalette();
        return;
      }

      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        setIsOpen(false);
        return;
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, Math.max(filteredCommands.length - 1, 0)));
        return;
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
        return;
      }

      if (e.key === 'Enter' && filteredCommands.length > 0) {
        e.preventDefault();
        handleSelect(filteredCommands[selectedIndex] || filteredCommands[0]);
      }
    };

    const handleOpenRequest = () => openPalette();

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('app:command-palette-open', handleOpenRequest);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('app:command-palette-open', handleOpenRequest);
    };
  }, [isOpen, filteredCommands, selectedIndex, handleSelect, openPalette]);

  useEffect(() => {
    if (!isOpen) return;
    setSelectedIndex(0);
  }, [query, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const raf = window.requestAnimationFrame(() => inputRef.current?.focus());
    return () => window.cancelAnimationFrame(raf);
  }, [isOpen]);

  useEffect(() => {
    if (selectedIndex < filteredCommands.length) return;
    setSelectedIndex(Math.max(filteredCommands.length - 1, 0));
  }, [filteredCommands.length, selectedIndex]);

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'cluster':
        return 'bg-primary';
      case 'idea':
        return 'bg-success';
      case 'page':
        return 'bg-muted-foreground';
      default:
        return 'bg-muted-foreground';
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={() => setIsOpen(false)}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" />
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
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-lg border border-border bg-popover shadow-lg transition-all">
                <Dialog.Title className="sr-only">Command palette</Dialog.Title>

                {/* Search Input */}
                <div className="relative border-b border-border">
                  <MagnifyingGlassIcon className="absolute left-4 top-4 h-5 w-5 text-muted-foreground" />
                  <input
                    ref={inputRef}
                    id="command-palette-input"
                    type="text"
                    placeholder="Search clusters, ideas, or pages…"
                    className="w-full bg-transparent py-4 pl-12 pr-4 text-foreground placeholder:text-muted-foreground focus:outline-none"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    aria-label="Search commands, pages, and ideas"
                    role="combobox"
                    aria-autocomplete="list"
                    aria-controls={listboxId}
                    aria-expanded={isOpen}
                    aria-activedescendant={filteredCommands[selectedIndex] ? `command-result-${filteredCommands[selectedIndex].id}` : undefined}
                  />
                  <div className="absolute right-4 top-4 rounded bg-muted px-2 py-1 text-xs text-muted-foreground">
                    ⌘K
                  </div>
                </div>

                {/* Results */}
                <div id={listboxId} role="listbox" aria-label="Command results" className="max-h-[60vh] overflow-y-auto">
                  {!query && recentSearches.length > 0 && (
                    <div className="p-2">
                      <div id="command-palette-recent-searches" className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-muted-foreground">
                        <ClockIcon className="h-4 w-4" />
                        Recent Searches
                      </div>
                      {recentSearches.map((search, idx) => (
                        <button
                          type="button"
                          key={idx}
                          onClick={() => setQuery(search)}
                          className="w-full rounded-md px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                          aria-describedby="command-palette-recent-searches"
                        >
                          {search}
                        </button>
                      ))}
                    </div>
                  )}

                  {filteredCommands.length === 0 ? (
                    <div className="p-8 text-center text-muted-foreground">
                      <p>No results found</p>
                      <p className="mt-1 text-sm">Try a different search term</p>
                    </div>
                  ) : (
                    <div className="p-2">
                      {filteredCommands.map((cmd, index) => (
                        <button
                          type="button"
                          key={cmd.id}
                          id={`command-result-${cmd.id}`}
                          onClick={() => handleSelect(cmd)}
                          onMouseEnter={() => setSelectedIndex(index)}
                          className={cn(
                            "group w-full rounded-md px-3 py-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                            index === selectedIndex ? "bg-muted" : "hover:bg-muted/50"
                          )}
                          role="option"
                          aria-selected={index === selectedIndex}
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                              <div className={cn("h-2 w-2 rounded-full", getTypeColor(cmd.type))} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="truncate font-medium text-foreground">
                                {cmd.title}
                              </div>
                              {cmd.subtitle && (
                                <div className="truncate text-sm text-muted-foreground">{cmd.subtitle}</div>
                              )}
                            </div>
                            <div className="shrink-0 rounded bg-muted px-2 py-1 text-xs uppercase text-muted-foreground">
                              {cmd.type}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between border-t border-border px-4 py-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <kbd className="rounded bg-muted px-2 py-1">↑↓</kbd> Navigate
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="rounded bg-muted px-2 py-1">↵</kbd> Select
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="rounded bg-muted px-2 py-1">esc</kbd> Close
                    </span>
                  </div>
                  <span>{filteredCommands.length} results</span>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};
