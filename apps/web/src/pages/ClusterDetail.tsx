
import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Share2, BarChart3, Sparkles } from 'lucide-react';

import { apiClient } from '@/services/api';
import { IdeaCard } from '@/components/IdeaCard';
import { EmptyIdeasList } from '@/components/EmptyStates';
import { Button } from '@/components/ui/button';
import { cn } from '@/utils/cn';
import { Idea, RelatedCluster } from '@/types';

export default function ClusterDetail() {
  const { id } = useParams<{ id: string }>();

  // Fetch cluster details
  const { data: cluster, isLoading, error } = useQuery({
    queryKey: ['cluster', id],
    queryFn: () => apiClient.getCluster(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="container max-w-5xl py-8 space-y-8 animate-pulse">
        <div className="h-8 bg-muted rounded w-1/3"></div>
        <div className="h-64 bg-muted rounded-xl"></div>
      </div>
    );
  }

  if (error || !cluster) {
    return (
      <div className="container max-w-5xl py-8">
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-6 text-destructive">
          <p>Failed to load cluster details. Please try again.</p>
          <Button variant="link" asChild className="mt-4 px-0 text-destructive hover:text-destructive/80">
            <Link to="/clusters">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Clusters
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const getSentimentColor = (score: number) => {
    if (score >= 0.05) return 'text-green-500';
    if (score <= -0.05) return 'text-red-500';
    return 'text-muted-foreground';
  };

  const getSentimentLabel = (score: number) => {
    if (score >= 0.05) return 'Positive';
    if (score <= -0.05) return 'Negative';
    return 'Neutral';
  };

  return (
    <div className="container max-w-5xl py-8 space-y-8">
      {/* Back Button */}
      <Button variant="ghost" asChild className="-ml-4 text-muted-foreground hover:text-foreground">
        <Link to="/clusters">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to All Clusters
        </Link>
      </Button>

      {/* Header */}
      <div className="card overflow-hidden border bg-card text-card-foreground shadow-sm rounded-xl">
        <div className="p-6">
          <div className="flex justify-between items-start gap-4 mb-6">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight">
                {cluster.label}
              </h1>
              {cluster.description && (
                <p className="text-lg text-muted-foreground">{cluster.description}</p>
              )}
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                // Could toast here
              }}
              title="Share this cluster"
            >
              <Share2 className="h-4 w-4" />
            </Button>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="rounded-lg bg-muted/50 p-4">
              <div className="text-sm text-muted-foreground mb-1">Ideas</div>
              <div className="text-2xl font-bold">{cluster.idea_count}</div>
            </div>

            <div className="rounded-lg bg-muted/50 p-4">
              <div className="text-sm text-muted-foreground mb-1">Quality</div>
              <div className="text-2xl font-bold">
                {(cluster.quality_score * 100).toFixed(0)}%
              </div>
            </div>

            <div className="rounded-lg bg-muted/50 p-4">
              <div className="text-sm text-muted-foreground mb-1">Sentiment</div>
              <div className={cn("text-xl font-bold", getSentimentColor(cluster.avg_sentiment))}>
                {getSentimentLabel(cluster.avg_sentiment)}
              </div>
            </div>

            <div className="rounded-lg bg-muted/50 p-4">
              <div className="text-sm text-muted-foreground mb-1">Trend</div>
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                <div className="text-2xl font-bold">
                  {(cluster.trend_score * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Keywords Section */}
      <div className="card border bg-card text-card-foreground shadow-sm rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold">Key Topics</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {cluster.keywords.map((keyword: string, index: number) => (
            <span
              key={index}
              className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium bg-secondary text-secondary-foreground"
            >
              {keyword}
            </span>
          ))}
        </div>
      </div>

      {/* Evidence Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold tracking-tight">Representative Ideas</h2>
          <p className="text-sm text-muted-foreground">(Top examples from this cluster)</p>
        </div>

        {cluster.evidence && cluster.evidence.length > 0 ? (
          <div className="grid gap-4">
            {cluster.evidence.map((idea: Idea) => (
              <IdeaCard key={idea.id} idea={idea} />
            ))}
          </div>
        ) : (
          <EmptyIdeasList />
        )}
      </div>

      {/* Related Clusters */}
      {cluster.related_clusters && cluster.related_clusters.length > 0 && (
        <div className="card border bg-card text-card-foreground shadow-sm rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">
            Related Opportunities
          </h2>
          <div className="grid gap-3">
            {cluster.related_clusters.map((related: RelatedCluster) => (
              <Link
                key={related.id}
                to={`/clusters/${related.id}`}
                className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div>
                  <h3 className="font-medium">{related.label}</h3>
                  {related.similarity_score && (
                    <p className="text-sm text-muted-foreground">
                      {(related.similarity_score * 100).toFixed(0)}% similar
                    </p>
                  )}
                </div>
                <div className="inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold text-muted-foreground">
                  {related.idea_count} ideas
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
