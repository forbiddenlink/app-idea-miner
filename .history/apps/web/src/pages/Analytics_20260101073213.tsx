import React, { useState } from 'react';
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
import { ChartBarIcon, ClockIcon } from '@heroicons/react/24/outline';
import { apiClient } from '@/services/api';
import { EmptyAnalytics } from '@/components/EmptyStates';
import { ExportButton } from '@/components/ExportButton';

type TimeRange = '7d' | '30d' | '90d' | 'all';

export const Analytics: React.FC = () => {
  const [timeRange] = useState<TimeRange>('30d');
  const [trendMetric, setTrendMetric] = useState<'ideas' | 'clusters'>('ideas');

  // Fetch analytics summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: apiClient.getAnalyticsSummary,
  });

  // Fetch trend data
  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics', 'trends', trendMetric, timeRange],
    queryFn: () => apiClient.getAnalyticsTrends({ metric: trendMetric, interval: 'day' }),
  });

  // Fetch domain breakdown
  const { data: domains, isLoading: domainsLoading } = useQuery({
    queryKey: ['analytics', 'domains'],
    queryFn: apiClient.getAnalyticsDomains,
  });

  // Colors for charts
  const COLORS = {
    primary: '#6366f1',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    slate: '#64748b',
  };

  // Prepare sentiment pie chart data
  const sentimentData = summary
    ? [
        { name: 'Positive', value: summary.sentiment_distribution.positive },
        { name: 'Negative', value: summary.sentiment_distribution.negative },
      ]
    : [];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-purple-500/10 blur-3xl -z-10" />
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-purple-400 mb-2">
            Analytics Dashboard
          </h1>
          <p className="text-slate-400">
            Comprehensive insights and trends across all opportunities
          </p>
        </div>
        <ExportButton type="analytics" data={summary} />
      </div>

      {/* Check if we have any data */}
      {!summaryLoading && summary && summary.overview.total_posts === 0 ? (
        <EmptyAnalytics />
      ) : (
        <>
          {/* Overview Stats */}
          {summaryLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse h-24"></div>
          ))}
        </div>
      ) : summary ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="text-slate-400 text-sm mb-1">Total Posts</div>
            <div className="text-3xl font-bold text-white">
              {summary.overview.total_posts.toLocaleString()}
            </div>
          </div>
          <div className="card">
            <div className="text-slate-400 text-sm mb-1">Valid Ideas</div>
            <div className="text-3xl font-bold text-success-400">
              {summary.overview.total_ideas.toLocaleString()}
            </div>
          </div>
          <div className="card">
            <div className="text-slate-400 text-sm mb-1">Clusters</div>
            <div className="text-3xl font-bold text-primary-400">
              {summary.overview.total_clusters.toLocaleString()}
            </div>
          </div>
          <div className="card">
            <div className="text-slate-400 text-sm mb-1">Avg Sentiment</div>
            <div
              className={`text-3xl font-bold ${
                summary.overview.avg_sentiment >= 0.05
                  ? 'text-success-400'
                  : summary.overview.avg_sentiment <= -0.05
                  ? 'text-danger-400'
                  : 'text-slate-400'
              }`}
            >
              {summary.overview.avg_sentiment >= 0 ? '+' : ''}
              {summary.overview.avg_sentiment.toFixed(2)}
            </div>
          </div>
        </div>
      ) : null}

      {/* Trends Chart */}
      <div className="card mb-8 relative">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-purple-500/5 rounded-2xl" />
        <div className="relative z-10">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5 text-primary-400" />
              <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-purple-400">
                Trends Over Time
              </h2>
            </div>
          <div className="flex gap-2">
            {/* Metric Toggle */}
            <div className="flex bg-slate-700 rounded-lg p-1">
              <button
                onClick={() => setTrendMetric('ideas')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  trendMetric === 'ideas'
                    ? 'bg-primary-500 text-white'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                Ideas
              </button>
              <button
                onClick={() => setTrendMetric('clusters')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  trendMetric === 'clusters'
                    ? 'bg-primary-500 text-white'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                Clusters
              </button>
            </div>

            {/* Time Range (placeholder for future) */}
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <ClockIcon className="w-4 h-4" />
              <span>Last 30 days</span>
            </div>
          </div>
        </div>

        {trendsLoading ? (
          <div className="h-80 bg-slate-700/30 rounded animate-pulse"></div>
        ) : trends && trends.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="date"
                stroke="#94a3b8"
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#e2e8f0' }}
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
          <div className="h-80 flex items-center justify-center text-slate-400">
            No trend data available yet
          </div>
        )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Domain Breakdown */}
        <div className="card relative">
          <div className="absolute inset-0 bg-gradient-to-br from-success-500/5 to-emerald-500/5 rounded-2xl" />
          <div className="relative z-10">
            <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-success-400 to-emerald-400 mb-6">
              Ideas by Domain
            </h2>
          {domainsLoading ? (
            <div className="h-80 bg-slate-700/30 rounded animate-pulse"></div>
          ) : domains && domains.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={domains}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Bar dataKey="count" fill={COLORS.primary} radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-80 flex items-center justify-center text-slate-400">
              No domain data available
            </div>
          )}
        </div>

        {/* Sentiment Distribution */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-6">Sentiment Distribution</h2>
          {summaryLoading ? (
            <div className="h-80 bg-slate-700/30 rounded animate-pulse"></div>
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
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-80 flex items-center justify-center text-slate-400">
              No sentiment data available
            </div>
          )}
        </div>
      </div>

      {/* Top Domains Table */}
      {!domainsLoading && domains && domains.length > 0 && (
        <div className="card mt-8">
          <h2 className="text-xl font-bold text-white mb-6">Domain Details</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Domain</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Ideas</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Percentage</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Avg Sentiment</th>
                </tr>
              </thead>
              <tbody>
                {domains.map((domain: any, index: number) => (
                  <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="py-3 px-4 text-white font-medium capitalize">
                      {domain.name}
                    </td>
                    <td className="py-3 px-4 text-slate-300">{domain.count}</td>
                    <td className="py-3 px-4 text-slate-300">
                      {domain.percentage?.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded text-sm font-medium ${
                          domain.avg_sentiment >= 0.05
                            ? 'bg-success-500/20 text-success-400'
                            : domain.avg_sentiment <= -0.05
                            ? 'bg-danger-500/20 text-danger-400'
                            : 'bg-slate-500/20 text-slate-400'
                        }`}
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
};
