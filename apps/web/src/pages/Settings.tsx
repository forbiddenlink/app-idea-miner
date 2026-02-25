import { useState } from "react"
import {
  Settings as SettingsIcon,
  Rss,
  MessageSquare,
  Rocket,
  Clock,
  Info,
} from "lucide-react"

import { cn } from "@/utils/cn"

// ---------------------------------------------------------------------------
// Hook: useRefreshSettings
// ---------------------------------------------------------------------------

export function useRefreshSettings() {
  const enabled = localStorage.getItem("aim_auto_refresh") !== "false"
  const interval = Number.parseInt(
    localStorage.getItem("aim_refresh_interval") || "60000",
    10,
  )
  return { enabled, interval }
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const INTERVAL_OPTIONS = [
  { label: "15 seconds", value: 15_000 },
  { label: "30 seconds", value: 30_000 },
  { label: "60 seconds", value: 60_000 },
  { label: "5 minutes", value: 300_000 },
] as const

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
] as const

// ---------------------------------------------------------------------------
// Settings Page
// ---------------------------------------------------------------------------

export default function Settings() {
  const [autoRefresh, setAutoRefresh] = useState(
    () => localStorage.getItem("aim_auto_refresh") !== "false",
  )

  const [refreshInterval, setRefreshInterval] = useState(() =>
    Number.parseInt(localStorage.getItem("aim_refresh_interval") || "60000", 10),
  )

  // ---- handlers ----

  function toggleAutoRefresh() {
    const next = !autoRefresh
    setAutoRefresh(next)
    localStorage.setItem("aim_auto_refresh", String(next))
  }

  function handleIntervalChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = Number(e.target.value)
    setRefreshInterval(value)
    localStorage.setItem("aim_refresh_interval", String(value))
  }

  // ---- render ----

  return (
    <div className="mx-auto max-w-3xl px-6 py-8 space-y-8">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <SettingsIcon className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
      </div>

      {/* ── Data Refresh Settings ────────────────────────────────── */}
      <section className="rounded-xl border bg-card p-6 space-y-4">
        <h2 className="text-lg font-semibold">Data Refresh Settings</h2>
        <p className="text-sm text-muted-foreground">
          Control how frequently the dashboard polls for new data. The summary
          panel refreshes every 30 s and other queries every 60 s by default.
        </p>

        {/* Auto-refresh toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Auto-refresh</p>
            <p className="text-xs text-muted-foreground">
              Automatically fetch the latest data in the background
            </p>
          </div>
          <button
            onClick={toggleAutoRefresh}
            type="button"
            className={cn(
              "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
              autoRefresh ? "bg-primary" : "bg-muted",
            )}
            aria-label={`Auto-refresh is ${autoRefresh ? "on" : "off"}. Click to toggle.`}
          >
            <span
              className={cn(
                "inline-block h-4 w-4 rounded-full bg-white transition-transform",
                autoRefresh ? "translate-x-6" : "translate-x-1",
              )}
            />
          </button>
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
            disabled={!autoRefresh}
            aria-label="Refresh interval"
            className={cn(
              "rounded-md border border-input bg-background px-3 py-1.5 text-sm",
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
      <section className="rounded-xl border bg-card p-6 space-y-4">
        <h2 className="text-lg font-semibold">Data Sources</h2>
        <p className="text-sm text-muted-foreground">
          Plugins that feed raw posts into the pipeline for clustering and
          analysis.
        </p>

        <div className="space-y-3">
          {DATA_SOURCES.map((source) => {
            const Icon = source.icon
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
            )
          })}
        </div>

        <div className="flex items-center gap-2 rounded-lg bg-surface-sunken px-4 py-3 text-sm text-muted-foreground">
          <Clock className="h-4 w-4 shrink-0" />
          <span>Ingestion cycle: Every 6 hours</span>
        </div>
      </section>

      {/* ── About ────────────────────────────────────────────────── */}
      <section className="rounded-xl border bg-card p-6 space-y-4">
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
  )
}
