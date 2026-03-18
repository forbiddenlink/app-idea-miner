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
} from 'recharts'
import type { AnalyticsSummary, DomainStats, TrendDataPoint } from '@/types'
import { cn } from '@/utils/cn'

const COLORS = {
  primary: 'hsl(218, 80%, 47%)',
  success: 'hsl(148, 66%, 38%)',
  danger: 'hsl(1, 73%, 52%)',
}

function TrendsChart({
  data,
  isLoading,
  trendMetric,
  onMetricChange,
}: Readonly<{
  data: TrendDataPoint[] | undefined
  isLoading: boolean
  trendMetric: 'ideas' | 'clusters'
  onMetricChange: (metric: 'ideas' | 'clusters') => void
}>) {
  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="h-80 animate-pulse rounded bg-muted/30" />
      </div>
    )
  }

  return (
    <div className="card p-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Trends Over Time</h2>
        <div className="flex items-center gap-4">
          <div className="flex rounded-xl bg-secondary p-1">
            <button
              type="button"
              onClick={() => onMetricChange('ideas')}
              className={cn(
                "focus-ring rounded-lg px-3 py-1 text-sm font-semibold transition-colors",
                trendMetric === 'ideas'
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Ideas
            </button>
            <button
              type="button"
              onClick={() => onMetricChange('clusters')}
              className={cn(
                "focus-ring rounded-lg px-3 py-1 text-sm font-semibold transition-colors",
                trendMetric === 'clusters'
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Clusters
            </button>
          </div>
          <span className="text-sm text-muted-foreground">Last 30 days</span>
        </div>
      </div>

      {data && data.length > 0 ? (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
            <XAxis
              dataKey="date"
              className="text-muted-foreground"
              tick={{ fill: 'currentColor' }}
              tickFormatter={(value) =>
                new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(value))
              }
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
  )
}

function DomainBreakdown({ data, isLoading }: Readonly<{ data: DomainStats[] | undefined; isLoading: boolean }>) {
  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="h-80 animate-pulse rounded bg-muted/30" />
      </div>
    )
  }

  return (
    <div className="card p-6">
      <h2 className="mb-6 text-lg font-semibold">Ideas by Domain</h2>
      {data && data.length > 0 ? (
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
      ) : (
        <div className="flex h-80 items-center justify-center text-muted-foreground">
          No domain data available
        </div>
      )}
    </div>
  )
}

function SentimentChart({
  summary,
  isLoading,
}: Readonly<{
  summary: AnalyticsSummary | undefined
  isLoading: boolean
}>) {
  const sentimentData = summary
    ? [
      { name: 'Positive', value: summary.sentiment_distribution.positive },
      { name: 'Negative', value: summary.sentiment_distribution.negative },
    ]
    : []

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="h-80 animate-pulse rounded bg-muted/30" />
      </div>
    )
  }

  return (
    <div className="card p-6">
      <h2 className="mb-6 text-lg font-semibold">Sentiment Distribution</h2>
      {sentimentData.length > 0 ? (
        <ResponsiveContainer width="100%" height={320}>
          <PieChart>
            <Pie
              data={sentimentData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={120}
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
  )
}

interface AnalyticsVisualsProps {
  trends: TrendDataPoint[] | undefined
  trendsLoading: boolean
  trendMetric: 'ideas' | 'clusters'
  onMetricChange: (metric: 'ideas' | 'clusters') => void
  domains: DomainStats[] | undefined
  domainsLoading: boolean
  summary: AnalyticsSummary | undefined
  summaryLoading: boolean
}

export default function AnalyticsVisuals(props: Readonly<AnalyticsVisualsProps>) {
  const {
    trends,
    trendsLoading,
    trendMetric,
    onMetricChange,
    domains,
    domainsLoading,
    summary,
    summaryLoading,
  } = props

  return (
    <>
      <TrendsChart
        data={trends}
        isLoading={trendsLoading}
        trendMetric={trendMetric}
        onMetricChange={onMetricChange}
      />
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <DomainBreakdown data={domains} isLoading={domainsLoading} />
        <SentimentChart summary={summary} isLoading={summaryLoading} />
      </div>
    </>
  )
}
