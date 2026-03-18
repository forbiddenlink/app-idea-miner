import { lazy, Suspense, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import { EmptyAnalytics } from '@/components/EmptyStates'
import { ExportButton } from '@/components/ExportButton'
import DataFreshness from '@/components/DataFreshness'
import { useRefreshSettings } from './Settings'
import { AnalyticsSummary, DomainStats } from '@/types'
import { cn } from '@/utils/cn'

const AnalyticsVisuals = lazy(() => import('@/components/analytics/AnalyticsVisuals'))

type SummaryData = Awaited<ReturnType<typeof apiClient.getAnalyticsSummary>>

function OverviewStats({ data, isLoading }: Readonly<{ data: SummaryData | undefined; isLoading: boolean }>) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={`skeleton-stat-${i}`} className="card h-24 animate-pulse bg-muted/45" />
        ))}
      </div>
    )
  }
  if (!data) return null
  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
      <div className="card p-6">
        <div className="mb-1 text-sm text-muted-foreground">Total Posts</div>
        <div className="text-3xl font-semibold">{data.overview.total_posts.toLocaleString()}</div>
      </div>
      <div className="card p-6">
        <div className="mb-1 text-sm text-muted-foreground">Valid Ideas</div>
        <div className="text-3xl font-semibold text-success">{data.overview.total_ideas.toLocaleString()}</div>
      </div>
      <div className="card p-6">
        <div className="mb-1 text-sm text-muted-foreground">Clusters</div>
        <div className="text-3xl font-semibold text-primary">{data.overview.total_clusters.toLocaleString()}</div>
      </div>
      <div className="card p-6">
        <div className="mb-1 text-sm text-muted-foreground">Avg Sentiment</div>
        <div
          className={cn(
            "text-3xl font-semibold",
            data.overview.avg_sentiment >= 0.05 && "text-success",
            data.overview.avg_sentiment <= -0.05 && "text-destructive"
          )}
        >
          {data.overview.avg_sentiment >= 0 ? '+' : ''}
          {data.overview.avg_sentiment.toFixed(2)}
        </div>
      </div>
    </div>
  )
}

function DomainTable({ data, isLoading }: Readonly<{ data: DomainStats[] | undefined; isLoading: boolean }>) {
  if (isLoading || !data || data.length === 0) return null
  return (
    <div className="card p-6">
      <h2 className="mb-6 text-lg font-semibold">Domain Details</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Domain</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Ideas</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Percentage</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Avg Sentiment</th>
            </tr>
          </thead>
          <tbody>
            {data.map((domain) => (
              <tr key={domain.domain} className="border-b border-border/50 transition-colors hover:bg-muted/50">
                <td className="px-4 py-3 font-medium capitalize">{domain.domain}</td>
                <td className="px-4 py-3 text-muted-foreground">{domain.idea_count}</td>
                <td className="px-4 py-3 text-muted-foreground">{domain.percentage?.toFixed(1)}%</td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      "rounded px-2 py-1 text-sm font-medium",
                      domain.avg_sentiment >= 0.05 && "bg-success/10 text-success",
                      domain.avg_sentiment <= -0.05 && "bg-destructive/10 text-destructive",
                      domain.avg_sentiment > -0.05 && domain.avg_sentiment < 0.05 && "bg-muted text-muted-foreground"
                    )}
                  >
                    {domain.avg_sentiment >= 0 ? '+' : ''}
                    {domain.avg_sentiment.toFixed(2)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function VisualsSkeleton() {
  return (
    <div className="space-y-8">
      <div className="card h-[380px] animate-pulse bg-muted/40" />
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div className="card h-[380px] animate-pulse bg-muted/40" />
        <div className="card h-[380px] animate-pulse bg-muted/40" />
      </div>
    </div>
  )
}

export default function Analytics() {
  const { enabled: autoRefresh, interval: refreshInterval } = useRefreshSettings()
  const [trendMetric, setTrendMetric] = useState<'ideas' | 'clusters'>('ideas')

  const {
    data: summary,
    isLoading: summaryLoading,
    dataUpdatedAt: summaryUpdatedAt,
    isRefetching: summaryRefetching,
  } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => apiClient.getAnalyticsSummary(),
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  })

  const hasAnalyticsData = (summary?.overview.total_posts ?? 0) > 0

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics', 'trends', trendMetric],
    queryFn: async () => {
      const response = await apiClient.getAnalyticsTrends({ metric: trendMetric, interval: 'day' })
      return response.data_points
    },
    enabled: hasAnalyticsData,
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  })

  const { data: domains, isLoading: domainsLoading } = useQuery({
    queryKey: ['analytics', 'domains'],
    queryFn: () => apiClient.getAnalyticsDomains(),
    enabled: hasAnalyticsData,
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  })

  return (
    <div className="app-page">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="section-kicker">Performance Intelligence</p>
          <h1 className="mt-1 text-2xl sm:text-3xl font-bold">Analytics Dashboard</h1>
          <p className="mt-1 text-muted-foreground">Comprehensive insights and trends across all opportunities</p>
        </div>
        <div className="flex items-center gap-3">
          {summaryUpdatedAt > 0 && (
            <DataFreshness dataUpdatedAt={summaryUpdatedAt} isRefetching={summaryRefetching} />
          )}
          <ExportButton type="analytics" data={summary as AnalyticsSummary | undefined} />
        </div>
      </div>

      {!summaryLoading && !hasAnalyticsData ? (
        <EmptyAnalytics />
      ) : (
        <>
          <OverviewStats data={summary} isLoading={summaryLoading} />
          <Suspense fallback={<VisualsSkeleton />}>
            <AnalyticsVisuals
              trends={trends}
              trendsLoading={trendsLoading}
              trendMetric={trendMetric}
              onMetricChange={setTrendMetric}
              domains={domains}
              domainsLoading={domainsLoading}
              summary={summary}
              summaryLoading={summaryLoading}
            />
          </Suspense>
          <DomainTable data={domains} isLoading={domainsLoading} />
        </>
      )}
    </div>
  )
}
