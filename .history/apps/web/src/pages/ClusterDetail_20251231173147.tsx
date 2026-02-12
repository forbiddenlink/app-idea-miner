import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeftIcon,
  ShareIcon,
  ChartBarIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { apiClient } from '@/services/api';
import { IdeaCard } from '@/components/IdeaCard';

export const ClusterDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  // Fetch cluster details
  const { data: cluster, isLoading, error } = useQuery({
    queryKey: ['cluster', id],
    queryFn: () => apiClient.getCluster(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-700 rounded w-1/3 mb-4"></div>
          <div className="h-12 bg-slate-700 rounded w-2/3 mb-8"></div>
          <div className="card h-64"></div>
        </div>
      </div>
    );
  }

  if (error || !cluster) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="card bg-danger-500/10 border border-danger-500/20">
          <p className="text-danger-400">
            Failed to load cluster details. Please try again.
          </p>
          <Link
            to="/clusters"
            className="mt-4 inline-flex items-center gap-2 text-primary-400 hover:text-primary-300"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Clusters
          </Link>
        </div>
      </div>
    );
  }

  const getSentimentLabel = (score: number) => {
    if (score >= 0.05) return 'Positive';
    if (score <= -0.05) return 'Negative';
    return 'Neutral';
  };

  const getSentimentColor = (score: number) => {
    if (score >= 0.05) return 'success';
    if (score <= -0.05) return 'danger';
    return 'slate';
  };

  const sentimentColor = getSentimentColor(cluster.avg_sentiment);

  return (
    <div className="max-w-5xl mx-auto">
      {/* Back Button */}
      <Link
        to="/clusters"
        className="inline-flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeftIcon className="w-4 h-4" />
        Back to All Clusters
      </Link>

      {/* Header */}
      <div className="card mb-8">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-white mb-2">
              {cluster.label}
            </h1>
            {cluster.description && (
              <p className="text-slate-400 text-lg">{cluster.description}</p>
            )}
          </div>
          <button
            onClick={() => {
              navigator.clipboard.writeText(window.location.href);
              alert('Link copied to clipboard!');
            }}
            className="p-2 rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors"
            title="Share this cluster"
          >
            <ShareIcon className="w-5 h-5 text-slate-300" />
          </button>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm mb-1">Ideas</div>
            <div className="text-2xl font-bold text-white">
              {cluster.idea_count}
            </div>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm mb-1">Quality</div>
            <div className="text-2xl font-bold text-white">
              {(cluster.quality_score * 100).toFixed(0)}%
            </div>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm mb-1">Sentiment</div>
            <div className={`text-xl font-bold text-${sentimentColor}-400`}>
              {getSentimentLabel(cluster.avg_sentiment)}
            </div>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm mb-1">Trend</div>
            <div className="flex items-center gap-1">
              <ChartBarIcon className="w-5 h-5 text-primary-400" />
              <div className="text-2xl font-bold text-white">
                {(cluster.trend_score * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Keywords Section */}
      <div className="card mb-8">
        <div className="flex items-center gap-2 mb-4">
          <SparklesIcon className="w-5 h-5 text-primary-400" />
          <h2 className="text-xl font-bold text-white">Key Topics</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {cluster.keywords.map((keyword, index) => (
            <span
              key={index}
              className="px-4 py-2 bg-primary-500/10 text-primary-400 rounded-full text-sm font-medium ring-1 ring-inset ring-primary-500/20"
            >
              {keyword}
            </span>
          ))}
        </div>
      </div>

      {/* Evidence Section */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <span>Representative Ideas</span>
          <span className="text-sm font-normal text-slate-400">
            (Top examples from this cluster)
          </span>
        </h2>

        {cluster.evidence && cluster.evidence.length > 0 ? (
          <div className="space-y-4">
              {cluster.evidence.map((idea: any) => (
              <IdeaCard key={idea.id} idea={idea} />
            ))}
          </div>
        ) : (
          <div className="card text-center py-8">
            <p className="text-slate-400">
              No representative ideas available for this cluster yet.
            </p>
          </div>
        )}
      </div>

      {/* Related Clusters */}
      {cluster.related_clusters && cluster.related_clusters.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4">
            Related Opportunities
          </h2>
          <div className="space-y-3">
            {cluster.related_clusters.map((related) => (
              <Link
                key={related.id}
                to={`/clusters/${related.id}`}
                className="block p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-semibold text-white">
                    {related.label}
                  </h3>
                  <span className="badge">
                    {related.idea_count} ideas
                  </span>
                </div>
                {related.similarity_score && (
                  <div className="text-sm text-slate-400">
                    {(related.similarity_score * 100).toFixed(0)}% similar
                  </div>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
