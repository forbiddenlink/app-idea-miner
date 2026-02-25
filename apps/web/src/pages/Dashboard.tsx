import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import {
  RefreshCw,
  Play,
  Sparkles,
  Download,
  LightbulbIcon,
  Clock,
  ArrowRight,
} from "lucide-react"

import { apiClient } from "@/services/api"
import { Cluster, Opportunity } from "@/types"
import StatCard from "@/components/StatCard"
import ClusterCard from "@/components/ClusterCard"
import DataFreshness from "@/components/DataFreshness"
import { useRefreshSettings } from "./Settings"
import { EmptyClusterList } from "@/components/EmptyStates"
import { Button } from "@/components/ui/button"
import { useGlobalToast } from "@/contexts/ToastContext"

function getGradeColor(grade: string): string {
  switch (grade) {
    case "A": return "text-grade-a"
    case "B": return "text-grade-b"
    case "C": return "text-grade-c"
    case "D": return "text-grade-d"
    case "F": return "text-grade-f"
    default: return "text-muted-foreground"
  }
}

function getGradeBg(grade: string): string {
  switch (grade) {
    case "A": return "bg-grade-a/10 border-grade-a/20"
    case "B": return "bg-grade-b/10 border-grade-b/20"
    case "C": return "bg-grade-c/10 border-grade-c/20"
    case "D": return "bg-grade-d/10 border-grade-d/20"
    case "F": return "bg-grade-f/10 border-grade-f/20"
    default: return "bg-muted/10"
  }
}

function timeAgo(dateString: string | null | undefined): string {
  if (!dateString) return ""
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return "just now"
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function getSentimentTrend(value: number): "up" | "down" | "neutral" {
  if (value > 0) return "up"
  if (value < 0) return "down"
  return "neutral"
}

interface StatItem {
  name: string
  value: string
  trend?: "up" | "down" | "neutral"
  trendValue?: string
  change?: string
}

function buildStats(summary: ReturnType<typeof apiClient.getAnalyticsSummary> extends Promise<infer T> ? T : never): StatItem[] {
  return [
    {
      name: "Total Clusters",
      value: summary.overview.total_clusters.toString(),
      trend: summary.trending.new_clusters_this_week > 0 ? "up" : "neutral",
      trendValue: summary.trending.new_clusters_this_week > 0 ? `+${summary.trending.new_clusters_this_week}` : undefined,
      change: "this week",
    },
    {
      name: "Ideas Analyzed",
      value: summary.overview.total_ideas.toString(),
      trend: summary.trending.new_ideas_today > 0 ? "up" : "neutral",
      trendValue: summary.trending.new_ideas_today > 0 ? `+${summary.trending.new_ideas_today}` : undefined,
      change: "today",
    },
    {
      name: "Posts Ingested",
      value: summary.overview.total_posts.toString(),
      change: "from multiple sources",
    },
    {
      name: "Avg Sentiment",
      value: summary.overview.avg_sentiment.toFixed(2),
      trend: getSentimentTrend(summary.overview.avg_sentiment),
      change: `${summary.sentiment_distribution.positive} positive`,
    },
  ]
}

function StatsGrid({ summary, isLoading }: Readonly<{ summary: (ReturnType<typeof apiClient.getAnalyticsSummary> extends Promise<infer T> ? T : never) | undefined; isLoading: boolean }>) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={`skeleton-stat-${i}`} className="card h-32 animate-pulse bg-muted/50" />
        ))}
      </div>
    )
  }

  const stats = summary ? buildStats(summary) : []

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <StatCard key={stat.name} {...stat} />
      ))}
    </div>
  )
}

function TrendingClusters({ clusters, isLoading }: Readonly<{ clusters: Cluster[] | undefined; isLoading: boolean }>) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={`skeleton-cluster-${i}`} className="card h-48 animate-pulse bg-muted/50" />
        ))}
      </div>
    )
  }

  if (!clusters || clusters.length === 0) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="col-span-full">
          <EmptyClusterList />
        </div>
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {clusters.map((cluster: Cluster) => (
        <ClusterCard key={cluster.id} cluster={cluster} />
      ))}
    </div>
  )
}

export default function Dashboard() {
  const queryClient = useQueryClient()
  const toast = useGlobalToast()
  const { enabled: autoRefresh, interval: refreshInterval } = useRefreshSettings()
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["analytics", "summary"] }),
      queryClient.invalidateQueries({ queryKey: ["clusters"] }),
      queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
      queryClient.invalidateQueries({ queryKey: ["ideas", "recent"] }),
    ])
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  // Queries with auto-refresh polling
  const { data: summary, isLoading: summaryLoading, dataUpdatedAt: summaryUpdatedAt, isRefetching: summaryRefetching } = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: () => apiClient.getAnalyticsSummary(),
    refetchInterval: autoRefresh ? refreshInterval : false,
  })

  const { data: clustersData, isLoading: clustersLoading } = useQuery({
    queryKey: ["clusters", { sort_by: "trend", limit: 6 }],
    queryFn: async () => {
      const res = await apiClient.getClusters({ sort_by: "trend", order: "desc", limit: 6 })
      return res.clusters
    },
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  })

  const { data: opportunitiesData } = useQuery({
    queryKey: ["opportunities", { sort_by: "score", limit: 3 }],
    queryFn: () => apiClient.getOpportunities({ sort_by: "score", limit: 3 }),
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  })

  const { data: recentIdeasData } = useQuery({
    queryKey: ["ideas", "recent"],
    queryFn: () => apiClient.getIdeas({ sort_by: "date", order: "desc", limit: 5 }),
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  })

  // Mutations for quick actions
  const ingestMutation = useMutation({
    mutationFn: () => apiClient.triggerIngestion(),
    onSuccess: () => {
      toast.success("Ingestion job started successfully!")
      queryClient.invalidateQueries({ queryKey: ["analytics"] })
    },
    onError: () => {
      toast.error("Failed to start ingestion. Check server status.")
    },
  })

  const clusterMutation = useMutation({
    mutationFn: () => apiClient.triggerClustering(),
    onSuccess: () => {
      toast.success("Clustering job started successfully!")
      queryClient.invalidateQueries({ queryKey: ["clusters"] })
      queryClient.invalidateQueries({ queryKey: ["opportunities"] })
    },
    onError: () => {
      toast.error("Failed to start clustering. Check server status.")
    },
  })

  const topOpportunities = opportunitiesData?.opportunities || []
  const recentIdeas = recentIdeasData?.ideas || []

  return (
    <div className="mx-auto max-w-7xl px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Discover validated app opportunities from real user needs.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {summaryUpdatedAt > 0 && (
            <DataFreshness
              dataUpdatedAt={summaryUpdatedAt}
              isRefetching={summaryRefetching}
              onRefresh={handleRefresh}
            />
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <StatsGrid summary={summary} isLoading={summaryLoading} />

      {/* Quick Actions */}
      <div className="rounded-xl border border-border bg-card/50 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium text-muted-foreground mr-2">Quick Actions</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => ingestMutation.mutate()}
            disabled={ingestMutation.isPending}
          >
            <Play className={`mr-2 h-4 w-4 ${ingestMutation.isPending ? "animate-pulse" : ""}`} />
            {ingestMutation.isPending ? "Ingesting..." : "Run Ingestion"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => clusterMutation.mutate()}
            disabled={clusterMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${clusterMutation.isPending ? "animate-spin" : ""}`} />
            {clusterMutation.isPending ? "Clustering..." : "Re-cluster"}
          </Button>
          <Link to="/opportunities">
            <Button variant="outline" size="sm">
              <Sparkles className="mr-2 h-4 w-4" />
              View Opportunities
            </Button>
          </Link>
          <Link to="/ideas">
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export Data
            </Button>
          </Link>
        </div>
      </div>

      {/* Top Opportunities Preview */}
      {topOpportunities.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h2 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Top Opportunities
              </h2>
              <p className="text-sm text-muted-foreground">
                Highest-scoring market opportunities by validation signals.
              </p>
            </div>
            <Link to="/opportunities">
              <Button variant="ghost" size="sm">
                View All <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {topOpportunities.map((opp: Opportunity) => (
              <motion.div
                key={opp.cluster_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`rounded-xl border p-5 ${getGradeBg(opp.opportunity_score.grade)}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <Link
                      to={`/clusters/${opp.cluster_id}`}
                      className="font-semibold hover:text-primary transition-colors line-clamp-1"
                    >
                      {opp.cluster_label}
                    </Link>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {opp.opportunity_score.verdict}
                    </p>
                  </div>
                  <div className="text-center flex-shrink-0">
                    <div className={`text-xl font-bold ${getGradeColor(opp.opportunity_score.grade)}`}>
                      {opp.opportunity_score.total}
                    </div>
                    <div className={`text-[10px] font-semibold ${getGradeColor(opp.opportunity_score.grade)}`}>
                      Grade {opp.opportunity_score.grade}
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1 mt-3">
                  {opp.keywords.slice(0, 3).map((kw) => (
                    <span key={kw} className="text-[10px] bg-background/50 rounded px-1.5 py-0.5 text-muted-foreground">
                      {kw}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {recentIdeas.length > 0 && (
        <div className="space-y-4">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
              <Clock className="h-5 w-5 text-muted-foreground" />
              Recent Activity
            </h2>
            <p className="text-sm text-muted-foreground">
              Latest ideas extracted from ingested posts.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-card divide-y divide-border">
            {recentIdeas.map((idea) => (
              <div key={idea.id} className="flex items-start gap-3 px-4 py-3">
                <div className="mt-0.5 rounded-full bg-primary/10 p-1.5">
                  <LightbulbIcon className="h-3.5 w-3.5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm line-clamp-1">
                    {idea.problem_statement.length > 80
                      ? `${idea.problem_statement.slice(0, 80)}...`
                      : idea.problem_statement}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    {idea.domain && (
                      <span className="text-[10px] bg-muted/50 rounded px-1.5 py-0.5 text-muted-foreground">
                        {idea.domain}
                      </span>
                    )}
                    <span className="text-[10px] text-muted-foreground">
                      Quality: {(idea.quality_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {timeAgo(idea.extracted_at)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Trending Clusters */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold tracking-tight">Trending Opportunities</h2>
            <p className="text-sm text-muted-foreground">
              High-growth clusters identified in the last 7 days.
            </p>
          </div>
          <Link to="/clusters">
            <Button variant="ghost">View All</Button>
          </Link>
        </div>

        <TrendingClusters clusters={clustersData} isLoading={clustersLoading} />
      </div>
    </div>
  )
}
