import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Clock,
  Code2,
  Info,
  MessageSquare,
  Rocket,
  Rss,
  Save,
  Settings as SettingsIcon,
  Trash2,
} from "lucide-react";
import { useState } from "react";

import { apiClient } from "@/services/api";
import { cn } from "@/utils/cn";

// ---------------------------------------------------------------------------
// Hook: useRefreshSettings
// ---------------------------------------------------------------------------

export function useRefreshSettings() {
  const enabled = localStorage.getItem("aim_auto_refresh") !== "false";
  const interval = Number.parseInt(
    localStorage.getItem("aim_refresh_interval") || "60000",
    10,
  );
  return { enabled, interval };
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const INTERVAL_OPTIONS = [
  { label: "15 seconds", value: 15_000 },
  { label: "30 seconds", value: 30_000 },
  { label: "60 seconds", value: 60_000 },
  { label: "5 minutes", value: 300_000 },
] as const;

const DATA_SOURCES = [
  {
    name: "RSS Feeds",
    description: "Aggregates posts from configured RSS/Atom feeds",
    icon: Rss,
  },
  {
    name: "Reddit",
    description: "Monitors subreddits for app idea discussions",
    icon: MessageSquare,
  },
  {
    name: "ProductHunt",
    description: "Tracks trending launches and community feedback",
    icon: Rocket,
  },
  {
    name: "HackerNews",
    description: "Scans Ask HN and Show HN posts for product ideas",
    icon: Code2,
  },
] as const;

// ---------------------------------------------------------------------------
// Settings Page
// ---------------------------------------------------------------------------

export default function Settings() {
  const queryClient = useQueryClient();
  const [autoRefresh, setAutoRefresh] = useState(
    () => localStorage.getItem("aim_auto_refresh") !== "false",
  );

  const [refreshInterval, setRefreshInterval] = useState(() =>
    Number.parseInt(
      localStorage.getItem("aim_refresh_interval") || "60000",
      10,
    ),
  );
  const authToken = localStorage.getItem("aim_auth_token");

  const [savedSearchName, setSavedSearchName] = useState("");
  const [savedSearchDomain, setSavedSearchDomain] = useState("");
  const [savedSearchQuality, setSavedSearchQuality] = useState("0.7");
  const [savedSearchAlertEnabled, setSavedSearchAlertEnabled] = useState(true);
  const [savedSearchFrequency, setSavedSearchFrequency] = useState<
    "daily" | "weekly"
  >("weekly");

  const savedSearchesQuery = useQuery({
    queryKey: ["saved-searches"],
    queryFn: () => apiClient.getSavedSearches({ limit: 20, offset: 0 }),
    enabled: Boolean(authToken),
  });

  const createSavedSearchMutation = useMutation({
    mutationFn: () =>
      apiClient.createSavedSearch({
        name: savedSearchName,
        query_params: {
          domain: savedSearchDomain || undefined,
          min_quality: Number.parseFloat(savedSearchQuality),
        },
        alert_enabled: savedSearchAlertEnabled,
        alert_frequency: savedSearchFrequency,
      }),
    onSuccess: () => {
      setSavedSearchName("");
      setSavedSearchDomain("");
      setSavedSearchQuality("0.7");
      queryClient.invalidateQueries({ queryKey: ["saved-searches"] });
    },
  });

  const deleteSavedSearchMutation = useMutation({
    mutationFn: (savedSearchId: string) =>
      apiClient.deleteSavedSearch(savedSearchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-searches"] });
    },
  });

  // ---- handlers ----

  function toggleAutoRefresh() {
    const next = !autoRefresh;
    setAutoRefresh(next);
    localStorage.setItem("aim_auto_refresh", String(next));
  }

  function handleIntervalChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = Number(e.target.value);
    setRefreshInterval(value);
    localStorage.setItem("aim_refresh_interval", String(value));
  }

  function handleCreateSavedSearch(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!savedSearchName.trim()) return;
    createSavedSearchMutation.mutate();
  }

  // ---- render ----

  return (
    <div className="app-page mx-auto max-w-3xl space-y-8">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <SettingsIcon className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
      </div>

      {/* ── Data Refresh Settings ────────────────────────────────── */}
      <section className="card p-6 space-y-4">
        <h2 className="text-lg font-semibold">Data Refresh Settings</h2>
        <p className="text-sm text-muted-foreground">
          Control how frequently the dashboard polls for new data. The summary
          panel refreshes every 60 s and most other queries every 120 s by
          default.
        </p>

        {/* Auto-refresh toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Auto-refresh</p>
            <p className="text-xs text-muted-foreground">
              Automatically fetch the latest data in the background
            </p>
          </div>
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={toggleAutoRefresh}
            className="h-5 w-5 accent-primary"
            aria-label={`Auto-refresh is ${autoRefresh ? "on" : "off"}. Click to toggle.`}
          />
        </div>

        {/* Refresh interval */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Refresh interval</p>
            <p className="text-xs text-muted-foreground">
              How often queries re-fetch when auto-refresh is enabled
            </p>
          </div>
          <select
            value={refreshInterval}
            onChange={handleIntervalChange}
            onBlur={handleIntervalChange}
            disabled={!autoRefresh}
            aria-label="Refresh interval"
            className={cn(
              "field-control h-9 min-w-[10rem] py-0",
              !autoRefresh && "opacity-50 cursor-not-allowed",
            )}
          >
            {INTERVAL_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* ── Data Sources ─────────────────────────────────────────── */}
      <section className="card p-6 space-y-4">
        <h2 className="text-lg font-semibold">Data Sources</h2>
        <p className="text-sm text-muted-foreground">
          Plugins that feed raw posts into the pipeline for clustering and
          analysis.
        </p>

        <div className="space-y-3">
          {DATA_SOURCES.map((source) => {
            const Icon = source.icon;
            return (
              <div
                key={source.name}
                className="flex items-center justify-between rounded-lg bg-surface-sunken px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">{source.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {source.description}
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                  Active
                </span>
              </div>
            );
          })}
        </div>

        <div className="flex items-center gap-2 rounded-lg bg-surface-sunken px-4 py-3 text-sm text-muted-foreground">
          <Clock className="h-4 w-4 shrink-0" />
          <span>Ingestion cycle: Every 6 hours</span>
        </div>
      </section>

      {/* ── Saved Searches ─────────────────────────────────────── */}
      <section className="card p-6 space-y-4">
        <h2 className="text-lg font-semibold">Saved Searches</h2>
        <p className="text-sm text-muted-foreground">
          Save your favorite filter combinations and enable digest alerts.
        </p>

        {authToken ? (
          <>
            <form
              onSubmit={handleCreateSavedSearch}
              className="grid gap-3 md:grid-cols-2"
            >
              <input
                type="text"
                value={savedSearchName}
                onChange={(e) => setSavedSearchName(e.target.value)}
                placeholder="Search name"
                className="field-control"
                aria-label="Saved search name"
                required
              />
              <input
                type="text"
                value={savedSearchDomain}
                onChange={(e) => setSavedSearchDomain(e.target.value)}
                placeholder="Domain (optional)"
                className="field-control"
                aria-label="Saved search domain"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={savedSearchQuality}
                onChange={(e) => setSavedSearchQuality(e.target.value)}
                className="field-control"
                aria-label="Minimum quality"
              />
              <select
                value={savedSearchFrequency}
                onBlur={(e) =>
                  setSavedSearchFrequency(e.target.value as "daily" | "weekly")
                }
                className="field-control"
                aria-label="Alert frequency"
              >
                <option value="daily">Daily alerts</option>
                <option value="weekly">Weekly alerts</option>
              </select>

              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  checked={savedSearchAlertEnabled}
                  onChange={(e) => setSavedSearchAlertEnabled(e.target.checked)}
                />
                <span>Enable alert digest</span>
              </label>

              <button
                type="submit"
                className="focus-ring inline-flex items-center justify-center gap-2 rounded-xl border border-border bg-card px-4 py-2 text-sm font-semibold shadow-raised transition hover:bg-accent disabled:opacity-60"
                disabled={createSavedSearchMutation.isPending}
              >
                <Save className="h-4 w-4" />
                Save Search
              </button>
            </form>

            <div className="space-y-2">
              {(savedSearchesQuery.data?.saved_searches || []).map(
                (savedSearch) => (
                  <div
                    key={savedSearch.id}
                    className="flex items-center justify-between rounded-lg bg-surface-sunken px-4 py-3"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">
                        {savedSearch.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {savedSearch.alert_enabled
                          ? `${savedSearch.alert_frequency} alerts enabled`
                          : "alerts disabled"}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        deleteSavedSearchMutation.mutate(savedSearch.id)
                      }
                      className="focus-ring inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-destructive hover:bg-destructive/10"
                      aria-label={`Delete saved search ${savedSearch.name}`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </button>
                  </div>
                ),
              )}

              {savedSearchesQuery.isSuccess &&
                (savedSearchesQuery.data?.saved_searches.length || 0) === 0 && (
                  <div className="rounded-lg bg-surface-sunken px-4 py-3 text-sm text-muted-foreground">
                    No saved searches yet.
                  </div>
                )}
            </div>
          </>
        ) : (
          <div className="rounded-lg bg-surface-sunken px-4 py-3 text-sm text-muted-foreground">
            Sign in to create and manage saved searches.
          </div>
        )}
      </section>

      {/* ── About ────────────────────────────────────────────────── */}
      <section className="card p-6 space-y-4">
        <h2 className="text-lg font-semibold">About</h2>

        <dl className="space-y-3 text-sm">
          <div className="flex items-center justify-between">
            <dt className="text-muted-foreground">App version</dt>
            <dd className="font-medium">0.1.0 MVP</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-muted-foreground">Build</dt>
            <dd className="font-medium">React 18 + FastAPI + PostgreSQL</dd>
          </div>
        </dl>

        <div className="flex items-start gap-2 rounded-lg bg-surface-sunken px-4 py-3 text-xs text-muted-foreground">
          <Info className="h-4 w-4 shrink-0 mt-0.5" />
          <span>
            App-Idea Miner discovers, clusters, and analyzes "I wish there was
            an app…" posts using ML-powered clustering (HDBSCAN + TF-IDF).
          </span>
        </div>
      </section>
    </div>
  );
}
