import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import StatCard from '@/components/StatCard'
import ClusterCard from '@/components/ClusterCard'
import {
  CubeIcon,
  LightBulbIcon,
  DocumentTextIcon,
  FaceSmileIcon
} from '@heroicons/react/24/outline'

export default function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => apiClient.getAnalyticsSummary(),
  })

  const { data: clustersData, isLoading: clustersLoading } = useQuery({
    queryKey: ['clusters', { sort_by: 'trend', limit: 6 }],
    queryFn: () => apiClient.getClusters({ sort_by: 'trend', order: 'desc', limit: 6 }),
  })

  const stats = summary ? [
    {
      name: 'Total Clusters',
      value: summary.overview.total_clusters.toString(),
      icon: CubeIcon,
      color: 'primary' as const,
      change: `${summary.trending.new_clusters_this_week} this week`,
    },
    {
      name: 'Ideas Analyzed',
      value: summary.overview.total_ideas.toString(),
      icon: LightBulbIcon,
      color: 'success' as const,
      change: `${summary.trending.new_ideas_today} today`,
    },
    {
      name: 'Posts Ingested',
      value: summary.overview.total_posts.toString(),
      icon: DocumentTextIcon,
      color: 'warning' as const,
      change: 'From multiple sources',
    },
    {
      name: 'Avg Sentiment',
      value: summary.overview.avg_sentiment.toFixed(2),
      icon: FaceSmileIcon,
      color: summary.overview.avg_sentiment > 0 ? ('success' as const) : ('danger' as const),
      change: `${summary.sentiment_distribution.positive} positive`,
    },
  ] : []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-purple-500/10 blur-3xl -z-10" />
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-300">
          Dashboard
        </h1>
        <p className="mt-2 text-slate-400">
          Discover validated app opportunities from real user needs
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {summaryLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card p-6 animate-pulse">
                <div className="h-4 bg-slate-700 rounded w-3/4 mb-4" />
                <div className="h-8 bg-slate-700 rounded w-1/2" />
              </div>
            ))}
          </>
        ) : (
          stats.map((stat) => (
            <StatCard key={stat.name} {...stat} />
          ))
        )}
      </div>

      {/* Top Trending Clusters */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-red-500/20 blur-2xl -z-10" />
            <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-400">
              🔥 Trending Opportunities
            </h2>
          </div>
          <button className="btn-primary">
            Refresh Clusters
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clustersLoading ? (
            <>
              {[...Array(6)].map((_, i) => (
                <div key={i} className="card p-6 animate-pulse">
                  <div className="h-6 bg-slate-700 rounded w-3/4 mb-4" />
                  <div className="h-4 bg-slate-700 rounded w-full mb-2" />
                  <div className="h-4 bg-slate-700 rounded w-2/3" />
                </div>
              ))}
            </>
          ) : clustersData?.clusters ? (
            clustersData.clusters.map((cluster: any) => (
              <ClusterCard key={cluster.id} cluster={cluster} />
            ))
          ) : (
            <div className="col-span-3 text-center py-12 text-slate-400">
              No clusters found. Try running ingestion first.
            </div>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      {summary && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Top Domains</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {summary.top_domains.slice(0, 4).map((domain: any) => (
              <div key={domain.domain} className="text-center">
                <div className="text-2xl font-bold text-primary-400">{domain.count}</div>
                <div className="text-sm text-slate-400 capitalize">{domain.domain}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
