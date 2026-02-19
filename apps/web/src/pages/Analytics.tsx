import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { apiClient } from '@/services/api';
import { EmptyAnalytics } from '@/components/EmptyStates';
import { ExportButton } from '@/components/ExportButton';
import { DomainStats } from '@/types';
import { cn } from '@/utils/cn';

type TimeRange = '7d' | '30d' | '90d' | 'all';

export default function Analytics() {
  const [timeRange] = useState<TimeRange>('30d');
  const [trendMetric, setTrendMetric] = useState<'ideas' | 'clusters'>('ideas');

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => apiClient.getAnalyticsSummary(),
  });

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics', 'trends', trendMetric, timeRange],
    queryFn: async () => {
      const res = await apiClient.getAnalyticsTrends({ metric: trendMetric, interval: 'day' });
      return res.data_points;
    },
  });

  const { data: domains, isLoading: domainsLoading } = useQuery({
    queryKey: ['analytics', 'domains'],
    queryFn: () => apiClient.getAnalyticsDomains(),
  });

  // Chart colors using CSS variable values
  const COLORS = {
    primary: 'hsl(221, 83%, 53%)',
    success: 'hsl(142, 76%, 36%)',
    warning: 'hsl(38, 92%, 50%)',
    danger: 'hsl(0, 84%, 60%)',
    muted: 'hsl(215, 20%, 65%)',
  };

  const sentimentData = summary
    ? [
      { name: 'Positive', value: summary.sentiment_distribution.positive },
      { name: 'Negative', value: summary.sentiment_distribution.negative },
    ]
    : [];

  return (
    <div className="container max-w-7xl py-8 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive insights and trends across all opportunities
          </p>
        </div>
        <ExportButton type="analytics" data={summary} />
      </div>

      {!summaryLoading && summary && summary.overview.total_posts === 0 ? (
        <EmptyAnalytics />
      ) : (
        <>
          {/* Overview Stats */}
          {summaryLoading ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-24 animate-pulse rounded-lg border border-border bg-card"></div>
              ))}
            </div>
          ) : summary ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              <div className="rounded-lg border border-border bg-card p-6">
                <div className="mb-1 text-sm text-muted-foreground">Total Posts</div>
                <div className="text-3xl font-semibold">
                  {summary.overview.total_posts.toLocaleString()}
                </div>
              </div>
              <div className="rounded-lg border border-border bg-card p-6">
                <div className="mb-1 text-sm text-muted-foreground">Valid Ideas</div>
                <div className="text-3xl font-semibold text-success">
                  {summary.overview.total_ideas.toLocaleString()}
                </div>
              </div>
              <div className="rounded-lg border border-border bg-card p-6">
                <div className="mb-1 text-sm text-muted-foreground">Clusters</div>
                <div className="text-3xl font-semibold text-primary">
                  {summary.overview.total_clusters.toLocaleString()}
                </div>
              </div>
              <div className="rounded-lg border border-border bg-card p-6">
                <div className="mb-1 text-sm text-muted-foreground">Avg Sentiment</div>
                <div
                  className={cn(
                    "text-3xl font-semibold",
                    summary.overview.avg_sentiment >= 0.05 && "text-success",
                    summary.overview.avg_sentiment <= -0.05 && "text-destructive"
                  )}
                >
                  {summary.overview.avg_sentiment >= 0 ? '+' : ''}
                  {summary.overview.avg_sentiment.toFixed(2)}
                </div>
              </div>
            </div>
          ) : null}

          {/* Trends Chart */}
          <div className="rounded-lg border border-border bg-card p-6">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Trends Over Time</h2>
              <div className="flex items-center gap-4">
                {/* Metric Toggle */}
                <div className="flex rounded-md bg-muted p-1">
                  <button
                    onClick={() => setTrendMetric('ideas')}
                    className={cn(
                      "rounded px-3 py-1 text-sm font-medium transition-colors",
                      trendMetric === 'ideas'
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    Ideas
                  </button>
                  <button
                    onClick={() => setTrendMetric('clusters')}
                    className={cn(
                      "rounded px-3 py-1 text-sm font-medium transition-colors",
                      trendMetric === 'clusters'
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    Clusters
                  </button>
                </div>

                <span className="text-sm text-muted-foreground">Last 30 days</span>
              </div>
            </div>

            {trendsLoading ? (
              <div className="h-80 animate-pulse rounded bg-muted/30"></div>
            ) : trends && trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis
                    dataKey="date"
                    className="text-muted-foreground"
                    tick={{ fill: 'currentColor' }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis className="text-muted-foreground" tick={{ fill: 'currentColor' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: 'hsl(var(--foreground))' }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke={COLORS.primary}
                    strokeWidth={2}
                    dot={{ fill: COLORS.primary, r: 4 }}
                    activeDot={{ r: 6 }}
                    name={trendMetric === 'ideas' ? 'Ideas Created' : 'Clusters Formed'}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-80 items-center justify-center text-muted-foreground">
                No trend data available yet
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            {/* Domain Breakdown */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h2 className="mb-6 text-lg font-semibold">Ideas by Domain</h2>
              {domainsLoading ? (
                <div className="h-80 animate-pulse rounded bg-muted/30"></div>
              ) : domains && domains.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={domains}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                    <XAxis dataKey="domain" className="text-muted-foreground" tick={{ fill: 'currentColor' }} />
                    <YAxis className="text-muted-foreground" tick={{ fill: 'currentColor' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                    />
                    <Bar dataKey="idea_count" fill={COLORS.primary} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-80 items-center justify-center text-muted-foreground">
                  No domain data available
                </div>
              )}
            </div>

            {/* Sentiment Distribution */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h2 className="mb-6 text-lg font-semibold">Sentiment Distribution</h2>
              {summaryLoading ? (
                <div className="h-80 animate-pulse rounded bg-muted/30"></div>
              ) : sentimentData.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={sentimentData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      <Cell fill={COLORS.success} />
                      <Cell fill={COLORS.danger} />
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-80 items-center justify-center text-muted-foreground">
                  No sentiment data available
                </div>
              )}
            </div>
          </div>

          {/* Top Domains Table */}
          {!domainsLoading && domains && domains.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-6">
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
                    {domains.map((domain: DomainStats, index: number) => (
                      <tr key={index} className="border-b border-border/50 transition-colors hover:bg-muted/50">
                        <td className="px-4 py-3 font-medium capitalize">
                          {domain.domain}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{domain.idea_count}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {domain.percentage?.toFixed(1)}%
                        </td>
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
          )}
        </>
      )}
    </div>
  );
}
