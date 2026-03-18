
import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Share2, Sparkles, Download, TrendingUp, MessageSquare, Star, Users } from 'lucide-react';

import { apiClient } from '@/services/api';
import { IdeaCard } from '@/components/IdeaCard';
import { EmptyIdeasList } from '@/components/EmptyStates';
import DataFreshness from '@/components/DataFreshness';
import { useRefreshSettings } from './Settings';
import { DetailHeaderSkeleton } from '@/components/LoadingSkeleton';
import { Button } from '@/components/ui/button';
import { cn } from '@/utils/cn';
import { Idea, RelatedCluster } from '@/types';
import { useGlobalToast } from '@/contexts/ToastContext';

export default function ClusterDetail() {
  const { enabled: autoRefresh, interval: refreshInterval } = useRefreshSettings()
  const { id } = useParams<{ id: string }>();
  const toast = useGlobalToast();

  // Fetch cluster details with auto-refresh
  const { data: cluster, isLoading, error, dataUpdatedAt, isRefetching, refetch } = useQuery({
    queryKey: ['cluster', id],
    queryFn: () => apiClient.getCluster(id!),
    enabled: !!id,
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  });

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(globalThis.location.href);
      toast.success('Link copied to clipboard!');
    } catch {
      toast.error('Could not copy link. Please copy from the address bar.');
    }
  };

  const handleExport = () => {
    if (!cluster) return;
    const data = JSON.stringify(cluster, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const safeLabel = cluster.label.replaceAll(/[^a-zA-Z0-9-_]+/g, '-').toLowerCase();
    a.download = `cluster-${cluster.id}-${safeLabel}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Cluster data exported!');
  };

  if (isLoading) {
    return (
      <div className="app-page max-w-5xl space-y-8">
        <div className="h-8 bg-muted rounded w-24 animate-pulse" />
        <DetailHeaderSkeleton />
      </div>
    );
  }

  if (error || !cluster) {
    return (
      <div className="app-page max-w-5xl">
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

  const getQualityGrade = (score: number) => {
    if (score >= 0.8) return { grade: 'A', color: 'text-grade-a', bg: 'bg-grade-a/10' };
    if (score >= 0.6) return { grade: 'B', color: 'text-grade-b', bg: 'bg-grade-b/10' };
    if (score >= 0.4) return { grade: 'C', color: 'text-grade-c', bg: 'bg-grade-c/10' };
    if (score >= 0.2) return { grade: 'D', color: 'text-grade-d', bg: 'bg-grade-d/10' };
    return { grade: 'F', color: 'text-grade-f', bg: 'bg-grade-f/10' };
  };

  const qualityInfo = getQualityGrade(cluster.quality_score);

  return (
    <div className="app-page max-w-5xl space-y-8">
      {/* Navigation Bar */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" asChild className="-ml-4 text-muted-foreground hover:text-foreground">
          <Link to="/clusters">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to All Clusters
          </Link>
        </Button>
        <div className="flex items-center gap-3">
          {dataUpdatedAt > 0 && (
            <DataFreshness
              dataUpdatedAt={dataUpdatedAt}
              isRefetching={isRefetching}
              onRefresh={() => refetch()}
            />
          )}
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="outline" size="sm" onClick={handleShare}>
            <Share2 className="mr-2 h-4 w-4" />
            Share
          </Button>
        </div>
      </div>

      {/* Header Card */}
      <div className="card overflow-hidden">
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
            <div className={cn("rounded-lg px-3 py-1.5 text-center", qualityInfo.bg)}>
              <div className={cn("text-2xl font-bold", qualityInfo.color)}>
                {qualityInfo.grade}
              </div>
              <div className="text-xs text-muted-foreground">Grade</div>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="rounded-lg bg-surface-sunken p-4">
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground mb-1">
                <Users className="h-3.5 w-3.5" />
                Ideas
              </div>
              <div className="text-2xl font-bold">{cluster.idea_count}</div>
            </div>

            <div className="rounded-lg bg-surface-sunken p-4">
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground mb-1">
                <Star className="h-3.5 w-3.5" />
                Quality
              </div>
              <div className={cn("text-2xl font-bold", qualityInfo.color)}>
                {(cluster.quality_score * 100).toFixed(0)}%
              </div>
            </div>

            <div className="rounded-lg bg-surface-sunken p-4">
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground mb-1">
                <MessageSquare className="h-3.5 w-3.5" />
                Sentiment
              </div>
              <div className={cn("text-xl font-bold", getSentimentColor(cluster.avg_sentiment))}>
                {getSentimentLabel(cluster.avg_sentiment)}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">
                Score: {cluster.avg_sentiment.toFixed(2)}
              </div>
            </div>

            <div className="rounded-lg bg-surface-sunken p-4">
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground mb-1">
                <TrendingUp className="h-3.5 w-3.5" />
                Trend
              </div>
              <div className="text-2xl font-bold text-primary">
                {(cluster.trend_score * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Keywords Section */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold">Key Topics</h2>
          <span className="text-xs text-muted-foreground ml-auto">
            {cluster.keywords.length} keywords extracted
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {cluster.keywords.map((keyword: string) => (
            <span
              key={keyword}
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
          <p className="text-sm text-muted-foreground">
            {cluster.evidence?.length || 0} top examples from this cluster
          </p>
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
        <div className="card p-6">
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
