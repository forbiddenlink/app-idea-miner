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
import DataFreshness from '@/components/DataFreshness';
import { useRefreshSettings } from './Settings';
import { DomainStats } from '@/types';
import { cn } from '@/utils/cn';

type TimeRange = '7d' | '30d' | '90d' | 'all';

// Chart colors using CSS variable values
const COLORS = {
  primary: 'hsl(221, 83%, 53%)',
  success: 'hsl(142, 76%, 36%)',
  warning: 'hsl(38, 92%, 50%)',
  danger: 'hsl(0, 84%, 60%)',
  muted: 'hsl(215, 20%, 65%)',
};

type SummaryData = Awaited<ReturnType<typeof apiClient.getAnalyticsSummary>>;
type TrendPoint = { date: string; value: number };

function OverviewStats({ data, isLoading }: Readonly<{ data: SummaryData | undefined; isLoading: boolean }>) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={`skeleton-stat-${i}`} className="h-24 animate-pulse rounded-lg border border-border bg-card"></div>
        ))}
      </div>
    );
  }
  if (!data) return null;
  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-1 text-sm text-muted-foreground">Total Posts</div>
        <div className="text-3xl font-semibold">
          {data.overview.total_posts.toLocaleString()}
        </div>
      </div>
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-1 text-sm text-muted-foreground">Valid Ideas</div>
        <div className="text-3xl font-semibold text-success">
          {data.overview.total_ideas.toLocaleString()}
        </div>
      </div>
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-1 text-sm text-muted-foreground">Clusters</div>
        <div className="text-3xl font-semibold text-primary">
          {data.overview.total_clusters.toLocaleString()}
        </div>
      </div>
      <div className="rounded-lg border border-border bg-card p-6">
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
  );
}

function TrendsChart({
  data,
  isLoading,
  trendMetric,
  onMetricChange,
}: Readonly<{
  data: TrendPoint[] | undefined;
  isLoading: boolean;
  trendMetric: 'ideas' | 'clusters';
  onMetricChange: (metric: 'ideas' | 'clusters') => void;
}>) {
  function renderChart() {
    if (isLoading) {
      return <div className="h-80 animate-pulse rounded bg-muted/30"></div>;
    }
    if (data && data.length > 0) {
      return (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data}>
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
      );
    }
    return (
      <div className="flex h-80 items-center justify-center text-muted-foreground">
        No trend data available yet
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Trends Over Time</h2>
        <div className="flex items-center gap-4">
          {/* Metric Toggle */}
          <div className="flex rounded-md bg-muted p-1">
            <button
              onClick={() => onMetricChange('ideas')}
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
              onClick={() => onMetricChange('clusters')}
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

      {renderChart()}
    </div>
  );
}

function DomainBreakdown({ data, isLoading }: Readonly<{ data: DomainStats[] | undefined; isLoading: boolean }>) {
  function renderChart() {
    if (isLoading) {
      return <div className="h-80 animate-pulse rounded bg-muted/30"></div>;
    }
    if (data && data.length > 0) {
      return (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data}>
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
      );
    }
    return (
      <div className="flex h-80 items-center justify-center text-muted-foreground">
        No domain data available
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="mb-6 text-lg font-semibold">Ideas by Domain</h2>
      {renderChart()}
    </div>
  );
}

function SentimentChart({ data, isLoading }: Readonly<{ data: SummaryData | undefined; isLoading: boolean }>) {
  const sentimentData = data
    ? [
      { name: 'Positive', value: data.sentiment_distribution.positive },
      { name: 'Negative', value: data.sentiment_distribution.negative },
    ]
    : [];

  function renderChart() {
    if (isLoading) {
      return <div className="h-80 animate-pulse rounded bg-muted/30"></div>;
    }
    if (sentimentData.length > 0) {
      return (
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
      );
    }
    return (
      <div className="flex h-80 items-center justify-center text-muted-foreground">
        No sentiment data available
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="mb-6 text-lg font-semibold">Sentiment Distribution</h2>
      {renderChart()}
    </div>
  );
}

function DomainTable({ data, isLoading }: Readonly<{ data: DomainStats[] | undefined; isLoading: boolean }>) {
  if (isLoading || !data || data.length === 0) return null;
  return (
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
            {data.map((domain: DomainStats) => (
              <tr key={domain.domain} className="border-b border-border/50 transition-colors hover:bg-muted/50">
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
  );
}

export default function Analytics() {
  const { enabled: autoRefresh, interval: refreshInterval } = useRefreshSettings()
  const [timeRange] = useState<TimeRange>('30d');
  const [trendMetric, setTrendMetric] = useState<'ideas' | 'clusters'>('ideas');

  const { data: summary, isLoading: summaryLoading, dataUpdatedAt: summaryUpdatedAt, isRefetching: summaryRefetching } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => apiClient.getAnalyticsSummary(),
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  });

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics', 'trends', trendMetric, timeRange],
    queryFn: async () => {
      const res = await apiClient.getAnalyticsTrends({ metric: trendMetric, interval: 'day' });
      return res.data_points;
    },
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  });

  const { data: domains, isLoading: domainsLoading } = useQuery({
    queryKey: ['analytics', 'domains'],
    queryFn: () => apiClient.getAnalyticsDomains(),
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  });

  return (
    <div className="mx-auto max-w-7xl px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive insights and trends across all opportunities
          </p>
        </div>
        <div className="flex items-center gap-3">
          {summaryUpdatedAt > 0 && (
            <DataFreshness
              dataUpdatedAt={summaryUpdatedAt}
              isRefetching={summaryRefetching}
            />
          )}
          <ExportButton type="analytics" data={summary} />
        </div>
      </div>

      {!summaryLoading && summary?.overview.total_posts === 0 ? (
        <EmptyAnalytics />
      ) : (
        <>
          <OverviewStats data={summary} isLoading={summaryLoading} />
          <TrendsChart
            data={trends}
            isLoading={trendsLoading}
            trendMetric={trendMetric}
            onMetricChange={setTrendMetric}
          />
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <DomainBreakdown data={domains} isLoading={domainsLoading} />
            <SentimentChart data={summary} isLoading={summaryLoading} />
          </div>
          <DomainTable data={domains} isLoading={domainsLoading} />
        </>
      )}
    </div>
  );
}
