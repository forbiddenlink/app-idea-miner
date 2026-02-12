import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Activity,
  Box,
  FileText,
  Lightbulb,
  RefreshCw
} from "lucide-react"

import { apiClient } from "@/services/api"
import { Cluster } from "@/types"
import StatCard from "@/components/StatCard"
import ClusterCard from "@/components/ClusterCard"
import { Button } from "@/components/ui/button"

export default function Dashboard() {
  const queryClient = useQueryClient()
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["analytics", "summary"] }),
      queryClient.invalidateQueries({ queryKey: ["clusters"] })
    ])
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: () => apiClient.getAnalyticsSummary(),
  })

  const { data: clustersData, isLoading: clustersLoading } = useQuery({
    queryKey: ["clusters", { sort_by: "trend", limit: 6 }],
    queryFn: async () => {
      const res = await apiClient.getClusters({ sort_by: "trend", order: "desc", limit: 6 });
      return res.clusters;
    },
  })

  const stats = summary ? [
    {
      name: "Total Clusters",
      value: summary.overview.total_clusters.toString(),
      icon: Box,
      color: "primary" as const,
      change: `${summary.trending.new_clusters_this_week} this week`,
    },
    {
      name: "Ideas Analyzed",
      value: summary.overview.total_ideas.toString(),
      icon: Lightbulb,
      color: "success" as const,
      change: `${summary.trending.new_ideas_today} today`,
    },
    {
      name: "Posts Ingested",
      value: summary.overview.total_posts.toString(),
      icon: FileText,
      color: "warning" as const,
      change: "From multiple sources",
    },
    {
      name: "Avg Sentiment",
      value: summary.overview.avg_sentiment.toFixed(2),
      icon: Activity,
      color: summary.overview.avg_sentiment > 0 ? ("success" as const) : ("danger" as const),
      change: `${summary.sentiment_distribution.positive} positive`,
    },
  ] : []

  return (
    <div className="space-y-8 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Discover validated app opportunities from real user needs.
          </p>
        </div>
        <div className="flex items-center space-x-2">
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {summaryLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card h-32 animate-pulse bg-muted/50" />
          ))
        ) : (
          stats.map((stat) => (
            <StatCard key={stat.name} {...stat} />
          ))
        )}
      </div>

      {/* Top Trending Clusters */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold tracking-tight">Trending Opportunities</h2>
            <p className="text-sm text-muted-foreground">
              High-growth clusters identified in the last 7 days.
            </p>
          </div>
          <Button variant="ghost">View All</Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {clustersLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="card h-48 animate-pulse bg-muted/50" />
            ))
          ) : clustersData && clustersData.length > 0 ? (
            clustersData.map((cluster: Cluster) => (
              <ClusterCard key={cluster.id} cluster={cluster} />
            ))
          ) : (
            <div className="col-span-full flex h-[450px] shrink-0 items-center justify-center rounded-md border border-dashed text-muted-foreground">
              No clusters found. Try triggering ingestion.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
